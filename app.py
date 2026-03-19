import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="서울시 공영주차장 분석", layout="wide")

st.title("🚗 서울시 공영주차장 실시간 분석 대시보드")

# -----------------------------
# 1. 파일 업로드 (핵심 해결)
# -----------------------------
st.sidebar.header("📂 데이터 업로드")

info_file = st.sidebar.file_uploader("공영주차장 안내 정보 업로드", type=["csv"])
live_file = st.sidebar.file_uploader("실시간 주차 정보 업로드", type=["csv"])

# -----------------------------
# 2. 데이터 로드 함수
# -----------------------------
@st.cache_data
def load_data(info_file, live_file):
    df_info = pd.read_csv(info_file)
    df_live = pd.read_csv(live_file)
    return df_info, df_live

# -----------------------------
# 3. 데이터 존재 체크
# -----------------------------
if info_file is None or live_file is None:
    st.warning("⚠️ CSV 파일 2개를 모두 업로드해주세요.")
    st.stop()

df_info, df_live = load_data(info_file, live_file)

# -----------------------------
# 4. 컬럼 자동 정리 (유연하게 처리)
# -----------------------------
# 컬럼명 확인용
st.sidebar.write("컬럼 미리보기")
st.sidebar.write(df_info.columns)
st.sidebar.write(df_live.columns)

# ⚠️ 실제 컬럼명 맞게 수정 필요할 수 있음
# 자동 매칭 (기본 가정)
merge_key = "주차장명"

if merge_key not in df_info.columns or merge_key not in df_live.columns:
    st.error("❌ '주차장명' 컬럼이 없습니다. 컬럼명을 확인해주세요.")
    st.stop()

# -----------------------------
# 5. 데이터 병합
# -----------------------------
df = pd.merge(df_info, df_live, on=merge_key, how="inner")

# -----------------------------
# 6. 파생 변수 생성
# -----------------------------
# 컬럼명 fallback 처리
def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None

total_col = find_column(df, ["총", "면"])
current_col = find_column(df, ["현재", "주차"])

if total_col is None or current_col is None:
    st.error("❌ 주차면수/현재주차 컬럼을 찾을 수 없습니다.")
    st.stop()

df["총주차면수"] = df[total_col]
df["현재주차대수"] = df[current_col]

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
# 7. 필터
# -----------------------------
st.sidebar.header("🔎 필터")

level_filter = st.sidebar.multiselect(
    "혼잡등급 선택",
    ["여유", "보통", "혼잡"],
    default=["여유", "보통", "혼잡"]
)

filtered_df = df[df["혼잡등급"].isin(level_filter)]

# -----------------------------
# 8. KPI
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("총 주차장 수", len(filtered_df))
col2.metric("평균 혼잡도", f"{filtered_df['혼잡도'].mean():.2f}")
col3.metric("총 여유공간", int(filtered_df["여유공간"].sum()))

# -----------------------------
# 9. 테이블
# -----------------------------
st.subheader("📊 주차장 현황")

st.dataframe(
    filtered_df[[
        merge_key,
        "총주차면수",
        "현재주차대수",
        "여유공간",
        "혼잡도",
        "혼잡등급"
    ]],
    use_container_width=True
)

# -----------------------------
# 10. 막대 그래프
# -----------------------------
st.subheader("📈 혼잡도 TOP 20")

chart_df = filtered_df.sort_values("혼잡도", ascending=False).head(20)

st.bar_chart(
    chart_df.set_index(merge_key)["혼잡도"]
)

# -----------------------------
# 11. 인사이트
# -----------------------------
st.subheader("💡 인사이트")

if len(df) > 0:
    st.write(f"""
    - 혼잡 비율: {(df['혼잡등급'] == '혼잡').mean()*100:.1f}%
    - 평균 혼잡도: {df['혼잡도'].mean():.2f}
    - 최혼잡 주차장: {df.sort_values('혼잡도', ascending=False)[merge_key].iloc[0]}
    """)
