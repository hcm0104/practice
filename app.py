import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="서울 공영주차장 실시간 현황", layout="wide")

st.title("🚗 서울 공영주차장 실시간 현황 지도")

# -------------------------
# 데이터 로드 (샘플 구조)
# -------------------------
@st.cache_data
def load_data():
    # 👉 실제로는 CSV 또는 API로 교체
    data = pd.DataFrame({
        "주차장명": ["구파발역", "잠실역", "종묘", "청량리", "강남"],
        "위도": [37.6367, 37.5133, 37.5740, 37.5800, 37.4979],
        "경도": [126.9180, 127.1000, 126.9910, 127.0480, 127.0276],
        "총주차면": [399, 357, 1317, 1260, 500],
        "현재차량": [475, 330, 1210, 1114, 450]
    })

    data["가동률"] = (data["현재차량"] / data["총주차면"]) * 100
    return data

df = load_data()

# -------------------------
# 사이드바 필터
# -------------------------
st.sidebar.header("🔍 필터")

min_rate, max_rate = st.sidebar.slider(
    "가동률 범위 (%)",
    0, 150, (0, 120)
)

filtered_df = df[
    (df["가동률"] >= min_rate) &
    (df["가동률"] <= max_rate)
]

# -------------------------
# 색상 설정 (가동률 기준)
# -------------------------
def get_color(rate):
    if rate < 50:
        return [0, 128, 255]  # 파랑 (여유)
    elif rate < 80:
        return [0, 200, 0]    # 초록 (적정)
    elif rate < 100:
        return [255, 165, 0]  # 주황 (혼잡)
    else:
        return [255, 0, 0]    # 빨강 (포화)

filtered_df["color"] = filtered_df["가동률"].apply(get_color)

# -------------------------
# PyDeck 지도
# -------------------------
layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position='[경도, 위도]',
    get_fill_color="color",
    get_radius=200,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=37.55,
    longitude=126.98,
    zoom=11,
    pitch=0,
)

tooltip = {
    "html": """
    <b>{주차장명}</b><br/>
    가동률: {가동률:.1f}%<br/>
    현재: {현재차량} / {총주차면}
    """,
    "style": {"color": "white"}
}

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

# -------------------------
# 하단 요약
# -------------------------
st.subheader("📊 요약 지표")

col1, col2, col3 = st.columns(3)

col1.metric("총 주차장 수", len(filtered_df))
col2.metric("평균 가동률", f"{filtered_df['가동률'].mean():.1f}%")
col3.metric("최대 가동률", f"{filtered_df['가동률'].max():.1f}%")

# -------------------------
# 데이터 테이블
# -------------------------
st.subheader("📋 상세 데이터")
st.dataframe(filtered_df)
