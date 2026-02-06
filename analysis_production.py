import streamlit as st
import numpy as np
import pandas as pd

# =========================
# Page Header
# =========================
st.header("📊 생산 분석 (Production Analysis)")

st.markdown("""
**분석 목적**
- LOT 단위 생산 실적을 집계합니다.
- 가동 시간 대비 생산량(UPS)으로 **생산 효율을 비교**합니다.
- 정지 시간이 생산에 미치는 영향을 확인해 **개선 대상 LOT**을 찾습니다.
""")

# =========================
# 사용자 파라미터
# =========================
with st.expander("분석 옵션", expanded=True):
    ups_threshold = st.slider("UPS 기준 (저효율 판별)", 0.0, 5.0, 1.0, 0.1)
    top_n = st.selectbox("LOT 표시 개수", [10, 20, 50], index=1)

# =========================
# Run Analysis
# =========================
if st.button("Run 생산 분석"):
    result = production_kpis(lot_machine_view)
    lot_level = result["lot_level"]

    # =========================
    # KPI Summary
    # =========================
    st.subheader("🔎 생산 KPI 요약")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "총 생산량",
        f"{int(lot_level['actual_qty'].sum()):,}"
    )

    col2.metric(
        "평균 UPS",
        f"{lot_level['ups'].mean():.2f}"
    )

    col3.metric(
        "총 가동 시간 (h)",
        f"{lot_level['running_time_sec'].sum() / 3600:.1f}"
    )

    col4.metric(
        "총 정지 시간 (h)",
        f"{lot_level['total_stop_time_sec'].sum() / 3600:.1f}"
    )

    # =========================
    # LOT 생산 효율 분포
    # =========================
    st.subheader("📈 LOT별 생산 효율 (UPS)")

    ups_sorted = (
        lot_level
        .sort_values("ups", ascending=False)
        .head(top_n)
        .set_index("lot_name")
    )

    st.bar_chart(ups_sorted["ups"])

    st.caption("• UPS가 낮은 LOT은 생산 효율 저하 후보")

    # =========================
    # Stop Time vs Output Scatter
    # =========================
    st.subheader("📉 정지시간 vs 생산량 분포")

    scatter_df = lot_level.copy()
    scatter_df["stop_time_hr"] = scatter_df["total_stop_time_sec"] / 3600

    st.scatter_chart(
        scatter_df,
        x="stop_time_hr",
        y="actual_qty",
    )

    st.caption(
        "• 정지시간이 많고 생산량이 낮은 LOT은 개선 우선 대상\n"
        "• 정지시간이 적은데 생산량이 낮으면 설비/조건 문제 가능"
    )

    # =========================
    # Low Efficiency LOT Highlight
    # =========================
    st.subheader("⚠️ 저효율 LOT 목록 (UPS 기준 이하)")

    low_eff = lot_level[lot_level["ups"] < ups_threshold]

    if low_eff.empty:
        st.success("UPS 기준 이하 LOT 없음")
    else:
        st.dataframe(
            low_eff
            .sort_values("ups")
            .loc[:, [
                "lot_name",
                "line_id",
                "actual_qty",
                "ups",
                "running_time_sec",
                "total_stop_time_sec",
            ]],
            use_container_width=True,
        )

    # =========================
    # Detail Table
    # =========================
    st.subheader("📋 LOT 생산 상세 데이터")

    st.dataframe(
        lot_level
        .sort_values("ups")
        .reset_index(drop=True),
        use_container_width=True,
    )
