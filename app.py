import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import xml.etree.ElementTree as ET

st.set_page_config(page_title="서울 주차장 지도", layout="wide")

st.title("🚗 서울 시영주차장 실시간 현황")

# -------------------------
# 🔑 API KEY
# -------------------------
API_KEY = st.secrets.get("SEOUL_API_KEY", "sample")

# -------------------------
# 📡 데이터 로드 (XML 전용)
# -------------------------
@st.cache_data(ttl=300)
def load_data():
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/GetParkingInfo/1/100"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            st.error(f"API 요청 실패: {response.status_code}")
            return pd.DataFrame()

        root = ET.fromstring(response.text)

        rows = []
        for row in root.findall(".//row"):
            item = {}
            for child in row:
                item[child.tag] = child.text
            rows.append(item)

        df = pd.DataFrame(rows)

        if df.empty:
            st.warning("데이터 없음")
            return df

        # -------------------------
        # 컬럼 정리 (유연 대응)
        # -------------------------
        col_map = {
            "PARKING_NAME": "주차장명",
            "ADDR": "주소",
            "LAT": "위도",
            "LNG": "경도",
            "CAPACITY": "총주차면",
            "CUR_PARKING": "현재차량"
        }

        for k, v in col_map.items():
            if k in df.columns:
                df.rename(columns={k: v}, inplace=True)

        # -------------------------
        # 숫자 변환
        # -------------------------
        df["총주차면"] = pd.to_numeric(df.get("총주차면"), errors="coerce")
        df["현재차량"] = pd.to_numeric(df.get("현재차량"), errors="coerce")

        # -------------------------
        # 가동률 계산
        # -------------------------
        df["가동률"] = (df["현재차량"] / df["총주차면"]) * 100

        # -------------------------
        # 좌표 처리
        # -------------------------
        df["위도"] = pd.to_numeric(df.get("위도"), errors="coerce")
        df["경도"] = pd.to_numeric(df.get("경도"), errors="coerce")

        df = df.dropna(subset=["위도", "경도"])

        return df

    except Exception as e:
        st.error(f"에러 발생: {e}")
        return pd.DataFrame()


df = load_data()

# -------------------------
# ❗ 데이터 없으면 종료
# -------------------------
if df.empty:
    st.stop()

# -------------------------
# 🔍 필터
# -------------------------
st.sidebar.header("🔍 가동률 필터")

min_rate, max_rate = st.sidebar.slider(
    "가동률 (%)", 0, 150, (0, 120)
)

filtered_df = df[
    (df["가동률"] >= min_rate) &
    (df["가동률"] <= max_rate)
].copy()

# -------------------------
# 🎨 색상
# -------------------------
def get_color(rate):
    if rate < 50:
        return [0, 128, 255]   # 여유
    elif rate < 80:
        return [0, 200, 0]     # 적정
    elif rate < 100:
        return [255, 165, 0]   # 혼잡
    else:
        return [255, 0, 0]     # 포화

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
    zoom=11
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
st.subheader("📊 요약")

col1, col2, col3 = st.columns(3)

col1.metric("주차장 수", len(filtered_df))
col2.metric("평균 가동률", f"{filtered_df['가동률'].mean():.1f}%")
col3.metric("최대 가동률", f"{filtered_df['가동률'].max():.1f}%")

# -------------------------
# 📋 테이블
# -------------------------
st.subheader("📋 상세 데이터")
st.dataframe(filtered_df)
