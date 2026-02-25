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


def _fmt_num(value, digits=2):
    if pd.isna(value):
        return "-"
    return f"{value:,.{digits}f}"

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

        lot_level = result["lot_level"].copy()

        stop_denominator = (
            lot_level["running_time_sec"].fillna(0)
            + lot_level["total_stop_time_sec"].fillna(0)
        ).to_numpy(dtype=float)
        stop_numerator = lot_level["total_stop_time_sec"].fillna(0).to_numpy(dtype=float)
        lot_level["stop_ratio"] = np.divide(
            stop_numerator,
            stop_denominator,
            out=np.zeros_like(stop_numerator, dtype=float),
            where=stop_denominator != 0,
        )


        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LOT 수", f"{len(lot_level):,}")
        c2.metric("총 생산 수량", _fmt_num(lot_level["actual_qty"].sum(), 0))
        c3.metric("평균 UPS", _fmt_num(lot_level["ups"].mean(), 3))
        c4.metric("평균 정지비율", f"{_fmt_num(lot_level['stop_ratio'].mean() * 100, 1)}%")

        st.markdown("#### 시각화")
        left, right = st.columns(2)

        with left:
            st.caption("Top 10 LOT 생산 수량")
            top_qty = (
                lot_level[["lot_id", "actual_qty"]]
                .sort_values("actual_qty", ascending=False)
                .head(10)
                .set_index("lot_id")
            )
            st.bar_chart(top_qty)

            st.caption("라인별 평균 UPS")
            line_ups = (
                lot_level.groupby("line_id", dropna=False)["ups"]
                .mean()
                .sort_values(ascending=False)
                .rename("avg_ups")
            )
            st.bar_chart(line_ups)

        with right:
            st.caption("LOT 러닝시간(시간) vs 생산수량")
            scatter_df = lot_level[["running_time_hr", "actual_qty"]].dropna()
            if not scatter_df.empty:
                st.scatter_chart(scatter_df, x="running_time_hr", y="actual_qty")
            else:
                st.info("산점도 표시를 위한 데이터가 부족합니다.")

            st.caption("LOT별 정지시간(시간) Top 10")
            top_stop = (
                lot_level[["lot_id", "stop_time_hr"]]
                .sort_values("stop_time_hr", ascending=False)
                .head(10)
                .set_index("lot_id")
            )
            st.bar_chart(top_stop)

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

        c1, c2, c3 = st.columns(3)
        c1.metric("분석 설비 수", f"{len(result):,}")
        c2.metric("이상 설비 수", f"{int(result['is_anomaly'].sum()):,}")
        c3.metric("최대 이상 점수", _fmt_num(result["anomaly_score"].max(), 2))

        st.markdown("#### 시각화")
        left, right = st.columns(2)

        with left:
            st.caption("설비별 이상 점수 Top 15")
            anomaly_top = (
                result[["machine_id", "anomaly_score"]]
                .sort_values("anomaly_score", ascending=False)
                .head(15)
                .set_index("machine_id")
            )
            st.bar_chart(anomaly_top)

            st.caption("라인별 총 정지시간(시간)")
            line_stop = (
                result.groupby("line_id", dropna=False)["total_stop_sec"]
                .sum()
                .div(3600)
                .rename("stop_hour")
            )
            st.bar_chart(line_stop)

        with right:
            st.caption("정지시간 vs 정지횟수")
            scatter_df = result[["total_stop_sec", "total_stop_count"]].dropna()
            if not scatter_df.empty:
                st.scatter_chart(scatter_df, x="total_stop_sec", y="total_stop_count")
            else:
                st.info("산점도 표시를 위한 데이터가 부족합니다.")

            reason_cols = [
                col for col in ["ERROR", "SETUP", "MATERIAL", "OPERATION"] if col in result.columns
            ]
            if reason_cols:
                st.caption("주요 정지 사유 합계(초)")
                reason_sum = result[reason_cols].sum().sort_values(ascending=False)
                st.bar_chart(reason_sum)

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

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("분석 건수", f"{len(result):,}")
        c2.metric("HIGH 리스크 건수", f"{int((result['risk_level'] == 'HIGH').sum()):,}")
        c3.metric("이상치 건수", f"{int(result['is_anomaly'].sum()):,}")
        c4.metric("평균 리스크 점수", _fmt_num(result["risk_score"].mean(), 4))

        st.markdown("#### 시각화")
        left, right = st.columns(2)

        with left:
            st.caption("리스크 레벨 분포")
            level_dist = result["risk_level"].astype(str).value_counts()
            st.bar_chart(level_dist)

            st.caption("리스크 점수 Top 15")
            risk_top = (
                result[["lot_id", "risk_score"]]
                .sort_values("risk_score", ascending=False)
                .head(15)
                .set_index("lot_id")
            )
            st.bar_chart(risk_top)

        with right:
            st.caption("Pickup 수량 vs 리스크 점수")
            scatter_df = result[["total_pickup_count", "risk_score"]].dropna()
            if not scatter_df.empty:
                st.scatter_chart(scatter_df, x="total_pickup_count", y="risk_score")
            else:
                st.info("산점도 표시를 위한 데이터가 부족합니다.")

            st.caption("리스크 점수 분포")
            hist_input = result[["risk_score"]].dropna()
            if not hist_input.empty:
                st.bar_chart(hist_input)
