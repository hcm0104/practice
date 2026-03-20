import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

st.set_page_config(page_title="서울 공영주차장 실시간 지도", layout="wide")

st.title("🚗 서울 시영주차장 실시간 현황")

# -------------------------
# 🔑 API KEY 입력
# -------------------------
API_KEY = st.secrets.get("SEOUL_API_KEY", "YOUR_API_KEY")

# -------------------------
# 📡 데이터 불러오기
# -------------------------
@st.cache_data(ttl=300)
def load_data():
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/GetParkingInfo/1/200"

    response = requests.get(url)
    data = response.json()

    rows = data['GetParkingInfo']['row']
    df = pd.DataFrame(rows)

    # 필요한 컬럼 정리 (컬럼명은 실제 API에 따라 다를 수 있음)
    df = df.rename(columns={
        "PARKING_NAME": "주차장명",
        "ADDR": "주소",
        "LAT": "위도",
        "LNG": "경도",
        "CAPACITY": "총주차면",
        "CUR_PARKING": "현재차량"
    })

    # 숫자형 변환
    df["총주차면"] = pd.to_numeric(df["총주차면"], errors="coerce")
    df["현재차량"] = pd.to_numeric(df["현재차량"], errors="coerce")

    # 가동률 계산
    df["가동률"] = (df["현재차량"] / df["총주차면"]) * 100

    # 좌표 결측 제거
    df = df.dropna(subset=["위도", "경도"])

    return df

df = load_data()

# -------------------------
# 🔍 필터
# -------------------------
st.sidebar.header("필터")

min_rate, max_rate = st.sidebar.slider(
    "가동률 범위 (%)",
    0, 150, (0, 120)
)

filtered_df = df[
    (df["가동률"] >= min_rate) &
    (df["가동률"] <= max_rate)
]

# -------------------------
# 🎨 색상 설정
# -------------------------
def get_color(rate):
    if rate < 50:
        return [0, 128, 255]
    elif rate < 80:
        return [0, 200, 0]
    elif rate < 100:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

filtered_df["color"] = filtered_df["가동률"].apply(get_color)

# -------------------------
# 🗺️ 지도
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
)

tooltip = {
    "html": """
    <b>{주차장명}</b><br/>
    가동률: {가동률:.1f}%<br/>
    현재: {현재차량} / {총주차면}<br/>
    주소: {주소}
    """,
    "style": {"color": "white"}
}

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

# -------------------------
# 📊 요약
# -------------------------
st.subheader("📊 실시간 요약")

col1, col2, col3 = st.columns(3)

col1.metric("주차장 수", len(filtered_df))
col2.metric("평균 가동률", f"{filtered_df['가동률'].mean():.1f}%")
col3.metric("최대 가동률", f"{filtered_df['가동률'].max():.1f}%")

# -------------------------
# 📋 테이블
# -------------------------
st.subheader("📋 상세 데이터")
st.dataframe(filtered_df)
