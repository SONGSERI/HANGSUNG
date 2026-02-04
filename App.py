import streamlit as st
import pandas as pd

from db import db_health_check, load_table

status = db_health_check()

if not status["direct_ok"]:
    st.error(status["direct_msg"])
    st.stop()
else:
    st.success(status["direct_msg"])

if not status["sqlalchemy_ok"]:
    st.error(status["sqlalchemy_msg"])
    st.stop()
else:
    st.success(status["sqlalchemy_msg"])


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
    engine = get_engine(
        user="postgres",
        password="postgres",
        host="host.docker.internal",  # 필요시 localhost로 변경
        port=5432,
        dbname="smt",
    )

    lot = load_table(engine, "lot")
    lot_machine = load_table(engine, "lot_machine")
    machine = load_table(engine, "machine")
    time_summary = load_table(engine, "machine_time_summary")
    pickup_summary = load_table(engine, "pickup_error_summary")
    stop_log = load_table(engine, "stop_log")
    stop_reason = load_table(engine, "stop_reason")

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
    ["📊 생산 분석", "🛠 설비 이상 분석", "🧪 품질 분석"],
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
