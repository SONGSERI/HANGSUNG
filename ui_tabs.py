from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from transform import (
    ACTION_TEMPLATES,
    build_full_period_data_inventory,
    build_mounter_item_fact,
    build_data_category_summary,
    build_data_linkage_summary,
    build_data_scope_summary,
    build_data_structure_summary,
    build_process_coverage,
    build_process_flow_summary,
    build_rca_capability_summary,
    build_table_linkage_matrix,
    build_equipment_overview,
    build_lot_analysis_view,
    build_process_overview,
    build_quality_overview,
    build_rca_card_summary,
    build_rca_candidate_view,
    build_rca_drilldown_view,
    build_rca_hotspot_view,
    build_rca_loss_path_view,
    build_rca_repeat_pattern_view,
    build_time_pattern_view,
    build_rca_timeline_view,
)
from utils import _fmt_sec, _safe_div


DARK_TEMPLATE = "plotly_dark"
PRIMARY = "#1f77b4"
SECONDARY = "#ff7f0e"


def _css() -> None:
    st.markdown(
        """
        <style>
        .hero{padding:1.1rem 1.2rem;border-radius:20px;background:linear-gradient(135deg,#121826,#0d121b);border:1px solid rgba(255,255,255,.08);margin-bottom:1rem}
        .hero h1{margin:0;color:#fff;font-size:2rem}
        .hero p{margin:.4rem 0 0;color:#c7cfdb}
        .box{padding:1rem 1.05rem;border-radius:18px;background:rgba(17,21,29,.85);border:1px solid rgba(255,255,255,.07);margin:.8rem 0 1rem}
        .card{padding:.85rem .95rem;border-radius:16px;background:linear-gradient(180deg,#141b28,#0f1520);border:1px solid rgba(255,255,255,.08)}
        .card .k{color:#aab3c2;font-size:.82rem}
        .card .v{color:#fff;font-size:1.8rem;font-weight:700;margin-top:.15rem}
        .card .f{color:#97a2b3;font-size:.82rem}
        .pill{display:inline-block;padding:.24rem .55rem;border-radius:999px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);margin:.15rem .2rem 0 0;color:#e7edf6;font-size:.82rem}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, foot: str = "", accent: str = PRIMARY) -> str:
    return f'<div class="card" style="border-top:3px solid {accent}"><div class="k">{label}</div><div class="v">{value}</div><div class="f">{foot}</div></div>'


def _basis_card(label: str, value: str, foot: str = "", accent: str = PRIMARY) -> str:
    return _card(label, value, foot, accent)


def _section_header(title: str, question: str, accent: str) -> str:
    return f'''
    <div style="margin:1rem 0 .75rem 0;padding:.8rem .95rem;border-radius:16px;border:1px solid rgba(255,255,255,.08);background:linear-gradient(90deg, rgba(255,255,255,.06), rgba(255,255,255,.03));border-left:4px solid {accent};">
        <div style="font-size:1rem;font-weight:700;color:#eef2f7">{title}</div>
        <div style="margin-top:.15rem;font-size:.82rem;color:#aab3c2">{question}</div>
    </div>
    '''


def _plot_style(fig, title: str, height: int = None):
    fig.update_layout(
        template=DARK_TEMPLATE,
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#eef2f7"),
        margin=dict(l=10, r=10, t=45, b=10),
    )
    if height is not None:
        fig.update_layout(height=height)
    return fig


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _status_badge(status: str) -> str:
    mapping = {
        "개선필요": "🔴 개선필요",
        "주의": "🟠 주의",
        "정상": "🔵 정상",
        "심각": "🔴 심각",
        "생산성 손실형": "🟠 생산성 손실형",
        "품질 집중형": "🟠 품질 집중형",
        "구조적 문제": "🔴 구조적 문제",
        "공정 연계형": "🟠 공정 연계형",
        "국소 LOT 문제": "🟠 국소 LOT 문제",
        "전파 LOT 문제": "🔴 전파 LOT 문제",
        "우선 점검 LOT": "🟠 우선 점검 LOT",
        "복합 문제형": "🔴 복합 문제형",
        "정상": "🔵 정상",
        "복합 병목": "🔴 복합 병목",
        "정지 병목": "🟠 정지 병목",
        "품질 병목": "🟠 품질 병목",
        "흐름 병목": "🟠 흐름 병목",
        "안정성 문제": "🟠 안정성 문제",
        "국소 문제": "🟠 국소 문제",
    }
    return mapping.get(str(status), f"🔵 {status}")


def _confidence_label(has_direct: bool, has_proxy: bool) -> str:
    if has_direct:
        return "Actual"
    if has_proxy:
        return "Estimated"
    return "Low confidence"


def _quadrant_label(stop_val: float, defect_val: float, stop_th: float, defect_th: float) -> str:
    if stop_val >= stop_th and defect_val >= defect_th:
        return "심각"
    if stop_val >= stop_th and defect_val < defect_th:
        return "생산성 손실형"
    if stop_val < stop_th and defect_val >= defect_th:
        return "품질 집중형"
    return "정상"


def _problem_type_from_signals(stop_val: float, defect_val: float, wait_val: float, repeat_val: float, stop_th: float, defect_th: float, wait_th: float) -> str:
    if stop_val >= stop_th and defect_val >= defect_th:
        return "복합 문제형"
    if wait_val >= wait_th:
        return "공정 연계형"
    if stop_val >= stop_th and defect_val < defect_th:
        return "생산성 손실형"
    if stop_val < stop_th and defect_val >= defect_th:
        return "품질 집중형"
    if repeat_val > 0.6:
        return "구조적 문제"
    return "정상"


def _reason_action_hint(reason_text: str) -> str:
    text = str(reason_text or "").upper()
    if any(tok in text for tok in ["PICK", "FEED", "NOZZ", "REEL"]):
        return "nozzle / feeder / reel check"
    if any(tok in text for tok in ["RECOG", "VISION", "MARK", "CAM"]):
        return "vision / camera / lighting tuning"
    if any(tok in text for tok in ["PLACE", "OFFSET", "ALIGN"]):
        return "placement offset / calibration"
    if "WAIT_PRE" in text or "BWAIT" in text or "MCFWAIT" in text:
        return "upstream balance / feeder timing"
    if "WAIT_POST" in text or "RWAIT" in text or "MCRWAIT" in text:
        return "downstream congestion / buffer"
    if "TRANSFER" in text or "CNV" in text:
        return "conveyor / interlock issue"
    return "reason code refinement / detailed check"


def _classification_basis_machine(row: pd.Series, stop_th: float, defect_th: float, wait_th: float) -> str:
    stop_time = _safe_float(row.get("stop_time", 0))
    defect_rate = _safe_float(row.get("defect_rate", 0))
    wait_count = _safe_float(row.get("wait_count", 0))
    retry_rate = _safe_float(row.get("retry_rate", 0))
    if stop_time >= stop_th and defect_rate >= defect_th:
        return "정지 상위구간 + 불량 상위구간 동시 충족"
    if wait_count >= wait_th:
        return "WAIT 비중이 높아 전후공정 연계가 우선"
    if stop_time >= stop_th and defect_rate < defect_th:
        return "정지는 높고 불량은 낮아 생산성 손실형"
    if defect_rate >= defect_th and stop_time < stop_th:
        return "불량은 높고 정지는 낮아 품질 집중형"
    if retry_rate > 0:
        return "재작업 proxy가 보여 안정성 저하 가능성"
    return "기준치 내 변동으로 주의 단계"


def _classification_basis_process(row: pd.Series, output_th: float, stop_th: float, wait_th: float, ct_th: float) -> str:
    output_qty = _safe_float(row.get("output_qty", 0))
    stop_time = _safe_float(row.get("stop_time", 0))
    wait_count = _safe_float(row.get("wait_count", 0))
    ct_std = _safe_float(row.get("ct_std_sec", 0))
    fail_rate = _safe_float(row.get("fail_rate", row.get("defect_rate", 0)))
    if output_qty <= output_th and stop_time >= stop_th:
        return "출력 하락 + 정지 증가로 전형적 병목"
    if stop_time >= stop_th and fail_rate >= 0.5:
        return "정지와 불량이 함께 높아 복합 병목"
    if wait_count >= wait_th:
        return "WAIT가 높아 라인 밸런스/연계 문제"
    if fail_rate >= 0.5:
        return "불량 비중이 높아 품질 병목"
    if ct_std >= ct_th:
        return "CT 편차가 커 공정 안정성 이슈"
    return "현재 기준에서는 주의 수준"


def _classification_basis_lot(row: pd.Series, machine_th: float, process_th: float, impact_th: float) -> str:
    machine_count = _safe_float(row.get("machine_count", 0))
    process_count = _safe_float(row.get("process_count", 0))
    impact_score = _safe_float(row.get("impact_score", 0))
    stop_time = _safe_float(row.get("stop_time", 0))
    if machine_count <= machine_th and stop_time >= impact_th:
        return "특정 설비 한정 영향이 커 국소 LOT 문제"
    if process_count >= process_th:
        return "다수 공정으로 퍼져 구조적 전파 가능성"
    if impact_score >= impact_th:
        return "영향 점수가 높아 우선 점검 LOT"
    return "영향 범위가 제한된 주의 LOT"


def _status_score(value: str) -> int:
    v = str(value)
    if v == "분석 가능":
        return 2
    if v in {"직접 확인", "간접 해석"}:
        return 2 if v == "직접 확인" else 1
    if v == "✔" or v.startswith("가능"):
        return 2
    if str(value) == "제한":
        return 1
    return 0


def _status_chart(df: pd.DataFrame, label_col: str, status_col: str, title: str, color_map: Dict[str, str] = None):
    if df.empty or label_col not in df.columns or status_col not in df.columns:
        return None
    view = df[[label_col, status_col]].copy()
    view["score"] = view[status_col].astype(str).map(_status_score)
    if color_map is None:
        color_map = {
            "분석 가능": "#22c55e",
            "제한": "#f59e0b",
            "없음": "#64748b",
            "직접 확인": "#22c55e",
            "간접 해석": "#f59e0b",
            "✔": "#22c55e",
            "가능": "#22c55e",
            "불가": "#ef4444",
        }
    view["color"] = view[status_col].astype(str).map(lambda x: color_map.get(x, "#64748b"))
    fig = px.bar(
        view,
        x="score",
        y=label_col,
        orientation="h",
        text=status_col,
        color=status_col,
        color_discrete_map=color_map,
    )
    fig.update_traces(textposition="outside")
    status_values = set(view[status_col].astype(str).tolist())
    if {"분석 가능", "제한", "없음"} & status_values:
        fig.update_xaxes(range=[0, 2.3], tickmode="array", tickvals=[0, 1, 2], ticktext=["없음", "제한", "분석 가능"])
    elif any(view[status_col].astype(str).isin(["직접 확인", "간접 해석"])):
        fig.update_xaxes(range=[0, 2.3], tickmode="array", tickvals=[0, 1, 2], ticktext=["없음", "간접 해석", "직접 확인"])
    else:
        fig.update_xaxes(range=[0, 2.3], tickmode="array", tickvals=[0, 1, 2], ticktext=["없음", "제한", "가능"])
    fig.update_yaxes(categoryorder="total ascending")
    return _plot_style(fig, title)


def _top_reason_series(stop: pd.DataFrame) -> pd.Series:
    if stop.empty or "stop_like_reason" not in stop.columns:
        return pd.Series(dtype="object")
    return stop["stop_like_reason"].fillna("미상").astype(str)


def _compute_reliability_indicators(stop: pd.DataFrame) -> Dict[str, float]:
    total = len(stop)
    if total == 0:
        return {
            "total": 0,
            "aggregated_ratio": 0,
            "duplicate_ratio": 0,
            "coverage_ratio": 0,
            "approx_ratio": 0,
            "aggregated_count": 0,
            "duplicate_count": 0,
            "coverage_count": 0,
            "approx_count": 0,
        }
    aggregated_count = int(stop.get("stop_count", 0).fillna(0).gt(1).sum()) if "stop_count" in stop.columns else 0
    duplicate_count = int(stop.duplicated(subset=[c for c in ["lot_id", "machine_id", "stop_like_reason"] if c in stop.columns], keep=False).sum()) if any(c in stop.columns for c in ["lot_id", "machine_id", "stop_like_reason"]) else 0
    coverage_count = int(stop.get("join_coverage", pd.Series([0] * total)).fillna(0).gt(0).sum()) if "join_coverage" in stop.columns else 0
    approx_count = int(stop.get("approx_event", pd.Series([False] * total)).fillna(False).sum()) if "approx_event" in stop.columns else 0
    return {
        "total": total,
        "aggregated_ratio": _safe_div(aggregated_count, total),
        "duplicate_ratio": _safe_div(duplicate_count, total),
        "coverage_ratio": _safe_div(coverage_count, total),
        "approx_ratio": _safe_div(approx_count, total),
        "aggregated_count": aggregated_count,
        "duplicate_count": duplicate_count,
        "coverage_count": coverage_count,
        "approx_count": approx_count,
    }


def _loss_path_priority(stop: pd.DataFrame) -> pd.DataFrame:
    if stop.empty:
        return pd.DataFrame()
    group_cols = [c for c in ["line_id", "stage_no", "machine_id", "stop_like_reason"] if c in stop.columns]
    if len(group_cols) < 2:
        return pd.DataFrame()
    loss = (
        stop.groupby(group_cols, as_index=False)
        .agg(
            loss_time=("duration_sec", "sum"),
            event_count=("stop_count", "sum"),
        )
        .sort_values("loss_time", ascending=False)
    )
    total_loss = loss["loss_time"].sum() or 1
    loss["share"] = loss["loss_time"] / total_loss
    loss["avg_duration"] = loss.apply(lambda row: _safe_div(row["loss_time"], row["event_count"]), axis=1)
    return loss.head(5)


def _render_reliability_badge(indicators: Dict[str, float]):
    if not indicators or indicators.get("total", 0) == 0:
        return
    text = (
        f"이벤트형/누적형(추정): stop_count>1 {indicators['aggregated_ratio'] * 100:.1f}% "
        f"(n={indicators['aggregated_count']}/{indicators['total']}) · "
        f"중복 {indicators['duplicate_ratio'] * 100:.1f}% (n={indicators['duplicate_count']}) · "
        f"FILE coverage {indicators['coverage_ratio'] * 100:.1f}% (n={indicators['coverage_count']}) · "
        f"시간 근사 {indicators['approx_ratio'] * 100:.1f}% (n={indicators['approx_count']})"
    )
    st.markdown(
        f"""
        <div style='padding:8px 12px;border-radius:14px;background:#121826;color:#cfcfcf;font-size:12px;margin:0 0 .8rem 0;'>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _quality_status(null_ratio: float) -> str:
    if null_ratio <= 0.05:
        return "정상"
    if null_ratio <= 0.20:
        return "부분 사용 가능"
    return "제한적 분석"


def _quality_color(status: str) -> str:
    return {
        "정상": "#0f9d58",
        "부분 사용 가능": "#f5b642",
        "제한적 분석": "#ef553b",
    }.get(status, "#97a2b3")


def _non_empty_options(series_list: List[pd.Series], fallback: str = "전체") -> List[str]:
    values: List[str] = []
    for series in series_list:
        if series is None or series.empty:
            continue
        values.extend([str(v) for v in series.dropna().astype(str).tolist() if str(v) != ""])
    deduped = sorted(set(values))
    return [fallback] + deduped if deduped else [fallback]


def _apply_selection(df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if filters.get("line") and filters["line"] != "전체" and "line_id" in out.columns:
        out = out[out["line_id"].astype(str) == filters["line"]]
    if filters.get("stage") and filters["stage"] != "전체" and "stage_no" in out.columns:
        out = out[out["stage_no"].astype(str) == filters["stage"]]
    if filters.get("machine") and filters["machine"] != "전체" and "machine_id" in out.columns:
        out = out[out["machine_id"].astype(str) == filters["machine"]]
    if filters.get("lot") and filters["lot"] != "전체" and "lot_id" in out.columns:
        out = out[out["lot_id"].astype(str) == filters["lot"]]
    if filters.get("model") and filters["model"] != "전체" and "model_label" in out.columns:
        out = out[out["model_label"].astype(str) == filters["model"]]
    defect = filters.get("defect")
    if defect and defect != "전체":
        mask = pd.Series(False, index=out.index)
        if "quality_flag" in out.columns:
            mask = mask | out["quality_flag"].astype(str).eq(defect)
        if "result_primary" in out.columns:
            mask = mask | out["result_primary"].astype(str).eq(defect)
        if "cause_detail" in out.columns:
            mask = mask | out["cause_detail"].astype(str).eq(defect)
        out = out[mask] if mask.any() else out.iloc[0:0]
    return out


def _build_filter_panel(clean: Dict[str, pd.DataFrame], prefix: str) -> Dict[str, str]:
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame())
    stop = clean.get("vw_stop_event_fact", pd.DataFrame())
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame())
    tag = clean.get("vw_tag_event_fact", pd.DataFrame())
    machine_series = []
    lot_series = []
    model_series = []
    line_series = []
    stage_series = []
    defect_series = []
    for df in [shop, stop, insp, tag]:
        if not df.empty:
            if "machine_id" in df.columns:
                machine_series.append(df["machine_id"])
            if "lot_id" in df.columns:
                lot_series.append(df["lot_id"])
            if "model_label" in df.columns:
                model_series.append(df["model_label"])
            if "line_id" in df.columns:
                line_series.append(df["line_id"])
            if "stage_no" in df.columns:
                stage_series.append(df["stage_no"].astype(str))
            if "quality_flag" in df.columns:
                defect_series.append(df["quality_flag"])
            if "result_primary" in df.columns:
                defect_series.append(df["result_primary"])
            if "stop_like_reason" in df.columns:
                defect_series.append(df["stop_like_reason"])
            if "cause_detail" in df.columns:
                defect_series.append(df["cause_detail"])
    cols = st.columns(6)
    options = {
        "line": _non_empty_options(line_series),
        "stage": _non_empty_options(stage_series),
        "machine": _non_empty_options(machine_series),
        "lot": _non_empty_options(lot_series),
        "model": _non_empty_options(model_series),
        "defect": _non_empty_options(defect_series),
    }
    labels = {
        "line": "line",
        "stage": "stage",
        "machine": "machine_id",
        "lot": "lot_id",
        "model": "model_label",
        "defect": "defect/result_flag",
    }
    filters = {}
    for col, key in zip(cols, ["line", "stage", "machine", "lot", "model", "defect"]):
        with col:
            filters[key] = st.selectbox(labels[key], options[key], key=f"{prefix}_{key}_filter")
    return filters


def _render_card_row(card_df: pd.DataFrame) -> None:
    if card_df.empty:
        st.info("카드 요약을 만들 수 있는 데이터가 충분하지 않습니다.")
        return
    order = {"when": 0, "where": 1, "how_much": 2, "repeat": 3, "what": 4}
    view = card_df.copy()
    view["_order"] = view["card_key"].map(order).fillna(99)
    view = view.sort_values("_order")
    cols = st.columns(min(5, len(view)))
    title_map = {"when": "언제", "where": "어디", "how_much": "얼마나", "repeat": "반복", "what": "무엇"}
    for col, (_, row) in zip(cols, view.iterrows()):
        with col:
            st.markdown(_card(title_map.get(str(row.get("card_key", "-")), str(row.get("card_key", "-")).upper()), str(row.get("headline_value", "-")), f"{row.get('sub_label', '')} · {row.get('evidence', '')}", PRIMARY), unsafe_allow_html=True)


def _field_null_ratio(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 1.0
    return _safe_div(df[col].isna().sum(), len(df))


def _build_quality_summary(clean: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame())
    stop = clean.get("vw_stop_event_fact", pd.DataFrame())
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame())
    tag = clean.get("vw_tag_event_fact", pd.DataFrame())
    rows = []

    def add_row(label: str, ratio: float, meaning: str):
        rows.append({
            "항목": label,
            "null율": float(ratio),
            "상태": _quality_status(float(ratio)),
            "해석": meaning,
        })

    if not stop.empty:
        add_row("timestamp", _field_null_ratio(stop, "event_ts"), "정지/알람 시각")
        add_row("설비 식별자", _field_null_ratio(stop, "machine_id"), "정지 대상 설비")
        add_row("정지사유", _field_null_ratio(stop, "stop_like_reason"), "정지 원인 분류")
        add_row("runtime/downtime", _field_null_ratio(stop, "duration_sec"), "정지시간/가동손실")
        add_row("알람", _field_null_ratio(stop, "stop_like_reason"), "알람/정지 이벤트")
    elif not tag.empty:
        add_row("timestamp", _field_null_ratio(tag, "event_ts"), "태그 이벤트 시각")
        add_row("설비 식별자", _field_null_ratio(tag, "machine_id"), "장비별 추적 키")
        add_row("runtime/downtime", _field_null_ratio(tag, "tag_value_num"), "wait/run proxy")
        add_row("알람", _field_null_ratio(tag, "tag_metric"), "태그 기반 이상 신호")
    elif not shop.empty:
        add_row("timestamp", _field_null_ratio(shop, "event_ts"), "공정 이벤트 시각")
        add_row("설비 식별자", _field_null_ratio(shop, "machine_id"), "공정 장비 식별")
        add_row("runtime/downtime", _field_null_ratio(shop, "output_qty"), "산출량 proxy")
        add_row("알람", _field_null_ratio(shop, "result_primary"), "검사 결과 proxy")
    if not insp.empty:
        add_row("검사 timestamp", _field_null_ratio(insp, "event_ts"), "검사/품질 이벤트")
        add_row("모델", _field_null_ratio(insp, "model_label"), "품질 분석 기준")

    return pd.DataFrame(rows)


def _quality_summary(clean: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    stop = clean.get("vw_stop_event_fact", pd.DataFrame())
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame())
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame())
    rows = []
    if not shop.empty:
        for label in ["timestamp", "설비 식별자", "model"]:
            rows.append({"항목": label, "null율": 0.0, "상태": "정상", "해석": "커버됨"})
    if not stop.empty:
        rows.append({"항목": "정지사유", "null율": _safe_div(stop["stop_like_reason"].isna().sum(), len(stop)), "상태": "정상" if _safe_div(stop["stop_like_reason"].isna().sum(), len(stop)) <= 0.05 else "주의", "해석": "정지 / 알람 분석"})
        rows.append({"항목": "timestamp", "null율": _safe_div(stop["event_ts"].isna().sum(), len(stop)), "상태": "정상" if _safe_div(stop["event_ts"].isna().sum(), len(stop)) <= 0.05 else "주의", "해석": "이벤트 시각"})
    if not insp.empty:
        rows.append({"항목": "inspection", "null율": _safe_div(insp["event_ts"].isna().sum(), len(insp)), "상태": "정상" if _safe_div(insp["event_ts"].isna().sum(), len(insp)) <= 0.05 else "주의", "해석": "검사 시각"})
    return pd.DataFrame(rows)


def _pickup_item_summary(item: pd.DataFrame) -> pd.DataFrame:
    if item.empty or "item_key" not in item.columns:
        return pd.DataFrame()
    view = item.copy()
    view["item_key"] = view["item_key"].fillna("").astype(str)
    view["item_group"] = view["item_group"].fillna("").astype(str) if "item_group" in view.columns else ""
    pickup_mask = view["item_key"].str.contains("PICK|NOZZ|FEED|REEL|VAC|SUCTION|SUCK", case=False, na=False)
    if "item_group" in view.columns:
        pickup_mask = pickup_mask | view["item_group"].str.contains("PICK|FEED|NOZZ|REEL", case=False, na=False)
    pickup = view[pickup_mask].copy()
    if pickup.empty:
        return pd.DataFrame()
    source = pickup
    out = source.groupby(["item_group", "item_key"], as_index=False).agg(
        건수=("item_key", "size"),
        설비수=("machine_id", "nunique") if "machine_id" in source.columns else ("item_key", "size"),
        공정수=("stage_no", "nunique") if "stage_no" in source.columns else ("item_key", "size"),
        LOT수=("lot_id", "nunique") if "lot_id" in source.columns else ("item_key", "size"),
    )
    out = out.sort_values(["건수", "설비수", "공정수"], ascending=[False, False, False]).head(10).reset_index(drop=True)
    out["비고"] = "pickup 관련 항목"
    return out


def _core_category_status(raw: Dict[str, pd.DataFrame], item: pd.DataFrame) -> pd.DataFrame:
    frames = [item] + [df for df in raw.values() if isinstance(df, pd.DataFrame)]

    def _present_cols(aliases: List[str]) -> List[str]:
        found = []
        for alias in aliases:
            alias_low = str(alias).lower()
            for df in frames:
                if df.empty:
                    continue
                for col in df.columns:
                    col_low = str(col).lower()
                    if col_low == alias_low or col_low.endswith(f"_{alias_low}") or alias_low in col_low:
                        found.append(str(col))
        return sorted(set(found))

    specs = [
        {
            "카테고리": "PRODUCTION",
            "설명": "생산 실적",
            "핵심": ["Actual", "Output", "Prod", "Mount", "Pickup", "Board"],
            "보조": ["Machine", "Stage", "Lane", "LotName"],
            "note": "실제 생산량과 기본 흐름을 확인하는 축",
            "aliases": {
                "Actual": ["actual"],
                "Output": ["output", "output_qty"],
                "Prod": ["prod"],
                "Mount": ["mount"],
                "Pickup": ["pickup"],
                "Board": ["board"],
                "Machine": ["machine_id", "mach_cd"],
                "Stage": ["stage_no", "stage"],
                "Lane": ["line_id", "lane"],
                "LotName": ["lot_nm", "lot_id", "lot_name"],
            },
        },
        {
            "카테고리": "QUALITY",
            "설명": "불량 / 미스",
            "핵심": ["PMiss", "DMiss", "HMiss", "MMiss", "RMiss", "RetryBoard"],
            "보조": ["BadParts", "BadBoard", "LotRetryBoard", "Result"],
            "note": "미스/불량/재작업을 확인하는 축",
            "aliases": {
                "PMiss": ["pmiss"],
                "DMiss": ["dmiss"],
                "HMiss": ["hmiss"],
                "MMiss": ["mmiss"],
                "RMiss": ["rmiss"],
                "RetryBoard": ["retryboard", "retry_board"],
                "BadParts": ["badparts"],
                "BadBoard": ["badboard"],
                "LotRetryBoard": ["lotretryboard"],
                "Result": ["result"],
            },
        },
        {
            "카테고리": "EQUIPMENT_STATE",
            "설명": "설비 상태",
            "핵심": ["TotalStop", "PowerON", "Bwait", "Pwait", "Cwait", "CnvStop"],
            "보조": ["Idle", "PRDStop", "SCStop", "SCEStop"],
            "note": "정지/대기/가동 상태를 확인하는 축",
            "aliases": {
                "TotalStop": ["totalstop"],
                "PowerON": ["poweron"],
                "Bwait": ["bwait"],
                "Pwait": ["pwait"],
                "Cwait": ["cwait"],
                "CnvStop": ["cnvstop"],
                "Idle": ["idle"],
                "PRDStop": ["prdstop"],
                "SCStop": ["scstop"],
                "SCEStop": ["scestop"],
            },
        },
        {
            "카테고리": "TIME_METRIC",
            "설명": "시간",
            "핵심": ["CTime1", "CTime2", "CTime3", "Date"],
            "보조": ["TDispense", "TPriming", "Diff"],
            "note": "사이클/공정 시간 변동을 보는 축",
            "aliases": {
                "CTime1": ["ctime1"],
                "CTime2": ["ctime2"],
                "CTime3": ["ctime3"],
                "TDispense": ["tdispense"],
                "TPriming": ["tpriming"],
                "Diff": ["diff"],
                "Date": ["event_ts", "file_dt", "make_dt", "date"],
            },
        },
        {
            "카테고리": "COMPONENT",
            "설명": "부품 / 자재",
            "핵심": ["PartsName", "ReelID", "NozzleName", "Vendor"],
            "보조": ["UseF", "UseR", "FAdd", "FSAdd", "NCAdd", "NHAdd"],
            "note": "자재/노즐/릴 연계 여부를 보는 축",
            "aliases": {
                "PartsName": ["partsname"],
                "ReelID": ["reelid"],
                "NozzleName": ["nozzlename"],
                "Vendor": ["vendor"],
                "UseF": ["usef"],
                "UseR": ["user"],  # fallback lower-case match on useR
                "FAdd": ["fadd"],
                "FSAdd": ["fsadd"],
                "NCAdd": ["ncadd"],
                "NHAdd": ["nhadd"],
            },
        },
        {
            "카테고리": "TRACEABILITY",
            "설명": "추적",
            "핵심": ["Serial", "TGSerial", "BLKSerial", "BcrStatus", "Code", "MJSID"],
            "보조": ["SerialStatus", "BLKCode"],
            "note": "시리얼/바코드/시스템 추적 축",
            "aliases": {
                "Serial": ["serial"],
                "TGSerial": ["tgserial"],
                "BLKSerial": ["blkserial"],
                "SerialStatus": ["serialstatus"],
                "BcrStatus": ["bcrstatus"],
                "Code": ["code"],
                "BLKCode": ["blkcode"],
                "MJSID": ["mjsid"],
            },
        },
        {
            "카테고리": "IDENTITY",
            "설명": "기준 정보",
            "핵심": ["Machine", "Stage", "Lane", "LName", "LotName", "ProductID", "PlanID", "Rev"],
            "보조": ["MasterWO", "SubWO"],
            "note": "설비/공정/LOT/제품 기준 축",
            "aliases": {
                "Machine": ["machine_id", "mach_cd", "machine"],
                "Stage": ["stage_no", "stage"],
                "Lane": ["line_id", "lane"],
                "LName": ["lname", "line_name"],
                "LotName": ["lot_nm", "lot_name", "lot_id"],
                "ProductID": ["productid", "model_label", "model", "pcbmodel"],
                "PlanID": ["planid"],
                "MasterWO": ["masterwo"],
                "SubWO": ["subwo"],
                "Rev": ["rev"],
            },
        },
        {
            "카테고리": "OPERATION_META",
            "설명": "운영",
            "핵심": ["Author", "AuthorType", "Comment", "Change", "DataEdit", "Simulation", "Version"],
            "보조": ["UnitAdjust", "Format"],
            "note": "운영 이력/수정/버전 관리 축",
            "aliases": {
                "Author": ["author"],
                "AuthorType": ["authortype"],
                "Comment": ["comment"],
                "Change": ["change"],
                "DataEdit": ["dataedit"],
                "UnitAdjust": ["unitadjust"],
                "Simulation": ["simulation"],
                "Format": ["format"],
                "Version": ["version"],
            },
        },
    ]

    rows = []
    for spec in specs:
        matched_core = []
        matched_proxy = []
        rep_cols = []
        for item_name in spec["핵심"]:
            cols = _present_cols(spec["aliases"].get(item_name, [item_name]))
            if cols:
                matched_core.append(item_name)
                rep_cols.extend(cols[:2])
        for item_name in spec["보조"]:
            cols = _present_cols(spec["aliases"].get(item_name, [item_name]))
            if cols:
                matched_proxy.append(item_name)
                rep_cols.extend(cols[:2])
        total = len(spec["핵심"]) + len(spec["보조"])
        hit = len(matched_core) + len(matched_proxy)
        if hit == 0:
            status = "없음"
        elif len(matched_core) >= max(3, len(spec["핵심"]) // 2):
            status = "충분"
        else:
            status = "부분"
        rows.append({
            "카테고리": spec["카테고리"],
            "설명": spec["설명"],
            "핵심 확인 항목": " / ".join(spec["핵심"]),
            "현재 상태": status,
            "확인된 항목": " / ".join(matched_core + matched_proxy) if (matched_core or matched_proxy) else "-",
            "대표 컬럼": ", ".join(sorted(set(rep_cols))) if rep_cols else "-",
            "판단": spec["note"],
            "핵심 커버리지": f"{hit}/{total}",
        })
    return pd.DataFrame(rows)


def _problem_type_guide() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "문제유형": "생산성 손실형",
            "설명": "정지는 많지만 불량은 상대적으로 낮은 상태",
            "판정 기준": "stop/대기 손실이 output 대비 높음",
            "개선 포인트": "라인 밸런스, 보급 타이밍, 전환 구간 점검",
        },
        {
            "문제유형": "품질 문제형",
            "설명": "불량/미스가 높지만 정지는 상대적으로 낮은 상태",
            "판정 기준": "defect/retry가 output 대비 높음",
            "개선 포인트": "노즐, 피더, 비전, 헤드, 자재 조건 점검",
        },
        {
            "문제유형": "복합 문제형",
            "설명": "정지와 불량이 함께 높은 상태",
            "판정 기준": "stop_time과 defect_rate가 동시에 상위권",
            "개선 포인트": "설비 조건과 공정 조건을 동시에 조치",
        },
        {
            "문제유형": "정지 병목",
            "설명": "특정 공정의 정지가 흐름 전체를 막는 상태",
            "판정 기준": "output 저하 + stop_time 상위 + wait 동반",
            "개선 포인트": "전후 stage 연결, 전환 시간, 보급 타이밍 점검",
        },
        {
            "문제유형": "흐름 병목",
            "설명": "정지보다는 대기/연계 불균형이 주된 상태",
            "판정 기준": "wait 비중이 높고 output 편차가 큼",
            "개선 포인트": "upstream/downstream buffer와 라인 밸런스 점검",
        },
        {
            "문제유형": "국소 LOT",
            "설명": "특정 LOT에만 영향이 집중된 상태",
            "판정 기준": "machine_count, stage_count가 낮음",
            "개선 포인트": "해당 LOT의 자재/작업 조건/trace 우선 확인",
        },
        {
            "문제유형": "전파 LOT",
            "설명": "한 LOT의 영향이 여러 설비/공정으로 퍼진 상태",
            "판정 기준": "machine_count 또는 stage_count가 넓음",
            "개선 포인트": "대표 설비와 대표 공정을 먼저 잡고 확산 차단",
        },
        {
            "문제유형": "주의",
            "설명": "현재는 경계 수준이지만 추적이 필요한 상태",
            "판정 기준": "절대/상대 지표가 기준선 부근",
            "개선 포인트": "추이 모니터링과 반복성 확인",
        },
    ])


def _build_structure_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    if inventory.empty:
        return pd.DataFrame()
    view = inventory.copy()

    def _structure_type(row: pd.Series) -> str:
        table_name = str(row.get("table_name", "")).lower()
        if table_name == "fa_26_34_mounter_dtl":
            if int(row.get("item_distinct", 0) or 0) > 0:
                return "정형 + ITEM 정규화"
            return "정형"
        if bool(row.get("has_quality_cols", False)) or bool(row.get("has_result_cols", False)):
            return "검사/결과형"
        if bool(row.get("has_join_cols", False)):
            return "이벤트형"
        return "기초 raw"

    view["structure_type"] = view.apply(_structure_type, axis=1)
    view["analysis_ready"] = np.where(
        view["has_join_cols"].fillna(False) | view["has_result_cols"].fillna(False) | view["has_quality_cols"].fillna(False),
        "가능",
        "제한",
    )
    show_cols = [c for c in [
        "table_name",
        "structure_type",
        "analysis_ready",
        "has_join_cols",
        "has_result_cols",
        "has_quality_cols",
        "item_distinct",
        "item_groups",
        "item_numeric_ratio",
    ] if c in view.columns]
    if not show_cols:
        return pd.DataFrame()
    return view[show_cols].sort_values(["analysis_ready", "table_name"], ascending=[False, True])


def render_summary(raw: Dict[str, pd.DataFrame], clean: Dict[str, pd.DataFrame], marts: Dict[str, pd.DataFrame], sample_mode: bool):
    item = clean.get("vw_mounter_item_fact", pd.DataFrame()).copy()
    summary = marts.get("vw_mounter_summary", pd.DataFrame()).copy()
    equipment = marts.get("vw_equipment_overview", pd.DataFrame()).copy()
    process = marts.get("vw_process_overview", pd.DataFrame()).copy()
    lot = marts.get("vw_lot_analysis", pd.DataFrame()).copy()
    time_view = marts.get("vw_time_pattern_view", pd.DataFrame()).copy()
    priority = marts.get("vw_priority_view", pd.DataFrame()).copy()
    core_status = _core_category_status(raw, item)
    problem_guide = _problem_type_guide()

    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("### 1. 데이터 요약")
    st.caption("현재 화면은 mounter 테이블만 사용한 생산 집계 요약입니다.")
    source = raw.get("_meta", {}).get("source", "unknown") if isinstance(raw.get("_meta", {}), dict) else "unknown"
    st.info(f"데이터 소스: `{source}` · 분석 대상은 `fa_26_34_mounter_dtl` 중심으로만 구성됩니다.")

    if summary.empty:
        st.info("요약 데이터를 만들 수 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    period_start = pd.to_datetime(item["event_ts"], errors="coerce").min() if not item.empty and "event_ts" in item.columns else pd.NaT
    period_end = pd.to_datetime(item["event_ts"], errors="coerce").max() if not item.empty and "event_ts" in item.columns else pd.NaT
    period_text = f"{period_start:%Y-%m-%d} ~ {period_end:%Y-%m-%d}" if pd.notna(period_start) and pd.notna(period_end) else "-"

    card_cols = st.columns(6)
    card_map = {str(r["항목"]): r for _, r in summary.iterrows()}
    cards = [
        ("총 생산기록", card_map.get("총 생산기록", {}).get("값", "-"), "mounter 행 수"),
        ("총 출력", card_map.get("총 출력", {}).get("값", "-"), "output 합계"),
        ("설비 수", card_map.get("설비 수", {}).get("값", "-"), "machine_id distinct"),
        ("공정 수", card_map.get("공정 수", {}).get("값", "-"), "line/stage distinct"),
        ("LOT 수", card_map.get("LOT 수", {}).get("값", "-"), "lot_id distinct"),
        ("활성 일수", card_map.get("활성 일수", {}).get("값", "-"), period_text),
    ]
    for col, (label, value, foot) in zip(card_cols, cards):
        with col:
            st.markdown(_card(label, str(value), foot), unsafe_allow_html=True)

    st.markdown("#### 요약표")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    if not priority.empty:
        st.markdown("#### 우선 점검 대상")
        st.dataframe(priority.head(5), use_container_width=True, hide_index=True)

    st.markdown("#### 핵심 데이터 카테고리 현황")
    if not core_status.empty:
        st.dataframe(core_status, use_container_width=True, hide_index=True)
    else:
        st.info("핵심 데이터 카테고리 요약을 만들 수 없습니다.")

    st.markdown("#### 문제유형 설명표")
    st.dataframe(problem_guide, use_container_width=True, hide_index=True)

    st.markdown("#### 데이터 해석 가이드")
    st.markdown("- 설비는 출력이 낮고 cycle 편차가 큰 곳부터 봅니다.")
    st.markdown("- 공정은 출력이 낮고 병목 점수가 높은 stage부터 봅니다.")
    st.markdown("- LOT는 다수 설비/공정으로 퍼지는지 먼저 확인합니다.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_equipment(clean: Dict[str, pd.DataFrame], marts: Dict[str, pd.DataFrame]):
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame())
    stop = clean.get("vw_stop_event_fact", pd.DataFrame())
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame())
    tag = clean.get("vw_tag_event_fact", pd.DataFrame())
    comp = clean.get("vw_component_error_fact", pd.DataFrame())
    filters = _build_filter_panel(clean, "equipment")
    filtered_clean = {
        **clean,
        "vw_shopfloor_event_fact": _apply_selection(shop, filters),
        "vw_stop_event_fact": _apply_selection(stop, filters),
        "vw_inspection_event_fact": _apply_selection(insp, filters),
        "vw_tag_event_fact": _apply_selection(tag, filters),
        "vw_component_error_fact": _apply_selection(comp, filters),
    }
    equipment = build_equipment_overview(filtered_clean)
    process = build_process_overview(filtered_clean)
    process_all = build_process_overview(clean)
    lot = build_lot_analysis_view(filtered_clean)
    filtered_stop = filtered_clean.get("vw_stop_event_fact", pd.DataFrame())
    filtered_tag = filtered_clean.get("vw_tag_event_fact", pd.DataFrame())
    filtered_shop = filtered_clean.get("vw_shopfloor_event_fact", pd.DataFrame())

    def _safe_float(v, default: float = 0.0) -> float:
        try:
            if pd.isna(v):
                return default
            return float(v)
        except Exception:
            return default

    def _fmt_pct(v) -> str:
        return f"{_safe_float(v) * 100:.1f}%"

    def _fmt_stop(v) -> str:
        return _fmt_sec(_safe_float(v))

    def _label_machine(row: pd.Series) -> str:
        machine_id = str(row.get("machine_id", "-"))
        line_id = str(row.get("line_id", "-"))
        stage_no = str(row.get("stage_no", "-"))
        stop_text = _fmt_stop(row.get("stop_time", 0))
        defect_text = _fmt_pct(row.get("defect_rate", 0))
        mtbf_text = _fmt_stop(row.get("mtbf_sec", 0))
        mttr_text = _fmt_stop(row.get("mttr_sec", 0))
        outlier_text = " · 이상치" if bool(row.get("is_outlier", False)) else ""
        return f"{machine_id} · line {line_id} · stage {stage_no} · 정지 {stop_text} · 불량률 {defect_text} · MTBF {mtbf_text} · MTTR {mttr_text}{outlier_text}"

    def _label_process(row: pd.Series) -> str:
        name = str(row.get("process_display", row.get("process_name", "-")))
        line_id = str(row.get("line_id", "-"))
        stage_no = str(row.get("stage_no", "-"))
        output_status = str(row.get("output_status", "데이터 있음"))
        stop_status = str(row.get("stop_status", "데이터 있음"))
        defect_status = str(row.get("defect_status", "데이터 있음"))
        output_qty = f"{_safe_float(row.get('output_qty', 0), 0):.0f}" if output_status == "데이터 있음" else "데이터 없음"
        stop_text = _fmt_stop(row.get("stop_time", 0)) if stop_status == "데이터 있음" else "데이터 없음"
        defect_text = _fmt_pct(row.get("fail_rate", row.get("defect_rate", 0))) if defect_status == "데이터 있음" else "데이터 없음"
        hint = str(row.get("bottleneck_hint", "평균권"))
        status = str(row.get("data_status", "데이터 있음"))
        status_text = "" if status == "데이터 있음" else f" · {status}"
        return f"{name} · line {line_id} · stage {stage_no} · output {output_qty} · 정지 {stop_text} · 불량률 {defect_text} · {hint}{status_text}"

    def _label_lot(row: pd.Series) -> str:
        lot_id = str(row.get("lot_id", "-"))
        model_label = str(row.get("model_label", "-"))
        impact_text = f"{_safe_float(row.get('impact_score', 0), 0):.1f}"
        stop_text = _fmt_stop(row.get("stop_time", 0))
        defect_text = _fmt_pct(row.get("fail_rate", 0))
        return f"{lot_id} · model {model_label} · 영향도 {impact_text} · 정지 {stop_text} · 불량률 {defect_text}"

    def _display_process_name(value: object) -> str:
        name = str(value or "-").strip()
        mapping = {
            "mounter": "Mounter",
            "spi": "SPI",
            "aoi_14": "AOI",
            "aoi_42": "AOI",
            "moi": "MOI",
            "marking": "Marking",
            "stop": "Stop",
            "inspection": "Inspection",
            "mounter_tag": "Mounter Tag",
        }
        return mapping.get(name.lower(), name)

    def _process_analysis_basis(row: pd.Series) -> str:
        process_name = str(row.get("process_name", "")).lower()
        process_display = str(row.get("process_display", row.get("process_name", "-"))).upper()
        if process_name == "spi" or process_display == "SPI":
            return "시간 + 설비 + 결과"
        if process_name in {"aoi_14", "aoi_42", "aoi"} or process_display == "AOI":
            return "시간 + 설비 + 결과"
        if process_name in {"moi", "aoi_post"} or process_display in {"MOI", "AOI_POST"}:
            return "최종검사 결과 + 설비"
        if process_name == "mounter" or process_display == "MOUNTER":
            return "설비 + stage + LOT"
        if process_name == "printer" or process_display == "PRINTER":
            return "공정 이벤트 + 산출"
        if process_name == "reflow" or process_display == "REFLOW":
            return "현재 데이터 없음"
        return "공정별 기준 별도"

    def _process_analysis_content(row: pd.Series) -> str:
        process_name = str(row.get("process_name", "")).lower()
        process_display = str(row.get("process_display", row.get("process_name", "-"))).upper()
        if process_name == "spi" or process_display == "SPI":
            return "machineresult/reviewresult, panelbarcode/model, line/lane/time"
        if process_name in {"aoi_14", "aoi_42", "aoi"} or process_display == "AOI":
            return "machineresult/reviewresult, barcode/panelbarcode, line/lane/time"
        if process_name in {"moi", "aoi_post"} or process_display in {"MOI", "AOI_POST"}:
            return "최종검사 result, barcode/panelbarcode, line/time"
        if process_name == "mounter" or process_display == "MOUNTER":
            return "output, stop, lot, item, tag event"
        if process_name == "printer" or process_display == "PRINTER":
            return "현재 raw는 marking proxy 중심, 시간/라인/LOT 흐름"
        if process_name == "reflow" or process_display == "REFLOW":
            return "현재 raw 데이터 없음"
        return "공정별 분석 내용 별도"

    def _process_analysis_status(row: pd.Series) -> str:
        process_name = str(row.get("process_name", "")).lower()
        process_display = str(row.get("process_display", row.get("process_name", "-"))).upper()
        if process_name == "reflow" or process_display == "REFLOW":
            return "없음"
        if process_name == "printer" or process_display == "PRINTER":
            return "제한"
        if process_name == "mounter" or process_display == "MOUNTER":
            return "분석 가능"
        if process_name in {"spi", "aoi_14", "aoi_42", "aoi", "moi", "aoi_post"} or process_display in {"SPI", "AOI", "MOI", "AOI_POST"}:
            return "분석 가능" if row.get("output_status", "") == "데이터 있음" or row.get("defect_status", "") == "데이터 있음" else "제한"
        return "제한"

    def _build_process_analysis_table(process_df: pd.DataFrame) -> pd.DataFrame:
        if process_df.empty:
            return pd.DataFrame()
        base = process_df.copy()
        if "process_name" not in base.columns:
            return pd.DataFrame()
        rows = []
        analysis_map = {
            "Printer": {
                "분석축": "공정 이벤트 / 산출",
                "분석내용": "marking proxy, 시간대 분포, line 흐름",
                "판정기준": "현재 raw는 제한적",
            },
            "SPI": {
                "분석축": "검사결과 / 불량률",
                "분석내용": "machineresult/reviewresult, inspect_count, fail_rate, line/stage",
                "판정기준": "inspect_count와 fail_rate가 있으면 분석 가능",
            },
            "Mounter": {
                "분석축": "정지 / 출력 / LOT",
                "분석내용": "output_qty, stop_time, stop_count, lot_count, machine_order",
                "판정기준": "stop_time과 output_qty가 모두 있어야 해석 가능",
            },
            "AOI": {
                "분석축": "검사결과 / 품질",
                "분석내용": "inspect_count, fail_rate, line/stage, model/bcode proxy",
                "판정기준": "inspection result와 fail signal 기반",
            },
            "AOI_POST": {
                "분석축": "최종검사 / 재작업",
                "분석내용": "final inspection, fail_rate, barcode/panelbarcode, line",
                "판정기준": "MOI/최종검사 데이터가 있어야 분석 가능",
            },
            "Reflow": {
                "분석축": "현재 데이터 없음",
                "분석내용": "-",
                "판정기준": "원천 테이블 부재",
            },
        }
        for _, row in base.iterrows():
            pname = str(row.get("process_name", ""))
            spec = analysis_map.get(pname, {"분석축": "공정별 기준 별도", "분석내용": "-", "판정기준": "기준 미정"})
            stop_time = _safe_float(row.get("stop_time", 0))
            output_qty = _safe_float(row.get("output_qty", 0))
            fail_rate = _safe_float(row.get("fail_rate", 0))
            inspect_count = _safe_float(row.get("inspect_count", 0))
            if pname == "Printer":
                status = "제한" if output_qty <= 0 else "분석 가능"
                headline = "marking proxy 중심"
            elif pname == "SPI":
                status = "분석 가능" if inspect_count > 0 else "제한"
                headline = "검사 결과 중심"
            elif pname == "Mounter":
                status = "분석 가능" if stop_time > 0 or output_qty > 0 else "제한"
                headline = "정지/출력 중심"
            elif pname == "AOI":
                status = "분석 가능" if inspect_count > 0 or fail_rate > 0 else "제한"
                headline = "검사/품질 중심"
            elif pname == "AOI_POST":
                status = "분석 가능" if inspect_count > 0 or fail_rate > 0 else "제한"
                headline = "최종검사 중심"
            elif pname == "Reflow":
                status = "없음"
                headline = "데이터 없음"
            else:
                status = "제한"
                headline = "미정"
            rows.append({
                "공정": row.get("process_display", pname.lower()),
                "분석 상태": status,
                "핵심 초점": headline,
                "분석축": spec["분석축"],
                "분석내용": spec["분석내용"],
                "판정기준": spec["판정기준"],
                "output_qty": output_qty,
                "stop_time": stop_time,
                "inspect_count": inspect_count,
                "fail_rate": fail_rate,
                "line_id": row.get("line_id", "-"),
                "stage_no": row.get("stage_no", "-"),
            })
        out = pd.DataFrame(rows)
        if not out.empty:
            order = {name.lower(): i for i, name in enumerate(["Printer", "SPI", "Mounter", "AOI", "Reflow", "AOI_POST"])}
            out["_order"] = out["공정"].astype(str).str.lower().map(order).fillna(99)
            out = out.sort_values("_order").drop(columns=["_order"])
        return out

    machine_focus = equipment.copy()
    if not machine_focus.empty:
        machine_focus = machine_focus.sort_values(
            ["stop_time", "defect_rate", "event_density"],
            ascending=[False, False, False],
            kind="mergesort",
        )
    process_focus = process[process["scope"].eq("process")] if not process.empty and "scope" in process.columns else process.copy()
    process_universe = process_all[process_all["scope"].eq("process")] if not process_all.empty and "scope" in process_all.columns else process_all.copy()
    if process_focus.empty and not process_universe.empty:
        process_focus = process_universe.copy()
        process_focus["selection_note"] = "선택 필터 결과가 비어 전체 공정 기준으로 표시"
    else:
        process_focus["selection_note"] = ""
    if not process_focus.empty:
        process_focus["process_display"] = process_focus["process_display"].fillna(process_focus["process_name"].map(_display_process_name))
        if "stage_no" in process_focus.columns:
            process_focus["stage_no"] = process_focus["stage_no"].astype("string").fillna("-").str.strip()
        if "line_id" in process_focus.columns:
            process_focus["line_id"] = process_focus["line_id"].astype("string").fillna("-").str.strip()
        process_focus["analysis_basis"] = process_focus.apply(_process_analysis_basis, axis=1)
        for col in ["stop_time", "stop_count", "inspect_count", "fail_count", "output_qty"]:
            if col not in process_focus.columns:
                process_focus[col] = 0
            process_focus[col] = pd.to_numeric(process_focus[col], errors="coerce").fillna(0)
        process_focus["fail_rate"] = process_focus.apply(lambda r: _safe_div(r.get("fail_count", 0), r.get("inspect_count", 0)), axis=1)
        for col in ["output_status", "stop_status", "defect_status"]:
            if col not in process_focus.columns:
                process_focus[col] = "데이터 없음"
            process_focus[col] = process_focus[col].fillna("데이터 없음")
        process_focus = process_focus.sort_values(
            ["stop_time", "fail_rate", "output_qty"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        stop_q3 = pd.to_numeric(process_focus["stop_time"], errors="coerce").quantile(0.75)
        output_q1 = pd.to_numeric(process_focus["output_qty"], errors="coerce").quantile(0.25)
        defect_q3 = pd.to_numeric(process_focus["fail_rate"], errors="coerce").quantile(0.75)

        def _bottleneck_hint(row: pd.Series) -> str:
            hints = []
            if pd.notna(stop_q3) and row.get("stop_time", 0) >= stop_q3 and stop_q3 > 0:
                hints.append("정지↑")
            if pd.notna(output_q1) and row.get("output_qty", 0) <= output_q1:
                hints.append("산출↓")
            if pd.notna(defect_q3) and row.get("fail_rate", 0) >= defect_q3 and defect_q3 > 0:
                hints.append("불량↑")
            return " / ".join(hints) if hints else "평균권"

        process_focus["bottleneck_hint"] = process_focus.apply(_bottleneck_hint, axis=1)
    lot_focus = lot.copy()
    if not lot_focus.empty:
        lot_focus = lot_focus.sort_values(
            ["impact_score", "fail_rate", "stop_time"],
            ascending=[False, False, False],
            kind="mergesort",
        )
    time_view = build_time_pattern_view(filtered_clean)
    time_hour = time_view[time_view["grain"].eq("hour")].copy() if not time_view.empty and "grain" in time_view.columns else pd.DataFrame()
    time_shift = time_view[time_view["grain"].eq("shift")].copy() if not time_view.empty and "grain" in time_view.columns else pd.DataFrame()

    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("### 설비/공정 분석")
    st.caption("이 탭은 RCA가 아니라 문제 위치를 찾는 화면입니다. 설비는 어디가 문제인지, 공정은 어디가 막히는지, LOT는 어디에 영향이 번지는지 확인합니다.")
    st.markdown("#### 분류별 분석 기준")
    criteria_view = pd.DataFrame([
        {"분류": "설비", "기준 키": "machine_id", "판정 포인트": "정지와 불량이 설비별로 갈리는가"},
        {"분류": "공정", "기준 키": "process_display / line_id / stage_no", "판정 포인트": "공정별 output / stop / defect가 함께 보이는가"},
        {"분류": "LOT", "기준 키": "lot_id / model_label", "판정 포인트": "LOT 영향이 공정/설비로 전파되는가"},
    ])
    st.dataframe(criteria_view, use_container_width=True, hide_index=True)
    _render_reliability_badge(_compute_reliability_indicators(filtered_stop))
    st.markdown(
        """
        <div style="margin:.6rem 0 1rem 0;padding:.75rem .9rem;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);color:#cdd5df;">
            현재 탭은 <b>문제 위치 탐색</b> 용도이며, 아래 순서로 읽습니다: <b>설비 관점 → 공정 관점 → LOT 관점 → 시간 관점</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if machine_focus.empty and process_focus.empty and lot_focus.empty:
        st.warning("설비/공정 분석을 위한 데이터가 부족합니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    top_machine = machine_focus.iloc[0] if not machine_focus.empty else pd.Series(dtype="object")
    top_process = process_focus.iloc[0] if not process_focus.empty else pd.Series(dtype="object")
    top_lot = lot_focus.iloc[0] if not lot_focus.empty else pd.Series(dtype="object")
    major_error = "-"
    if not filtered_tag.empty and "event_class" in filtered_tag.columns:
        error_counts = filtered_tag["event_class"].astype(str).value_counts()
        error_counts = error_counts[~error_counts.index.isin(["OTHER", "META", "FLOW", "INSPECTION", "STOP"])]
        if not error_counts.empty:
            major_error = str(error_counts.index[0]).replace("_", " ")
    summary_parts = []
    if not machine_focus.empty:
        summary_parts.append(f"문제 설비 `{top_machine.get('machine_id', '-')}`")
    if not process_focus.empty:
        summary_parts.append(f"문제 공정 `{top_process.get('process_display', top_process.get('process_name', '-'))}`")
    if not lot_focus.empty:
        summary_parts.append(f"영향 LOT `{top_lot.get('lot_id', '-')}`")
    summary_text = " · ".join(summary_parts) if summary_parts else "현재 데이터에서 먼저 볼 위치를 정하기 어렵습니다."
    if summary_text and major_error != "-":
        line_id = str(top_machine.get("line_id", "-")) if not machine_focus.empty else "-"
        summary_text = f"{line_id} {top_machine.get('machine_id', '-') if not machine_focus.empty else '-'}에서 {major_error}가 두드러지고, {top_process.get('process_display', top_process.get('process_name', '-')) if not process_focus.empty else '-'} 공정이 막히며, {top_lot.get('lot_id', '-') if not lot_focus.empty else '-'} LOT 영향이 큽니다."
    st.markdown("#### 한줄 요약")
    st.markdown(
        f"""
        <div style="padding:10px 14px;border-radius:14px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);margin:0 0 .85rem 0;color:#e6edf7;">
            {summary_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_card("문제 설비", str(top_machine.get("machine_id", "-")), _label_machine(top_machine), PRIMARY), unsafe_allow_html=True)
    with c2:
        proc_label = str(top_process.get("process_display", top_process.get("process_name", "-")))
        if "stage_no" in top_process.index:
            proc_label = f"{proc_label} / stage {top_process.get('stage_no', '-')}"
        st.markdown(_card("문제 공정", proc_label, _label_process(top_process), SECONDARY), unsafe_allow_html=True)
    with c3:
        st.markdown(_card("영향 LOT", str(top_lot.get("lot_id", "-")), _label_lot(top_lot), "#22c55e"), unsafe_allow_html=True)
    with c4:
        st.markdown(_card("주요 오류 유형", major_error, "WAIT / PICKUP / FEEDER / RECOG / PLACE / TRANSFER / SETUP", "#8b5cf6"), unsafe_allow_html=True)

    def _avg_compare_label(label: str, value: float, mean_value: float, unit: str = "") -> str:
        return f"{label} {value:.2f}{unit} vs 평균 {mean_value:.2f}{unit} ({'+' if value - mean_value >= 0 else ''}{value - mean_value:.2f}{unit})"

    machine_mean_stop = pd.to_numeric(machine_focus["stop_time"], errors="coerce").fillna(0).mean() if not machine_focus.empty and "stop_time" in machine_focus.columns else 0
    machine_mean_defect = pd.to_numeric(machine_focus["defect_rate"], errors="coerce").fillna(0).mean() if not machine_focus.empty and "defect_rate" in machine_focus.columns else 0
    process_mean_stop = pd.to_numeric(process_focus["stop_time"], errors="coerce").fillna(0).mean() if not process_focus.empty and "stop_time" in process_focus.columns else 0
    process_mean_output = pd.to_numeric(process_focus["output_qty"], errors="coerce").fillna(0).mean() if not process_focus.empty and "output_qty" in process_focus.columns else 0
    process_all_mean_stop = pd.to_numeric(process_universe["stop_time"], errors="coerce").fillna(0).mean() if not process_universe.empty and "stop_time" in process_universe.columns else 0
    process_all_mean_output = pd.to_numeric(process_universe["output_qty"], errors="coerce").fillna(0).mean() if not process_universe.empty and "output_qty" in process_universe.columns else 0
    lot_mean_impact = pd.to_numeric(lot_focus["impact_score"], errors="coerce").fillna(0).mean() if not lot_focus.empty and "impact_score" in lot_focus.columns else 0
    lot_mean_defect = pd.to_numeric(lot_focus["fail_rate"], errors="coerce").fillna(0).mean() if not lot_focus.empty and "fail_rate" in lot_focus.columns else 0

    if not machine_focus.empty and "stop_time" in machine_focus.columns:
        total_stop = pd.to_numeric(machine_focus["stop_time"], errors="coerce").fillna(0).sum()
        top_n = max(1, int(np.ceil(len(machine_focus) * 0.2)))
        pareto_share = _safe_div(pd.to_numeric(machine_focus.head(top_n)["stop_time"], errors="coerce").fillna(0).sum(), total_stop)
        outlier_count = int(machine_focus["is_outlier"].fillna(False).sum()) if "is_outlier" in machine_focus.columns else 0
        st.caption(f"Pareto: 상위 20% 설비가 전체 stop_time의 {pareto_share * 100:.1f}%를 차지. outlier 설비 {outlier_count}개 탐지.")
        st.caption(_avg_compare_label("선택 설비 stop_time", _safe_float(top_machine.get("stop_time", 0)), machine_mean_stop, "s"))
        st.caption(_avg_compare_label("선택 설비 defect_rate", _safe_float(top_machine.get("defect_rate", 0)) * 100, machine_mean_defect * 100, "%"))
        stop_high = _safe_float(top_machine.get("stop_time", 0)) > machine_mean_stop
        defect_high = _safe_float(top_machine.get("defect_rate", 0)) > machine_mean_defect
        machine_interpretation = "복합형" if stop_high and defect_high else "정지형" if stop_high else "품질형" if defect_high else "안정형"
        if stop_high and not defect_high:
            machine_interpretation = "정지형"
        elif not stop_high and defect_high:
            machine_interpretation = "품질형"
        machine_summary = pd.DataFrame([
            {
                "지표": "정지 리스크",
                "선택": f"{_safe_float(top_machine.get('stop_time', 0)):.2f}s",
                "평균": f"{machine_mean_stop:.2f}s",
                "차이": f"{_safe_float(top_machine.get('stop_time', 0)) - machine_mean_stop:.2f}s",
                "판정": "높음" if stop_high else "낮음",
                "해석": "정지 시간이 평균보다 높은지 확인",
            },
            {
                "지표": "불량 리스크",
                "선택": f"{_safe_float(top_machine.get('defect_rate', 0)) * 100:.2f}%",
                "평균": f"{machine_mean_defect * 100:.2f}%",
                "차이": f"{(_safe_float(top_machine.get('defect_rate', 0)) - machine_mean_defect) * 100:.2f}%",
                "판정": "높음" if defect_high else "낮음",
                "해석": "불량률이 평균보다 높은지 확인",
            },
            {
                "지표": "복합 문제 여부",
                "선택": f"{pareto_share * 100:.1f}%",
                "평균": f"{(1 / max(len(machine_focus), 1)) * 100:.1f}%",
                "차이": f"{(pareto_share - (1 / max(len(machine_focus), 1))) * 100:.1f}%",
                "판정": "문제 설비" if stop_high and defect_high else "단일 리스크",
                "해석": "정지와 불량이 함께 높은 설비만 문제 설비로 본다",
            },
            {
                "지표": "설비 유형",
                "선택": machine_interpretation,
                "평균": "전체 평균",
                "차이": "-",
                "판정": "최종 해석",
                "해석": "정지형 / 품질형 / 복합형 / 안정형으로 묶음",
            },
        ])
        st.dataframe(machine_summary, use_container_width=True, hide_index=True)

    st.markdown(_section_header("설비 관점", "어느 설비가 문제인가?", PRIMARY), unsafe_allow_html=True)
    if not machine_focus.empty:
        top_machine_view = machine_focus.head(10).copy()
        machine_order_view = top_machine_view.copy()
        if "machine_order" in machine_order_view.columns:
            machine_order_view = machine_order_view.sort_values(["machine_order", "machine_id"], ascending=[True, True], kind="mergesort")
        else:
            machine_order_view = machine_order_view.sort_values(["machine_id"], ascending=[True], kind="mergesort")
        machine_axis_order = machine_order_view["machine_id"].astype(str).tolist()
        if not filtered_tag.empty and "event_class" in filtered_tag.columns:
            overall_error = (
                filtered_tag.groupby("event_class", as_index=False)
                .agg(count=("event_class", "size"))
                .sort_values("count", ascending=False)
            )
            overall_error = overall_error[~overall_error["event_class"].astype(str).isin(["OTHER", "META", "FLOW", "INSPECTION", "STOP"])]
        else:
            overall_error = pd.DataFrame()
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        machine_order_view,
                        x="machine_id",
                        y="stop_time",
                        color="line_id" if "line_id" in top_machine_view.columns else None,
                        text="stop_time",
                        category_orders={"machine_id": machine_axis_order},
                    ),
                    "설비별 stop_time",
                ),
                use_container_width=True,
            )
        with right:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        machine_order_view,
                        x="machine_id",
                        y="defect_rate",
                        color="line_id" if "line_id" in top_machine_view.columns else None,
                        text="defect_rate",
                        category_orders={"machine_id": machine_axis_order},
                    ),
                    "설비별 defect_rate",
                ),
                use_container_width=True,
            )
        if not overall_error.empty:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        overall_error.head(8),
                        x="event_class",
                        y="count",
                        text="count",
                    ),
                    "주요 오류 유형",
                ),
                use_container_width=True,
            )
        machine_compare = pd.DataFrame([
            {"항목": "stop_time", "선택": _safe_float(top_machine.get("stop_time", 0)), "전체 평균": machine_mean_stop, "차이": _safe_float(top_machine.get("stop_time", 0)) - machine_mean_stop},
            {"항목": "defect_rate(%)", "선택": _safe_float(top_machine.get("defect_rate", 0)) * 100, "전체 평균": machine_mean_defect * 100, "차이": (_safe_float(top_machine.get("defect_rate", 0)) - machine_mean_defect) * 100},
            {"항목": "MTBF(s)", "선택": _safe_float(top_machine.get("mtbf_sec", 0)), "전체 평균": pd.to_numeric(machine_focus.get("mtbf_sec", pd.Series([0])), errors="coerce").fillna(0).mean() if "mtbf_sec" in machine_focus.columns else 0, "차이": _safe_float(top_machine.get("mtbf_sec", 0)) - (pd.to_numeric(machine_focus.get("mtbf_sec", pd.Series([0])), errors="coerce").fillna(0).mean() if "mtbf_sec" in machine_focus.columns else 0)},
            {"항목": "MTTR(s)", "선택": _safe_float(top_machine.get("mttr_sec", 0)), "전체 평균": pd.to_numeric(machine_focus.get("mttr_sec", pd.Series([0])), errors="coerce").fillna(0).mean() if "mttr_sec" in machine_focus.columns else 0, "차이": _safe_float(top_machine.get("mttr_sec", 0)) - (pd.to_numeric(machine_focus.get("mttr_sec", pd.Series([0])), errors="coerce").fillna(0).mean() if "mttr_sec" in machine_focus.columns else 0)},
        ])
        st.dataframe(machine_compare, use_container_width=True, hide_index=True)
        st.plotly_chart(
            _plot_style(
                px.scatter(
                    top_machine_view,
                    x="stop_time",
                    y="defect_rate",
                    size="event_density" if "event_density" in top_machine_view.columns else None,
                    color="line_id" if "line_id" in top_machine_view.columns else None,
                    hover_name="machine_id",
                ),
                "정지시간 vs 불량률",
            ),
            use_container_width=True,
        )
        machine_error_cols = [c for c in ["setup_events", "feeder_error_events", "pickup_error_events", "recog_error_events", "place_error_events", "transfer_error_events", "wait_events"] if c in top_machine_view.columns]
        if machine_error_cols:
            error_long = top_machine_view[["machine_id"] + machine_error_cols].melt(id_vars="machine_id", var_name="error_type", value_name="count")
            error_long["count"] = pd.to_numeric(error_long["count"], errors="coerce").fillna(0)
            error_long = error_long[error_long["count"] > 0]
            if not error_long.empty:
                st.plotly_chart(
                    _plot_style(
                        px.bar(
                            error_long,
                            x="machine_id",
                            y="count",
                            color="error_type",
                            barmode="stack",
                        ),
                        "설비별 에러 유형 분포",
                    ),
                    use_container_width=True,
                )
        st.dataframe(
            top_machine_view[
                [c for c in ["rank", "machine_id", "line_id", "stage_no", "output_qty", "stop_time", "stop_count", "mtbf_sec", "mttr_sec", "defect_rate", "inspect_count", "fail_count", "event_density", "is_outlier"] if c in top_machine_view.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("설비 비교 데이터를 만들 수 없습니다.")

    st.markdown(_section_header("공정 관점", "어느 공정이 막히는가?", SECONDARY), unsafe_allow_html=True)
    if not process_focus.empty:
        top_process_view = process_focus.head(10).copy()
        process_order_map = {"aoi_post": 0, "aoi": 1, "mounter": 2, "spi": 3, "reflow": 4, "printer": 5}
        top_process_view["process_key"] = top_process_view["process_display"].astype(str).str.lower().map(lambda x: x if x in process_order_map else x)
        top_process_view["process_order_ui"] = top_process_view["process_key"].map(lambda x: process_order_map.get(str(x), 99))
        top_process_view = top_process_view.sort_values(["process_order_ui", "stop_time", "fail_rate", "output_qty"], ascending=[True, False, False, False], kind="mergesort")
        top_process_view["process_label"] = top_process_view.apply(
            lambda row: f"{row.get('process_display', row.get('process_name', '-'))}<br>L{row.get('line_id', '-')}/S{row.get('stage_no', '-')}", axis=1
        )
        top_process_view["output_text"] = np.where(top_process_view["output_status"].astype(str).eq("데이터 있음"), top_process_view["output_qty"].round(0).astype(int).astype(str), "데이터 없음")
        top_process_view["stop_text"] = np.where(top_process_view["stop_status"].astype(str).eq("데이터 있음"), top_process_view["stop_time"].round(0).astype(int).astype(str), "데이터 없음")
        top_process_view["defect_text"] = np.where(top_process_view["defect_status"].astype(str).eq("데이터 있음"), (top_process_view["fail_rate"] * 100).round(1).astype(str) + "%", "데이터 없음")
        top_process_view["basis_text"] = top_process_view.get("analysis_basis", pd.Series(["공정별 기준 별도"] * len(top_process_view), index=top_process_view.index)).fillna("공정별 기준 별도")
        p1, p2, p3 = st.columns(3)
        with p1:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        top_process_view.sort_values("process_order_ui", ascending=True),
                        x="process_display",
                        y="output_qty",
                        color="line_id" if "line_id" in top_process_view.columns else None,
                        text="output_text",
                    ),
                    "공정별 output(throughput)",
                ),
                use_container_width=True,
            )
        with p2:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        top_process_view.sort_values("process_order_ui", ascending=True),
                        x="process_display",
                        y="stop_time",
                        color="line_id" if "line_id" in top_process_view.columns else None,
                        text="stop_text",
                    ),
                    "공정별 stop_time",
                ),
                use_container_width=True,
            )
        with p3:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        top_process_view.sort_values("process_order_ui", ascending=True),
                        x="process_display",
                        y="fail_rate",
                        color="line_id" if "line_id" in top_process_view.columns else None,
                        text="defect_text",
                    ),
                    "공정별 defect_rate",
                ),
                use_container_width=True,
            )
        process_compare = pd.DataFrame([
            {"항목": "output(throughput)", "선택": f"{_safe_float(top_process.get('output_qty', 0)):.0f}" if str(top_process.get("output_status", "데이터 없음")) == "데이터 있음" else "데이터 없음", "전체 평균": f"{process_all_mean_output:.0f}" if process_all_mean_output > 0 else "데이터 없음", "차이": "-" if str(top_process.get("output_status", "데이터 없음")) != "데이터 있음" else f"{_safe_float(top_process.get('output_qty', 0)) - process_all_mean_output:.0f}"},
            {"항목": "stop_time", "선택": _fmt_stop(top_process.get("stop_time", 0)) if str(top_process.get("stop_status", "데이터 없음")) == "데이터 있음" else "데이터 없음", "전체 평균": _fmt_stop(process_all_mean_stop) if process_all_mean_stop > 0 else "데이터 없음", "차이": "-" if str(top_process.get("stop_status", "데이터 없음")) != "데이터 있음" else f"{_safe_float(top_process.get('stop_time', 0)) - process_all_mean_stop:.0f}s"},
            {"항목": "defect_rate(%)", "선택": _fmt_pct(top_process.get("fail_rate", 0)) if str(top_process.get("defect_status", "데이터 없음")) == "데이터 있음" else "데이터 없음", "전체 평균": _fmt_pct(pd.to_numeric(process_universe.get("fail_rate", pd.Series([0])), errors="coerce").fillna(0).mean()) if "fail_rate" in process_universe.columns and pd.to_numeric(process_universe.get("fail_rate", pd.Series([0])), errors="coerce").fillna(0).mean() > 0 else "데이터 없음", "차이": "-" if str(top_process.get("defect_status", "데이터 없음")) != "데이터 있음" else f"{(_safe_float(top_process.get('fail_rate', 0)) - (pd.to_numeric(process_universe.get('fail_rate', pd.Series([0])), errors='coerce').fillna(0).mean() if 'fail_rate' in process_universe.columns else 0)) * 100:.1f}%"},
        ])
        st.dataframe(process_compare, use_container_width=True, hide_index=True)
        process_analysis = _build_process_analysis_table(process_universe if not process_universe.empty else process_focus)
        if not process_analysis.empty:
            st.markdown("#### 공정별 분석 결과")
            st.dataframe(
                process_analysis[
                    [c for c in ["공정", "분석 상태", "핵심 초점", "분석축", "분석내용", "판정기준", "line_id", "stage_no", "output_qty", "stop_time", "inspect_count", "fail_rate"] if c in process_analysis.columns]
                ],
                use_container_width=True,
                hide_index=True,
            )
        if process_focus["selection_note"].astype(str).str.len().fillna(0).gt(0).any():
            st.info("선택 필터에서 공정 데이터가 비어 있어 전체 공정 기준으로 표시합니다.")
        st.dataframe(
            top_process_view[
                [c for c in ["rank", "process_display", "basis_text", "line_id", "stage_no", "machine_order", "output_qty", "output_status", "stop_time", "stop_status", "stop_count", "fail_count", "defect_status", "fail_rate", "bottleneck_hint", "production_rows", "distinct_machines", "lot_count"] if c in top_process_view.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("공정 비교 데이터를 만들 수 없습니다.")

    st.markdown(_section_header("LOT 관점", "어느 LOT에 영향이 번졌는가?", "#22c55e"), unsafe_allow_html=True)
    if not lot_focus.empty:
        lot_view = lot_focus.head(10).copy()
        lot_compare = pd.DataFrame([
            {"항목": "impact_score", "선택": _safe_float(top_lot.get("impact_score", 0)), "전체 평균": lot_mean_impact, "차이": _safe_float(top_lot.get("impact_score", 0)) - lot_mean_impact},
            {"항목": "defect_rate(%)", "선택": _safe_float(top_lot.get("fail_rate", 0)) * 100, "전체 평균": lot_mean_defect * 100, "차이": (_safe_float(top_lot.get("fail_rate", 0)) - lot_mean_defect) * 100},
        ])
        st.dataframe(lot_compare, use_container_width=True, hide_index=True)
        l1, l2 = st.columns(2)
        with l1:
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        lot_view.sort_values("impact_score", ascending=False),
                        x="lot_id",
                        y="impact_score",
                        color="model_label" if "model_label" in lot_view.columns else None,
                        text="impact_score",
                    ),
                    "LOT 영향도",
                ),
                use_container_width=True,
            )
        with l2:
            st.plotly_chart(
                _plot_style(
                    px.scatter(
                        lot_view,
                        x="production_rows" if "production_rows" in lot_view.columns else "output_qty",
                        y="fail_rate",
                        size="stop_time" if "stop_time" in lot_view.columns else None,
                        color="model_label" if "model_label" in lot_view.columns else None,
                        hover_name="lot_id",
                    ),
                    "LOT vs defect",
                ),
                use_container_width=True,
            )
        st.plotly_chart(
            _plot_style(
                px.scatter(
                    lot_view,
                    x="production_rows" if "production_rows" in lot_view.columns else "output_qty",
                    y="stop_time",
                    size="impact_score" if "impact_score" in lot_view.columns else None,
                    color="model_label" if "model_label" in lot_view.columns else None,
                    hover_name="lot_id",
                ),
                "LOT vs 생산량",
            ),
            use_container_width=True,
        )
        st.dataframe(
            lot_view[
                [c for c in ["rank", "lot_id", "model_label", "production_rows", "output_qty", "stop_time", "stop_count", "inspect_count", "fail_count", "fail_rate", "impact_score", "machine_count", "process_count", "representative_machine", "representative_process"] if c in lot_view.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )
        if filters.get("lot") and filters["lot"] != "전체":
            lot_detail = _apply_selection(shop, filters)
            if not lot_detail.empty:
                st.caption(f"선택 LOT `{filters['lot']}` 드릴다운")
                st.dataframe(
                    lot_detail[[c for c in ["event_ts", "process_name", "machine_id", "stage_no", "line_id", "model_label", "result_primary", "output_qty"] if c in lot_detail.columns]].head(50),
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        st.info("LOT 영향 데이터를 만들 수 없습니다.")

    st.markdown(_section_header("시간 관점", "언제 문제가 집중됐는가?", "#10b981"), unsafe_allow_html=True)
    if not time_view.empty:
        if not time_hour.empty:
            hour_plot = time_hour.sort_values("bucket_order") if "bucket_order" in time_hour.columns else time_hour
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        hour_plot,
                        x="bucket",
                        y="stop_time" if "stop_time" in hour_plot.columns else "error_count",
                        text="stop_time" if "stop_time" in hour_plot.columns else "error_count",
                        color="shift" if "shift" in hour_plot.columns else None,
                    ),
                    "시간대별 stop_time / error_count",
                ),
                use_container_width=True,
            )
        if not time_shift.empty:
            shift_cols = [c for c in ["shift", "stop_time", "stop_count", "error_count", "production_rows"] if c in time_shift.columns]
            st.dataframe(time_shift[shift_cols].sort_values("shift"), use_container_width=True, hide_index=True)
            st.plotly_chart(
                _plot_style(
                    px.bar(
                        time_shift.sort_values("stop_time", ascending=False),
                        x="shift",
                        y="stop_time" if "stop_time" in time_shift.columns else "error_count",
                        text="stop_time" if "stop_time" in time_shift.columns else "error_count",
                        color="shift" if "shift" in time_shift.columns else None,
                    ),
                    "shift별 stop_time",
                ),
                use_container_width=True,
            )
    else:
        st.info("시간 패턴 데이터를 만들 수 없습니다.")
    st.markdown("#### 해석 메모")
    st.markdown("- 설비는 `stop_time`, `defect_rate`, 에러 유형 분포를 같이 봅니다.")
    st.markdown("- 공정은 `output`, `stop_time`, `defect_rate`, 병목 사유를 같이 봅니다.")
    st.markdown("- LOT는 영향도와 생산량/불량의 동시 변화를 봅니다.")
    st.markdown("- 시간은 hour / shift별 stop_time과 error_count 집중 구간을 봅니다.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_rca(clean: Dict[str, pd.DataFrame], marts: Dict[str, pd.DataFrame], sample_mode: bool):
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame())
    stop = clean.get("vw_stop_event_fact", pd.DataFrame())
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame())
    tag = clean.get("vw_tag_event_fact", pd.DataFrame())
    comp = clean.get("vw_component_error_fact", pd.DataFrame())
    filters = _build_filter_panel(clean, "rca")
    filtered_clean = {
        **clean,
        "vw_shopfloor_event_fact": _apply_selection(shop, filters),
        "vw_stop_event_fact": _apply_selection(stop, filters),
        "vw_inspection_event_fact": _apply_selection(insp, filters),
        "vw_tag_event_fact": _apply_selection(tag, filters),
        "vw_component_error_fact": _apply_selection(comp, filters),
    }
    loss_paths = build_rca_loss_path_view(filtered_clean)
    card_summary = build_rca_card_summary(filtered_clean)
    timeline = build_rca_timeline_view(filtered_clean)
    hotspot = build_rca_hotspot_view(filtered_clean)
    repeat = build_rca_repeat_pattern_view(filtered_clean)
    drilldown = build_rca_drilldown_view(filtered_clean)
    proxy_candidates = build_rca_candidate_view(filtered_clean)
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("### RCA 분석")
    st.caption("RCA는 불량과 정지의 추적·드릴다운 탭입니다. 원인 단정 대신 관측된 후보와 반복 패턴을 좁혀 봅니다.")
    _render_reliability_badge(_compute_reliability_indicators(stop))
    if filtered_clean["vw_stop_event_fact"].empty and proxy_candidates.empty and filtered_clean["vw_inspection_event_fact"].empty and filtered_clean["vw_component_error_fact"].empty:
        st.warning("RCA 분석을 위한 데이터가 부족합니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not stop.empty:
        total_stop = float(stop["duration_sec"].sum()) if "duration_sec" in stop.columns else 0.0
        total_count = int(stop["stop_count"].sum()) if "stop_count" in stop.columns else len(stop)
        aggregated_count = int((stop["stop_count"] > 1).sum()) if "stop_count" in stop.columns else 0
        event_count = max(len(stop) - aggregated_count, 0)
        macro_avg = float(stop[stop["stop_count"] > 1]["duration_sec"].mean()) if "stop_count" in stop.columns and not stop[stop["stop_count"] > 1].empty else 0.0
        micro_avg = float(stop[stop["stop_count"] <= 1]["duration_sec"].mean()) if "stop_count" in stop.columns and not stop[stop["stop_count"] <= 1].empty else 0.0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(_card("총 정지", _fmt_sec(total_stop), f"{total_count:,}회", PRIMARY), unsafe_allow_html=True)
        with c2:
            st.markdown(_card("누적형 비중", f"{_safe_div(aggregated_count, len(stop)) * 100:.1f}%", f"n={aggregated_count}", SECONDARY), unsafe_allow_html=True)
        with c3:
            st.markdown(_card("이벤트형 비중", f"{_safe_div(event_count, len(stop)) * 100:.1f}%", f"n={event_count}", PRIMARY), unsafe_allow_html=True)
        with c4:
            st.markdown(_card("평균 정지", _fmt_sec(_safe_div(total_stop, total_count or 1)), f"micro {_fmt_sec(micro_avg)} / macro {_fmt_sec(macro_avg)}", SECONDARY), unsafe_allow_html=True)

    st.markdown("#### 선택 손실경로 카드")
    active_key = None
    if not loss_paths.empty:
        path_options = ["전체"] + (loss_paths["path_key"].astype(str).tolist() if "path_key" in loss_paths.columns else [f"rank {int(r.get('rank', i + 1))}" for i, (_, r) in enumerate(loss_paths.iterrows())])
        selected_key = st.selectbox("손실경로 선택", path_options, index=0, key="rca_loss_path_select")
        active_key = None if selected_key == "전체" else str(selected_key)
        selected_rows = loss_paths.head(1) if active_key is None else (loss_paths[loss_paths["path_key"].astype(str).eq(active_key)] if "path_key" in loss_paths.columns else loss_paths.head(1))
        selected = selected_rows.iloc[0] if not selected_rows.empty else loss_paths.iloc[0]
        st.markdown(f"- 현재 드릴다운 대상: `{selected.get('path_key', '-')}`")
        c1, c2, c3, c4, c5 = st.columns(5)
        cards = [
            ("언제", str(selected.get("when", "-")), f"rank {int(selected.get('rank', 0))}"),
            ("어디", str(selected.get("where", "-")), f"path {selected.get('machine_id', '-') }"),
            ("얼마나", str(selected.get("how_much", "-")), f"impact {selected.get('impact', 0):.0f}"),
            ("반복", str(selected.get("repeat", "-")), f"score {selected.get('repeat_score', 0):.2f}"),
            ("무엇", str(selected.get("what", "-")), f"{selected.get('cause_group', 'Proxy')}"),
        ]
        for col, (label, value, foot) in zip([c1, c2, c3, c4, c5], cards):
            with col:
                st.markdown(_card(label, value, foot), unsafe_allow_html=True)
        st.markdown("#### 손실경로 우선순위")
        display_cols = [c for c in ["rank", "path_key", "when", "where", "how_much", "repeat", "what", "impact", "events"] if c in loss_paths.columns]
        st.dataframe(loss_paths[display_cols].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("손실경로 우선순위를 만들 수 있는 데이터가 부족합니다. 아래는 기존 RCA 후보 흐름입니다.")
        _render_card_row(card_summary.sort_values("card_key") if not card_summary.empty else card_summary)
        selected = None

    if active_key is not None:
        if "path_key" in drilldown.columns:
            drilldown = drilldown[drilldown["path_key"].astype(str).eq(active_key)].copy()
        if "path_key" in repeat.columns:
            repeat = repeat[repeat["path_key"].astype(str).eq(active_key)].copy()
        if "path_key" in hotspot.columns:
            hotspot = hotspot[hotspot["path_key"].astype(str).eq(active_key)].copy()
    st.markdown("#### 카드 상세 연결")
    if not timeline.empty:
        if active_key is not None and "path_key" in timeline.columns:
            tl = timeline[timeline["path_key"].astype(str).eq(active_key)].copy()
        else:
            tl = timeline.copy()
        if not tl.empty:
            st.plotly_chart(_plot_style(px.line(tl.groupby(["hour"], as_index=False).agg(metric_value=("metric_value", "sum")), x="hour", y="metric_value", markers=True), "언제: 시간대별 추이"), use_container_width=True)
        else:
            st.info("선택 손실경로에 대한 시간대 추이를 만들 수 있는 데이터가 부족합니다.")
    else:
        st.info("시간대 추이를 만들 수 있는 데이터가 부족합니다.")
    if not hotspot.empty:
        machine_hotspot = hotspot[hotspot["hotspot_type"].eq("machine")] if "hotspot_type" in hotspot.columns else hotspot
        if not machine_hotspot.empty:
            machine_plot = machine_hotspot.copy().head(10)
            if "line_id" in machine_plot.columns:
                machine_plot["대상"] = machine_plot.apply(lambda r: f"{r.get('machine_id', '-')}\n{r.get('line_id', '-')}", axis=1)
            else:
                machine_plot["대상"] = machine_plot["machine_id"].astype(str)
            st.plotly_chart(_plot_style(px.bar(machine_plot, x="대상", y="impact", text="impact"), "어디: hotspot 설비/라인"), use_container_width=True)
        if "hotspot_type" in hotspot.columns and "defect" in hotspot["hotspot_type"].astype(str).unique():
            defect_hotspot = hotspot[hotspot["hotspot_type"].eq("defect")]
            if not defect_hotspot.empty:
                defect_plot = defect_hotspot.head(10).copy()
                if "model_label" in defect_plot.columns:
                    defect_plot["대상"] = defect_plot.apply(lambda r: f"{r.get('machine_id', '-')}\n{r.get('model_label', '-')}", axis=1)
                else:
                    defect_plot["대상"] = defect_plot["machine_id"].astype(str)
                st.plotly_chart(_plot_style(px.bar(defect_plot, x="대상", y="impact", text="impact"), "어디: defect hotspot"), use_container_width=True)
    if not card_summary.empty and "how_much" in card_summary["card_key"].values:
        hm = card_summary.loc[card_summary["card_key"].eq("how_much")].iloc[0]
        st.markdown(f"- 얼마나: `{hm['headline_value']}` · {hm['evidence']}")
        scale_df = drilldown.copy()
        if not scale_df.empty:
            scale_df = scale_df.groupby(["source_type"], as_index=False).agg(metric_value=("metric_value", "sum"))
            st.plotly_chart(_plot_style(px.bar(scale_df, x="source_type", y="metric_value", text="metric_value"), "영향 규모 분포"), use_container_width=True)
    if not repeat.empty:
        st.plotly_chart(_plot_style(px.bar(repeat.head(10), x="pattern", y="impact", color="cause_group" if "cause_group" in repeat.columns else None, text="impact"), "반복: 재발 패턴"), use_container_width=True)
        st.dataframe(repeat[[c for c in ["path_key", "pattern", "machine_id", "cause_group", "cause_detail", "hour", "lot_id", "events", "impact"] if c in repeat.columns]].head(15), use_container_width=True, hide_index=True)
    if not hotspot.empty:
        cause_view = hotspot[hotspot["cause_group"].notna()] if "cause_group" in hotspot.columns else hotspot
        if not cause_view.empty:
            if {"cause_group", "cause_detail"}.issubset(cause_view.columns):
                cause_plot = (
                    cause_view.groupby(["cause_group", "cause_detail"], as_index=False)
                    .agg(impact=("impact", "sum"), events=("events", "sum"))
                    .sort_values(["impact", "events"], ascending=False)
                )
                cause_plot["대상"] = cause_plot.apply(lambda r: f"{r.get('cause_group', '-')}\n{r.get('cause_detail', '-')}", axis=1)
            else:
                cause_plot = cause_view.head(10).copy()
                cause_plot["대상"] = cause_plot.get("cause_detail", pd.Series(["-"] * len(cause_plot), index=cause_plot.index)).astype(str)
            st.plotly_chart(_plot_style(px.bar(cause_plot.head(10), x="대상", y="impact", text="impact"), "무엇: cause_group / cause_detail"), use_container_width=True)
            st.dataframe(cause_plot[[c for c in ["cause_group", "cause_detail", "impact", "events"] if c in cause_plot.columns]].head(15), use_container_width=True, hide_index=True)

    st.markdown("#### 최종 드릴다운 시나리오")
    st.markdown("- 1) 에러 / 피더 정보로 영향 대상의 범위를 좁힙니다.")
    st.markdown("- 2) 피더 / 노즐 핫스팟으로 반복되는 부품·장치 조합을 찾습니다.")
    st.markdown("- 3) 픽업 오류와 정지 상관으로 알람 우선순위와 조치 순서를 정합니다.")
    if sample_mode:
        st.info("이 시나리오는 샘플 데이터로 설명용 구성입니다. 실제 RCA에서는 동일 흐름으로 원인 후보를 좁힙니다.")

    feeder_like = comp.copy()
    if not feeder_like.empty:
        st.markdown("##### 1. 에러 / 피더 정보")
        feeder_cols = [c for c in ["machine_id", "part_number", "feeder_id", "feeder_serial", "nozzle_serial", "lot_id", "error_count", "pickup_count"] if c in feeder_like.columns]
        if feeder_cols:
            feeder_like["error_rate"] = feeder_like.apply(lambda r: _safe_div(r.get("error_count", 0), max(r.get("pickup_count", 0), 1)), axis=1) if "error_rate" not in feeder_like.columns else feeder_like["error_rate"]
            feeder_summary = feeder_like[feeder_cols + (["error_rate"] if "error_rate" not in feeder_cols else [])].copy()
            st.dataframe(feeder_summary.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("에러 / 피더 정보를 만들 수 있는 데이터가 부족합니다.")

        st.markdown("##### 2. 피더 / 노즐 핫스팟")
        hotspot_cols = [c for c in ["part_number", "feeder_id", "feeder_serial", "nozzle_serial", "machine_id"] if c in feeder_like.columns]
        if hotspot_cols:
            top_components = feeder_like.groupby(hotspot_cols, as_index=False).agg(error_count=("error_count", "sum"), pickup_count=("pickup_count", "sum"))
            top_components["error_rate"] = top_components.apply(lambda r: _safe_div(r.get("error_count", 0), max(r.get("pickup_count", 0), 1)), axis=1)
            top_components = top_components.sort_values(["error_rate", "error_count"], ascending=False).head(10)
            st.dataframe(top_components, use_container_width=True, hide_index=True)
            if "part_number" in feeder_like.columns and "lot_id" in feeder_like.columns:
                part_lot = feeder_like.groupby(["part_number", "lot_id"], as_index=False).agg(error_count=("error_count", "sum"), pickup_count=("pickup_count", "sum"))
                part_lot["error_rate"] = part_lot.apply(lambda r: _safe_div(r.get("error_count", 0), max(r.get("pickup_count", 0), 1)), axis=1)
                part_variance = part_lot.groupby("part_number")["error_rate"].var().reset_index(name="variance").dropna()
                if not part_variance.empty:
                    top_part = part_variance.sort_values("variance", ascending=False).iloc[0]
                    top_lot_row = part_lot[part_lot["part_number"] == top_part["part_number"]].sort_values("error_rate", ascending=False).head(1)
                    lot_label = top_lot_row.iloc[0]["lot_id"] if not top_lot_row.empty else "Unknown"
                    st.markdown(f"- `{top_part['part_number']}` LOT {lot_label}의 error_rate 분산 {top_part['variance']:.4f} → 특정 LOT 편중 가능성")
        else:
            st.info("피더 / 노즐 / 부품 핫스팟 데이터가 부족합니다.")

        st.markdown("##### 3. 픽업 오류와 정지 상관")
        if "machine_id" in feeder_like.columns and not stop.empty and "machine_id" in stop.columns:
            corr_df = feeder_like.copy()
            corr_df["pickup_count"] = pd.to_numeric(corr_df.get("pickup_count", 0), errors="coerce").fillna(0)
            corr_df["error_count"] = pd.to_numeric(corr_df.get("error_count", 0), errors="coerce").fillna(0)
            corr_df = corr_df.groupby("machine_id", as_index=False).agg(pickup_error_count=("error_count", "sum"), pickup_count=("pickup_count", "sum"))
            corr_df["rate"] = corr_df.apply(lambda r: _safe_div(r.get("pickup_error_count", 0), max(r.get("pickup_count", 0), 1)), axis=1)
            stops_per_machine = stop.groupby("machine_id", as_index=False)["duration_sec"].sum()
            total_stop = float(stops_per_machine["duration_sec"].sum()) or 1.0
            stops_per_machine["stop_share"] = stops_per_machine["duration_sec"] / total_stop
            corr_df = corr_df.merge(stops_per_machine[["machine_id", "stop_share"]], on="machine_id", how="left").fillna(0)
            reason_col = "stop_reason_group" if "stop_reason_group" in stop.columns else "stop_like_reason" if "stop_like_reason" in stop.columns else "stop_reason_code"
            if reason_col in stop.columns:
                stop_group = stop.groupby(["machine_id", reason_col], as_index=False)["duration_sec"].sum()
                if not stop_group.empty:
                    idx = stop_group.groupby("machine_id")["duration_sec"].idxmax().dropna()
                    stop_group = stop_group.loc[idx]
                    corr_df = corr_df.merge(stop_group[["machine_id", reason_col]], on="machine_id", how="left")
                    if reason_col != "stop_reason_group":
                        corr_df = corr_df.rename(columns={reason_col: "stop_reason_group"})
            corr_df = corr_df.sort_values(["rate", "stop_share"], ascending=False)
            if not corr_df.empty:
                rate_max = max(float(corr_df["rate"].max()), 0.01)
                stop_max = max(float(corr_df["stop_share"].max()), 0.01)
                fig_corr = px.scatter(
                    corr_df,
                    x="rate",
                    y="stop_share",
                    size="pickup_count",
                    color="stop_reason_group" if "stop_reason_group" in corr_df.columns else None,
                    template=DARK_TEMPLATE,
                    title="Pickup vs Stop Correlation",
                    hover_name="machine_id",
                    hover_data={"pickup_count": True, "pickup_error_count": True, "rate": ":.1%", "stop_share": ":.1%"},
                )
                fig_corr.update_xaxes(range=[0, rate_max * 1.15], tickformat=".0%")
                fig_corr.update_yaxes(range=[0, stop_max * 1.15], tickformat=".0%")
                st.plotly_chart(_plot_style(fig_corr, "픽업 오류와 정지 상관", 360), use_container_width=True)
                corr_coef = corr_df["rate"].corr(corr_df["stop_share"])
                if pd.notna(corr_coef):
                    st.markdown(f"- 상관계수: `{corr_coef:.2f}`")
                    if corr_coef > 0.3:
                        st.markdown("- 해석: 픽업 오류가 높은 설비에서 정지 비중도 같이 높게 관측됩니다.")
                    elif corr_coef < -0.3:
                        st.markdown("- 해석: 픽업 오류와 정지가 분리되어 나타납니다.")
                    else:
                        st.markdown("- 해석: 현재 데이터에서는 뚜렷한 동행 패턴이 약합니다.")
        else:
            st.info("픽업 오류와 정지 상관을 만들 데이터가 부족합니다.")

    st.markdown("#### 드릴다운 테이블")
    if not drilldown.empty:
        st.dataframe(drilldown[[c for c in ["event_ts", "day", "hour", "source_type", "line_id", "stage_no", "machine_id", "lot_id", "model_label", "cause_group", "cause_detail", "result_primary", "quality_flag", "metric_value", "path_key"] if c in drilldown.columns]].head(50), use_container_width=True, hide_index=True)
    else:
        st.info("드릴다운용 상세 데이터가 충분하지 않습니다.")
    if sample_mode or len(filtered_clean["vw_stop_event_fact"]) < 10:
        st.markdown("#### 샘플 / proxy 모드 안내")
        st.markdown("- 실제 stop 데이터가 적으면 tag proxy와 inspection 결과를 함께 사용합니다.")
        st.markdown("- RUN / Information 같은 값은 설명용 메타일 수 있으므로 원인 후보로 직접 해석하지 않습니다.")
        st.markdown("- 카드 headline은 관측 집중도이며, 아래 상세 표에서 근거를 함께 확인해야 합니다.")
    st.markdown("#### 해석 한계")
    st.markdown("- RCA는 관측 패턴 기반이며, 확정 원인으로 쓰면 안 됩니다.")
    st.markdown("- stop event 우선, 그 다음 tag proxy, inspection 순으로 보완합니다.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_equipment_screen(clean: Dict[str, pd.DataFrame], marts: Dict[str, pd.DataFrame]):
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame()).copy()
    stop = clean.get("vw_stop_event_fact", pd.DataFrame()).copy()
    insp = clean.get("vw_inspection_event_fact", pd.DataFrame()).copy()
    tag = clean.get("vw_tag_event_fact", pd.DataFrame()).copy()
    comp = clean.get("vw_component_error_fact", pd.DataFrame()).copy()

    filters = _build_filter_panel(clean, "problem")
    filtered_clean = {
        **clean,
        "vw_shopfloor_event_fact": _apply_selection(shop, filters),
        "vw_stop_event_fact": _apply_selection(stop, filters),
        "vw_inspection_event_fact": _apply_selection(insp, filters),
        "vw_tag_event_fact": _apply_selection(tag, filters),
        "vw_component_error_fact": _apply_selection(comp, filters),
    }

    filtered_shop = filtered_clean.get("vw_shopfloor_event_fact", pd.DataFrame()).copy()
    filtered_stop = filtered_clean.get("vw_stop_event_fact", pd.DataFrame()).copy()
    filtered_insp = filtered_clean.get("vw_inspection_event_fact", pd.DataFrame()).copy()
    filtered_tag = filtered_clean.get("vw_tag_event_fact", pd.DataFrame()).copy()
    filtered_comp = filtered_clean.get("vw_component_error_fact", pd.DataFrame()).copy()

    equipment = build_equipment_overview(filtered_clean)
    process = build_process_overview(filtered_clean)
    lot = build_lot_analysis_view(filtered_clean)
    time_view = build_time_pattern_view(filtered_clean)
    quality_overview = build_quality_overview(filtered_clean)

    def _safe_float(v, default: float = 0.0) -> float:
        try:
            if pd.isna(v):
                return default
            return float(v)
        except Exception:
            return default

    def _fmt_pct(v) -> str:
        return f"{_safe_float(v) * 100:.1f}%"

    def _fmt_sec_value(v) -> str:
        return _fmt_sec(_safe_float(v))

    def _fmt_sec_base(v: float) -> str:
        return _fmt_sec(v)

    def _norm(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce").fillna(0)
        if s.empty:
            return s
        mn = s.min()
        mx = s.max()
        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return pd.Series([0.0] * len(s), index=s.index)
        return (s - mn) / (mx - mn)

    def _top_reason(df: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
        if df.empty or group_col not in df.columns:
            return pd.DataFrame(columns=[group_col, value_col])
        out = df.groupby(group_col, as_index=False).agg(**{value_col: (value_col, "sum")})
        return out.sort_values(value_col, ascending=False)

    def _first_value(series: pd.Series, default: str = "-") -> str:
        if series is None or series.empty:
            return default
        vals = series.dropna().astype(str)
        vals = vals[vals.ne("") & vals.ne("nan") & vals.ne("None")]
        return str(vals.iloc[0]) if not vals.empty else default

    def _machine_ct(source: pd.DataFrame) -> pd.DataFrame:
        if source.empty or "machine_id" not in source.columns or "event_ts" not in source.columns:
            return pd.DataFrame(columns=["machine_id", "avg_ct_sec", "ct_std_sec"])
        tmp = source[["machine_id", "event_ts"]].copy()
        tmp["event_ts"] = pd.to_datetime(tmp["event_ts"], errors="coerce")
        tmp = tmp.dropna(subset=["machine_id", "event_ts"]).sort_values(["machine_id", "event_ts"])
        if tmp.empty:
            return pd.DataFrame(columns=["machine_id", "avg_ct_sec", "ct_std_sec"])
        tmp["ct_sec"] = tmp.groupby("machine_id")["event_ts"].diff().dt.total_seconds()
        out = tmp.groupby("machine_id", as_index=False).agg(avg_ct_sec=("ct_sec", "mean"), ct_std_sec=("ct_sec", "std"))
        out["avg_ct_sec"] = pd.to_numeric(out["avg_ct_sec"], errors="coerce").fillna(0)
        out["ct_std_sec"] = pd.to_numeric(out["ct_std_sec"], errors="coerce").fillna(0)
        return out

    def _process_ct(source: pd.DataFrame) -> pd.DataFrame:
        if source.empty or "process_name" not in source.columns or "event_ts" not in source.columns:
            return pd.DataFrame(columns=["process_name", "avg_ct_sec", "ct_std_sec"])
        tmp = source[["process_name", "event_ts"]].copy()
        tmp["event_ts"] = pd.to_datetime(tmp["event_ts"], errors="coerce")
        tmp = tmp.dropna(subset=["process_name", "event_ts"]).sort_values(["process_name", "event_ts"])
        if tmp.empty:
            return pd.DataFrame(columns=["process_name", "avg_ct_sec", "ct_std_sec"])
        tmp["ct_sec"] = tmp.groupby("process_name")["event_ts"].diff().dt.total_seconds()
        out = tmp.groupby("process_name", as_index=False).agg(avg_ct_sec=("ct_sec", "mean"), ct_std_sec=("ct_sec", "std"))
        out["avg_ct_sec"] = pd.to_numeric(out["avg_ct_sec"], errors="coerce").fillna(0)
        out["ct_std_sec"] = pd.to_numeric(out["ct_std_sec"], errors="coerce").fillna(0)
        return out

    def _retry_proxy_by_machine(source: pd.DataFrame) -> pd.DataFrame:
        if source.empty or "machine_id" not in source.columns:
            return pd.DataFrame(columns=["machine_id", "retry_rate"])
        key_cols = [c for c in ["machine_id", "lot_id", "model_label", "process_name", "result_primary"] if c in source.columns]
        if len(key_cols) < 2:
            return pd.DataFrame(columns=["machine_id", "retry_rate"])
        tmp = source[key_cols].copy()
        tmp["retry_flag"] = tmp.duplicated(subset=key_cols, keep=False).astype(int)
        out = tmp.groupby("machine_id", as_index=False).agg(retry_flag=("retry_flag", "sum"), total=("retry_flag", "size"))
        out["retry_rate"] = out.apply(lambda r: _safe_div(r.get("retry_flag", 0), r.get("total", 0)), axis=1)
        return out[["machine_id", "retry_rate"]]

    def _retry_proxy_by_lot(source: pd.DataFrame) -> pd.DataFrame:
        if source.empty or "lot_id" not in source.columns:
            return pd.DataFrame(columns=["lot_id", "retry_rate"])
        key_cols = [c for c in ["lot_id", "machine_id", "model_label", "process_name", "result_primary"] if c in source.columns]
        if len(key_cols) < 2:
            return pd.DataFrame(columns=["lot_id", "retry_rate"])
        tmp = source[key_cols].copy()
        tmp["retry_flag"] = tmp.duplicated(subset=key_cols, keep=False).astype(int)
        out = tmp.groupby("lot_id", as_index=False).agg(retry_flag=("retry_flag", "sum"), total=("retry_flag", "size"))
        out["retry_rate"] = out.apply(lambda r: _safe_div(r.get("retry_flag", 0), r.get("total", 0)), axis=1)
        return out[["lot_id", "retry_rate"]]

    def _issue_type_machine(row: pd.Series) -> str:
        stop_time = _safe_float(row.get("stop_time", 0))
        defect_rate = _safe_float(row.get("defect_rate", 0))
        retry_rate = _safe_float(row.get("retry_rate", 0))
        wait_count = _safe_float(row.get("wait_count", 0))
        if stop_time > 0.7 and defect_rate > 0.7:
            return "복합 문제형"
        if stop_time > 0.7 and defect_rate <= 0.7:
            return "생산성 손실형"
        if defect_rate > 0.7 and stop_time <= 0.4:
            return "품질 집중형"
        if wait_count > 0.6:
            return "공정 연계형"
        if retry_rate > 0.6:
            return "재작업 집중형"
        return "주의"

    def _issue_comment_machine(row: pd.Series) -> str:
        stop_reason = str(row.get("top_stop_reason", "-"))
        wait_reason = str(row.get("top_wait_reason", "-"))
        if "WAIT" in wait_reason.upper() or row.get("wait_count", 0) > 0:
            return "WAIT 비중이 높아 전후공정 연계와 자재 흐름을 우선 확인해야 합니다."
        if any(tok in stop_reason.upper() for tok in ["PICK", "FEED", "NOZZ", "REEL"]):
            return "PICKUP/FEEDER 계열 정지가 보여 자재 공급과 흡착 조건을 먼저 봐야 합니다."
        if any(tok in stop_reason.upper() for tok in ["RECOG", "VISION", "MARK", "CAM"]):
            return "RECOG/비전 계열 정지가 보여 인식 조건과 조명/카메라 상태 점검이 필요합니다."
        if any(tok in stop_reason.upper() for tok in ["PLACE", "OFFSET", "ALIGN"]):
            return "PLACE 계열 이슈 가능성이 높아 좌표 보정과 head 상태를 확인해야 합니다."
        if _safe_float(row.get("defect_rate", 0)) > _safe_float(row.get("stop_time", 0)) and _safe_float(row.get("defect_rate", 0)) > 0:
            return "정지보다 불량이 더 높아 품질 조건 중심으로 접근하는 것이 효율적입니다."
        return "정지와 불량의 조합을 기준으로 원인 우선순위를 정해야 합니다."

    def _action_machine(row: pd.Series) -> str:
        wait_reason = str(row.get("top_wait_reason", "-")).upper()
        stop_reason = str(row.get("top_stop_reason", "-")).upper()
        if "WAIT" in wait_reason:
            return "전후공정 buffer, feeder 보급 타이밍, line balance 점검"
        if any(tok in stop_reason for tok in ["PICK", "FEED", "NOZZ", "REEL"]):
            return "nozzle 점검, feeder 정렬, reel 품질 확인"
        if any(tok in stop_reason for tok in ["RECOG", "VISION", "MARK", "CAM"]):
            return "camera/vision tuning, mark 인식 조건, 조명 calibration 점검"
        if any(tok in stop_reason for tok in ["PLACE", "OFFSET", "ALIGN"]):
            return "placement offset 보정, head calibration, 흡착 안정성 점검"
        return "상위 reason Pareto 기준으로 설비 조건과 알람 코드 정비"

    def _issue_type_process(row: pd.Series) -> str:
        stop_time = _safe_float(row.get("stop_time", 0))
        defect_rate = _safe_float(row.get("fail_rate", row.get("defect_rate", 0)))
        wait_count = _safe_float(row.get("wait_count", 0))
        ct_std = _safe_float(row.get("ct_std_sec", 0))
        if stop_time > 0.7 and defect_rate > 0.7:
            return "복합 병목"
        if stop_time > 0.7:
            return "정지 병목"
        if defect_rate > 0.7:
            return "품질 병목"
        if wait_count > 0.6:
            return "흐름 병목"
        if ct_std > 0.7:
            return "안정성 문제"
        return "주의"

    def _action_process(row: pd.Series) -> str:
        process_name = str(row.get("process_display", row.get("process_name", "-"))).upper()
        if "AOI" in process_name:
            return "검사 조건, false call, review capacity 점검"
        if "SPI" in process_name:
            return "인쇄 품질, threshold, 검사 조건 재점검"
        if "MOUNTER" in process_name:
            return "feeder, nozzle, line balance, 자재 보급 타이밍 점검"
        if "PRINTER" in process_name:
            return "printing recipe, stencil, raw event 보강"
        return "공정별 stop/wait Pareto를 기준으로 병목 원인 정리"

    def _issue_type_lot(row: pd.Series) -> str:
        stop_time = _safe_float(row.get("stop_time", 0))
        machine_count = _safe_float(row.get("machine_count", 0))
        process_count = _safe_float(row.get("process_count", 0))
        impact = _safe_float(row.get("impact_score", 0))
        if stop_time > 0.7 and machine_count <= 0.4:
            return "국소 LOT 문제"
        if stop_time > 0.7 and process_count > 0.7:
            return "전파 LOT 문제"
        if impact > 0.8:
            return "우선 점검 LOT"
        return "주의"

    def _action_lot(row: pd.Series) -> str:
        machine_count = _safe_float(row.get("machine_count", 0))
        process_count = _safe_float(row.get("process_count", 0))
        if process_count > machine_count:
            return "trace 재확인, upstream/downstream 확산 여부 확인"
        if machine_count <= 1:
            return "대표 설비와 자재 lot 매핑 우선 확인"
        return "LOT별 자재, 교대, 셋업 이력과 반복 발생 패턴 확인"

    def _priority_comment(row: pd.Series) -> str:
        kind = str(row.get("대상유형", "-"))
        issue = str(row.get("문제유형", "-"))
        if kind == "설비":
            return "설비 조건을 손보면 바로 stop/defect 둘 다 줄일 가능성이 큽니다."
        if kind == "공정":
            return "공정 흐름을 막고 있어 throughput 회복 효과가 큽니다."
        if kind == "LOT":
            return "특정 LOT 확산을 막으면 고객 영향 범위를 빠르게 줄일 수 있습니다."
        return issue

    def _priority_action(row: pd.Series) -> str:
        kind = str(row.get("대상유형", "-"))
        issue = str(row.get("문제유형", "-"))
        if kind == "설비":
            return "nozzle / feeder / vision / interlock 중 상위 reason부터 조치"
        if kind == "공정":
            return "line balance, buffer, recipe, review capacity 순서로 개선"
        if kind == "LOT":
            return "대표 설비와 공정 trace를 먼저 확인하고 원인 확산을 차단"
        return issue

    machine_ct = _machine_ct(filtered_shop)
    process_ct = _process_ct(filtered_shop)
    retry_machine = _retry_proxy_by_machine(filtered_insp if not filtered_insp.empty else filtered_shop)
    retry_lot = _retry_proxy_by_lot(filtered_insp if not filtered_insp.empty else filtered_shop)

    if not equipment.empty and not machine_ct.empty:
        equipment = equipment.merge(machine_ct, on="machine_id", how="left")
    if not equipment.empty and not retry_machine.empty:
        equipment = equipment.merge(retry_machine, on="machine_id", how="left")
    if not process.empty and not process_ct.empty:
        process = process.merge(process_ct, on="process_name", how="left")
    if not lot.empty and not retry_lot.empty:
        lot = lot.merge(retry_lot, on="lot_id", how="left")

    if not filtered_tag.empty and "event_class" in filtered_tag.columns and "machine_id" in filtered_tag.columns:
        wait_machine = filtered_tag[filtered_tag["event_class"].eq("WAIT")].groupby("machine_id", as_index=False).size().rename(columns={"size": "wait_count"})
        if not equipment.empty:
            equipment = equipment.merge(wait_machine, on="machine_id", how="left")
    elif not equipment.empty:
        equipment["wait_count"] = 0

    if not filtered_tag.empty and "event_class" in filtered_tag.columns and "machine_id" in filtered_tag.columns:
        wait_reason = (
            filtered_tag[filtered_tag["event_class"].eq("WAIT")]
            .groupby(["machine_id", "cause_detail"], as_index=False)
            .agg(wait_count=("event_class", "size"))
            .sort_values(["machine_id", "wait_count"], ascending=[True, False])
        )
        wait_reason = wait_reason.groupby("machine_id").head(1).rename(columns={"cause_detail": "top_wait_reason"})
        if not equipment.empty:
            equipment = equipment.merge(wait_reason[["machine_id", "top_wait_reason"]], on="machine_id", how="left")

    if not filtered_stop.empty and "machine_id" in filtered_stop.columns:
        stop_reason = (
            filtered_stop.groupby(["machine_id", "stop_like_reason"], as_index=False)
            .agg(stop_time=("duration_sec", "sum"))
            .sort_values(["machine_id", "stop_time"], ascending=[True, False])
        )
        stop_reason = stop_reason.groupby("machine_id").head(1).rename(columns={"stop_like_reason": "top_stop_reason"})
        if not equipment.empty:
            equipment = equipment.merge(stop_reason[["machine_id", "top_stop_reason"]], on="machine_id", how="left")

    if not filtered_shop.empty and "process_name" in filtered_shop.columns and "machine_id" in filtered_shop.columns:
        process_map = (
            filtered_shop.groupby("machine_id", as_index=False)
            .agg(process_name=("process_name", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]))
        )
        if not filtered_tag.empty and "event_class" in filtered_tag.columns:
            tag_wait = filtered_tag[filtered_tag["event_class"].eq("WAIT")][["machine_id"]].copy()
            if not tag_wait.empty:
                tag_wait = tag_wait.merge(process_map, on="machine_id", how="left")
                wait_by_process = tag_wait.groupby("process_name", as_index=False).size().rename(columns={"size": "wait_count"})
                if not process.empty:
                    process = process.merge(wait_by_process, on="process_name", how="left")
    if not process.empty and "wait_count" not in process.columns:
        process["wait_count"] = 0

    def _series_or_zeros(frame: pd.DataFrame, col: str) -> pd.Series:
        if col in frame.columns:
            return pd.to_numeric(frame[col], errors="coerce")
        return pd.Series([0] * len(frame), index=frame.index, dtype="float64")

    if not lot.empty and "retry_rate" not in lot.columns:
        lot["retry_rate"] = 0
    if not equipment.empty and "retry_rate" not in equipment.columns:
        equipment["retry_rate"] = 0
    if not process.empty and "avg_ct_sec" not in process.columns:
        process["avg_ct_sec"] = 0
        process["ct_std_sec"] = 0

    if not equipment.empty:
        equipment["wait_count"] = _series_or_zeros(equipment, "wait_count").fillna(0)
        equipment["retry_rate"] = _series_or_zeros(equipment, "retry_rate").fillna(0)
        equipment["avg_ct_sec"] = _series_or_zeros(equipment, "avg_ct_sec").fillna(0)
        equipment["ct_std_sec"] = _series_or_zeros(equipment, "ct_std_sec").fillna(0)
        equipment["stop_time_norm"] = _norm(equipment["stop_time"] if "stop_time" in equipment.columns else pd.Series([0] * len(equipment)))
        equipment["defect_norm"] = _norm(equipment["defect_rate"] if "defect_rate" in equipment.columns else pd.Series([0] * len(equipment)))
        equipment["retry_norm"] = _norm(equipment["retry_rate"])
        equipment["wait_norm"] = _norm(equipment["wait_count"])
        equipment["ct_norm"] = _norm(equipment["ct_std_sec"])
        equipment["severity_score"] = (
            equipment["stop_time_norm"] * 0.35
            + equipment["defect_norm"] * 0.30
            + equipment["retry_norm"] * 0.15
            + equipment["wait_norm"] * 0.10
            + equipment["ct_norm"] * 0.10
        )
        q1 = equipment["severity_score"].quantile(0.50) if len(equipment) else 0
        q2 = equipment["severity_score"].quantile(0.80) if len(equipment) else 0
        equipment["상태 등급"] = np.select(
            [equipment["severity_score"].ge(q2), equipment["severity_score"].ge(q1)],
            ["개선필요", "주의"],
            default="정상",
        )
        equipment["문제유형"] = equipment.apply(_issue_type_machine, axis=1)
        equipment["해석"] = equipment.apply(_issue_comment_machine, axis=1)
        equipment["개선액션"] = equipment.apply(_action_machine, axis=1)

    if not process.empty:
        process["avg_ct_sec"] = _series_or_zeros(process, "avg_ct_sec").fillna(0)
        process["ct_std_sec"] = _series_or_zeros(process, "ct_std_sec").fillna(0)
        process["wait_count"] = _series_or_zeros(process, "wait_count").fillna(0)
        process["stop_norm"] = _norm(process["stop_time"] if "stop_time" in process.columns else pd.Series([0] * len(process)))
        process["defect_norm"] = _norm(process["fail_rate"] if "fail_rate" in process.columns else pd.Series([0] * len(process)))
        process["wait_norm"] = _norm(process["wait_count"])
        process["ct_norm"] = _norm(process["ct_std_sec"])
        process["throughput_norm"] = 1 - _norm(process["output_qty"] if "output_qty" in process.columns else pd.Series([0] * len(process)))
        process["bottleneck_norm"] = (
            process["stop_norm"] * 0.35
            + process["defect_norm"] * 0.25
            + process["wait_norm"] * 0.20
            + process["ct_norm"] * 0.20
        )
        process["문제유형"] = process.apply(_issue_type_process, axis=1)
        process["해석"] = process.apply(
            lambda r: "output 저하와 stop 증가가 함께 보여 전형적 병목입니다."
            if _safe_float(r.get("stop_time", 0)) > 0.7 and _safe_float(r.get("output_qty", 0)) <= _safe_float(process["output_qty"].median() if not process.empty else 0)
            else ("wait 증가로 전후공정 연계 문제를 먼저 봐야 합니다." if _safe_float(r.get("wait_count", 0)) > 0.6 else "CT 편차와 stop reason을 함께 봐야 합니다."),
            axis=1,
        )
        process["개선액션"] = process.apply(_action_process, axis=1)

    if not lot.empty:
        lot["retry_rate"] = _series_or_zeros(lot, "retry_rate").fillna(0)
        lot["impact_norm"] = _norm(lot["impact_score"] if "impact_score" in lot.columns else pd.Series([0] * len(lot)))
        lot["stop_norm"] = _norm(lot["stop_time"] if "stop_time" in lot.columns else pd.Series([0] * len(lot)))
        lot["defect_norm"] = _norm(lot["fail_rate"] if "fail_rate" in lot.columns else pd.Series([0] * len(lot)))
        lot["spread_norm"] = _norm(_series_or_zeros(lot, "machine_count").fillna(0) + _series_or_zeros(lot, "process_count").fillna(0))
        lot["retry_norm"] = _norm(lot["retry_rate"])
        lot["priority_score"] = (
            lot["impact_norm"] * 0.40
            + lot["stop_norm"] * 0.25
            + lot["defect_norm"] * 0.20
            + lot["spread_norm"] * 0.15
        )
        lot["문제유형"] = lot.apply(_issue_type_lot, axis=1)
        lot["해석"] = lot.apply(
            lambda r: "특정 설비에 국한된 국소 문제 가능성이 높습니다."
            if _safe_float(r.get("machine_count", 0)) <= 1.0
            else ("다수 공정/설비로 번지는 전파형 문제 가능성이 높습니다." if _safe_float(r.get("process_count", 0)) > _safe_float(r.get("machine_count", 0)) else "LOT 영향과 산출 손실을 함께 봐야 합니다."),
            axis=1,
        )
        lot["개선액션"] = lot.apply(_action_lot, axis=1)

    if not quality_overview.empty and "scope" in quality_overview.columns:
        quality_overview = quality_overview.copy()

    total_stop_time = _safe_float(equipment["stop_time"].sum() if not equipment.empty and "stop_time" in equipment.columns else 0)
    total_defect_count = _safe_float(filtered_insp[filtered_insp.get("quality_flag", pd.Series(dtype=str)).astype(str).eq("FAIL")].shape[0] if not filtered_insp.empty and "quality_flag" in filtered_insp.columns else 0)
    total_insp = _safe_float(len(filtered_insp))
    total_defect_rate = _safe_div(total_defect_count, total_insp)
    total_retry_rate = _safe_float(lot["retry_rate"].mean() if not lot.empty and "retry_rate" in lot.columns else 0)
    total_wait_count = _safe_float(filtered_tag[filtered_tag.get("event_class", pd.Series(dtype=str)).astype(str).eq("WAIT")].shape[0] if not filtered_tag.empty and "event_class" in filtered_tag.columns else 0)
    bottleneck_stage = process.sort_values("bottleneck_norm", ascending=False).iloc[0] if not process.empty else pd.Series(dtype="object")
    impact_lot_count = _safe_float((lot["impact_score"] > lot["impact_score"].median()).sum() if not lot.empty and "impact_score" in lot.columns else 0)
    top_machine = equipment.sort_values("severity_score", ascending=False).iloc[0] if not equipment.empty else pd.Series(dtype="object")
    top_process = process.sort_values("bottleneck_norm", ascending=False).iloc[0] if not process.empty else pd.Series(dtype="object")
    top_lot = lot.sort_values("priority_score", ascending=False).iloc[0] if not lot.empty else pd.Series(dtype="object")

    machine_stop_th = pd.to_numeric(equipment["stop_time"], errors="coerce").quantile(0.75) if not equipment.empty and "stop_time" in equipment.columns else 0
    machine_defect_th = pd.to_numeric(equipment["defect_rate"], errors="coerce").quantile(0.75) if not equipment.empty and "defect_rate" in equipment.columns else 0
    machine_wait_th = pd.to_numeric(equipment["wait_count"], errors="coerce").quantile(0.75) if not equipment.empty and "wait_count" in equipment.columns else 0
    process_output_th = pd.to_numeric(process["output_qty"], errors="coerce").quantile(0.25) if not process.empty and "output_qty" in process.columns else 0
    process_stop_th = pd.to_numeric(process["stop_time"], errors="coerce").quantile(0.75) if not process.empty and "stop_time" in process.columns else 0
    lot_spread_th = pd.to_numeric((lot.get("machine_count", 0) + lot.get("process_count", 0)), errors="coerce").quantile(0.75) if not lot.empty else 0
    lot_machine_th = pd.to_numeric(lot.get("machine_count", pd.Series([0])), errors="coerce").quantile(0.25) if not lot.empty else 0
    lot_process_th = pd.to_numeric(lot.get("process_count", pd.Series([0])), errors="coerce").quantile(0.75) if not lot.empty else 0
    lot_impact_th = pd.to_numeric(lot.get("impact_score", pd.Series([0])), errors="coerce").quantile(0.75) if not lot.empty else 0

    if not equipment.empty:
        equipment["problem_type"] = equipment.apply(
            lambda r: _problem_type_from_signals(
                _safe_float(r.get("stop_time", 0)),
                _safe_float(r.get("defect_rate", 0)),
                _safe_float(r.get("wait_count", 0)),
                _safe_float(r.get("retry_rate", 0)),
                machine_stop_th,
                machine_defect_th,
                machine_wait_th,
            ),
            axis=1,
        )
        equipment["quadrant"] = equipment.apply(
            lambda r: _quadrant_label(_safe_float(r.get("stop_time", 0)), _safe_float(r.get("defect_rate", 0)), machine_stop_th, machine_defect_th),
            axis=1,
        )
        equipment["confidence"] = equipment.apply(lambda r: _confidence_label(True, bool(_safe_float(r.get("wait_count", 0)) > 0 or _safe_float(r.get("retry_rate", 0)) > 0)), axis=1)
        equipment["status_label"] = equipment["quadrant"].map(_status_badge)
    if not process.empty:
        process["problem_type"] = process.apply(
            lambda r: _problem_type_from_signals(
                _safe_float(r.get("stop_time", 0)),
                _safe_float(r.get("fail_rate", r.get("defect_rate", 0))),
                _safe_float(r.get("wait_count", 0)),
                _safe_float(r.get("ct_std_sec", 0)),
                process_stop_th,
                pd.to_numeric(process["fail_rate"], errors="coerce").quantile(0.75) if "fail_rate" in process.columns else 0,
                pd.to_numeric(process["wait_count"], errors="coerce").quantile(0.75) if "wait_count" in process.columns else 0,
            ),
            axis=1,
        )
        process["confidence"] = process.apply(lambda r: _confidence_label(True, bool(_safe_float(r.get("wait_count", 0)) > 0)), axis=1)
    if not lot.empty:
        lot["problem_type"] = lot.apply(
            lambda r: "전파 LOT 문제"
            if _safe_float(r.get("process_count", 0)) >= lot_spread_th
            else ("국소 LOT 문제" if _safe_float(r.get("machine_count", 0)) <= 1 else ("우선 점검 LOT" if _safe_float(r.get("impact_score", 0)) >= 0.75 else "주의")),
            axis=1,
        )
        lot["confidence"] = lot.apply(lambda r: _confidence_label(True, bool(_safe_float(r.get("retry_rate", 0)) > 0)), axis=1)

    if not equipment.empty:
        equipment["분류 근거"] = equipment.apply(lambda r: _classification_basis_machine(r, machine_stop_th, machine_defect_th, machine_wait_th), axis=1)
    if not process.empty:
        process["분류 근거"] = process.apply(
            lambda r: _classification_basis_process(
                r,
                process_output_th,
                process_stop_th,
                pd.to_numeric(process["wait_count"], errors="coerce").quantile(0.75) if "wait_count" in process.columns else 0,
                pd.to_numeric(process["ct_std_sec"], errors="coerce").quantile(0.75) if "ct_std_sec" in process.columns else 0,
            ),
            axis=1,
        )
    if not lot.empty:
        lot["분류 근거"] = lot.apply(lambda r: _classification_basis_lot(r, lot_machine_th, lot_process_th, lot_impact_th), axis=1)

    alert_rows = []
    if not equipment.empty and _safe_float(top_machine.get("severity_score", 0)) >= 0.7:
        alert_rows.append({
            "대상": str(top_machine.get("machine_id", "-")),
            "경고": f"{top_machine.get('problem_type', '정상')} / {top_machine.get('quadrant', '정상')}",
            "액션": top_machine.get("개선액션", "-"),
        })
    if not process.empty and _safe_float(top_process.get("bottleneck_norm", 0)) >= 0.7:
        alert_rows.append({
            "대상": str(top_process.get("process_display", top_process.get("process_name", "-"))),
            "경고": str(top_process.get("problem_type", "정상")),
            "액션": top_process.get("개선액션", "-"),
        })
    if not lot.empty and _safe_float(top_lot.get("priority_score", 0)) >= 0.7:
        alert_rows.append({
            "대상": str(top_lot.get("lot_id", "-")),
            "경고": str(top_lot.get("problem_type", "정상")),
            "액션": top_lot.get("개선액션", "-"),
        })

    stop_reason = (
        filtered_stop.groupby("stop_like_reason", as_index=False).agg(loss_time=("duration_sec", "sum"), event_count=("stop_count", "sum")).sort_values("loss_time", ascending=False)
        if not filtered_stop.empty and "stop_like_reason" in filtered_stop.columns
        else pd.DataFrame(columns=["stop_like_reason", "loss_time", "event_count"])
    )
    wait_reason = (
        filtered_tag[filtered_tag["event_class"].eq("WAIT")].groupby("cause_detail", as_index=False).agg(wait_count=("event_class", "size")).sort_values("wait_count", ascending=False)
        if not filtered_tag.empty and "event_class" in filtered_tag.columns and "cause_detail" in filtered_tag.columns
        else pd.DataFrame(columns=["cause_detail", "wait_count"])
    )
    defect_reason = (
        filtered_insp.groupby("quality_flag", as_index=False).agg(defect_count=("quality_flag", "size")).sort_values("defect_count", ascending=False)
        if not filtered_insp.empty and "quality_flag" in filtered_insp.columns
        else pd.DataFrame(columns=["quality_flag", "defect_count"])
    )

    hour_view = time_view[time_view["grain"].eq("hour")].copy() if not time_view.empty and "grain" in time_view.columns else pd.DataFrame()
    shift_view = time_view[time_view["grain"].eq("shift")].copy() if not time_view.empty and "grain" in time_view.columns else pd.DataFrame()

    priority_parts = []
    if not equipment.empty:
        tmp = equipment.copy()
        tmp["대상유형"] = "설비"
        tmp["대상"] = tmp["machine_id"].astype(str)
        tmp["문제유형"] = tmp["문제유형"] if "문제유형" in tmp.columns else "주의"
        tmp["priority_score"] = tmp["severity_score"]
        tmp["근거 KPI"] = tmp.apply(lambda r: f"stop { _fmt_sec_base(_safe_float(r.get('stop_time', 0))) } / defect {_fmt_pct(r.get('defect_rate', 0)) }", axis=1)
        tmp["예상 영향"] = tmp.apply(lambda r: "정지와 불량 동시 개선" if r.get("문제유형") == "복합 문제형" else "정지 또는 품질 개선", axis=1)
        tmp["추천 액션"] = tmp["개선액션"] if "개선액션" in tmp.columns else "설비 조건 점검"
        tmp["기대 효과"] = tmp.apply(lambda r: "stop/defect 동시 개선 가능" if r.get("상태 등급") == "개선필요" else "일부 손실 회수", axis=1)
        priority_parts.append(tmp[["대상유형", "대상", "문제유형", "priority_score", "근거 KPI", "예상 영향", "추천 액션", "기대 효과"]])
    if not process.empty:
        tmp = process.copy()
        tmp["대상유형"] = "공정"
        tmp["대상"] = tmp["process_display"].astype(str)
        tmp["문제유형"] = tmp["문제유형"] if "문제유형" in tmp.columns else "주의"
        tmp["priority_score"] = tmp["bottleneck_norm"]
        tmp["근거 KPI"] = tmp.apply(lambda r: f"output {_safe_float(r.get('output_qty', 0)):.0f} / stop {_fmt_sec_base(_safe_float(r.get('stop_time', 0)))}", axis=1)
        tmp["예상 영향"] = tmp.apply(lambda r: "throughput 회복" if "병목" in str(r.get("문제유형", "")) else "품질 안정화", axis=1)
        tmp["추천 액션"] = tmp["개선액션"] if "개선액션" in tmp.columns else "공정 조건 점검"
        tmp["기대 효과"] = tmp.apply(lambda r: "병목 완화" if r.get("priority_score", 0) >= 0.7 else "공정 안정성 향상", axis=1)
        priority_parts.append(tmp[["대상유형", "대상", "문제유형", "priority_score", "근거 KPI", "예상 영향", "추천 액션", "기대 효과"]])
    if not lot.empty:
        tmp = lot.copy()
        tmp["대상유형"] = "LOT"
        tmp["대상"] = tmp["lot_id"].astype(str)
        tmp["문제유형"] = tmp["문제유형"] if "문제유형" in tmp.columns else "주의"
        tmp["priority_score"] = tmp["priority_score"] if "priority_score" in tmp.columns else tmp["impact_score"]
        tmp["근거 KPI"] = tmp.apply(lambda r: f"impact {_safe_float(r.get('impact_score', 0)):.1f} / stop {_fmt_sec_base(_safe_float(r.get('stop_time', 0)))}", axis=1)
        tmp["예상 영향"] = tmp.apply(lambda r: "다중 설비/공정 전파 차단" if _safe_float(r.get("process_count", 0)) > _safe_float(r.get("machine_count", 0)) else "국소 LOT 문제 차단", axis=1)
        tmp["추천 액션"] = tmp["개선액션"] if "개선액션" in tmp.columns else "LOT trace 확인"
        tmp["기대 효과"] = tmp.apply(lambda r: "재발 범위 축소" if r.get("priority_score", 0) >= 0.7 else "영향 LOT 분리", axis=1)
        priority_parts.append(tmp[["대상유형", "대상", "문제유형", "priority_score", "근거 KPI", "예상 영향", "추천 액션", "기대 효과"]])
    priority = pd.concat(priority_parts, ignore_index=True, sort=False) if priority_parts else pd.DataFrame()
    if not priority.empty:
        priority = priority.sort_values("priority_score", ascending=False).head(10).copy()
        priority["순위"] = np.arange(1, len(priority) + 1)
        priority = priority[["순위", "대상유형", "대상", "문제유형", "근거 KPI", "예상 영향", "추천 액션", "기대 효과", "priority_score"]]

    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("### 2. 문제 분석 및 개선")
    st.caption("이 탭은 고객이 설비 / 공정 / LOT / 정지 / 불량을 한 화면에서 연결해 보고, 바로 개선 우선순위를 정하는 화면입니다.")
    st.markdown(
        """
        <div style="margin:.4rem 0 1rem 0;padding:.75rem .9rem;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:#d7dee8;">
            <b>읽는 순서</b> : 전체 문제 요약 → 설비 문제 → 공정 병목 → 정지/대기 원인 → 불량/미스 → LOT 영향 → 개선 우선순위
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [
        ("총 정지 시간", _fmt_sec_base(total_stop_time), "절대 정지 손실"),
        ("총 불량률", _fmt_pct(total_defect_rate), "불량 비율"),
        ("총 재작업률", _fmt_pct(total_retry_rate), "재작업 추정치"),
        ("총 대기 건수", f"{int(total_wait_count):,}", "대기 이벤트 수"),
        ("병목 공정", str(bottleneck_stage.get("process_display", bottleneck_stage.get("process_name", "-"))), "bottleneck_score 최고"),
        ("영향 LOT", f"{int(impact_lot_count):,}", "중간 이상 영향 LOT"),
    ]
    for col, (label, value, foot) in zip([c1, c2, c3, c4, c5, c6], cards):
        with col:
            st.markdown(_card(label, value, foot), unsafe_allow_html=True)

    if alert_rows:
        st.markdown("#### 경보 현황")
        alert_df = pd.DataFrame(alert_rows)
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
    else:
        st.info("현재 필터 조건에서 즉시 경고 수준의 이상은 제한적입니다.")

    st.markdown("#### 행동형 인사이트 카드")
    insight_cols = st.columns(3)
    insight_items = [
        {
            "target": str(top_machine.get("machine_id", "-")),
            "type": str(top_machine.get("problem_type", "정상")),
            "evidence": f"정지 { _fmt_sec_base(_safe_float(top_machine.get('stop_time', 0))) } / 불량 { _fmt_pct(top_machine.get('defect_rate', 0)) } / 대기 { int(_safe_float(top_machine.get('wait_count', 0))) }",
            "cause": str(top_machine.get("top_wait_reason", top_machine.get("top_stop_reason", "-"))),
            "action": str(top_machine.get("개선액션", "설비 조건 점검")),
            "confidence": str(top_machine.get("confidence", "Actual")),
        },
        {
            "target": str(top_process.get("process_display", top_process.get("process_name", "-"))),
            "type": str(top_process.get("problem_type", "정상")),
            "evidence": f"출력 {_safe_float(top_process.get('output_qty', 0)):.0f} / 정지 {_fmt_sec_base(_safe_float(top_process.get('stop_time', 0)))} / 대기 {int(_safe_float(top_process.get('wait_count', 0)))}",
            "cause": str(top_process.get("bottleneck_hint", top_process.get("문제유형", "-"))),
            "action": str(top_process.get("개선액션", "공정 조건 점검")),
            "confidence": str(top_process.get("confidence", "Actual")),
        },
        {
            "target": str(top_lot.get("lot_id", "-")),
            "type": str(top_lot.get("problem_type", "정상")),
            "evidence": f"영향도 {_safe_float(top_lot.get('impact_score', 0)):.1f} / 확산 {int(_safe_float(top_lot.get('machine_count', 0)) + _safe_float(top_lot.get('process_count', 0)))}",
            "cause": f"확산 = 설비 {int(_safe_float(top_lot.get('machine_count', 0)))}개 / 공정 {int(_safe_float(top_lot.get('process_count', 0)))}개",
            "action": str(top_lot.get("개선액션", "LOT trace 확인")),
            "confidence": str(top_lot.get("confidence", "Actual")),
        },
    ]
    for col, item in zip(insight_cols, insight_items):
        with col:
            st.markdown(
                f"""
                <div style="padding:.9rem 1rem;border-radius:16px;background:linear-gradient(180deg,#141b28,#0f1520);border:1px solid rgba(255,255,255,.08);min-height:180px">
                    <div style="font-size:.78rem;color:#9fb0c4;">대상</div>
                    <div style="font-size:1.15rem;font-weight:800;color:#fff;margin:.15rem 0 .35rem 0;">{item['target']}</div>
                    <div style="margin-bottom:.3rem;color:#ffd1a1;font-weight:700;">분류: {item['type']}</div>
                    <div style="font-size:.82rem;color:#c8d2df;">{item['evidence']}</div>
                    <div style="font-size:.82rem;color:#c8d2df;margin-top:.25rem;">원인: {item['cause']}</div>
                    <div style="font-size:.82rem;color:#9ad7ff;margin-top:.35rem;">권장 조치: {item['action']}</div>
                    <div style="font-size:.75rem;color:#8ea1b7;margin-top:.35rem;">신뢰도: {item['confidence']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(_section_header("전체 문제 요약", "고객이 첫 화면에서 어디가 문제인지 바로 보게 하는 구역", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.5, 0.5])
    with left:
        st.markdown("#### 문제 대상 상위 3개")
        summary_rows = []
        if not equipment.empty:
            for _, row in equipment.sort_values("severity_score", ascending=False).head(3).iterrows():
                summary_rows.append({
                    "대상": str(row.get("machine_id", "-")),
                    "분류": row.get("문제유형", "-"),
                    "분류 근거": row.get("분류 근거", "-"),
                    "개선 아이디어": row.get("개선액션", "-"),
                })
        if not process.empty:
            for _, row in process.sort_values("bottleneck_norm", ascending=False).head(3).iterrows():
                summary_rows.append({
                    "대상": f"{row.get('process_display', row.get('process_name', '-'))}",
                    "분류": row.get("문제유형", "-"),
                    "분류 근거": row.get("분류 근거", "-"),
                    "개선 아이디어": row.get("개선액션", "-"),
                })
        if not lot.empty:
            for _, row in lot.sort_values("priority_score", ascending=False).head(3).iterrows():
                summary_rows.append({
                    "대상": str(row.get("lot_id", "-")),
                    "분류": row.get("문제유형", "-"),
                    "분류 근거": row.get("분류 근거", "-"),
                    "개선 아이디어": row.get("개선액션", "-"),
                })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
        st.markdown("#### 분류 기준 표")
        basis_rows = []
        if not equipment.empty:
            for _, row in equipment.sort_values("severity_score", ascending=False).head(2).iterrows():
                basis_rows.append({"구분": "설비", "대상": str(row.get("machine_id", "-")), "분류": row.get("문제유형", "-"), "기준": row.get("분류 근거", "-")})
        if not process.empty:
            for _, row in process.sort_values("bottleneck_norm", ascending=False).head(2).iterrows():
                basis_rows.append({"구분": "공정", "대상": str(row.get("process_display", row.get("process_name", "-"))), "분류": row.get("문제유형", "-"), "기준": row.get("분류 근거", "-")})
        if not lot.empty:
            for _, row in lot.sort_values("priority_score", ascending=False).head(2).iterrows():
                basis_rows.append({"구분": "LOT", "대상": str(row.get("lot_id", "-")), "분류": row.get("문제유형", "-"), "기준": row.get("분류 근거", "-")})
        st.dataframe(pd.DataFrame(basis_rows), use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### 원인 및 시간대")
        rc1, rc2 = st.columns(2)
        rc3, rc4 = st.columns(2)
        with rc1:
            if not stop_reason.empty:
                fig = px.bar(stop_reason.head(5), x="stop_like_reason", y="loss_time", text="loss_time", title="상위 정지 원인")
                st.plotly_chart(_plot_style(fig, "상위 정지 원인", 260), use_container_width=True)
        with rc2:
            if not wait_reason.empty:
                fig = px.bar(wait_reason.head(5), x="cause_detail", y="wait_count", text="wait_count", title="상위 대기 원인")
                st.plotly_chart(_plot_style(fig, "상위 대기 원인", 260), use_container_width=True)
        with rc3:
            if not defect_reason.empty:
                fig = px.bar(defect_reason.head(5), x="quality_flag", y="defect_count", text="defect_count", title="상위 불량 유형")
                st.plotly_chart(_plot_style(fig, "상위 불량 유형", 260), use_container_width=True)
        with rc4:
            if not hour_view.empty and "stop_time" in hour_view.columns:
                fig = px.line(hour_view, x="bucket", y="stop_time", markers=True, title="정지 집중 시간대")
                st.plotly_chart(_plot_style(fig, "정지 집중 시간대", 260), use_container_width=True)

    st.markdown(_section_header("설비별 문제 분석", "설비별 stop / defect / wait / CT 편차를 한 번에 보는 구역", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not equipment.empty:
            machine_table = equipment.sort_values("severity_score", ascending=False).head(10).copy()
            display_cols = [c for c in ["machine_id", "line_id", "stage_no", "stop_time", "stop_count", "defect_rate", "retry_rate", "avg_ct_sec", "ct_std_sec", "wait_count", "top_stop_reason", "top_wait_reason", "status_label", "problem_type", "분류 근거", "confidence", "해석", "개선액션"] if c in machine_table.columns]
            st.dataframe(machine_table[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("설비 분석 데이터가 부족합니다.")
    with right:
        if not equipment.empty:
            x_th = machine_stop_th if pd.notna(machine_stop_th) else pd.to_numeric(equipment["stop_time"], errors="coerce").median()
            y_th = machine_defect_th if pd.notna(machine_defect_th) else pd.to_numeric(equipment["defect_rate"], errors="coerce").median()
            machine_plot = equipment.copy()
            machine_plot["quadrant"] = machine_plot.apply(
                lambda r: _quadrant_label(_safe_float(r.get("stop_time", 0)), _safe_float(r.get("defect_rate", 0)), x_th, y_th),
                axis=1,
            )
            fig = px.scatter(
                machine_plot,
                x="stop_time",
                y="defect_rate",
                size="retry_rate" if "retry_rate" in machine_plot.columns else None,
                color="quadrant",
                hover_name="machine_id",
                text="machine_id",
                color_discrete_map={
                    "심각": "#ef4444",
                    "생산성 손실형": "#f59e0b",
                    "품질 집중형": "#3b82f6",
                    "정상": "#64748b",
                },
            )
            fig.add_vline(x=x_th, line_dash="dash", line_color="#94a3b8")
            fig.add_hline(y=y_th, line_dash="dash", line_color="#94a3b8")
            fig.update_layout(legend_title_text="분류 구역")
            st.plotly_chart(_plot_style(fig, "설비별 정지-불량 분류도", 320), use_container_width=True)
            if "top_stop_reason" in equipment.columns:
                reason_fig = px.bar(equipment.sort_values("severity_score", ascending=False).head(8), x="machine_id", y="stop_time", color="top_stop_reason", text="stop_time")
                st.plotly_chart(_plot_style(reason_fig, "설비별 정지 원인 순위", 280), use_container_width=True)
            st.markdown("##### 분류 해석 기준")
            st.markdown("- 심각: 정지와 불량이 동시에 높아 즉시 점검이 필요합니다.")
            st.markdown("- 생산성 손실형: 정지가 높고 불량은 낮아 설비/연계 손실이 핵심입니다.")
            st.markdown("- 품질 집중형: 불량이 높고 정지는 낮아 조건/자재/비전 점검이 우선입니다.")
            st.markdown("- 다음 확인: 상위 정지 원인과 대기 원인입니다.")

    st.markdown(_section_header("공정별 병목 분석", "output / stop / defect / wait / CT 편차로 병목을 판정하는 구역", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not process.empty:
            process_table = process.sort_values("bottleneck_norm", ascending=False).head(10).copy()
            display_cols = [c for c in ["process_display", "line_id", "stage_no", "output_qty", "stop_time", "fail_rate", "wait_count", "avg_ct_sec", "ct_std_sec", "bottleneck_norm", "problem_type", "분류 근거", "confidence", "해석", "개선액션"] if c in process_table.columns]
            st.dataframe(process_table[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("공정 분석 데이터가 부족합니다.")
    with right:
        if not process.empty:
            fig = px.scatter(
                process,
                x="output_qty",
                y="stop_time",
                size="bottleneck_norm",
                color="문제유형" if "문제유형" in process.columns else None,
                hover_name="process_display",
                text="process_display",
            )
            st.plotly_chart(_plot_style(fig, "공정별 출력-정지 분류도", 320), use_container_width=True)
            if "wait_count" in process.columns:
                fig = px.bar(process.sort_values("bottleneck_norm", ascending=False), x="process_display", y="wait_count", text="wait_count")
                st.plotly_chart(_plot_style(fig, "공정별 대기 분포", 280), use_container_width=True)
            st.markdown("##### 분류 해석 기준")
            st.markdown("- 정지 병목: 출력이 낮고 정지가 높아 흐름을 직접 막는 공정입니다.")
            st.markdown("- 품질 병목: 정지는 낮지만 불량이 높아 검사/조건 재점검이 필요합니다.")
            st.markdown("- 흐름 병목: 대기가 높아 전후공정 밸런스부터 봐야 합니다.")
            st.markdown("- 안정성 문제: CT 편차가 커서 takt drift와 recipe 변화를 확인해야 합니다.")

    st.markdown(_section_header("정지·대기 원인 분석", "정지와 대기를 분리해서 손실 구조를 보는 구역", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.56, 0.44])
    with left:
        if not stop_reason.empty:
            st.markdown("#### 정지 원인 상위 10개")
            st.dataframe(stop_reason.head(10), use_container_width=True, hide_index=True)
        if not wait_reason.empty:
            st.markdown("#### 대기 원인 상위 10개")
            st.dataframe(wait_reason.head(10), use_container_width=True, hide_index=True)
        st.markdown("#### 원인별 개선 방향")
        reason_map = pd.DataFrame(
            [
                {"원인": "Bwait / McFwait", "분류": "전공정 불균형", "개선 방향": "전공정 공급, feeder 보급, 버퍼 조정"},
                {"원인": "Rwait / McRwait", "분류": "후공정 적체", "개선 방향": "후공정 처리능력, 대기 버퍼, 인원 배치"},
                {"원인": "Cwait", "분류": "검사/비전 지연", "개선 방향": "camera, vision, review capacity 점검"},
                {"원인": "Pwait", "분류": "pickup/공급 문제", "개선 방향": "nozzle, feeder, reel, 보급 타이밍 점검"},
                {"원인": "CnvStop", "분류": "전달/인터락 문제", "개선 방향": "conveyor sensor, interlock, transfer 확인"},
                {"원인": "SCStop / SCEStop", "분류": "알람/시스템 불안정", "개선 방향": "알람 코드, 시스템 안정성, 재발 조건 확인"},
                {"원인": "OthrStop", "분류": "미분류", "개선 방향": "stop code 세분화 및 기록 표준화"},
            ]
        )
        st.dataframe(reason_map, use_container_width=True, hide_index=True)
    with right:
        right_top, right_bottom = st.columns(2)
        with right_top:
            if not hour_view.empty:
                metric_col = "stop_time" if "stop_time" in hour_view.columns and hour_view["stop_time"].sum() > 0 else "error_count"
                fig = px.bar(hour_view, x="bucket", y=metric_col, text=metric_col)
                st.plotly_chart(_plot_style(fig, "시간대별 정지 집중", 280), use_container_width=True)
        with right_bottom:
            if not shift_view.empty:
                metric_col = "stop_time" if "stop_time" in shift_view.columns else "error_count"
                fig = px.bar(shift_view, x="bucket", y=metric_col, text=metric_col)
                st.plotly_chart(_plot_style(fig, "Shift별 정지 비교", 280), use_container_width=True)

    st.markdown(_section_header("불량 / 미스 분석", "미스 유형과 불량이 어디서 발생하는지 보는 구역", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.56, 0.44])
    miss_view = pd.DataFrame()
    if not filtered_insp.empty and "quality_flag" in filtered_insp.columns:
        miss_view = filtered_insp["quality_flag"].astype(str).value_counts().reset_index()
        miss_view.columns = ["quality_flag", "count"]
    with left:
        if not miss_view.empty:
            st.markdown("#### 미스 유형 분포")
            st.dataframe(miss_view, use_container_width=True, hide_index=True)
        if not lot.empty:
            st.markdown("#### LOT 영향 상위 10개")
            lot_table = lot.sort_values("priority_score", ascending=False).head(10).copy()
            display_cols = [c for c in ["lot_id", "model_label", "output_qty", "stop_time", "fail_rate", "retry_rate", "impact_score", "machine_count", "process_count", "stop_machine_count", "stop_process_count", "representative_machine", "representative_process", "problem_type", "분류 근거", "confidence", "해석", "개선액션"] if c in lot_table.columns]
            st.dataframe(lot_table[display_cols], use_container_width=True, hide_index=True)
        st.markdown("#### 미스 유형별 개선 방향")
        miss_map = pd.DataFrame(
            [
                {"미스": "PMiss", "해석": "흡착 실패", "개선 방향": "nozzle, feeder, reel 공급 안정성 점검"},
                {"미스": "DMiss", "해석": "인식 실패", "개선 방향": "camera, lighting, vision threshold 점검"},
                {"미스": "HMiss", "해석": "헤드 실패", "개선 방향": "head calibration, 흡착 조건 점검"},
                {"미스": "MMiss", "해석": "배치 오프셋", "개선 방향": "placement offset, board alignment 보정"},
                {"미스": "RMiss", "해석": "리젝트 판정", "개선 방향": "reject 로직과 판정 기준 재점검"},
            ]
        )
        st.dataframe(miss_map, use_container_width=True, hide_index=True)
    with right:
        right_top, right_bottom = st.columns(2)
        with right_top:
            if not filtered_insp.empty and "quality_flag" in filtered_insp.columns:
                fig = px.bar(miss_view.head(5), x="quality_flag", y="count", text="count")
                st.plotly_chart(_plot_style(fig, "미스 분포", 260), use_container_width=True)
            if not hour_view.empty and "error_count" in hour_view.columns:
                fig = px.line(hour_view, x="bucket", y="error_count", markers=True)
                st.plotly_chart(_plot_style(fig, "시간대별 불량 추이", 260), use_container_width=True)
        with right_bottom:
            if not process.empty and "fail_rate" in process.columns:
                fig = px.bar(process.sort_values("fail_rate", ascending=False), x="process_display", y="fail_rate", text="fail_rate")
                st.plotly_chart(_plot_style(fig, "공정별 불량률", 260), use_container_width=True)
            if not equipment.empty and "defect_rate" in equipment.columns:
                fig = px.bar(equipment.sort_values("defect_rate", ascending=False).head(8), x="machine_id", y="defect_rate", text="defect_rate")
                st.plotly_chart(_plot_style(fig, "설비별 불량률", 260), use_container_width=True)
        st.markdown("##### 분류 해석 기준")
        st.markdown("- PMiss는 흡착/공급, DMiss는 인식/조명, HMiss는 헤드, MMiss는 위치 보정, RMiss는 리젝트 로직을 먼저 봅니다.")
        st.markdown("- Retry가 증가하면 첫 통과 품질이 흔들리고 있다는 뜻입니다.")

    st.markdown(_section_header("LOT 영향 분석", "문제가 특정 LOT에 국한되는지, 다수 공정으로 번지는지 보는 구역", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not lot.empty:
            lot_cols = [c for c in ["lot_id", "model_label", "output_qty", "stop_time", "fail_rate", "retry_rate", "impact_score", "machine_count", "process_count", "stop_machine_count", "stop_process_count", "representative_machine", "representative_process", "problem_type", "분류 근거", "confidence", "해석", "개선액션"] if c in lot.columns]
            st.dataframe(lot.sort_values("priority_score", ascending=False).head(10)[lot_cols], use_container_width=True, hide_index=True)
        else:
            st.info("LOT 분석 데이터가 부족합니다.")
    with right:
        right_top, right_bottom = st.columns(2)
        with right_top:
            if not lot.empty:
                fig = px.scatter(
                    lot,
                    x="machine_count" if "machine_count" in lot.columns else "impact_score",
                    y="process_count" if "process_count" in lot.columns else "impact_score",
                    size="impact_score" if "impact_score" in lot.columns else None,
                    color="문제유형" if "문제유형" in lot.columns else None,
                    hover_name="lot_id",
                    text="lot_id",
                )
                st.plotly_chart(_plot_style(fig, "LOT 확산-영향 분류도", 280), use_container_width=True)
        with right_bottom:
            if not lot.empty:
                fig = px.bar(lot.sort_values("impact_score", ascending=False).head(8), x="lot_id", y="impact_score", text="impact_score")
                st.plotly_chart(_plot_style(fig, "LOT 영향도 상위 8개", 280), use_container_width=True)
        st.markdown("##### 분류 해석 기준")
        st.markdown("- machine_count가 낮고 impact_score가 높으면 국소 LOT 문제입니다.")
        st.markdown("- process_count가 높으면 다수 공정으로 퍼지는 전파 LOT 문제입니다.")
        st.markdown("- 다음 확인: 대표 설비와 대표 공정입니다.")

    st.markdown(_section_header("개선 우선순위", "고객이 바로 무엇부터 할지 정하는 구역", PRIMARY), unsafe_allow_html=True)
    if not priority.empty:
        st.dataframe(priority, use_container_width=True, hide_index=True)
        st.markdown("#### 우선순위 산정 방식")
        st.markdown("- 정지 영향도, 불량 영향도, LOT 확산도, 반복 발생도를 합산합니다.")
        st.markdown("- `정지 + 불량 + 확산 + 반복`이 동시에 높은 대상을 먼저 개선합니다.")
    else:
        st.info("개선 우선순위를 만들 데이터가 부족합니다.")

    st.markdown("#### 자동 코멘트 예시")
    if not equipment.empty:
        st.markdown(f"- `{top_machine.get('machine_id', '-')}`: {top_machine.get('해석', '설비 조건을 점검해야 합니다.')} {top_machine.get('개선액션', '')}")
    if not process.empty:
        st.markdown(f"- `{top_process.get('process_display', top_process.get('process_name', '-'))}`: {top_process.get('해석', '공정 흐름을 점검해야 합니다.')} {top_process.get('개선액션', '')}")
    if not lot.empty:
        st.markdown(f"- `{top_lot.get('lot_id', '-')}`: {top_lot.get('해석', 'LOT 영향 범위를 확인해야 합니다.')} {top_lot.get('개선액션', '')}")
    st.markdown("#### 개선 액션 분류")
    st.markdown("- 설비 조건 개선: nozzle, feeder, head calibration, vision, conveyor/interlock")
    st.markdown("- 공정 조건 개선: line balance, buffer, recipe, review capacity, takt 안정화")
    st.markdown("- 자재/운영 개선: reel 품질, vendor lot, 교대시간, 보급 타이밍, reason 코드 정비")
    st.markdown("- 데이터 개선: stop/wait 구분, reason 코드 세분화, raw event 보강")
    st.markdown("#### 해석 주의")
    st.markdown("- Retry는 현재 데이터에서 원천 필드가 없으면 검사 중복 proxy로 계산합니다.")
    st.markdown("- CT는 event timestamp 간격 proxy이므로 설비 내부 cycle time과 다를 수 있습니다.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_equipment_screen(clean: Dict[str, pd.DataFrame], marts: Dict[str, pd.DataFrame]):
    item = clean.get("vw_mounter_item_fact", pd.DataFrame()).copy()
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("### 2. Mounter 문제 분석 및 개선")
    st.caption("이 탭은 mounter 테이블만 사용해 설비 / 공정 / LOT의 출력 집중도와 cycle 변동을 기준으로 판단합니다.")

    if item.empty:
        st.info("mounter 데이터가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    item["event_ts"] = pd.to_datetime(item.get("event_ts"), errors="coerce")
    item["day"] = pd.to_datetime(item["event_ts"], errors="coerce").dt.date
    item["hour"] = pd.to_datetime(item["event_ts"], errors="coerce").dt.hour
    item["shift"] = item["hour"].map(lambda h: "주간(06-14)" if pd.notna(h) and 6 <= int(h) < 14 else "석간(14-22)" if pd.notna(h) and 14 <= int(h) < 22 else "야간(22-06)" if pd.notna(h) else "미상")
    if "output_qty" in item.columns:
        item["output_qty"] = pd.to_numeric(item["output_qty"], errors="coerce").fillna(1)
    else:
        item["output_qty"] = pd.Series([1] * len(item), index=item.index)
    item["stage_no"] = pd.to_numeric(item.get("stage_no"), errors="coerce")

    def _cycle_frame(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
        if df.empty or not all(c in df.columns for c in group_cols + ["event_ts"]):
            return pd.DataFrame(columns=group_cols + ["avg_cycle_sec", "cycle_std_sec"])
        tmp = df[group_cols + ["event_ts"]].copy().dropna(subset=["event_ts"]).sort_values(group_cols + ["event_ts"])
        if tmp.empty:
            return pd.DataFrame(columns=group_cols + ["avg_cycle_sec", "cycle_std_sec"])
        tmp["cycle_sec"] = tmp.groupby(group_cols)["event_ts"].diff().dt.total_seconds()
        out = tmp.groupby(group_cols, as_index=False).agg(avg_cycle_sec=("cycle_sec", "mean"), cycle_std_sec=("cycle_sec", "std"))
        out["avg_cycle_sec"] = pd.to_numeric(out["avg_cycle_sec"], errors="coerce").fillna(0)
        out["cycle_std_sec"] = pd.to_numeric(out["cycle_std_sec"], errors="coerce").fillna(0)
        return out

    def _machine_view(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "machine_id" not in df.columns:
            return pd.DataFrame()
        out = df.groupby(["machine_id", "line_id", "stage_no"], as_index=False).agg(
            production_rows=("event_ts", "size"),
            output_qty=("output_qty", "sum"),
            lot_count=("lot_id", "nunique"),
            model_count=("model_label", "nunique"),
            first_event_ts=("event_ts", "min"),
            last_event_ts=("event_ts", "max"),
        )
        cycle = _cycle_frame(df, ["machine_id"])
        out = out.merge(cycle, on="machine_id", how="left")
        out["observed_span_sec"] = (pd.to_datetime(out["last_event_ts"], errors="coerce") - pd.to_datetime(out["first_event_ts"], errors="coerce")).dt.total_seconds().fillna(0)
        out["output_per_hour"] = out.apply(lambda r: _safe_div(r.get("output_qty", 0), max(r.get("observed_span_sec", 0), 1) / 3600), axis=1)
        total_output = float(df["output_qty"].sum()) or 1.0
        out["output_share"] = out["output_qty"] / total_output
        q1_out = pd.to_numeric(out["output_qty"], errors="coerce").quantile(0.25) if not out.empty else 0
        q3_cycle = pd.to_numeric(out["cycle_std_sec"], errors="coerce").quantile(0.75) if not out.empty else 0
        q3_share = pd.to_numeric(out["output_share"], errors="coerce").quantile(0.75) if not out.empty else 0

        def _ptype(r):
            if r.get("output_qty", 0) <= q1_out and r.get("cycle_std_sec", 0) >= q3_cycle:
                return "생산성 손실형"
            if r.get("output_share", 0) >= q3_share and r.get("output_qty", 0) > 0:
                return "집중형"
            if r.get("cycle_std_sec", 0) >= q3_cycle:
                return "안정성 문제"
            return "주의"

        out["problem_type"] = out.apply(_ptype, axis=1)
        out["bottleneck_score"] = (
            (1 - pd.to_numeric(out["output_qty"], errors="coerce").rank(pct=True, ascending=True).fillna(0)) * 0.45
            + pd.to_numeric(out["cycle_std_sec"], errors="coerce").rank(pct=True, ascending=True).fillna(0) * 0.35
            + pd.to_numeric(out["observed_span_sec"], errors="coerce").rank(pct=True, ascending=True).fillna(0) * 0.20
        )
        out["reasoning"] = out.apply(lambda r: f"출력 {r.get('output_qty', 0):.0f}, cycle 편차 {r.get('cycle_std_sec', 0):.1f}s, 점유율 {r.get('output_share', 0) * 100:.1f}%", axis=1)
        out["recommended_action"] = out.apply(
            lambda r: "라인 밸런스 및 자재 보급 타이밍 점검"
            if r.get("problem_type") == "생산성 손실형"
            else "부하 집중도와 전환 구간 점검"
            if r.get("problem_type") == "집중형"
            else "작업 표준화 및 cycle 변동 원인 확인"
            if r.get("problem_type") == "안정성 문제"
            else "상위 설비와 비교해 변동성 확인",
            axis=1,
        )
        q75 = out["bottleneck_score"].quantile(0.75) if not out.empty else 0
        q40 = out["bottleneck_score"].quantile(0.40) if not out.empty else 0
        out["status_label"] = out["bottleneck_score"].apply(lambda v: "개선필요" if v >= q75 else "주의" if v >= q40 else "정상")
        out["confidence"] = np.where(out["production_rows"].ge(10), "Actual", "Estimated")
        out["rank"] = np.arange(1, len(out) + 1)
        return out

    def _process_view(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or not {"line_id", "stage_no"}.issubset(df.columns):
            return pd.DataFrame()
        out = df.groupby(["line_id", "stage_no"], as_index=False).agg(
            production_rows=("event_ts", "size"),
            output_qty=("output_qty", "sum"),
            machine_count=("machine_id", "nunique"),
            lot_count=("lot_id", "nunique"),
            first_event_ts=("event_ts", "min"),
            last_event_ts=("event_ts", "max"),
        )
        cycle = _cycle_frame(df, ["line_id", "stage_no"])
        out = out.merge(cycle, on=["line_id", "stage_no"], how="left")
        out["observed_span_sec"] = (pd.to_datetime(out["last_event_ts"], errors="coerce") - pd.to_datetime(out["first_event_ts"], errors="coerce")).dt.total_seconds().fillna(0)
        out["output_per_hour"] = out.apply(lambda r: _safe_div(r.get("output_qty", 0), max(r.get("observed_span_sec", 0), 1) / 3600), axis=1)
        total_output = float(df["output_qty"].sum()) or 1.0
        out["output_share"] = out["output_qty"] / total_output
        q1_out = pd.to_numeric(out["output_qty"], errors="coerce").quantile(0.25) if not out.empty else 0
        q3_cycle = pd.to_numeric(out["cycle_std_sec"], errors="coerce").quantile(0.75) if not out.empty else 0

        def _ptype(r):
            if r.get("output_qty", 0) <= q1_out and r.get("cycle_std_sec", 0) >= q3_cycle:
                return "정지 병목"
            if r.get("cycle_std_sec", 0) >= q3_cycle:
                return "흐름 병목"
            if r.get("output_qty", 0) <= q1_out:
                return "주의"
            return "정상"

        out["process_display"] = out.apply(
            lambda r: f"Line-{r.get('line_id', '-')} / Stage-{int(r.get('stage_no', 0)) if pd.notna(r.get('stage_no', np.nan)) else '-'}",
            axis=1,
        )
        out["problem_type"] = out.apply(_ptype, axis=1)
        out["bottleneck_score"] = (
            (1 - pd.to_numeric(out["output_qty"], errors="coerce").rank(pct=True, ascending=True).fillna(0)) * 0.5
            + pd.to_numeric(out["cycle_std_sec"], errors="coerce").rank(pct=True, ascending=True).fillna(0) * 0.3
            + pd.to_numeric(out["observed_span_sec"], errors="coerce").rank(pct=True, ascending=True).fillna(0) * 0.2
        )
        out["reasoning"] = out.apply(lambda r: f"출력 {r.get('output_qty', 0):.0f}, cycle 편차 {r.get('cycle_std_sec', 0):.1f}s, machine {r.get('machine_count', 0):.0f}개", axis=1)
        out["recommended_action"] = out.apply(
            lambda r: "라인 밸런스와 보급 타이밍 조정"
            if r.get("problem_type") == "정지 병목"
            else "전후 stage 연결과 전환 시간 확인"
            if r.get("problem_type") == "흐름 병목"
            else "생산량 변동 원인과 기준선 재설정",
            axis=1,
        )
        out["confidence"] = np.where(out["production_rows"].ge(10), "Actual", "Estimated")
        out["rank"] = np.arange(1, len(out) + 1)
        return out

    def _lot_view(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "lot_id" not in df.columns:
            return pd.DataFrame()
        out = df.groupby(["lot_id", "model_label"], as_index=False).agg(
            production_rows=("event_ts", "size"),
            output_qty=("output_qty", "sum"),
            machine_count=("machine_id", "nunique"),
            stage_count=("stage_no", "nunique"),
            line_count=("line_id", "nunique"),
            first_event_ts=("event_ts", "min"),
            last_event_ts=("event_ts", "max"),
        )
        cycle = _cycle_frame(df, ["lot_id"])
        out = out.merge(cycle, on=["lot_id"], how="left")
        out["observed_span_sec"] = (pd.to_datetime(out["last_event_ts"], errors="coerce") - pd.to_datetime(out["first_event_ts"], errors="coerce")).dt.total_seconds().fillna(0)
        out["output_per_hour"] = out.apply(lambda r: _safe_div(r.get("output_qty", 0), max(r.get("observed_span_sec", 0), 1) / 3600), axis=1)
        out["spread_score"] = out[["machine_count", "stage_count", "line_count"]].sum(axis=1)
        out["concentration_score"] = 1 / (1 + out["spread_score"])
        out["priority_score"] = out["spread_score"] * 0.6 + out["concentration_score"] * 0.4
        machine_q = out["machine_count"].quantile(0.25) if not out.empty else 0
        stage_q = out["stage_count"].quantile(0.75) if not out.empty else 0
        density_q = out["output_per_hour"].quantile(0.25) if not out.empty else 0

        def _ptype(r):
            if r.get("machine_count", 0) <= machine_q and r.get("stage_count", 0) <= 1:
                return "국소 LOT"
            if r.get("stage_count", 0) >= stage_q or r.get("machine_count", 0) >= stage_q:
                return "전파 LOT"
            if r.get("output_per_hour", 0) <= density_q:
                return "저생산 LOT"
            return "주의"

        out["problem_type"] = out.apply(_ptype, axis=1)
        out["reasoning"] = out.apply(lambda r: f"설비 {r.get('machine_count', 0):.0f}개 / 공정 {r.get('stage_count', 0):.0f}개 / 집중도 {r.get('concentration_score', 0) * 100:.1f}%", axis=1)
        out["recommended_action"] = out.apply(
            lambda r: "대표 설비와 stage를 먼저 확인"
            if r.get("problem_type") == "국소 LOT"
            else "전파 범위와 연속 lot 비교"
            if r.get("problem_type") == "전파 LOT"
            else "생산 밀도와 스케줄 확인",
            axis=1,
        )
        out["confidence"] = np.where(out["production_rows"].ge(10), "Actual", "Estimated")
        out["rank"] = np.arange(1, len(out) + 1)
        return out

    def _machine_day_view(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or not {"machine_id", "day"}.issubset(df.columns):
            return pd.DataFrame()
        out = df.groupby(["machine_id", "day"], as_index=False).agg(
            actual_output=("output_qty", "sum"),
            production_rows=("event_ts", "size"),
            lot_count=("lot_id", "nunique"),
            stage_count=("stage_no", "nunique"),
            first_event_ts=("event_ts", "min"),
            last_event_ts=("event_ts", "max"),
        )
        cycle = _cycle_frame(df, ["machine_id", "day"])
        out = out.merge(cycle, on=["machine_id", "day"], how="left")
        out["span_sec"] = (
            pd.to_datetime(out["last_event_ts"], errors="coerce") - pd.to_datetime(out["first_event_ts"], errors="coerce")
        ).dt.total_seconds().fillna(0)
        out["actual_takt_sec"] = out.apply(lambda r: _safe_div(r.get("span_sec", 0), max(r.get("actual_output", 0), 1)), axis=1)
        ref = out.groupby("machine_id", as_index=False).agg(
            expected_output=("actual_output", "median"),
            expected_takt_sec=("actual_takt_sec", "median"),
            takt_std_sec=("actual_takt_sec", "std"),
        )
        out = out.merge(ref, on="machine_id", how="left")
        out["expected_output"] = pd.to_numeric(out["expected_output"], errors="coerce").fillna(out["actual_output"])
        out["expected_takt_sec"] = pd.to_numeric(out["expected_takt_sec"], errors="coerce").fillna(out["actual_takt_sec"])
        out["takt_std_sec"] = pd.to_numeric(out["takt_std_sec"], errors="coerce").fillna(0)
        out["output_gap"] = out["actual_output"] - out["expected_output"]
        out["output_gap_pct"] = out.apply(lambda r: _safe_div(r.get("output_gap", 0), max(r.get("expected_output", 0), 1)), axis=1)
        out["takt_gap_sec"] = out["actual_takt_sec"] - out["expected_takt_sec"]
        q1_gap = out["output_gap_pct"].quantile(0.25) if not out.empty else 0
        q3_gap = out["output_gap_pct"].quantile(0.75) if not out.empty else 0
        q3_takt = out["takt_gap_sec"].quantile(0.75) if not out.empty else 0

        def _ptype(r):
            if r.get("output_gap_pct", 0) <= -0.05 and r.get("takt_gap_sec", 0) >= q3_takt:
                return "생산성 손실형"
            if r.get("output_gap_pct", 0) <= q1_gap:
                return "정지 병목"
            if r.get("takt_gap_sec", 0) >= q3_takt:
                return "흐름 병목"
            if r.get("output_gap_pct", 0) >= q3_gap:
                return "주의"
            return "정상"

        def _hint(r):
            gap = r.get("output_gap", 0)
            takt_gap = r.get("takt_gap_sec", 0)
            if r.get("problem_type") == "생산성 손실형":
                return f"기준 대비 출력 {gap:.0f} 감소, 실측 택타임 {takt_gap:.1f}s 증가"
            if r.get("problem_type") == "정지 병목":
                return f"출력 편차 {gap:.0f}, 장시간 정체 가능성"
            if r.get("problem_type") == "흐름 병목":
                return f"기준 택타임 대비 {takt_gap:.1f}s 지연"
            return f"기준 대비 출력 {gap:.0f}, 택타임 변화 {takt_gap:.1f}s"

        def _action(r):
            if r.get("problem_type") == "생산성 손실형":
                return "라인 밸런스, 투입 타이밍, 전환 손실을 먼저 점검"
            if r.get("problem_type") == "정지 병목":
                return "정체 구간과 작업 전환 표준을 우선 조정"
            if r.get("problem_type") == "흐름 병목":
                return "전후 공정 연결과 buffer를 먼저 조정"
            if r.get("problem_type") == "주의":
                return "기준 대비 변동 구간을 재확인"
            return "현재 상태 유지, 추세만 모니터링"

        out["problem_type"] = out.apply(_ptype, axis=1)
        out["reasoning"] = out.apply(_hint, axis=1)
        out["recommended_action"] = out.apply(_action, axis=1)
        out["confidence"] = np.where(out["production_rows"].ge(10), "Actual", "Estimated")
        out["rank"] = np.arange(1, len(out) + 1)
        return out

    def _stage_day_view(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or not {"line_id", "stage_no", "day"}.issubset(df.columns):
            return pd.DataFrame()
        out = df.groupby(["line_id", "stage_no", "day"], as_index=False).agg(
            actual_output=("output_qty", "sum"),
            production_rows=("event_ts", "size"),
            machine_count=("machine_id", "nunique"),
            lot_count=("lot_id", "nunique"),
            first_event_ts=("event_ts", "min"),
            last_event_ts=("event_ts", "max"),
        )
        cycle = _cycle_frame(df, ["line_id", "stage_no", "day"])
        out = out.merge(cycle, on=["line_id", "stage_no", "day"], how="left")
        out["span_sec"] = (
            pd.to_datetime(out["last_event_ts"], errors="coerce") - pd.to_datetime(out["first_event_ts"], errors="coerce")
        ).dt.total_seconds().fillna(0)
        out["actual_takt_sec"] = out.apply(lambda r: _safe_div(r.get("span_sec", 0), max(r.get("actual_output", 0), 1)), axis=1)
        ref = out.groupby(["line_id", "stage_no"], as_index=False).agg(
            expected_output=("actual_output", "median"),
            expected_takt_sec=("actual_takt_sec", "median"),
            takt_std_sec=("actual_takt_sec", "std"),
        )
        out = out.merge(ref, on=["line_id", "stage_no"], how="left")
        out["expected_output"] = pd.to_numeric(out["expected_output"], errors="coerce").fillna(out["actual_output"])
        out["expected_takt_sec"] = pd.to_numeric(out["expected_takt_sec"], errors="coerce").fillna(out["actual_takt_sec"])
        out["takt_std_sec"] = pd.to_numeric(out["takt_std_sec"], errors="coerce").fillna(0)
        out["output_gap"] = out["actual_output"] - out["expected_output"]
        out["output_gap_pct"] = out.apply(lambda r: _safe_div(r.get("output_gap", 0), max(r.get("expected_output", 0), 1)), axis=1)
        out["takt_gap_sec"] = out["actual_takt_sec"] - out["expected_takt_sec"]
        q1_gap = out["output_gap_pct"].quantile(0.25) if not out.empty else 0
        q3_gap = out["output_gap_pct"].quantile(0.75) if not out.empty else 0
        q3_takt = out["takt_gap_sec"].quantile(0.75) if not out.empty else 0

        def _ptype(r):
            if r.get("output_gap_pct", 0) <= -0.05 and r.get("takt_gap_sec", 0) >= q3_takt:
                return "정지 병목"
            if r.get("takt_gap_sec", 0) >= q3_takt:
                return "흐름 병목"
            if r.get("output_gap_pct", 0) >= q3_gap:
                return "주의"
            return "정상"

        def _hint(r):
            gap = r.get("output_gap", 0)
            takt_gap = r.get("takt_gap_sec", 0)
            if r.get("problem_type") == "정지 병목":
                return f"Stage 출력 {gap:.0f} 감소, 택타임 {takt_gap:.1f}s 증가"
            if r.get("problem_type") == "흐름 병목":
                return f"Stage 전환 지연 {takt_gap:.1f}s"
            return f"기준 대비 출력 {gap:.0f}, 택타임 변화 {takt_gap:.1f}s"

        def _action(r):
            if r.get("problem_type") == "정지 병목":
                return "stage 간 handoff, 대기, 전환 시간을 먼저 점검"
            if r.get("problem_type") == "흐름 병목":
                return "전후 공정 buffer와 stage 연결을 먼저 조정"
            if r.get("problem_type") == "주의":
                return "기준 대비 변동 구간을 재확인"
            return "현재 상태 유지, 추세만 모니터링"

        out["process_display"] = out.apply(
            lambda r: f"Line-{r.get('line_id', '-')} / Stage-{int(r.get('stage_no', 0)) if pd.notna(r.get('stage_no', np.nan)) else '-'}",
            axis=1,
        )
        out["problem_type"] = out.apply(_ptype, axis=1)
        out["reasoning"] = out.apply(_hint, axis=1)
        out["recommended_action"] = out.apply(_action, axis=1)
        out["confidence"] = np.where(out["production_rows"].ge(10), "Actual", "Estimated")
        out["rank"] = np.arange(1, len(out) + 1)
        return out

    def _alarm_view(machine_df: pd.DataFrame, process_df: pd.DataFrame, lot_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        def _alarm_level(output_gap_pct: float, takt_gap_sec: float, spread: float = 0.0, fail_rows: int = 0) -> str:
            if fail_rows > 0:
                return "심각"
            if output_gap_pct <= -0.10 and takt_gap_sec >= 30:
                return "심각"
            if output_gap_pct <= -0.05 and takt_gap_sec >= 15:
                return "경고"
            if output_gap_pct <= -0.03 or takt_gap_sec >= 10:
                return "주의"
            if spread >= 5:
                return "주의"
            return "정상"

        if not machine_df.empty:
            m_top = machine_df.sort_values("bottleneck_score", ascending=False).iloc[0]
            out_gap = _safe_float(m_top.get("output_gap_pct", 0))
            takt_gap = _safe_float(m_top.get("takt_gap_sec", 0))
            rows.append({
                "알람유형": "생산성 경고",
                "기준": "출력 편차 -5% 이하 또는 택타임 +15초 이상",
                "판정": _alarm_level(out_gap, takt_gap),
                "현재상태": m_top.get("problem_type", "-"),
                "우선순위": "1. 라인서",
                "조치": m_top.get("recommended_action", "-"),
            })
        if not process_df.empty:
            p_top = process_df.sort_values("bottleneck_score", ascending=False).iloc[0]
            out_gap = _safe_float(p_top.get("output_gap_pct", 0))
            takt_gap = _safe_float(p_top.get("takt_gap_sec", 0))
            rows.append({
                "알람유형": "흐름 경고",
                "기준": "stage 기준 출력 -5% 이하 또는 택타임 +15초 이상",
                "판정": _alarm_level(out_gap, takt_gap),
                "현재상태": p_top.get("problem_type", "-"),
                "우선순위": "1. 라인서",
                "조치": p_top.get("recommended_action", "-"),
            })
        if not lot_df.empty:
            l_top = lot_df.sort_values("priority_score", ascending=False).iloc[0]
            spread = _safe_float(l_top.get("spread_score", 0))
            machine_count = _safe_float(l_top.get("machine_count", 0))
            stage_count = _safe_float(l_top.get("stage_count", 0))
            rows.append({
                "알람유형": "LOT 확산 경고",
                "기준": "machine 2개 이상 또는 stage 2개 이상 확산",
                "판정": "심각" if machine_count >= 2 or stage_count >= 2 else _alarm_level(0, 0, spread=spread),
                "현재상태": l_top.get("problem_type", "-"),
                "우선순위": "2. 자동 해소",
                "조치": l_top.get("recommended_action", "-"),
            })
        result_fail = 0
        if "result" in filtered.columns:
            result_fail = int((filtered["result"].astype(str).str.upper() != "PASS").sum())
        rows.append({
            "알람유형": "품질 경고",
            "기준": "PASS 이외 결과 1건 이상",
            "판정": "심각" if result_fail > 0 else "정상",
            "현재상태": "발생 없음" if result_fail == 0 else f"비정상 {result_fail:,}",
            "우선순위": "1. 라인서",
            "조치": "현재 백업에는 불량 결과가 없어 원천 품질 알람은 비활성",
        })
        return pd.DataFrame(rows)

    def _feeder_context_view() -> pd.DataFrame:
        rows = [
            {
                "항목": "피더 정보",
                "현재 백업 상태": "미수집",
                "대체 분석 기준": "machine_id / stage_no / model_label / lot_id",
                "조치 방향": "피더 테이블이 붙으면 자동 연결, 현재는 반복 출력 편차로 대체",
            },
            {
                "항목": "에러 메시지",
                "현재 백업 상태": "전용 에러코드 없음",
                "대체 분석 기준": "output_gap / takt_gap / stage 집중도",
                "조치 방향": "라인서 우선 경보 후 자동 해소 여부를 판단",
            },
            {
                "항목": "라인 위치",
                "현재 백업 상태": "수집",
                "대체 분석 기준": "line_id / stage_no / section / row_num",
                "조치 방향": "동일 라인, 동일 stage 반복 패턴부터 확인",
            },
        ]
        return pd.DataFrame(rows)

    def _priority_rule_view() -> pd.DataFrame:
        rows = [
            {
                "순위": "1",
                "구분": "라인서 우선",
                "설명": "output_gap_pct -5% 이하 또는 택타임 +15초 이상",
                "예시": "기준 대비 출력 감소, 택타임 지연",
                "조치": "설비 / 공정 / 투입 타이밍 우선 점검",
            },
            {
                "순위": "2",
                "구분": "자동 해소",
                "설명": "output_gap_pct -3% ~ -5% 또는 택타임 +10~15초",
                "예시": "일시적 cycle 흔들림, 단발성 지연",
                "조치": "재시도 / 경보 / 임계치 조정",
            },
            {
                "순위": "3",
                "구분": "세부 원인 확인",
                "설명": "단일 LOT 또는 단일 stage에만 국한된 반복 패턴",
                "예시": "특정 LOT, 특정 stage, 반복 편차",
                "조치": "원인 구간과 대표 lot 비교",
            },
        ]
        return pd.DataFrame(rows)

    machine = _machine_view(item)
    process = _process_view(item)
    lot = _lot_view(item)
    daily_view = _machine_day_view(item)
    stage_daily_view = _stage_day_view(item)
    time_view = item.groupby(["hour", "shift"], as_index=False).agg(
        production_rows=("event_ts", "size"),
        output_qty=("output_qty", "sum"),
        machine_count=("machine_id", "nunique"),
        lot_count=("lot_id", "nunique"),
    )
    if not time_view.empty:
        shift_order = {"주간(06-14)": 0, "석간(14-22)": 1, "야간(22-06)": 2, "미상": 3}
        time_view["bucket"] = time_view["hour"].astype("Int64").astype(str).str.zfill(2)
        time_view["bucket_order"] = time_view["hour"].fillna(99)
        time_view["grain"] = "hour"
        shift_view = time_view.groupby("shift", as_index=False).agg(
            production_rows=("production_rows", "sum"),
            output_qty=("output_qty", "sum"),
            machine_count=("machine_count", "sum"),
            lot_count=("lot_count", "sum"),
        )
        if not shift_view.empty:
            shift_view["grain"] = "shift"
            shift_view["bucket"] = shift_view["shift"]
            shift_view["bucket_order"] = shift_view["shift"].map(shift_order).fillna(99)
            time_view = pd.concat([time_view, shift_view], ignore_index=True, sort=False)
        time_view = time_view.sort_values(["grain", "bucket_order"])

    filters = {}
    cols = st.columns(5)
    options = {
        "line": ["전체"] + sorted(item["line_id"].dropna().astype(str).unique().tolist()) if "line_id" in item.columns else ["전체"],
        "stage": ["전체"] + sorted(item["stage_no"].dropna().astype(int).astype(str).unique().tolist()) if "stage_no" in item.columns else ["전체"],
        "machine": ["전체"] + sorted(item["machine_id"].dropna().astype(str).unique().tolist()) if "machine_id" in item.columns else ["전체"],
        "lot": ["전체"] + sorted(item["lot_id"].dropna().astype(str).unique().tolist()) if "lot_id" in item.columns else ["전체"],
        "model": ["전체"] + sorted(item["model_label"].dropna().astype(str).unique().tolist()) if "model_label" in item.columns else ["전체"],
    }
    labels = ["line", "stage", "machine", "lot", "model"]
    for col, key in zip(cols, labels):
        with col:
            filters[key] = st.selectbox(key, options[key], key=f"mounter_{key}_filter")

    filtered = item.copy()
    if filters.get("line") != "전체" and "line_id" in filtered.columns:
        filtered = filtered[filtered["line_id"].astype(str).eq(filters["line"])]
    if filters.get("stage") != "전체" and "stage_no" in filtered.columns:
        filtered = filtered[filtered["stage_no"].astype("Int64").astype(str).eq(filters["stage"])]
    if filters.get("machine") != "전체" and "machine_id" in filtered.columns:
        filtered = filtered[filtered["machine_id"].astype(str).eq(filters["machine"])]
    if filters.get("lot") != "전체" and "lot_id" in filtered.columns:
        filtered = filtered[filtered["lot_id"].astype(str).eq(filters["lot"])]
    if filters.get("model") != "전체" and "model_label" in filtered.columns:
        filtered = filtered[filtered["model_label"].astype(str).eq(filters["model"])]

    filtered_comp = clean.get("vw_component_error_fact", pd.DataFrame()).copy()

    if filtered.empty:
        st.warning("선택 조건에 해당하는 mounter 데이터가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    machine = _machine_view(filtered)
    process = _process_view(filtered)
    lot = _lot_view(filtered)
    time_view = filtered.groupby(["hour", "shift"], as_index=False).agg(
        production_rows=("event_ts", "size"),
        output_qty=("output_qty", "sum"),
        machine_count=("machine_id", "nunique"),
        lot_count=("lot_id", "nunique"),
    )
    if not time_view.empty:
        shift_order = {"주간(06-14)": 0, "석간(14-22)": 1, "야간(22-06)": 2, "미상": 3}
        time_view["bucket"] = time_view["hour"].astype("Int64").astype(str).str.zfill(2)
        time_view["bucket_order"] = time_view["hour"].fillna(99)
        time_view["grain"] = "hour"
        shift_view = time_view.groupby("shift", as_index=False).agg(
            production_rows=("production_rows", "sum"),
            output_qty=("output_qty", "sum"),
            machine_count=("machine_count", "sum"),
            lot_count=("lot_count", "sum"),
        )
        if not shift_view.empty:
            shift_view["grain"] = "shift"
            shift_view["bucket"] = shift_view["shift"]
            shift_view["bucket_order"] = shift_view["shift"].map(shift_order).fillna(99)
            time_view = pd.concat([time_view, shift_view], ignore_index=True, sort=False)
        time_view = time_view.sort_values(["grain", "bucket_order"])

    summary_cards = [
        ("총 출력", f"{int(filtered['output_qty'].sum()):,}", "mounter output 합계"),
        ("설비 수", f"{filtered['machine_id'].nunique():,}" if "machine_id" in filtered.columns else "0", "활성 설비"),
        ("공정 수", f"{filtered[['line_id', 'stage_no']].drop_duplicates().shape[0]:,}" if {"line_id", "stage_no"}.issubset(filtered.columns) else "0", "line/stage 조합"),
        ("LOT 수", f"{filtered['lot_id'].nunique():,}" if "lot_id" in filtered.columns else "0", "활성 LOT"),
        ("평균 cycle", _fmt_sec(_safe_float(machine["avg_cycle_sec"].mean() if not machine.empty and "avg_cycle_sec" in machine.columns else 0)), "설비 평균 cycle"),
        ("우선 점검", str(machine.sort_values("bottleneck_score", ascending=False).iloc[0].get("machine_id", "-") if not machine.empty else "-"), "bottleneck 최고"),
    ]
    cards = st.columns(6)
    for col, (label, value, foot) in zip(cards, summary_cards):
        with col:
            st.markdown(_card(label, value, foot), unsafe_allow_html=True)

    top_machine = machine.sort_values("bottleneck_score", ascending=False).head(1)
    top_process = process.sort_values("bottleneck_score", ascending=False).head(1)
    top_lot = lot.sort_values("priority_score", ascending=False).head(1)

    st.markdown("#### 행동형 인사이트")
    ic1, ic2, ic3 = st.columns(3)
    insight_data = [
        (
            top_machine.iloc[0] if not top_machine.empty else pd.Series(dtype=object),
            "설비",
            "출력 집중도와 cycle 변동을 동시에 봅니다.",
            "상위 설비의 부하 집중을 줄이고 변동성이 큰 구간을 먼저 잡아야 합니다.",
        ),
        (
            top_process.iloc[0] if not top_process.empty else pd.Series(dtype=object),
            "공정",
            "출력 낮음 + cycle 편차 큼이면 병목입니다.",
            "line balance, 전환 시간, 보급 타이밍을 먼저 확인해야 합니다.",
        ),
        (
            top_lot.iloc[0] if not top_lot.empty else pd.Series(dtype=object),
            "LOT",
            "다수 설비/공정으로 퍼지면 전파 LOT입니다.",
            "대표 설비와 stage를 먼저 잡고 확산을 차단해야 합니다.",
        ),
    ]
    for col, (row, kind, hint, action) in zip([ic1, ic2, ic3], insight_data):
        with col:
            if row is not None and not row.empty:
                target = row.get("machine_id", row.get("process_display", row.get("lot_id", "-")))
                problem = row.get("problem_type", "주의")
                evidence = row.get("reasoning", "-")
                rec = row.get("recommended_action", action)
                conf = row.get("confidence", "Estimated")
            else:
                target, problem, evidence, rec, conf = "-", "주의", "-", action, "Estimated"
            st.markdown(
                f"""
                <div style="padding:.9rem 1rem;border-radius:16px;background:linear-gradient(180deg,#141b28,#0f1520);border:1px solid rgba(255,255,255,.08);min-height:180px">
                    <div style="font-size:.78rem;color:#9fb0c4;">대상</div>
                    <div style="font-size:1.15rem;font-weight:800;color:#fff;margin:.15rem 0 .35rem 0;">{target}</div>
                    <div style="margin-bottom:.3rem;color:#ffd1a1;font-weight:700;">분류: {problem}</div>
                    <div style="font-size:.82rem;color:#c8d2df;">{hint}</div>
                    <div style="font-size:.82rem;color:#c8d2df;margin-top:.25rem;">근거: {evidence}</div>
                    <div style="font-size:.82rem;color:#9ad7ff;margin-top:.35rem;">권장 조치: {rec}</div>
                    <div style="font-size:.75rem;color:#8ea1b7;margin-top:.35rem;">신뢰도: {conf}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(_section_header("전체 문제 요약", "설비 / 공정 / LOT 중 어디가 먼저 문제인지 한눈에 보는 구역", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.55, 0.45])
    with left:
        summary = pd.DataFrame([
            {"구분": "설비", "대상": row.get("machine_id", "-"), "문제유형": row.get("problem_type", "-"), "근거": row.get("reasoning", "-"), "조치": row.get("recommended_action", "-")}
            for _, row in top_machine.iterrows()
        ] + [
            {"구분": "공정", "대상": row.get("process_display", "-"), "문제유형": row.get("problem_type", "-"), "근거": row.get("reasoning", "-"), "조치": row.get("recommended_action", "-")}
            for _, row in top_process.iterrows()
        ] + [
            {"구분": "LOT", "대상": row.get("lot_id", "-"), "문제유형": row.get("problem_type", "-"), "근거": row.get("reasoning", "-"), "조치": row.get("recommended_action", "-")}
            for _, row in top_lot.iterrows()
        ])
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with right:
        if not time_view.empty and "output_qty" in time_view.columns:
            if "grain" in time_view.columns:
                hour_view = time_view[time_view["grain"].eq("hour")].copy()
            elif "hour" in time_view.columns:
                hour_view = time_view.copy()
                hour_view["bucket"] = pd.to_numeric(hour_view["hour"], errors="coerce").astype("Int64").astype(str).str.zfill(2)
                hour_view["bucket_order"] = pd.to_numeric(hour_view["hour"], errors="coerce").fillna(99)
            else:
                hour_view = pd.DataFrame()
            if not hour_view.empty:
                fig = px.bar(hour_view.sort_values("bucket_order" if "bucket_order" in hour_view.columns else "hour"), x="bucket" if "bucket" in hour_view.columns else "hour", y="output_qty", text="output_qty")
                st.plotly_chart(_plot_style(fig, "시간대별 출력", 330), use_container_width=True)

    st.markdown(_section_header("설비별 문제 분석", "출력량, cycle 변동, 점유율로 설비를 분류합니다.", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.56, 0.44])
    with left:
        if not machine.empty:
            display_cols = [c for c in ["rank", "machine_id", "line_id", "stage_no", "production_rows", "output_qty", "output_per_hour", "avg_cycle_sec", "cycle_std_sec", "lot_count", "problem_type", "status_label", "reasoning", "recommended_action", "confidence"] if c in machine.columns]
            st.dataframe(machine.sort_values("bottleneck_score", ascending=False)[display_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("설비 분석 데이터가 없습니다.")
    with right:
        if not machine.empty:
            x_th = machine["output_qty"].quantile(0.25)
            y_th = machine["cycle_std_sec"].quantile(0.75)
            fig = px.scatter(
                machine,
                x="output_qty",
                y="cycle_std_sec",
                size="production_rows",
                color="problem_type",
                hover_name="machine_id",
                text="machine_id",
                color_discrete_map={"생산성 손실형": "#ef4444", "집중형": "#f59e0b", "안정성 문제": "#3b82f6", "주의": "#64748b"},
            )
            fig.add_vline(x=x_th, line_dash="dash", line_color="#94a3b8")
            fig.add_hline(y=y_th, line_dash="dash", line_color="#94a3b8")
            st.plotly_chart(_plot_style(fig, "설비별 출력-변동 분류도", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- 출력이 낮고 cycle 편차가 크면 생산성 손실형입니다.")
        st.markdown("- 출력 점유율이 크면 특정 설비에 부하가 집중된 것입니다.")
        st.markdown("- 다음 확인: 상위 설비의 line/stage 조합과 동일 LOT 분포입니다.")

    st.markdown(_section_header("공정별 병목 분석", "라인/Stage 단위의 출력과 변동성을 봅니다.", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.56, 0.44])
    with left:
        if not process.empty:
            display_cols = [c for c in ["rank", "process_display", "line_id", "stage_no", "production_rows", "output_qty", "output_per_hour", "machine_count", "lot_count", "avg_cycle_sec", "cycle_std_sec", "problem_type", "reasoning", "recommended_action", "confidence"] if c in process.columns]
            st.dataframe(process.sort_values("bottleneck_score", ascending=False)[display_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("공정 분석 데이터가 없습니다.")
    with right:
        if not process.empty:
            fig = px.scatter(
                process,
                x="output_qty",
                y="cycle_std_sec",
                size="production_rows",
                color="problem_type",
                hover_name="process_display",
                text="process_display",
                color_discrete_map={"정지 병목": "#ef4444", "흐름 병목": "#f59e0b", "주의": "#64748b", "정상": "#3b82f6"},
            )
            st.plotly_chart(_plot_style(fig, "공정별 출력-변동 분류도", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- 출력이 낮고 cycle 편차가 크면 병목 stage입니다.")
        st.markdown("- machine_count가 크면 해당 공정에 장비가 몰려 있는 것입니다.")
        st.markdown("- 다음 확인: stage별 전환 구간과 같은 lot의 분산입니다.")

    st.markdown(_section_header("LOT 영향 분석", "한 LOT이 얼마나 넓게 퍼지는지 봅니다.", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.56, 0.44])
    with left:
        if not lot.empty:
            display_cols = [c for c in ["rank", "lot_id", "model_label", "production_rows", "output_qty", "output_per_hour", "machine_count", "stage_count", "line_count", "spread_score", "priority_score", "problem_type", "reasoning", "recommended_action", "confidence"] if c in lot.columns]
            st.dataframe(lot.sort_values("priority_score", ascending=False)[display_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("LOT 분석 데이터가 없습니다.")
    with right:
        if not lot.empty:
            fig = px.scatter(
                lot,
                x="machine_count",
                y="stage_count",
                size="spread_score",
                color="problem_type",
                hover_name="lot_id",
                text="lot_id",
                color_discrete_map={"국소 LOT": "#ef4444", "전파 LOT": "#f59e0b", "저생산 LOT": "#3b82f6", "주의": "#64748b"},
            )
            st.plotly_chart(_plot_style(fig, "LOT 확산-영향 분류도", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- machine_count와 stage_count가 낮으면 국소 LOT입니다.")
        st.markdown("- machine_count 또는 stage_count가 넓으면 전파 LOT입니다.")
        st.markdown("- 다음 확인: 대표 설비와 대표 stage입니다.")

    st.markdown(_section_header("개선 우선순위", "먼저 개선해야 할 대상 순서입니다.", PRIMARY), unsafe_allow_html=True)
    priority_rows = []
    if not machine.empty:
        for _, row in machine.sort_values("bottleneck_score", ascending=False).head(4).iterrows():
            priority_rows.append({"대상유형": "설비", "대상": row.get("machine_id", "-"), "문제유형": row.get("problem_type", "-"), "근거 KPI": row.get("reasoning", "-"), "예상 영향": f"line {row.get('line_id', '-')}, stage {row.get('stage_no', '-')}", "추천 액션": row.get("recommended_action", "-"), "기대 효과": "기준 변동 축소", "priority_score": row.get("bottleneck_score", 0)})
    if not process.empty:
        for _, row in process.sort_values("bottleneck_score", ascending=False).head(4).iterrows():
            priority_rows.append({"대상유형": "공정", "대상": row.get("process_display", "-"), "문제유형": row.get("problem_type", "-"), "근거 KPI": row.get("reasoning", "-"), "예상 영향": f"machine {row.get('machine_count', 0):.0f}개", "추천 액션": row.get("recommended_action", "-"), "기대 효과": "흐름 안정화", "priority_score": row.get("bottleneck_score", 0)})
    if not lot.empty:
        for _, row in lot.sort_values("priority_score", ascending=False).head(4).iterrows():
            priority_rows.append({"대상유형": "LOT", "대상": row.get("lot_id", "-"), "문제유형": row.get("problem_type", "-"), "근거 KPI": row.get("reasoning", "-"), "예상 영향": f"machine {row.get('machine_count', 0):.0f}개 / stage {row.get('stage_count', 0):.0f}개", "추천 액션": row.get("recommended_action", "-"), "기대 효과": "확산 차단", "priority_score": row.get("priority_score", 0)})
    priority = pd.DataFrame(priority_rows)
    if not priority.empty:
        priority = priority.sort_values("priority_score", ascending=False).reset_index(drop=True)
        priority["순위"] = np.arange(1, len(priority) + 1)
        st.dataframe(priority[["순위", "대상유형", "대상", "문제유형", "근거 KPI", "예상 영향", "추천 액션", "기대 효과"]], use_container_width=True, hide_index=True)
    else:
        st.info("개선 우선순위를 만들 데이터가 부족합니다.")

    st.markdown("#### 자동 코멘트")
    if not machine.empty:
        top = machine.sort_values("bottleneck_score", ascending=False).iloc[0]
        st.markdown(f"- `{top.get('machine_id', '-')}`: {top.get('reasoning', '-')} → {top.get('recommended_action', '-')}")
    if not process.empty:
        top = process.sort_values("bottleneck_score", ascending=False).iloc[0]
        st.markdown(f"- `{top.get('process_display', '-')}`: {top.get('reasoning', '-')} → {top.get('recommended_action', '-')}")
    if not lot.empty:
        top = lot.sort_values("priority_score", ascending=False).iloc[0]
        st.markdown(f"- `{top.get('lot_id', '-')}`: {top.get('reasoning', '-')} → {top.get('recommended_action', '-')}")

    st.markdown(_section_header("알람 기준과 우선순위", "라인서 우선, 자동 해소 다음, 세부 원인 마지막 순서입니다.", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.52, 0.48])
    with left:
        prio_rule = _priority_rule_view()
        st.dataframe(prio_rule, use_container_width=True, hide_index=True)
    with right:
        alarm_note = pd.DataFrame([
            {"항목": "생산성 알람", "기준": "기준 출력 대비 음수 편차가 커질 때", "현재": "daily_view에서 자동 계산", "해소점": "라인 밸런스, 보급 타이밍, 전환 손실"},
            {"항목": "품질 알람", "기준": "PASS 이외 결과 증가", "현재": "현재 백업은 PASS만 존재", "해소점": "품질 이벤트 수집 시 즉시 활성화"},
            {"항목": "복합 알람", "기준": "출력 저하 + 택타임 지연 동시 발생", "현재": "machine / process / lot 조합으로 판정", "해소점": "병목 구간과 대표 lot 동시 확인"},
        ])
        st.dataframe(alarm_note, use_container_width=True, hide_index=True)
        st.markdown("##### 알람 해석")
        st.markdown("- 라인서 우선: 사람이 먼저 봐야 하는 경보")
        st.markdown("- 자동 해소: 반복되지만 구조가 단순한 경우")
        st.markdown("- 세부 원인: 협의 후 최종 순위 조정")

    st.markdown(_section_header("생산성 이상치 분석", "실측 출력이 기준 대비 얼마나 벗어났는지 봅니다.", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not daily_view.empty:
            anomaly = daily_view.copy()
            anomaly["abs_gap"] = anomaly["output_gap"].abs()
            anomaly = anomaly.sort_values(["output_gap_pct", "abs_gap"], ascending=[True, False])
            display_cols = [c for c in ["machine_id", "day", "actual_output", "expected_output", "output_gap", "output_gap_pct", "actual_takt_sec", "expected_takt_sec", "takt_gap_sec", "problem_type", "reasoning", "recommended_action", "confidence"] if c in anomaly.columns]
            st.dataframe(anomaly[display_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("생산성 이상치 분석 데이터가 없습니다.")
    with right:
        if not daily_view.empty:
            top_gap = daily_view.copy()
            top_gap["abs_gap"] = top_gap["output_gap"].abs()
            top_gap = top_gap.sort_values("abs_gap", ascending=False).head(8)
            fig = px.bar(
                top_gap,
                x=top_gap["machine_id"].astype(str) + " / " + top_gap["day"].astype(str),
                y="output_gap",
                text="output_gap",
                color="output_gap",
                color_continuous_scale=["#ef4444", "#94a3b8", "#22c55e"],
            )
            st.plotly_chart(_plot_style(fig, "기준 대비 출력 편차", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- 음수 편차가 크면 기대 출력 대비 부족입니다.")
        st.markdown("- 택타임이 길어지면 생산성 손실형으로 봅니다.")
        st.markdown("- 다음 확인: 같은 machine의 다른 day와 비교합니다.")

    st.markdown(_section_header("공정 / Stage 이상치 분석", "설비가 아니라 공정 단위의 출력 편차와 택타임을 봅니다.", SECONDARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not stage_daily_view.empty:
            stage_anomaly = stage_daily_view.copy()
            stage_anomaly["abs_gap"] = stage_anomaly["output_gap"].abs()
            stage_anomaly = stage_anomaly.sort_values(["output_gap_pct", "abs_gap"], ascending=[True, False])
            display_cols = [c for c in ["process_display", "day", "actual_output", "expected_output", "output_gap", "output_gap_pct", "actual_takt_sec", "expected_takt_sec", "takt_gap_sec", "problem_type", "reasoning", "recommended_action", "confidence"] if c in stage_anomaly.columns]
            st.dataframe(stage_anomaly[display_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("공정/Stage 이상치 분석 데이터가 없습니다.")
    with right:
        if not stage_daily_view.empty:
            top_stage_gap = stage_daily_view.copy()
            top_stage_gap["abs_gap"] = top_stage_gap["output_gap"].abs()
            top_stage_gap = top_stage_gap.sort_values("abs_gap", ascending=False).head(8)
            fig = px.bar(
                top_stage_gap,
                x=top_stage_gap["process_display"] + " / " + top_stage_gap["day"].astype(str),
                y="output_gap",
                text="output_gap",
                color="output_gap",
                color_continuous_scale=["#ef4444", "#94a3b8", "#22c55e"],
            )
            st.plotly_chart(_plot_style(fig, "Stage 기준 출력 편차", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- 기준 대비 출력 감소는 공정 병목 가능성입니다.")
        st.markdown("- 택타임 지연이 크면 stage handoff 문제입니다.")
        st.markdown("- 다음 확인: 같은 stage의 다른 day와 비교합니다.")

    st.markdown(_section_header("이론 택타임 vs 실측 택타임", "기준 택타임과 실제 택타임의 차이를 봅니다.", PRIMARY), unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42])
    with left:
        if not daily_view.empty:
            takt_view = daily_view.groupby("machine_id", as_index=False).agg(
                기준택타임_sec=("expected_takt_sec", "median"),
                실측택타임_sec=("actual_takt_sec", "median"),
                택타임편차_sec=("takt_gap_sec", "median"),
                기준출력=("expected_output", "median"),
                실측출력=("actual_output", "median"),
                택타임표준편차_sec=("takt_std_sec", "median"),
            )
            takt_view["편차율"] = takt_view.apply(lambda r: _safe_div(r.get("택타임편차_sec", 0), max(r.get("기준택타임_sec", 0), 1)), axis=1)
            takt_view = takt_view.sort_values("택타임편차_sec", ascending=False)
            st.dataframe(takt_view.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("택타임 분석 데이터가 없습니다.")
    with right:
        if not daily_view.empty:
            takt_view = daily_view.groupby("machine_id", as_index=False).agg(
                기준택타임_sec=("expected_takt_sec", "median"),
                실측택타임_sec=("actual_takt_sec", "median"),
            )
            fig = px.scatter(takt_view, x="기준택타임_sec", y="실측택타임_sec", text="machine_id", hover_name="machine_id")
            min_v = min(float(takt_view["기준택타임_sec"].min()), float(takt_view["실측택타임_sec"].min()))
            max_v = max(float(takt_view["기준택타임_sec"].max()), float(takt_view["실측택타임_sec"].max()))
            fig.add_shape(type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v, line=dict(color="#94a3b8", dash="dash"))
            st.plotly_chart(_plot_style(fig, "기준 택타임 vs 실측 택타임", 340), use_container_width=True)
        st.markdown("##### 해석 기준")
        st.markdown("- 대각선 위로 갈수록 실제가 기준보다 느립니다.")
        st.markdown("- 기준과 실측의 차이가 크면 라인서 조치 우선입니다.")
        st.markdown("- 다음 확인: 투입, 전환, 대기, 재가동 시간을 분리합니다.")

    st.markdown(_section_header("이슈 유형별 조치 방향", "문제 유형을 보면 어디를 먼저 손대야 하는지 정합니다.", SECONDARY), unsafe_allow_html=True)
    action_map = pd.DataFrame([
        {"문제유형": "생산성 손실형", "왜 그렇게 보이나": "출력 감소 + 택타임 지연", "먼저 볼 것": "라인 밸런스 / 투입 타이밍 / 전환 손실", "해소점": "기준 출력 회복"},
        {"문제유형": "정지 병목", "왜 그렇게 보이나": "출력 저하 + 정체 구간 집중", "먼저 볼 것": "정지 구간 / buffer / 전환 표준", "해소점": "정체 구간 축소"},
        {"문제유형": "흐름 병목", "왜 그렇게 보이나": "stage 간 편차와 지연 증가", "먼저 볼 것": "전후 공정 연결 / stage handoff", "해소점": "연결 시간 축소"},
        {"문제유형": "주의", "왜 그렇게 보이나": "기준 대비 변동이 있으나 임계 미만", "먼저 볼 것": "같은 machine의 다른 day", "해소점": "추세 모니터링"},
        {"문제유형": "국소 LOT", "왜 그렇게 보이나": "특정 lot에만 집중", "먼저 볼 것": "대표 설비 / 대표 stage", "해소점": "확산 차단"},
        {"문제유형": "전파 LOT", "왜 그렇게 보이나": "여러 machine / stage로 퍼짐", "먼저 볼 것": "원인 lot의 경계", "해소점": "연속 lot 비교"},
    ])
    st.dataframe(action_map, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
