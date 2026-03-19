import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="환경-보건 분석 대시보드", layout="wide")

st.title("🌍 환경 정책 실효성 분석 대시보드")
st.markdown("자가용 이용률 → NOx → 폐질환 구조를 시각적으로 확인합니다.")

# ---------------------------
# 1. 가상 데이터 생성
# ---------------------------
@st.cache_data
def load_data():
    np.random.seed(42)
    n = 50

    data = pd.DataFrame({
        "Region": [f"R{i}" for i in range(n)],
        "Car_Usage": np.random.uniform(40, 90, n),
        "Pop_Density": np.random.uniform(2000, 15000, n),
    })

    # NOx: 자가용 + 인구밀도 영향
    data["NOx"] = 0.02 * data["Car_Usage"] + 0.0005 * data["Pop_Density"] + np.random.normal(0, 0.5, n)

    # SOx: 랜덤 + 약한 영향
    data["SOx"] = np.random.uniform(0.01, 0.05, n)

    # 폐질환: NOx 영향 (핵심 구조)
    data["Lung_Disease"] = 18 * data["NOx"] + np.random.normal(0, 5, n)

    return data

df = load_data()

# ---------------------------
# 2. 사이드바 (정책 시뮬레이션)
# ---------------------------
st.sidebar.header("📊 정책 시나리오")

policy = st.sidebar.selectbox(
    "정책 선택",
    ["기본 상태", "대중교통 인센티브", "저배출구역(LEZ)", "통합 정책"]
)

df_sim = df.copy()

if policy == "대중교통 인센티브":
    df_sim["Car_Usage"] *= 0.9

elif policy == "저배출구역(LEZ)":
    df_sim["NOx"] *= 0.8

elif policy == "통합 정책":
    df_sim["Car_Usage"] *= 0.85
    df_sim["NOx"] *= 0.7

# 정책 반영 후 재계산
df_sim["NOx"] = 0.02 * df_sim["Car_Usage"] + 0.0005 * df_sim["Pop_Density"]
df_sim["Lung_Disease"] = 18 * df_sim["NOx"]

# ---------------------------
# 3. KPI
# ---------------------------
col1, col2, col3 = st.columns(3)

col1.metric("평균 NOx", f"{df_sim['NOx'].mean():.2f}")
col2.metric("평균 폐질환 지수", f"{df_sim['Lung_Disease'].mean():.2f}")
col3.metric("자가용 이용률", f"{df_sim['Car_Usage'].mean():.1f}%")

# ---------------------------
# 4. 시각화
# ---------------------------
st.subheader("📈 NOx vs 폐질환 관계")

fig1 = px.scatter(
    df_sim,
    x="NOx",
    y="Lung_Disease",
    trendline="ols",
    title="NOx 증가 → 폐질환 증가"
)
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------
# 5. 매개효과 구조 시각화
# ---------------------------
st.subheader("🔗 구조적 관계")

fig2 = px.scatter(
    df_sim,
    x="Car_Usage",
    y="NOx",
    trendline="ols",
    title="자가용 이용률 → NOx 증가"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 6. 정책 효과 비교
# ---------------------------
st.subheader("📊 정책 효과 비교")

baseline = df["Lung_Disease"].mean()
after = df_sim["Lung_Disease"].mean()

st.write(f"정책 전 폐질환 지수: {baseline:.2f}")
st.write(f"정책 후 폐질환 지수: {after:.2f}")
st.write(f"감소율: {(baseline - after)/baseline * 100:.2f}%")

# ---------------------------
# 7. 해석
# ---------------------------
st.subheader("🧠 해석")

st.markdown(f"""
- 현재 선택된 정책: **{policy}**
- 본 모델은 **자가용 → NOx → 폐질환**의 매개 구조를 반영합니다.
- 특히 NOx가 건강 영향의 핵심 변수입니다.
- 따라서 교통 정책이 곧 보건 정책으로 연결됩니다.
""")
