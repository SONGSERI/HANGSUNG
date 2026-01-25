import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="SMT Analysis Report – Explanation Locked", layout="wide")

# ==================================================
# Data
# ==================================================
np.random.seed(42)
n_lot = 180

df = pd.DataFrame({
    "Lot": np.arange(1, n_lot + 1),
    "Prod": np.random.uniform(16000, 19000, n_lot),
    "Actual": np.random.uniform(10000, 17000, n_lot),
    "Fwait": np.random.uniform(300, 5000, n_lot),
    "TotalStop": np.random.uniform(300, 2000, n_lot),
    "TPickup": np.random.randint(30000, 42000, n_lot),
})

df["CPErr"] = np.random.poisson(3, n_lot)
df["CRErr"] = np.random.poisson(2, n_lot)

df.loc[40:70, "Fwait"] += 2500
df.loc[80:100, "CPErr"] += 12
df.loc[120:135, "CRErr"] += 10

df["TPMiss"] = df["CPErr"]
df["TRMiss"] = df["CRErr"]
df["MissRate"] = (df["TPMiss"] + df["TRMiss"]) / df["TPickup"]

# ==================================================
# Quality anomaly logic
# ==================================================
baseline_window = 30
baseline_mean = df.loc[:baseline_window, "MissRate"].mean()

df["BaselineDrift"] = df["MissRate"] - baseline_mean
df["DeltaMissRate"] = df["MissRate"].diff().fillna(0)

df["PickRatio"] = df["TPMiss"] / (df["TPMiss"] + df["TRMiss"] + 1e-6)
df["RecoRatio"] = df["TRMiss"] / (df["TPMiss"] + df["TRMiss"] + 1e-6)

# ==================================================
# Executive Summary
# ==================================================
prod_score = df["Actual"].sum() / df["Prod"].sum()
equip_score = 1 - ((df["CPErr"] + df["CRErr"]).sum() / df["TotalStop"].sum())
quality_score = 1 - (
    (abs(df["BaselineDrift"]) > df["BaselineDrift"].std()) |
    (abs(df["DeltaMissRate"]) > df["DeltaMissRate"].std())
).mean()

def gauge(title, value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        title={"text": title},
        gauge={"axis": {"range": [0, 100]}}
    ))
    fig.update_layout(height=220, margin=dict(t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.title("SMT 공정 분석 보고서")
st.caption("그래프 + 해석 + 인사이트 고정 구조")

c1, c2, c3 = st.columns(3)
with c1: gauge("Production Stability", prod_score)
with c2: gauge("Equipment Stability", equip_score)
with c3: gauge("Quality Stability", quality_score)

st.markdown("---")

# ==================================================
# Production Analysis
# ==================================================
st.header("Time Loss Decomposition Analysis")
st.subheader("시간 손실 구조 분해 분석")

st.markdown("""
**개념**  
생산 시간을 Actual / Waiting / Stop으로 구조 분해합니다.

**인사이트**  
- 설비 문제인지  
- 흐름/계획 문제인지 구분 가능
""")

sankey = go.Figure(go.Sankey(
    node=dict(label=["Prod Time", "Actual Run", "Front Wait", "Stop Loss"]),
    link=dict(
        source=[0, 0, 0],
        target=[1, 2, 3],
        value=[df["Actual"].sum(), df["Fwait"].sum(), df["TotalStop"].sum()]
    )
))
sankey.update_layout(height=420)
st.plotly_chart(sankey, use_container_width=True)

st.markdown("---")

# ==================================================
# Equipment Analysis  ✅ FIXED
# ==================================================
st.header("Directional Equipment Error Analysis")
st.subheader("설비 오류 방향성 분석")

st.markdown("""
**개념**  
Pick Error와 Recognition Error의 상대적 방향성을 분석합니다.

**SMT 공정에서 중요한 이유**  
오류 유형에 따라 조치 대상이 완전히 달라집니다.

**이 분석으로 얻는 인사이트**  
- Pick 집중 → 자재, 피더, 노즐  
- Recognition 집중 → 조명, 카메라, 비전 라이브러리
""")

st.header("2. 설비 분석 – Pick / Recognition 오류")

fig_e = px.scatter(df, x="CPErr", y="CRErr", size="CPErr")
fig_e.update_layout(height=400)
st.plotly_chart(fig_e, use_container_width=True)

st.markdown("---")

# ==================================================
# Quality Analysis
# ==================================================
st.header("3. 품질 분석 – 이상 탐지")

fig_q1 = go.Figure()
fig_q1.add_trace(go.Scatter(y=df["MissRate"], mode="lines"))
fig_q1.add_hline(y=baseline_mean, line_dash="dash")
fig_q1.update_layout(height=300)
st.plotly_chart(fig_q1, use_container_width=True)

fig_q2 = px.scatter(df, x="PickRatio", y="RecoRatio")
fig_q2.update_layout(height=300)
st.plotly_chart(fig_q2, use_container_width=True)

fig_q3 = go.Figure()
fig_q3.add_trace(go.Scatter(y=df["DeltaMissRate"], mode="lines"))
fig_q3.add_hline(y=df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.add_hline(y=-df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.update_layout(height=300)
st.plotly_chart(fig_q3, use_container_width=True)
