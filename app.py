import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
 
# ────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="서울 공영주차장 혼잡도",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ────────────────────────────────────────────────────────────────────────────
# 글로벌 스타일
# ────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
 
:root {
  --bg0: #060b14;
  --bg1: #0a1120;
  --bg2: #0f1928;
  --border: rgba(255,255,255,0.07);
  --text1: #f0f4ff;
  --text2: #8899bb;
  --text3: #445577;
  --blue:  #3b82f6;
  --c-free:    #10b981;
  --c-normal:  #f59e0b;
  --c-busy:    #f97316;
  --c-full:    #ef4444;
}
 
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg0) !important;
    color: var(--text1);
    font-family: 'Noto Sans KR', sans-serif;
}
[data-testid="stSidebar"]            { background: var(--bg1) !important; border-right: 1px solid var(--border); }
[data-testid="stHeader"]             { background: transparent !important; }
[data-testid="stToolbar"]            { display: none; }
#MainMenu, footer, .stDeployButton   { display: none !important; }
 
/* 전체 패딩 */
.block-container { padding: 1.4rem 1.8rem 2rem !important; max-width: 100% !important; }
 
/* ── 헤더 ── */
.app-header {
    display: flex; align-items: baseline; gap: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
}
.app-header-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.25rem; font-weight: 600;
    letter-spacing: -0.01em; color: var(--text1);
}
.app-header-sub {
    font-size: 0.72rem; color: var(--text3);
    letter-spacing: 0.06em; text-transform: uppercase;
}
.live-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3);
    border-radius: 999px; padding: 2px 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; color: #10b981; letter-spacing: 0.06em;
    margin-left: auto;
}
.live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #10b981;
    animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { opacity: 1; } 50% { opacity: 0.3; }
}
 
/* ── KPI 바 ── */
.kpi-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px; margin-bottom: 16px;
}
.kpi {
    background: var(--bg1); border: 1px solid var(--border);
    border-radius: 10px; padding: 13px 16px;
    position: relative; overflow: hidden;
}
.kpi::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent-color, var(--blue));
}
.kpi-label { font-size: 0.65rem; color: var(--text3); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 5px; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.55rem; font-weight: 600; color: var(--text1); line-height: 1.1; }
.kpi-note  { font-size: 0.67rem; color: var(--text3); margin-top: 4px; }
 
/* ── 레이아웃 ── */
.main-grid {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 12px;
}
 
/* ── 패널 공통 ── */
.panel {
    background: var(--bg1); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden;
}
.panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 8px;
}
.panel-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; font-weight: 500;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--text2);
}
.panel-body { padding: 14px 16px; }
 
/* ── 범례 ── */
.legend {
    display: flex; gap: 16px; flex-wrap: wrap;
    padding: 8px 16px 10px;
    border-top: 1px solid var(--border);
}
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.71rem; color: var(--text2); }
.legend-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
 
/* ── 구 상세 패널 ── */
.gu-title {
    font-size: 1.15rem; font-weight: 700; color: var(--text1);
    margin-bottom: 3px;
}
.gu-badge {
    display: inline-block; font-size: 0.67rem; font-weight: 700;
    letter-spacing: 0.07em; padding: 2px 9px; border-radius: 999px;
    margin-bottom: 14px;
}
.gauge-wrap { margin: 4px 0 14px; }
.gauge-label { font-size: 0.63rem; color: var(--text3); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 5px; }
.gauge-bg { background: rgba(255,255,255,0.06); border-radius: 999px; height: 7px; overflow: hidden; }
.gauge-fill { height: 7px; border-radius: 999px; transition: width .4s ease; }
.gauge-num { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: var(--text2); margin-top: 4px; }
 
.stat { display: flex; justify-content: space-between; align-items: center;
        padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
        font-size: 0.78rem; }
.stat:last-child { border-bottom: none; }
.stat-k { color: var(--text3); }
.stat-v { font-family: 'IBM Plex Mono', monospace; color: var(--text2); }
 
/* ── 구 순위 리스트 ── */
.rank-item { margin-bottom: 10px; }
.rank-row  { display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 3px; }
.rank-name { color: var(--text1); }
.rank-val  { font-family: 'IBM Plex Mono', monospace; }
.bar-bg    { background: rgba(255,255,255,0.05); border-radius: 999px; height: 4px; overflow: hidden; }
.bar-fill  { height: 4px; border-radius: 999px; }
 
/* ── 주차장 카드 ── */
.lot-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px; padding: 9px 11px; margin-bottom: 6px;
}
.lot-name { font-size: 0.8rem; font-weight: 600; color: var(--text1); margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lot-sub  { font-size: 0.69rem; color: var(--text3); }
.lot-bar-bg   { background: rgba(255,255,255,0.06); border-radius: 999px; height: 3px; margin-top: 6px; overflow: hidden; }
.lot-bar-fill { height: 3px; border-radius: 999px; }
.lot-rate { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; margin-top: 3px; }
 
/* ── 섹션 타이틀 ── */
.sec-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--blue); margin: 14px 0 8px;
}
 
/* ── 필터 섹션 ── */
.filter-row {
    display: flex; gap: 10px; align-items: center;
    margin-bottom: 12px; flex-wrap: wrap;
}
 
/* dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}
 
/* selectbox */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg1) !important;
    border: 1px solid var(--border) !important;
    color: var(--text1) !important;
    border-radius: 8px !important;
}
/* slider */
[data-testid="stSlider"] label { font-size: 0.75rem !important; color: var(--text3) !important; }
</style>
""", unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# 서울 25개 구 중심 좌표
# ────────────────────────────────────────────────────────────────────────────
GU_COORDS = {
    "종로구":(37.5909,126.9718), "중구":(37.5636,126.9975), "용산구":(37.5326,126.9902),
    "성동구":(37.5633,127.0369), "광진구":(37.5386,127.0823), "동대문구":(37.5745,127.0396),
    "중랑구":(37.5953,127.0934), "성북구":(37.5894,127.0167), "강북구":(37.6396,127.0253),
    "도봉구":(37.6688,127.0471), "노원구":(37.6542,127.0568), "은평구":(37.6027,126.9295),
    "서대문구":(37.5791,126.9368), "마포구":(37.5664,126.9010), "양천구":(37.5170,126.8665),
    "강서구":(37.5509,126.8496), "구로구":(37.4954,126.8874), "금천구":(37.4570,126.8954),
    "영등포구":(37.5264,126.8963), "동작구":(37.5124,126.9395), "관악구":(37.4784,126.9516),
    "서초구":(37.4837,127.0324), "강남구":(37.5172,127.0473), "송파구":(37.5145,127.1059),
    "강동구":(37.5301,127.1238),
}
 
# ────────────────────────────────────────────────────────────────────────────
# 혼잡도 색상
# ────────────────────────────────────────────────────────────────────────────
def congestion(rate):
    if rate >= 90:   return "포화",   "#ef4444", [239, 68,  68],  "background:rgba(239,68,68,.15);color:#ef4444;"
    elif rate >= 70: return "혼잡",   "#f97316", [249,115,  22],  "background:rgba(249,115,22,.15);color:#f97316;"
    elif rate >= 40: return "보통",   "#f59e0b", [245,158,  11],  "background:rgba(245,158,11,.15);color:#f59e0b;"
    else:            return "여유",   "#10b981", [ 16,185, 129],  "background:rgba(16,185,129,.15);color:#10b981;"
 
# ────────────────────────────────────────────────────────────────────────────
# 데이터 로드
# ────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df1 = pd.read_csv("서울시_시영주차장_실시간_주차대수_정보.csv", encoding="cp949")
    df2 = pd.read_csv("서울시_공영주차장_안내_정보.csv", encoding="cp949")
 
    df1["구"] = df1["주소"].str.extract(r"([가-힣]+구)")
    df2["구"] = df2["주소"].str.extract(r"([가-힣]+구)")
    df1["가동률"] = (df1["현재 주차 차량수"] / df1["총 주차면"] * 100).clip(0, 200).round(1)
 
    gu_rt = df1[df1["총 주차면"] >= 1].groupby("구").agg(
        시영수=("주차장명","count"),
        시영면=("총 주차면","sum"),
        시영차량=("현재 주차 차량수","sum"),
    ).reset_index()
    gu_rt["가동률"] = (gu_rt["시영차량"] / gu_rt["시영면"] * 100).clip(0, 150).round(1)
 
    gu_pub = df2.groupby("구").agg(
        공영수=("주차장코드","count"),
        공영면=("총 주차면","sum"),
    ).reset_index()
 
    gu = gu_pub.merge(gu_rt, on="구", how="left")
    for c in ["시영수","시영면","시영차량","가동률"]:
        gu[c] = gu[c].fillna(0)
    gu["시영수"]  = gu["시영수"].astype(int)
    gu["시영면"]  = gu["시영면"].astype(int)
    gu["시영차량"] = gu["시영차량"].astype(int)
    gu["lat"] = gu["구"].map(lambda x: GU_COORDS.get(x,(37.55,126.98))[0])
    gu["lon"] = gu["구"].map(lambda x: GU_COORDS.get(x,(37.55,126.98))[1])
    gu["잔여"] = (gu["시영면"] - gu["시영차량"]).clip(0)
    return df1, df2, gu
 
df1, df2, gu = load_data()
 
# ────────────────────────────────────────────────────────────────────────────
# 사이드바 (필터)
# ────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 필터 & 설정")
    rate_range = st.slider("가동률 범위 (%)", 0, 150, (0, 150))
    pitch_val  = st.slider("지도 기울기 (3D)", 0, 60, 45)
    map_style  = st.radio("지도 스타일", ["다크", "위성"], horizontal=True)
    st.markdown("---")
    st.markdown("""
    **혼잡도 기준**
    - 🟢 여유 : ~40%
    - 🟡 보통 : 40–70%
    - 🟠 혼잡 : 70–90%
    - 🔴 포화 : 90%+
    """)
 
# ────────────────────────────────────────────────────────────────────────────
# 상태 초기화
# ────────────────────────────────────────────────────────────────────────────
if "selected_gu" not in st.session_state:
    st.session_state.selected_gu = None
 
# ────────────────────────────────────────────────────────────────────────────
# 헤더
# ────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <div class="app-header-title">서울시 공영주차장 혼잡도 현황</div>
    <div class="app-header-sub">Seoul Public Parking · Real-time Congestion Map</div>
  </div>
  <div class="live-badge"><span class="live-dot"></span>LIVE · 2026.03.19</div>
</div>
""", unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# KPI 바
# ────────────────────────────────────────────────────────────────────────────
total_lots   = int(gu["공영수"].sum())
total_spaces = int(gu["공영면"].sum())
rt_avg       = gu[gu["가동률"] > 0]["가동률"].mean()
n_saturated  = int((gu["가동률"] >= 90).sum())
 
st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi" style="--accent-color:#3b82f6;">
    <div class="kpi-label">공영주차장 총 개소</div>
    <div class="kpi-value">{total_lots:,}</div>
    <div class="kpi-note">서울시 전체</div>
  </div>
  <div class="kpi" style="--accent-color:#8b5cf6;">
    <div class="kpi-label">총 공급 주차면</div>
    <div class="kpi-value">{total_spaces:,}</div>
    <div class="kpi-note">공영주차장 기준</div>
  </div>
  <div class="kpi" style="--accent-color:#f59e0b;">
    <div class="kpi-label">실시간 평균 가동률</div>
    <div class="kpi-value">{rt_avg:.1f}%</div>
    <div class="kpi-note">시영주차장 기준</div>
  </div>
  <div class="kpi" style="--accent-color:#ef4444;">
    <div class="kpi-label">포화 지역 수</div>
    <div class="kpi-value">{n_saturated}개 구</div>
    <div class="kpi-note">가동률 90% 이상</div>
  </div>
</div>
""", unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# 구 선택 버튼 행 (클릭 → 상세)
# ────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">지역 선택 — 클릭하면 상세 정보가 표시됩니다</div>', unsafe_allow_html=True)
 
gu_sorted_btn = gu.sort_values("가동률", ascending=False)
cols_btn = st.columns(len(gu_sorted_btn))
 
for i, (_, row) in enumerate(gu_sorted_btn.iterrows()):
    r = float(row["가동률"])
    _, color, _, _ = congestion(r)
    is_active = st.session_state.selected_gu == row["구"]
    border = f"2px solid {color}" if is_active else "1px solid rgba(255,255,255,0.07)"
    bg     = f"rgba({','.join(str(x) for x in congestion(r)[2])}, 0.18)" if is_active else "rgba(255,255,255,0.03)"
    with cols_btn[i]:
        if st.button(
            f"{row['구'][:2]}\n{r:.0f}%",
            key=f"btn_{row['구']}",
            use_container_width=True,
            help=f"{row['구']} · 가동률 {r:.1f}%",
        ):
            if st.session_state.selected_gu == row["구"]:
                st.session_state.selected_gu = None
            else:
                st.session_state.selected_gu = row["구"]
            st.rerun()
 
# 버튼 색상 오버라이드 (개별 구 색상)
btn_css = ""
for _, row in gu_sorted_btn.iterrows():
    r = float(row["가동률"])
    _, color, rgb, _ = congestion(r)
    is_active = st.session_state.selected_gu == row["구"]
    key = f"btn_{row['구']}"
    if is_active:
        btn_css += f"""
        [data-testid="stButton"][key="{key}"] > button,
        div:has(> [data-testid="stButton"] button[aria-label="{row['구']} · 가동률 {r:.1f}%"]) button {{
            border: 2px solid {color} !important;
            background: rgba({rgb[0]},{rgb[1]},{rgb[2]},0.18) !important;
            color: {color} !important;
        }}"""
 
st.markdown(f"""
<style>
/* 구 버튼 공통 */
[data-testid="stButton"] > button {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    padding: 6px 4px !important;
    line-height: 1.4 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    background: rgba(255,255,255,0.03) !important;
    color: #8899bb !important;
    white-space: pre-line !important;
    transition: all .15s ease !important;
}}
[data-testid="stButton"] > button:hover {{
    border-color: rgba(255,255,255,0.2) !important;
    background: rgba(255,255,255,0.08) !important;
    color: #f0f4ff !important;
}}
{btn_css}
</style>
""", unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# 지도 + 상세 패널
# ────────────────────────────────────────────────────────────────────────────
gu_f = gu[
    (gu["가동률"] >= rate_range[0]) &
    (gu["가동률"] <= rate_range[1])
].copy()
 
gu_f["_color"]     = gu_f["가동률"].apply(lambda r: congestion(r)[2] + [210])
gu_f["_elevation"] = gu_f["가동률"].apply(lambda r: max(50, float(r) * 9))
gu_f["_radius"]    = gu_f["공영면"].apply(lambda v: max(350, min(800, float(v) * 0.09)))
 
col_map, col_panel = st.columns([2.6, 1], gap="medium")
 
MAP_STYLES = {
    "다크":  "mapbox://styles/mapbox/dark-v11",
    "위성":  "mapbox://styles/mapbox/satellite-streets-v12",
}
 
with col_map:
    tooltip_html = """
    <div style="background:#0a1120;border:1px solid rgba(255,255,255,0.12);
                border-radius:11px;padding:13px 15px;font-family:sans-serif;min-width:185px;">
      <div style="font-size:13px;font-weight:700;color:#f0f4ff;margin-bottom:7px;">{구}</div>
      <div style="height:1px;background:rgba(255,255,255,0.07);margin-bottom:9px;"></div>
      <div style="font-size:10px;color:#445577;margin-bottom:2px;letter-spacing:.06em;text-transform:uppercase;">실시간 가동률</div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:21px;font-weight:600;color:#3b82f6;margin-bottom:9px;">{가동률}%</div>
      <div style="font-size:10px;color:#8899bb;">🏢 공영 {공영수}개소 · {공영면}면</div>
      <div style="font-size:10px;color:#8899bb;margin-top:3px;">🚗 현재 {시영차량}대 / {시영면}면</div>
      <div style="font-size:10px;color:#445577;margin-top:3px;">잔여 {잔여}면</div>
    </div>"""
 
    layers = [
        pdk.Layer(
            "ColumnLayer",
            data=gu_f,
            get_position="[lon, lat]",
            get_elevation="_elevation",
            elevation_scale=10,
            radius=550,
            get_fill_color="_color",
            pickable=True,
            auto_highlight=True,
            extruded=True,
            coverage=0.8,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=gu_f,
            get_position="[lon, lat]",
            get_radius=130,
            get_fill_color="[255,255,255,240]",
            pickable=False,
        ),
    ]
 
    # 선택된 구 하이라이트 링
    sel = st.session_state.selected_gu
    if sel and sel in GU_COORDS:
        sel_row = gu_f[gu_f["구"] == sel]
        if not sel_row.empty:
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=sel_row,
                get_position="[lon, lat]",
                get_radius=820,
                get_fill_color="[255,255,255,12]",
                get_line_color="[255,255,255,220]",
                stroked=True,
                line_width_min_pixels=2,
            ))
 
    clat = GU_COORDS[sel][0] if sel and sel in GU_COORDS else 37.5665
    clon = GU_COORDS[sel][1] if sel and sel in GU_COORDS else 126.9780
    czoom = 13.2 if sel else 10.8
 
    st.pydeck_chart(pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=clat, longitude=clon,
            zoom=czoom, pitch=pitch_val, bearing=0
        ),
        tooltip={
            "html": tooltip_html,
            "style": {"background": "transparent", "border": "none"},
        },
        map_style=MAP_STYLES[map_style],
    ), use_container_width=True)
 
    st.markdown("""
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#10b981;"></div>여유 (~40%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;"></div>보통 (40–70%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#f97316;"></div>혼잡 (70–90%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>포화 (90%+)</div>
      <span style="margin-left:auto;font-size:.62rem;color:#334466;">기둥 높이 = 가동률 비례</span>
    </div>
    """, unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# 우측 패널
# ────────────────────────────────────────────────────────────────────────────
with col_panel:
    if sel:
        row = gu[gu["구"] == sel]
        if not row.empty:
            row = row.iloc[0]
            r = float(row["가동률"])
            status, color, _, badge_style = congestion(r)
            avail = int(row["잔여"])
 
            st.markdown(f"""
            <div class="panel">
              <div class="panel-header">
                <div class="panel-title">📍 지역 상세</div>
              </div>
              <div class="panel-body">
                <div class="gu-title">{sel}</div>
                <span class="gu-badge" style="{badge_style}">{status}</span>
                <div class="gauge-wrap">
                  <div class="gauge-label">실시간 가동률 (시영 기준)</div>
                  <div class="gauge-bg">
                    <div class="gauge-fill" style="width:{min(r,100):.1f}%;background:{color};"></div>
                  </div>
                  <div class="gauge-num">{r:.1f}%</div>
                </div>
                <div class="stat"><span class="stat-k">공영주차장</span><span class="stat-v">{int(row['공영수']):,}개소</span></div>
                <div class="stat"><span class="stat-k">공영 총 면수</span><span class="stat-v">{int(row['공영면']):,}면</span></div>
                <div class="stat"><span class="stat-k">시영 주차장</span><span class="stat-v">{int(row['시영수'])}개소</span></div>
                <div class="stat"><span class="stat-k">시영 총 면수</span><span class="stat-v">{int(row['시영면']):,}면</span></div>
                <div class="stat"><span class="stat-k">현재 주차 차량</span><span class="stat-v">{int(row['시영차량']):,}대</span></div>
                <div class="stat"><span class="stat-k">잔여 면수</span>
                  <span class="stat-v" style="color:{color};">{avail:,}면</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
 
            # 해당 구 주차장 목록
            lots = df1[(df1["구"] == sel) & (df1["총 주차면"] >= 1)].copy()
            lots = lots.sort_values("가동률", ascending=False)
 
            st.markdown('<div class="sec-title">주차장별 현황</div>', unsafe_allow_html=True)
            for _, lot in lots.head(9).iterrows():
                lr = float(lot["가동률"])
                _, lc, _, _ = congestion(lr)
                fee_str = f"기본 {int(lot['기본 주차 요금'])}원" if lot.get("기본 주차 요금", 0) > 0 else "무료"
                st.markdown(f"""
                <div class="lot-card">
                  <div class="lot-name">{lot['주차장명']}</div>
                  <div class="lot-sub">{int(lot['현재 주차 차량수'])}대 / {int(lot['총 주차면'])}면 · {fee_str}</div>
                  <div class="lot-bar-bg">
                    <div class="lot-bar-fill" style="width:{min(lr,100):.1f}%;background:{lc};"></div>
                  </div>
                  <div class="lot-rate" style="color:{lc};">{lr:.1f}%</div>
                </div>""", unsafe_allow_html=True)
 
            if st.button("✕ 선택 해제", key="deselect", use_container_width=True):
                st.session_state.selected_gu = None
                st.rerun()
    else:
        # 전체 혼잡도 순위
        st.markdown("""
        <div class="panel">
          <div class="panel-header"><div class="panel-title">📊 구별 혼잡도 순위</div></div>
          <div class="panel-body">
        """, unsafe_allow_html=True)
        ranked = gu[gu["가동률"] > 0].sort_values("가동률", ascending=False)
        for _, row in ranked.iterrows():
            r = float(row["가동률"])
            _, c, _, _ = congestion(r)
            st.markdown(f"""
            <div class="rank-item">
              <div class="rank-row">
                <span class="rank-name">{row['구']}</span>
                <span class="rank-val" style="color:{c};">{r:.1f}%</span>
              </div>
              <div class="bar-bg">
                <div class="bar-fill" style="width:{min(r,100):.1f}%;background:{c};"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:.68rem;color:#334466;margin-top:6px;">위 지도에서 구를 클릭하거나 상단 버튼을 눌러 상세 정보를 확인하세요.</div>', unsafe_allow_html=True)
 
# ────────────────────────────────────────────────────────────────────────────
# 하단 데이터 테이블
# ────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">전체 구별 통합 현황</div>', unsafe_allow_html=True)
 
disp = gu_f[["구","공영수","공영면","시영수","시영면","시영차량","가동률","잔여"]].copy()
disp.columns = ["자치구","공영(개소)","공영(면)","시영(개소)","시영(면)","현재차량","가동률(%)","잔여면"]
disp = disp.sort_values("가동률(%)", ascending=False).reset_index(drop=True)
disp.index += 1
 
st.dataframe(
    disp,
    use_container_width=True,
    height=290,
    column_config={
        "가동률(%)": st.column_config.ProgressColumn(
            "가동률(%)", min_value=0, max_value=150, format="%.1f%%"
        ),
        "공영(면)":  st.column_config.NumberColumn(format="%d 면"),
        "현재차량":  st.column_config.NumberColumn(format="%d 대"),
        "잔여면":    st.column_config.NumberColumn(format="%d 면"),
    }
)
