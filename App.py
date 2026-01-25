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
# Quality anomaly logic (used for explanation context)
# ==================================================
baseline_window = 30
baseline_mean = df.loc[:baseline_window, "MissRate"].mean()

df["BaselineDrift"] = df["MissRate"] - baseline_mean
df["DeltaMissRate"] = df["MissRate"].diff().fillna(0)

df["PickRatio"] = df["TPMiss"] / (df["TPMiss"] + df["TRMiss"] + 1e-6)
df["RecoRatio"] = df["TRMiss"] / (df["TPMiss"] + df["TRMiss"] + 1e-6)

# ==================================================
# Executive Summary (kept)
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
st.header("1. 생산 분석 – 시간 손실 구조")

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

st.markdown(
"""
**그래프 해석**  
- 흐름의 두께는 생산 시간이 어디에서 소비되는지를 의미한다.

**인사이트**  
- 생산 손실의 원인이 설비 문제인지, 라인 흐름 문제인지를 구분할 수 있다.

**왜 이런 결과가 나왔는가**  
- Front Wait 비중이 큰 경우: 앞 공정 투입 불균형 또는 계획 문제  
- Stop Loss 비중이 큰 경우: 설비 오류, 알람, Pick/Recognition 문제 누적
"""
)

st.markdown("---")

# ==================================================
# Equipment Analysis
# ==================================================
st.header("2. 설비 분석 – Pick / Recognition 오류")

fig_e = px.scatter(df, x="CPErr", y="CRErr", size="CPErr")
fig_e.update_layout(height=400)
st.plotly_chart(fig_e, use_container_width=True)

st.markdown(
"""
**그래프 해석**  
- X축은 Pick 오류, Y축은 Recognition 오류 빈도를 의미한다.

**인사이트**  
- 오류의 집중 영역을 통해 설비 취약 포인트를 파악할 수 있다.

**왜 이런 결과가 나왔는가**  
- Pick 오류 증가: 자재 품질, 피더, 흡착 조건  
- Recognition 오류 증가: 조명, 카메라, 라이브러리 설정
"""
)

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

st.markdown(
"""
**그래프 해석**  
- Miss Rate가 기준선에서 점진적으로 벗어나는지를 확인한다.

**인사이트**  
- 급격한 불량 이전에 누적되는 품질 리스크를 조기에 감지한다.

**왜 이런 결과가 나왔는가**  
- 자재 Lot 변경  
- 노즐/피더 교체 후 조건 미세 변화  
- 셋업 편차 누적
"""
)

st.markdown("---")

fig_q2 = px.scatter(df, x="PickRatio", y="RecoRatio")
fig_q2.update_layout(height=300)
st.plotly_chart(fig_q2, use_container_width=True)

st.markdown(
"""
**그래프 해석**  
- Pick 오류와 Recognition 오류 비중 분포를 나타낸다.

**인사이트**  
- 불량의 양이 아니라 성격 변화를 감지할 수 있다.

**왜 이런 결과가 나왔는가**  
- Pick 비중 증가: 자재/피더 계열 문제  
- Recognition 비중 증가: 비전 조건 문제
"""
)

st.markdown("---")

fig_q3 = go.Figure()
fig_q3.add_trace(go.Scatter(y=df["DeltaMissRate"], mode="lines"))
fig_q3.add_hline(y=df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.add_hline(y=-df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.update_layout(height=300)
st.plotly_chart(fig_q3, use_container_width=True)

st.markdown(
"""
**그래프 해석**  
- Lot 간 품질 변화의 크기를 나타낸다.

**인사이트**  
- 문제가 시작된 시점을 명확히 특정할 수 있다.

**왜 이런 결과가 나왔는가**  
- 작업자 교대  
- 자재 교체  
- 프로그램 또는 조건 변경
"""
)
