import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

st.set_page_config(page_title="서울 환경-보건 지도", layout="wide")

st.title("🌍 서울 환경 정책 실효성 지도 대시보드")
st.markdown("자가용 이용률 → NOx → 폐질환 구조를 공간적으로 시각화")

# ---------------------------
# 1. 서울 좌표 기반 데이터 생성
# ---------------------------
@st.cache_data
def load_data():
    np.random.seed(42)
    n = 50

    # 서울 중심 좌표
    lat_center = 37.5665
    lon_center = 126.9780

    data = pd.DataFrame({
        "Region": [f"R{i}" for i in range(n)],
        "lat": lat_center + np.random.uniform(-0.05, 0.05, n),
        "lon": lon_center + np.random.uniform(-0.05, 0.05, n),
        "Car_Usage": np.random.uniform(40, 90, n),
        "Pop_Density": np.random.uniform(5000, 20000, n),
    })

    data["NOx"] = 0.02 * data["Car_Usage"] + 0.0005 * data["Pop_Density"]
    data["Lung_Disease"] = 18 * data["NOx"]

    return data

df = load_data()

# ---------------------------
# 2. 정책 선택
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
# 3. KPI
# ---------------------------
col1, col2 = st.columns(2)

col1.metric("평균 NOx", f"{df_sim['NOx'].mean():.2f}")
col2.metric("평균 폐질환 지수", f"{df_sim['Lung_Disease'].mean():.2f}")

# ---------------------------
# 4. 지도 시각화 (핵심)
# ---------------------------
st.subheader("🗺️ 서울 지역 폐질환 위험도 지도")

layer = pdk.Layer(
    "ScatterplotLayer",
    df_sim,
    get_position='[lon, lat]',
    get_radius="Lung_Disease * 50",  # 크기로 위험도 표현
    get_fill_color='[255, 0, 0, 160]',  # 빨간색
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=37.5665,
    longitude=126.9780,
    zoom=10,
)

tooltip = {
    "html": """
    <b>지역:</b> {Region} <br/>
    <b>NOx:</b> {NOx} <br/>
    <b>폐질환:</b> {Lung_Disease}
    """
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
)

st.pydeck_chart(deck)

# ---------------------------
# 5. 핫스팟 Top 10
# ---------------------------
st.subheader("🔥 위험 지역 Top 10")

top10 = df_sim.sort_values("Lung_Disease", ascending=False).head(10)

st.dataframe(top10, use_container_width=True)

# ---------------------------
# 6. 해석
# ---------------------------
st.subheader("🧠 해석")

st.markdown(f"""
- 선택 정책: **{policy}**
- 지도에서 원의 크기가 클수록 건강 위험이 높은 지역
- 고밀도 + 자가용 이용률 높은 지역이 핫스팟
- 통합 정책 적용 시 전체적으로 위험도가 감소
""")
