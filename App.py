
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

st.header("Time Loss Decomposition Analysis")
st.subheader("시간 손실 구조 분해 분석")

st.markdown("""
**개념**  
생산 시간을 단일 가동률(OEE)로 보지 않고,  
Actual / Waiting / Stop으로 구조적으로 분해하여 분석합니다.

**SMT 공정에서 중요한 이유**  
SMT 라인은 설비 성능 문제와 공정 흐름 문제가 동시에 발생합니다.  
단일 지표(OEE)만으로는 개선 방향을 결정할 수 없습니다.

**이 분석으로 얻는 인사이트**  
- 설비를 고쳐야 할 문제인지  
- 계획·투입을 조정해야 할 문제인지  
를 사전에 구분할 수 있습니다.

**활용 화면**  
Sankey Diagram 기반 시간 흐름 분석
""")

with st.expander("📘 분석 방법 (Methodology)"):
    st.markdown("""
    - 입력 데이터: Prod / Actual / Front Wait / Stop  
    - 분해 논리: Planned → Actual + Wait + Stop  
    - 해석 기준:
      - Front Wait ↑ → 투입/계획 문제
      - Stop Loss ↑ → 설비/알람 문제
    """)

st.divider()

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

st.markdown("---")

# ==================================================
# Equipment Analysis 
# ==================================================
st.header("Directional Equipment Error Analysis")
st.subheader("설비 오류 방향성 분석")

st.markdown("""
**개념**  
오류 발생 건수를 단순 집계하지 않고,  
Pick Error와 Recognition Error의 상대적 방향성을 분석합니다.

**SMT 공정에서 중요한 이유**  
SMT 설비 문제는 대부분 자재/흡착 계열 또는 비전 계열로 분리됩니다.  
방향성이 다르면 조치 방법도 완전히 달라집니다.

**이 분석으로 얻는 인사이트**  
- Pick 집중 → 자재, 피더, 노즐, 흡착 조건  
- Recognition 집중 → 조명, 카메라, 비전 라이브러리
""")

with st.expander("📘 분석 방법 (Methodology)"):
    st.markdown("""
    - 사용 지표: CPErr / CRErr  
    - 시각화 목적: 오류 총량이 아닌 방향성 판단  
    - 판정 포인트: 한쪽 축 집중 여부
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

st.header("Baseline Drift Detection")
st.subheader("기준선 이탈 탐지")

st.markdown("""
**개념**  
전체 평균을 기준으로 하지 않고,  
초기 정상 Lot 구간을 Baseline으로 설정하여 이후 변화를 추적합니다.

**SMT 공정에서 중요한 이유**  
SMT 품질 문제는 대부분 서서히 악화되는 형태로 발생합니다.  
평균 기반 관리선은 감지 시점이 늦습니다.

**이 분석으로 얻는 인사이트**  
- 불량 발생 이전의 이상 징후 감지  
- 자재 Lot 변경 / 셋업 변화 영향 추적

**활용 화면**  
Miss Rate Trend + Baseline 비교
""")

with st.expander("📘 분석 방법 (Methodology)"):
    st.markdown("""
    - 기준선: 초기 정상 Lot 평균  
    - 판단 로직: 기준선 대비 Drift 누적 여부  
    - 목적: 평균 관리선 대비 조기 감지
    """)

fig_q1 = go.Figure()
fig_q1.add_trace(go.Scatter(y=df["MissRate"], mode="lines"))
fig_q1.add_hline(y=baseline_mean, line_dash="dash")
fig_q1.update_layout(height=300)
st.plotly_chart(fig_q1, use_container_width=True)

st.markdown("---")

st.header("Lot-to-Lot Change Detection")
st.subheader("Lot 간 급격한 변화 탐지")

st.markdown("""
**개념**  
절대 품질 수준이 아니라,  
이전 Lot 대비 변화량(Δ)을 기준으로 이상을 감지합니다.

**SMT 공정에서 중요한 이유**  
작업자 교대, 자재 교체, 조건 변경은 대부분 Lot 경계에서 발생합니다.

**이 분석으로 얻는 인사이트**  
- 품질 문제가 언제부터 시작되었는지 정확한 시점 특정  
- 변경 이벤트와의 연관성 분석 가능

**활용 화면**  
Lot-to-Lot Δ Trend + Change Point 표시
""")

with st.expander("📘 분석 방법 (Methodology)"):
    st.markdown("""
    - 분석 지표: Delta Miss Rate  
    - 판단 기준: 표준편차 초과 변화  
    - 활용: 이벤트 시점 역추적
    """)

fig_q2 = px.scatter(df, x="PickRatio", y="RecoRatio")
fig_q2.update_layout(height=300)
st.plotly_chart(fig_q2, use_container_width=True)

st.markdown("---")

st.header("Error Mix Pattern Analysis")
st.subheader("오류 성격 변화 분석")

st.markdown("""
**개념**  
Miss Rate를 단일 수치로 보지 않고,  
Pick Miss와 Recognition Miss 비중으로 분해하여 분석합니다.

**SMT 공정에서 중요한 이유**  
불량률이 같아도 불량의 성격이 변하면 공정 상태는 완전히 다릅니다.

**이 분석으로 얻는 인사이트**  
- 조건 붕괴 초기 단계 감지  
- 품질 악화 방향성 선제 파악

**활용 화면**  
Pick Ratio vs Recognition Ratio Scatter
""")

with st.expander("📘 분석 방법 (Methodology)"):
    st.markdown("""
    - 분해 지표: Pick Ratio / Recognition Ratio  
    - 해석 포인트: 비중 구조 변화  
    - 목적: 문제 방향성 조기 인식
    """)

fig_q3 = go.Figure()
fig_q3.add_trace(go.Scatter(y=df["DeltaMissRate"], mode="lines"))
fig_q3.add_hline(y=df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.add_hline(y=-df["DeltaMissRate"].std(), line_dash="dot", line_color="red")
fig_q3.update_layout(height=300)
st.plotly_chart(fig_q3, use_container_width=True)
