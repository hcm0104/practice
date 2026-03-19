import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="환경-보건 분석 대시보드", layout="wide")

st.title("🌍 환경 정책 실효성 분석 대시보드")

# ---------------------------
# 데이터 생성
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

    data["NOx"] = 0.02 * data["Car_Usage"] + 0.0005 * data["Pop_Density"]
    data["SOx"] = np.random.uniform(0.01, 0.05, n)
    data["Lung_Disease"] = 18 * data["NOx"]

    return data

df = load_data()

# ---------------------------
# 정책 선택
# ---------------------------
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

df_sim["NOx"] = 0.02 * df_sim["Car_Usage"] + 0.0005 * df_sim["Pop_Density"]
df_sim["Lung_Disease"] = 18 * df_sim["NOx"]

# ---------------------------
# KPI
# ---------------------------
col1, col2, col3 = st.columns(3)

col1.metric("평균 NOx", f"{df_sim['NOx'].mean():.2f}")
col2.metric("평균 폐질환 지수", f"{df_sim['Lung_Disease'].mean():.2f}")
col3.metric("자가용 이용률", f"{df_sim['Car_Usage'].mean():.1f}%")

# ---------------------------
# 📊 1. 지역별 막대그래프
# ---------------------------
st.subheader("📊 지역별 폐질환 수준 (Top 10)")

top10 = df_sim.sort_values("Lung_Disease", ascending=False).head(10)

fig_bar1 = px.bar(
    top10,
    x="Region",
    y="Lung_Disease",
    title="폐질환 위험 상위 지역",
)

st.plotly_chart(fig_bar1, use_container_width=True)

# ---------------------------
# 📊 2. 정책 비교 막대그래프 (핵심)
# ---------------------------
st.subheader("📉 정책별 효과 비교")

def simulate_policy(base_df, policy_name):
    temp = base_df.copy()

    if policy_name == "대중교통 인센티브":
        temp["Car_Usage"] *= 0.9
    elif policy_name == "저배출구역(LEZ)":
        temp["NOx"] *= 0.8
    elif policy_name == "통합 정책":
        temp["Car_Usage"] *= 0.85
        temp["NOx"] *= 0.7

    temp["NOx"] = 0.02 * temp["Car_Usage"] + 0.0005 * temp["Pop_Density"]
    temp["Lung_Disease"] = 18 * temp["NOx"]

    return temp

policies = ["기본 상태", "대중교통 인센티브", "저배출구역(LEZ)", "통합 정책"]

results = []

for p in policies:
    sim = simulate_policy(df, p)
    results.append({
        "정책": p,
        "평균 NOx": sim["NOx"].mean(),
        "평균 폐질환": sim["Lung_Disease"].mean()
    })

policy_df = pd.DataFrame(results)

# ---------------------------
# 막대그래프 (폐질환)
# ---------------------------
fig_bar2 = px.bar(
    policy_df,
    x="정책",
    y="평균 폐질환",
    title="정책별 폐질환 감소 효과"
)

st.plotly_chart(fig_bar2, use_container_width=True)

# ---------------------------
# 막대그래프 (NOx)
# ---------------------------
fig_bar3 = px.bar(
    policy_df,
    x="정책",
    y="평균 NOx",
    title="정책별 NOx 감소 효과"
)

st.plotly_chart(fig_bar3, use_container_width=True)

# ---------------------------
# 📋 데이터 테이블
# ---------------------------
st.subheader("📋 정책 비교 테이블")

baseline = policy_df.loc[policy_df["정책"] == "기본 상태", "평균 폐질환"].values[0]
policy_df["감소율(%)"] = (baseline - policy_df["평균 폐질환"]) / baseline * 100

st.dataframe(policy_df, use_container_width=True)

# ---------------------------
# 해석
# ---------------------------
st.subheader("🧠 해석")

st.markdown(f"""
- 선택 정책: **{policy}**
- 막대그래프를 통해 정책 간 효과 차이를 직관적으로 비교 가능
- 통합 정책이 가장 큰 감소 효과를 보임
- 교통 정책이 환경 및 건강 개선의 핵심 수단
""")
