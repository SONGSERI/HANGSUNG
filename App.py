import streamlit as st
import pandas as pd
import numpy as np
from typing import List

from db import load_table


from analysis_quality import (
    run_quality_risk_analysis,
    QualityRiskParams,
)
from analysis_equipment import (
    run_equipment_anomaly_analysis,
    EquipmentAnomalyParams,
)
from analysis_production import (
    build_lot_machine_view,
    production_kpis,
)


def ensure_columns(df: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(columns=required_columns)

    result = df.copy()
    for col in required_columns:
        if col not in result.columns:
            result[col] = pd.Series(dtype="object")
    return result

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="SMT Analysis Lab",
    layout="wide",
)

st.title("SMT Analysis Lab")
st.caption("PostgreSQL 기반 SMT 분석 실험 도구")

# =========================
# DB Load
# =========================
@st.cache_data(show_spinner="DB에서 데이터 로딩 중...")
def load_data():
    def safe_load(table_name: str) -> pd.DataFrame:
        try:
            return load_table(table_name)
        except Exception:
            return pd.DataFrame()

    lot = safe_load("lot")
    lot_machine = safe_load("lot_machine")
    machine = safe_load("machine")
    time_summary = safe_load("machine_time_summary")
    pickup_summary = safe_load("pickup_error_summary")
    stop_log = safe_load("stop_log")
    stop_reason = safe_load("stop_reason")
    component = safe_load("component")
    component_pickup_summary = safe_load("component_pickup_summary")
    tag_info = safe_load("tag_info")
    tag_spec = safe_load("tag_spec")
    tag_realtime = safe_load("tag_realtime")

    return (
        lot,
        lot_machine,
        machine,
        time_summary,
        pickup_summary,
        stop_log,
        stop_reason,
        component,
        component_pickup_summary,
        tag_info,
        tag_spec,
        tag_realtime,
    )


(
    lot,
    lot_machine,
    machine,
    time_summary,
    pickup_summary,
    stop_log,
    stop_reason,
    component,
    component_pickup_summary,
    tag_info,
    tag_spec,
    tag_realtime,
) = load_data()

lot = ensure_columns(lot, ["lot_id", "lot_name", "start_time", "end_time", "lane"])
lot_machine = ensure_columns(lot_machine, ["lot_machine_id", "lot_id", "machine_id"])
machine = ensure_columns(machine, ["machine_id", "line_id", "stage_no", "machine_order"])
time_summary = ensure_columns(
    time_summary,
    [
        "lot_machine_id",
        "power_on_time_sec",
        "running_time_sec",
        "real_running_time_sec",
        "total_stop_time_sec",
        "transfer_time_sec",
        "board_recognition_time_sec",
        "placement_time_sec",
    ],
)
pickup_summary = ensure_columns(
    pickup_summary,
    [
        "lot_machine_id",
        "total_pickup_count",
        "total_error_count",
        "pickup_error_count",
        "recognition_error_count",
        "thick_error_count",
        "placement_error_count",
        "part_drop_error_count",
        "transfer_unit_part_drop_error_count",
        "pre_pickup_inspection_error_count",
    ],
)

# =========================
# Base View (공통 Fact)
# =========================
lot_machine_view = build_lot_machine_view(
    lot,
    lot_machine,
    machine,
    time_summary,
    pickup_summary,
)

# =========================
# Sidebar Menu
# =========================
menu = st.sidebar.radio(
    "분석 선택",
    [
        "📊 생산 분석",
        "🛠 설비 이상 분석",
        "🧪 품질 분석",
        "📈 ERD 핵심 분석",
    ],
)

with st.sidebar.expander("공통 조건", expanded=True):
    line_filter = st.multiselect(
        "라인",
        sorted(lot_machine_view["line_id"].dropna().unique().tolist()),
    )

# 필터 적용
if line_filter:
    lot_machine_view = lot_machine_view[
        lot_machine_view["line_id"].isin(line_filter)
    ]

# =========================
# 📊 생산 분석
# =========================
if menu == "📊 생산 분석":
    st.header("📊 생산 분석")

    if st.button("Run 생산 분석"):
        result = production_kpis(lot_machine_view)

        st.subheader("LOT 기준 KPI")
        st.dataframe(
            result["lot_level"].head(20),
            use_container_width=True,
        )

# =========================
# 🛠 설비 이상 분석
# =========================
elif menu == "🛠 설비 이상 분석":
    st.header("🛠 설비 이상 분석")

    with st.expander("설비 이상 파라미터", expanded=True):
        w_stop_time = st.slider("정지시간 가중치", 0.5, 2.0, 1.0)
        w_stop_count = st.slider("정지횟수 가중치", 0.0, 2.0, 0.5)
        w_error_ratio = st.slider("ERROR 비중 가중치", 0.0, 3.0, 1.0)
        method = st.selectbox("이상 탐지 방법", ["zscore", "iqr"])

    if st.button("Run 설비 이상 분석"):
        params = EquipmentAnomalyParams(
            w_stop_time=w_stop_time,
            w_stop_count=w_stop_count,
            w_error_ratio=w_error_ratio,
            anomaly_method=method,
        )

        result = run_equipment_anomaly_analysis(
            lot_machine_view,
            stop_log,
            stop_reason,
            params,
        )

        st.subheader("이상 설비 TOP")
        st.dataframe(result.head(20), use_container_width=True)

# =========================
# 🧪 품질 분석
# =========================
elif menu == "🧪 품질 분석":
    st.header("🧪 품질 분석")

    with st.expander("품질 리스크 파라미터", expanded=True):
        w_pickup = st.slider("Pickup Error 가중치", 0.5, 3.0, 1.0)
        w_recognition = st.slider("Recognition Error 가중치", 0.5, 3.0, 1.0)
        w_pre_pickup = st.slider("Pre-Pickup Error 가중치", 0.0, 2.0, 0.5)
        w_stop = st.slider("Stop Time 가중치", 0.0, 2.0, 0.5)
        min_pickup = st.number_input("최소 Pickup 수", 100, 10000, 1000)

    if st.button("Run 품질 분석"):
        params = QualityRiskParams(
            w_pickup=w_pickup,
            w_recognition=w_recognition,
            w_pre_pickup=w_pre_pickup,
            w_stop_ratio=w_stop,
            min_pickup_count=min_pickup,
        )

        result = run_quality_risk_analysis(
            lot,
            lot_machine,
            machine,
            time_summary,
            pickup_summary,
            params,
        )

        st.subheader("LOT 품질 Risk TOP")
        st.dataframe(
            result[
                ["lot_id", "machine_id", "risk_score", "risk_level"]
            ].head(20),
            use_container_width=True,
        )

# =========================
# 📈 ERD 핵심 분석
# =========================
elif menu == "📈 ERD 핵심 분석":
    st.header("📈 ERD 핵심 분석")
    analysis_tab = st.selectbox(
        "분석 항목",
        [
            "Top 정지코드 10개 시간손실 기여도",
            "설비별 가동률 vs 에러율 매트릭스",
            "부품(Part Number)별 에러 Pareto",
            "태그 스펙 이탈 상위 20개",
        ],
    )

    if analysis_tab == "Top 정지코드 10개 시간손실 기여도":
        required = {"stop_reason_code", "duration_sec", "stop_count", "lot_machine_id"}
        if stop_log.empty or not required.issubset(stop_log.columns):
            st.warning("`stop_log` 테이블(필수 컬럼 포함)을 찾을 수 없어 분석을 실행할 수 없습니다.")
        else:
            stop_df = stop_log.copy()
            stop_df["duration_sec"] = pd.to_numeric(stop_df["duration_sec"], errors="coerce").fillna(0)
            stop_df["stop_count"] = pd.to_numeric(stop_df["stop_count"], errors="coerce").fillna(0)

            by_reason = (
                stop_df.groupby("stop_reason_code", dropna=False)
                .agg(total_duration_sec=("duration_sec", "sum"), total_stop_count=("stop_count", "sum"))
                .reset_index()
                .sort_values("total_duration_sec", ascending=False)
            )

            total_duration = by_reason["total_duration_sec"].sum()
            by_reason["contribution_pct"] = np.where(
                total_duration > 0,
                by_reason["total_duration_sec"] / total_duration * 100,
                0.0,
            )

            if not stop_reason.empty and {"stop_reason_code", "stop_reason_name", "stop_reason_group"}.issubset(stop_reason.columns):
                by_reason = by_reason.merge(
                    stop_reason[["stop_reason_code", "stop_reason_name", "stop_reason_group"]],
                    on="stop_reason_code",
                    how="left",
                )

            top10 = by_reason.head(10)
            st.metric("전체 정지시간(초)", f"{int(total_duration):,}")
            st.dataframe(top10, use_container_width=True)
            st.bar_chart(
                top10.set_index("stop_reason_code")["total_duration_sec"],
                use_container_width=True,
            )

    elif analysis_tab == "설비별 가동률 vs 에러율 매트릭스":
        required = {
            "machine_id",
            "power_on_time_sec",
            "running_time_sec",
            "total_pickup_count",
            "total_error_count",
        }
        if lot_machine_view.empty or not required.issubset(lot_machine_view.columns):
            st.warning("`lot_machine_view` 계산에 필요한 컬럼이 부족해 분석을 실행할 수 없습니다.")
        else:
            matrix_df = lot_machine_view.copy()
            matrix_df["power_on_time_sec"] = pd.to_numeric(matrix_df["power_on_time_sec"], errors="coerce")
            matrix_df["running_time_sec"] = pd.to_numeric(matrix_df["running_time_sec"], errors="coerce")
            matrix_df["total_pickup_count"] = pd.to_numeric(matrix_df["total_pickup_count"], errors="coerce").fillna(0)
            matrix_df["total_error_count"] = pd.to_numeric(matrix_df["total_error_count"], errors="coerce").fillna(0)

            by_machine = (
                matrix_df.groupby("machine_id", dropna=False)
                .agg(
                    power_on_time_sec=("power_on_time_sec", "sum"),
                    running_time_sec=("running_time_sec", "sum"),
                    total_pickup_count=("total_pickup_count", "sum"),
                    total_error_count=("total_error_count", "sum"),
                )
                .reset_index()
            )
            by_machine["uptime_ratio"] = by_machine["running_time_sec"] / by_machine["power_on_time_sec"].replace(0, np.nan)
            by_machine["error_rate"] = by_machine["total_error_count"] / by_machine["total_pickup_count"].replace(0, np.nan)

            x_median = by_machine["uptime_ratio"].median()
            y_median = by_machine["error_rate"].median()
            by_machine["quadrant"] = np.select(
                [
                    (by_machine["uptime_ratio"] >= x_median) & (by_machine["error_rate"] < y_median),
                    (by_machine["uptime_ratio"] >= x_median) & (by_machine["error_rate"] >= y_median),
                    (by_machine["uptime_ratio"] < x_median) & (by_machine["error_rate"] < y_median),
                ],
                ["우수(고가동·저에러)", "품질 개선 필요", "가동 개선 필요"],
                default="핵심 개선 대상",
            )

            st.caption(f"중앙값 기준선: 가동률={x_median:.3f}, 에러율={y_median:.3%}")
            st.dataframe(by_machine.sort_values(["error_rate", "uptime_ratio"], ascending=[False, True]), use_container_width=True)
            st.scatter_chart(
                by_machine,
                x="uptime_ratio",
                y="error_rate",
                size="total_pickup_count",
                color="quadrant",
                use_container_width=True,
            )

    elif analysis_tab == "부품(Part Number)별 에러 Pareto":
        required = {"component_id", "pickup_count", "error_count"}
        if component_pickup_summary.empty or not required.issubset(component_pickup_summary.columns):
            st.warning("`component_pickup_summary` 테이블(필수 컬럼 포함)을 찾을 수 없어 분석을 실행할 수 없습니다.")
        else:
            comp_df = component_pickup_summary.copy()
            comp_df["pickup_count"] = pd.to_numeric(comp_df["pickup_count"], errors="coerce").fillna(0)
            comp_df["error_count"] = pd.to_numeric(comp_df["error_count"], errors="coerce").fillna(0)

            by_part = comp_df.groupby("component_id", dropna=False).agg(
                pickup_count=("pickup_count", "sum"),
                error_count=("error_count", "sum"),
            ).reset_index()

            if not component.empty and {"component_id", "part_number"}.issubset(component.columns):
                by_part = by_part.merge(
                    component[["component_id", "part_number"]],
                    on="component_id",
                    how="left",
                )
            else:
                by_part["part_number"] = by_part["component_id"]

            by_part = by_part.groupby("part_number", dropna=False).agg(
                pickup_count=("pickup_count", "sum"),
                error_count=("error_count", "sum"),
            ).reset_index()
            by_part = by_part.sort_values("error_count", ascending=False)

            total_error = by_part["error_count"].sum()
            by_part["error_contribution_pct"] = np.where(
                total_error > 0,
                by_part["error_count"] / total_error * 100,
                0.0,
            )
            by_part["cumulative_pct"] = by_part["error_contribution_pct"].cumsum()
            by_part["error_rate"] = by_part["error_count"] / by_part["pickup_count"].replace(0, np.nan)

            top_n = st.slider("Pareto 표시 개수", min_value=10, max_value=min(100, len(by_part) if len(by_part) > 0 else 10), value=min(20, len(by_part) if len(by_part) > 0 else 10))
            top_parts = by_part.head(top_n)

            st.dataframe(top_parts, use_container_width=True)
            st.bar_chart(top_parts.set_index("part_number")["error_count"], use_container_width=True)

    elif analysis_tab == "태그 스펙 이탈 상위 20개":
        required_rt = {"tag_id", "tag_value"}
        required_spec = {"tag_id", "spec_type", "spec_value"}

        if tag_realtime.empty or tag_spec.empty or not required_rt.issubset(tag_realtime.columns) or not required_spec.issubset(tag_spec.columns):
            st.warning("`tag_realtime` 또는 `tag_spec` 테이블(필수 컬럼 포함)을 찾을 수 없어 분석을 실행할 수 없습니다.")
        else:
            rt_df = tag_realtime.copy()
            sp_df = tag_spec.copy()
            rt_df["tag_value"] = pd.to_numeric(rt_df["tag_value"], errors="coerce")
            sp_df["spec_value"] = pd.to_numeric(sp_df["spec_value"], errors="coerce")

            spec_pivot = (
                sp_df[sp_df["spec_type"].isin(["LCL", "UCL"])][["tag_id", "spec_type", "spec_value"]]
                .pivot_table(index="tag_id", columns="spec_type", values="spec_value", aggfunc="last")
                .reset_index()
            )

            merged = rt_df.merge(spec_pivot, on="tag_id", how="inner")
            merged = merged[merged["tag_value"].notna()]
            merged["out_of_spec"] = (
                (merged["LCL"].notna() & (merged["tag_value"] < merged["LCL"]))
                | (merged["UCL"].notna() & (merged["tag_value"] > merged["UCL"]))
            )

            outlier = (
                merged.groupby("tag_id", dropna=False)
                .agg(total_count=("tag_id", "size"), out_of_spec_count=("out_of_spec", "sum"))
                .reset_index()
            )
            outlier["out_of_spec_rate"] = outlier["out_of_spec_count"] / outlier["total_count"].replace(0, np.nan)

            if not tag_info.empty and {"tag_id", "tag_name", "tag_category_id"}.issubset(tag_info.columns):
                outlier = outlier.merge(
                    tag_info[["tag_id", "tag_name", "tag_category_id"]],
                    on="tag_id",
                    how="left",
                )

            top20 = outlier.sort_values(["out_of_spec_count", "out_of_spec_rate"], ascending=False).head(20)
            st.dataframe(top20, use_container_width=True)
            st.bar_chart(top20.set_index("tag_id")["out_of_spec_count"], use_container_width=True)
