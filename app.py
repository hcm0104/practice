import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# -----------------------
# 기본 설정
# -----------------------
st.set_page_config(page_title="환경 정책 효과 분석 대시보드", layout="wide")

st.title("🌍 환경-보건 통합 분석 대시보드")
st.markdown("교통, 대기오염, 건강 간의 관계를 분석하고 정책 효과를 시뮬레이션합니다.")

# -----------------------
# 데이터 로드
# -----------------------
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# -----------------------
# 사이드바 (필터)
# -----------------------
st.sidebar.header("📊 필터 설정")

car_usage = st.sidebar.slider("자가용 이용률 (%)", 0, 100, (20, 80))
pop_density = st.sidebar.slider("인구밀도", int(df["Pop_Density"].min()), int(df["Pop_Density"].max()))

filtered_df = df[
    (df["Car_Usage"] >= car_usage[0]) &
    (df["Car_Usage"] <= car_usage[1]) &
    (df["Pop_Density"] >= pop_density)
]

# -----------------------
# 1. 기본 현황
# -----------------------
st.subheader("📌 주요 지표")

col1, col2, col3 = st.columns(3)

col1.metric("평균 NOx", round(filtered_df["NOx_Conc"].mean(), 3))
col2.metric("평균 SOx", round(filtered_df["SOx_Conc"].mean(), 3))
col3.metric("폐질환 지수", round(filtered_df["Lung_Disease"].mean(), 1))

# -----------------------
# 2. 상관관계 시각화
# -----------------------
st.subheader("📈 NOx vs 폐질환")

fig = px.scatter(
    filtered_df,
    x="NOx_Conc",
    y="Lung_Disease",
    trendline="ols",
    title="NOx 농도와 폐질환 관계"
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------
# 3. 회귀 분석
# -----------------------
st.subheader("📊 회귀 분석 결과")

X = filtered_df[["NOx_Conc"]]
y = filtered_df["Lung_Disease"]

model = LinearRegression()
model.fit(X, y)

coef = model.coef_[0]
intercept = model.intercept_

st.write(f"👉 회귀식: Lung_Disease = {coef:.2f} * NOx + {intercept:.2f}")
st.write(f"👉 NOx 0.01 증가 시 영향: {coef * 0.01:.2f}")

# -----------------------
# 4. 정책 시뮬레이션
# -----------------------
st.subheader("🚦 정책 시뮬레이션")

scenario = st.selectbox(
    "정책 선택",
    ["기본 상태", "대중교통 활성화", "저배출구역 (LEZ)", "통합 정책"]
)

sim_df = filtered_df.copy()

if scenario == "대중교통 활성화":
    sim_df["Car_Usage"] *= 0.9
    sim_df["NOx_Conc"] *= 0.95

elif scenario == "저배출구역 (LEZ)":
    sim_df["NOx_Conc"] *= 0.85

elif scenario == "통합 정책":
    sim_df["Car_Usage"] *= 0.8
    sim_df["NOx_Conc"] *= 0.75

# 예측
pred = model.predict(sim_df[["NOx_Conc"]])

col1, col2 = st.columns(2)

col1.metric("기존 폐질환 평균", round(filtered_df["Lung_Disease"].mean(), 1))
col2.metric("정책 적용 후", round(pred.mean(), 1))

# -----------------------
# 5. 인사이트 자동 생성
# -----------------------
st.subheader("🧠 인사이트")

if coef > 0:
    st.success("NOx 농도가 증가할수록 폐질환이 증가하는 경향이 확인됩니다.")

if scenario == "통합 정책":
    st.info("통합 정책이 가장 큰 건강 개선 효과를 보입니다.")

# -----------------------
# 6. 지도 느낌 (선택)
# -----------------------
st.subheader("📍 지역별 분포")

fig2 = px.scatter(
    filtered_df,
    x="Pop_Density",
    y="NOx_Conc",
    size="Lung_Disease",
    color="Lung_Disease",
    title="인구밀도 기반 위험 분포"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------
# Footer
# -----------------------
st.markdown("---")
st.caption("환경-보건 통합 분석 | Data-driven Policy Simulation")
