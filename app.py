import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("🚗 서울 주차장 현황 지도 (파일 기반 MVP)")

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv("parking_data.csv")
    return df

df = load_data()

# 혼잡도 계산
df["usage_rate"] = (df["total"] - df["available"]) / df["total"] * 100

# 색상 함수
def get_color(rate):
    if rate < 30:
        return "green"
    elif rate < 70:
        return "blue"
    elif rate < 95:
        return "orange"
    else:
        return "red"

# 서울 중심 지도
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 마커 추가
for _, row in df.iterrows():
    color = get_color(row["usage_rate"])

    popup_text = f"""
    <b>{row['name']}</b><br>
    총면수: {row['total']}<br>
    가용: {row['available']}<br>
    이용률: {row['usage_rate']:.1f}%
    """

    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(m)

# 지도 출력
st_folium(m, width=1200, height=700)

# 요약 정보
st.subheader("📊 전체 요약")
col1, col2, col3 = st.columns(3)

col1.metric("총 주차장 수", len(df))
col2.metric("평균 이용률", f"{df['usage_rate'].mean():.1f}%")
col3.metric("총 가용면수", int(df["available"].sum()))
