import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(layout="wide")

st.title("🚗 Seoul ParkMap (파일 기반 MVP)")
st.caption("서울 공영주차장 현황을 한 눈에 확인하세요")

# ---------------------------
# 데이터 로드
# ---------------------------
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

uploaded_file = st.file_uploader("📂 주차장 CSV 업로드", type=["csv"])

# 샘플 데이터 fallback
def sample_data():
    return pd.DataFrame({
        "name": ["강남주차장", "종로주차장", "송파주차장", "마포주차장"],
        "lat": [37.4979, 37.5725, 37.5145, 37.5663],
        "lng": [127.0276, 126.9794, 127.1059, 126.9014],
        "gu": ["강남구", "종로구", "송파구", "마포구"],
        "total": [100, 80, 120, 90],
        "available": [20, 60, 10, 70],
    })

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.warning("⚠️ CSV가 없어 샘플 데이터를 사용합니다.")
    df = sample_data()

# ---------------------------
# 데이터 처리
# ---------------------------
required_cols = ["name", "lat", "lng", "total", "available"]
if not all(col in df.columns for col in required_cols):
    st.error("❌ 데이터 형식이 올바르지 않습니다.")
    st.stop()

df["usage_rate"] = (df["total"] - df["available"]) / df["total"] * 100

# ---------------------------
# 필터 (자치구)
# ---------------------------
if "gu" in df.columns:
    gu_list = ["전체"] + sorted(df["gu"].dropna().unique().tolist())
    selected_gu = st.selectbox("📍 자치구 선택", gu_list)

    if selected_gu != "전체":
        df = df[df["gu"] == selected_gu]

# ---------------------------
# 혼잡도 색상 함수
# ---------------------------
def get_color(rate):
    if rate < 30:
        return "green"   # 여유
    elif rate < 70:
        return "blue"    # 보통
    elif rate < 95:
        return "orange"  # 혼잡
    else:
        return "red"     # 만차

# ---------------------------
# 지도 생성 (서울 중심)
# ---------------------------
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 클러스터 적용 (성능 개선)
marker_cluster = MarkerCluster().add_to(m)

# ---------------------------
# 마커 생성
# ---------------------------
for _, row in df.iterrows():
    color = get_color(row["usage_rate"])

    popup = f"""
    <b>{row['name']}</b><br>
    이용률: {row['usage_rate']:.1f}%<br>
    가용: {row['available']} / {row['total']}
    """

    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=7,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=popup
    ).add_to(marker_cluster)

# ---------------------------
# 범례 (Legend)
# ---------------------------
legend_html = """
<div style="
position: fixed; 
bottom: 50px; left: 50px; width: 150px; height: 140px; 
background-color: white; z-index:9999; 
border:2px solid grey; border-radius:10px;
padding:10px;
font-size:14px;
">
<b>혼잡도</b><br>
<span style="color:green;">●</span> 여유 (<30%)<br>
<span style="color:blue;">●</span> 보통 (30~70%)<br>
<span style="color:orange;">●</span> 혼잡 (70~95%)<br>
<span style="color:red;">●</span> 만차 (>95%)
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ---------------------------
# 지도 출력
# ---------------------------
st_folium(m, width=1200, height=700)

# ---------------------------
# KPI 요약
# ---------------------------
st.subheader("📊 전체 현황")

col1, col2, col3 = st.columns(3)

col1.metric("주차장 수", len(df))
col2.metric("평균 이용률", f"{df['usage_rate'].mean():.1f}%")
col3.metric("총 가용면수", int(df["available"].sum()))
