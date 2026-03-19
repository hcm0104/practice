import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="서울시 공영주차장 분석", layout="wide")

st.title("🚗 서울시 공영주차장 실시간 분석 대시보드")

# -----------------------------
# 1. 데이터 로드
# -----------------------------
@st.cache_data
def load_data():
    df_info = pd.read_csv("서울시 공영주차장 안내 정보.csv")
    df_live = pd.read_csv("서울시 시영주차장 실시간 주차대수 정보.csv")
    return df_info, df_live

df_info, df_live = load_data()

# -----------------------------
# 2. 데이터 전처리
# -----------------------------
# (컬럼명은 실제 데이터에 맞게 수정 필요)
df = pd.merge(
    df_info,
    df_live,
    on="주차장명",  # 필요 시 '주차장ID'로 변경
    how="inner"
)

# 파생변수 생성
df["혼잡도"] = df["현재주차대수"] / df["총주차면수"]
df["여유공간"] = df["총주차면수"] - df["현재주차대수"]

def congestion_level(x):
    if x < 0.3:
        return "여유"
    elif x < 0.7:
        return "보통"
    else:
        return "혼잡"

df["혼잡등급"] = df["혼잡도"].apply(congestion_level)

# -----------------------------
# 3. 사이드바 필터
# -----------------------------
st.sidebar.header("🔎 필터")

level_filter = st.sidebar.multiselect(
    "혼잡등급 선택",
    options=["여유", "보통", "혼잡"],
    default=["여유", "보통", "혼잡"]
)

filtered_df = df[df["혼잡등급"].isin(level_filter)]

# -----------------------------
# 4. KPI
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("총 주차장 수", len(filtered_df))
col2.metric("평균 혼잡도", f"{filtered_df['혼잡도'].mean():.2f}")
col3.metric("총 여유공간", int(filtered_df["여유공간"].sum()))

# -----------------------------
# 5. 테이블
# -----------------------------
st.subheader("📊 주차장 현황")

st.dataframe(
    filtered_df[[
        "주차장명",
        "총주차면수",
        "현재주차대수",
        "여유공간",
        "혼잡도",
        "혼잡등급"
    ]],
    use_container_width=True
)

# -----------------------------
# 6. 시각화 (막대그래프)
# -----------------------------
st.subheader("📈 주차장별 혼잡도")

chart_df = filtered_df.sort_values("혼잡도", ascending=False).head(20)

st.bar_chart(
    chart_df.set_index("주차장명")["혼잡도"]
)

# -----------------------------
# 7. 인사이트 (간단)
# -----------------------------
st.subheader("💡 인사이트")

st.write(f"""
- 혼잡 주차장 비율: {(df['혼잡등급'] == '혼잡').mean()*100:.1f}%
- 평균 혼잡도: {df['혼잡도'].mean():.2f}
- 가장 혼잡한 주차장: {df.sort_values('혼잡도', ascending=False)['주차장명'].iloc[0]}
""")
