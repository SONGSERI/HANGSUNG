import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib

# ============================================================
# 한글 폰트 (macOS)
# ============================================================
# font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
# font_prop = fm.FontProperties(fname=font_path)
# matplotlib.rcParams["font.family"] = font_prop.get_name()
# matplotlib.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="SMT 설비 정지 KPI 분석", layout="wide")

# ============================================================
# Demo 데이터 (고객 DB 가정)
# ============================================================
np.random.seed(42)
df = pd.DataFrame({
    "설비": [f"M{i}" for i in range(1, 9)],
    "CPErr": np.random.randint(3, 30, 8),
    "CRErr": np.random.randint(2, 20, 8),
    "CPErrStop": np.random.randint(300, 2500, 8),
    "CRErrStop": np.random.randint(200, 2000, 8),
    "PRDStop": np.random.randint(500, 5000, 8),
    "AlarmCnt": np.random.randint(20, 200, 8),
    "Prod": np.random.randint(20000, 45000, 8),
})

# ============================================================
# KPI 계산 (Single Source of Truth)
# ============================================================
df["총 정지 시간"] = df["CPErrStop"] + df["CRErrStop"] + df["PRDStop"]
df["정지 횟수"] = df["CPErr"] + df["CRErr"]
df["평균 정지 시간"] = df["총 정지 시간"] / df["정지 횟수"]

df["Z"] = (df["총 정지 시간"] - df["총 정지 시간"].mean()) / df["총 정지 시간"].std()
df["ADI"] = df["AlarmCnt"] / df["Prod"]
df["PRDI"] = (df["정지 횟수"] * df["평균 정지 시간"]) / df["Prod"]
df["NRSR"] = (df["CPErrStop"] + df["CRErrStop"]) / df["총 정지 시간"]
df["SSI"] = df["평균 정지 시간"] / df["Prod"]

# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("분석 기준 설정")
PRDI_ALERT = st.sidebar.slider("PRDI 경고 기준", 0.05, 0.30, 0.15, 0.01)

selected = st.sidebar.selectbox("설비 선택", df["설비"])

sel = df[df["설비"] == selected].iloc[0]

def percentile(val, series):
    return int((series < val).mean() * 100)

# ============================================================
# Title
# ============================================================
st.title("SMT 설비 정지 데이터 기반 KPI 분석")
st.caption("설명 → 분석 → 판단 → 행동이 연결되는 운영 분석")

# ============================================================
# KPI 설명 패널 (접기/펼치기)
# ============================================================
with st.expander("📌 KPI 설명 (분석 판단 기준)", expanded=False):
    st.markdown("""
본 분석은 정지 데이터를 단순 집계하지 않고  
**설비를 어떻게 관리해야 하는지 판단하기 위한 KPI 체계**를 사용합니다.

아래 KPI는 이후 모든 분석 단계(①~⑤)에서 **공통 기준**으로 사용됩니다.
""")

    st.markdown("### 1️⃣ 설비 상태 신호 KPI")

    st.markdown(f"""
**Z-score (정적 이상도)**  
- 현재 값: **{sel['Z']:.2f}**  
- 전체 설비 중 **상위 {percentile(sel['Z'], df['Z'])}%**

→ 평균 대비 정지가 많은 설비일수록 우선 확인 대상입니다.
""")

    st.markdown(f"""
**ADI (알람 밀도)**  
- 현재 값: **{sel['ADI']:.4f}**  
- 전체 설비 중 **상위 {percentile(sel['ADI'], df['ADI'])}%**

→ 멈추지는 않지만 지속적으로 불안정한 설비 가능성이 있습니다.
""")

    st.markdown("### 2️⃣ 운영 영향 KPI")

    st.markdown(f"""
**PRDI (생산 리듬 붕괴)**  
- 값: **{sel['PRDI']:.3f}**  
- 상위 **{percentile(sel['PRDI'], df['PRDI'])}%**

→ 짧은 정지가 반복되어 생산 흐름을 방해합니다.
""")

    st.markdown(f"""
**NRSR (회복 불능 정지 비율)**  
- 값: **{sel['NRSR']:.1%}**

→ 한 번 멈추면 장시간 정지로 이어질 가능성이 큽니다.
""")

    st.markdown(f"""
**SSI (정지 민감도)**  
- 값: **{sel['SSI']:.4f}**

→ 동일한 정지도 생산에 미치는 영향이 큽니다.
""")

# ============================================================
# ① 설비 이상 탐색
# ============================================================
st.header("① 설비 이상 탐색 (어디가 문제인가)")

fig1, ax1 = plt.subplots()
ax1.bar(df["설비"], df["Z"], color=["red" if z > 1 else "steelblue" for z in df["Z"]])
ax1.axhline(0, linestyle="--")
ax1.set_ylabel("Z-score")
st.pyplot(fig1)

# ============================================================
# ② 정지 성격 분석
# ============================================================
st.header("② 정지 성격 분석 (자주 / 오래)")

fig2, ax2 = plt.subplots()
ax2.scatter(df["PRDI"], df["SSI"], s=120)
ax2.set_xlabel("PRDI (리듬 붕괴)")
ax2.set_ylabel("SSI (정지 민감도)")
st.pyplot(fig2)

# ============================================================
# ③ 원인 구조 분석
# ============================================================
st.header("③ 원인 구조 분석")

fig3, ax3 = plt.subplots()
ax3.pie(
    [sel["CPErrStop"], sel["CRErrStop"], sel["PRDStop"]],
    labels=["Pickup", "Recognition", "Production"],
    autopct="%1.1f%%"
)
ax3.set_title(f"{selected} 정지 사유 구성")
st.pyplot(fig3)

# ============================================================
# ④ 운영 영향 평가
# ============================================================
st.header("④ 운영 영향 평가")

c1, c2, c3 = st.columns(3)
c1.metric("PRDI", f"{sel['PRDI']:.3f}")
c2.metric("NRSR", f"{sel['NRSR']:.1%}")
c3.metric("SSI", f"{sel['SSI']:.4f}")

# ============================================================
# ⑤ 설비 상태 & Action Rule
# ============================================================
st.header("⑤ 설비 상태 판단 및 권장 Action")

def action_rules(row):
    rules = []
    if row["ADI"] > df["ADI"].mean() and row["Z"] < 1:
        rules.append("알람이 잦으나 정지로 이어지지 않는 상태 → 센서/조건 점검 권장")
    if row["PRDI"] > PRDI_ALERT and row["SSI"] > df["SSI"].mean():
        rules.append("짧은 정지가 반복되어 생산 리듬 붕괴 → 작업 조건/프로그램 튜닝")
    if row["NRSR"] > 0.4:
        rules.append("장시간 정지 비율 높음 → 예방 정비 또는 구조 점검")
    if not rules:
        rules.append("현재 KPI 기준 특이 사항 없음 → 정상 운영")
    return rules

for i, r in enumerate(action_rules(sel), 1):
    st.markdown(f"**Action {i}.** {r}")

st.success("KPI 기반으로 설비 상태를 판단하고, 즉시 행동으로 연결합니다.")
