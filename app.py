import streamlit as st
import pandas as pd

# =========================
# 분석 엔진 import
# =========================
from analysis_quality import (
    run_quality_risk_analysis,
    QualityRiskParams,
)

from analysis_equipment import (
    run_equipment_anomaly_analysis,
    EquipmentAnomalyParams,
)

from analysis_production import production_kpis, build_lot_machine_view


# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="SMT Analysis Lab",
    layout="wide",
)

st.title("SMT Analysis Lab")
st.caption("생산 · 설비 · 품질 분석 실험 도구")

# =========================
# 데이터 로딩 (예시)
# 실제로는 PostgreSQL에서 load
# =========================
@st.cache_data
def load_data():
    lot = pd.read_parquet("data/lot.parquet")
    lot_machine = pd.read_parquet("data/lot_machine.parquet")
    machine = pd.read_parquet("data/machine.parquet")
    time_summary = pd.read_parquet("data/machine_time_summary.parquet")
    pickup_summary = pd.read_parquet("data/pickup_error_summary.parquet")
    stop_log = pd.read_parquet("data/stop_log.parquet")
    stop_reason = pd.read_parquet("data/stop_reason.parquet")

    return (
        lot,
        lot_machine,
        machine,
        time_summary,
        pickup_summary,
        stop_log,
        stop_reason,
    )


(
    lot,
    lot_machine,
    machine,
    time_summary,
    pickup_summary,
    stop_log,
    stop_reason,
) = load_data()

# Base View (공통)
lot_machine_view = build_lot_machine_view(
    lot, lot_machine, machine, time_summary, pickup_summary
)

# =========================
# Sidebar 메뉴
# =========================
menu = st.sidebar.radio(
    "분석 선택",
    ["📊 생산 분석", "🛠 설비 이상 분석", "🧪 품질 분석"],
)

with st.sidebar.expander("공통 조건", expanded=True):
    date_range = st.date_input("분석 기간")
    line_filter = st.multiselect(
        "라인",
        options=sorted(lot_machine_view["line_id"].dropna().unique().tolist()),
    )

# =========================
# 📊 생산 분석
# =========================
if menu == "📊 생산 분석":
    st.header("📊 생산 분석")

    if st.button("Run 생산 분석"):
        result = production_kpis(lot_machine_view)

        st.subheader("LOT 기준 생산 KPI")
        st.dataframe(result["lot_level"].head(20), use_container_width=True)

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

        st.subheader("이상 설비 Top")
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

        st.subheader("LOT 품질 Risk Top")
        st.dataframe(
            result[
                ["lot_id", "machine_id", "risk_score", "risk_level"]
            ].head(20),
            use_container_width=True,
        )

