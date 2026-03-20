import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seoul ParkMap",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 글로벌 CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Syne:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg:       #07080f;
    --surface:  #0e1017;
    --surface2: #141720;
    --border:   rgba(255,255,255,0.07);
    --text1:    #eef2ff;
    --text2:    #7b8db0;
    --text3:    #343d52;
    --blue:     #4f8ef7;
    --green:    #22d3a5;
    --yellow:   #fbbf24;
    --orange:   #fb923c;
    --red:      #f87171;
}

/* 전체 배경 */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--bg) !important; }
[data-testid="stHeader"]   { background: transparent !important; box-shadow: none !important; }
[data-testid="stSidebar"]  { background: var(--surface) !important; }
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── 상단 헤더 바 ── */
.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 32px 16px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
}
.logo-wrap { display: flex; align-items: baseline; gap: 10px; }
.logo-main {
    font-family: 'Syne', sans-serif; font-size: 1.35rem; font-weight: 800;
    color: var(--text1); letter-spacing: -0.02em;
}
.logo-main span { color: var(--blue); }
.logo-sub {
    font-family: 'IBM Plex Mono', monospace; font-size: .65rem;
    color: var(--text3); letter-spacing: .1em; text-transform: uppercase;
}
.live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,211,165,.1); border: 1px solid rgba(34,211,165,.25);
    border-radius: 999px; padding: 4px 13px;
    font-family: 'IBM Plex Mono', monospace; font-size: .65rem;
    color: var(--green); letter-spacing: .07em;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--green);
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.25} }

/* ── KPI 스트립 ── */
.kpi-strip {
    display: grid; grid-template-columns: repeat(5, 1fr);
    border-bottom: 1px solid var(--border);
    background: var(--surface);
}
.kpi-cell {
    padding: 16px 24px; position: relative; overflow: hidden;
    border-right: 1px solid var(--border);
}
.kpi-cell:last-child { border-right: none; }
.kpi-cell::after {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent, var(--blue));
    transform: scaleX(0); transition: transform .3s ease;
}
.kpi-cell:hover::after { transform: scaleX(1); }
.kpi-label {
    font-size: .6rem; color: var(--text3);
    letter-spacing: .1em; text-transform: uppercase; margin-bottom: 6px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem;
    font-weight: 500; color: var(--text1); line-height: 1;
}
.kpi-note { font-size: .62rem; color: var(--text3); margin-top: 5px; }

/* ── 본문 레이아웃 ── */
.body-wrap {
    display: grid; grid-template-columns: 1fr 320px;
    height: calc(100vh - 116px);
    overflow: hidden;
}

/* ── 지도 영역 ── */
.map-wrap {
    position: relative; overflow: hidden;
    border-right: 1px solid var(--border);
}
.map-filter-bar {
    position: absolute; top: 14px; left: 14px; z-index: 999;
    display: flex; gap: 8px; flex-wrap: wrap;
}
.map-badge {
    background: rgba(14,16,23,.92); border: 1px solid var(--border);
    border-radius: 8px; padding: 6px 12px;
    font-family: 'IBM Plex Mono', monospace; font-size: .68rem;
    color: var(--text2); cursor: pointer; transition: all .15s;
    backdrop-filter: blur(8px);
}
.map-badge:hover { border-color: var(--blue); color: var(--text1); }
.map-badge.active { border-color: var(--blue); color: var(--blue); background: rgba(79,142,247,.12); }

/* ── 범례 ── */
.legend-bar {
    position: absolute; bottom: 14px; left: 14px; z-index: 999;
    background: rgba(14,16,23,.92); border: 1px solid var(--border);
    border-radius: 10px; padding: 10px 14px;
    backdrop-filter: blur(8px);
    display: flex; gap: 14px; align-items: center;
}
.leg-item { display: flex; align-items: center; gap: 5px; font-size: .68rem; color: var(--text2); }
.leg-dot  { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

/* ── 사이드 패널 ── */
.side-panel {
    background: var(--surface); overflow-y: auto;
    display: flex; flex-direction: column;
}
.side-panel::-webkit-scrollbar { width: 4px; }
.side-panel::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

.panel-section {
    border-bottom: 1px solid var(--border); padding: 18px 20px;
}
.panel-sec-title {
    font-family: 'IBM Plex Mono', monospace; font-size: .62rem;
    letter-spacing: .12em; text-transform: uppercase;
    color: var(--blue); margin-bottom: 12px;
}

/* ── 구 선택 그리드 ── */
.gu-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px;
}
.gu-btn {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 7px; padding: 7px 6px; cursor: pointer;
    transition: all .15s; text-align: center;
    font-family: 'Noto Sans KR', sans-serif;
}
.gu-btn:hover  { border-color: rgba(255,255,255,.18); background: rgba(255,255,255,.06); }
.gu-btn.active { border-color: var(--c,var(--blue)); background: rgba(var(--cr),0.12); }
.gu-name { font-size: .72rem; color: var(--text1); font-weight: 500; }
.gu-rate { font-family: 'IBM Plex Mono',monospace; font-size: .7rem; margin-top: 2px; }

/* ── 혼잡도 순위 ── */
.rank-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.rank-num { font-family: 'IBM Plex Mono',monospace; font-size: .65rem; color: var(--text3); width: 16px; }
.rank-info { flex: 1; }
.rank-name { font-size: .78rem; color: var(--text1); margin-bottom: 3px; }
.rank-bar-bg  { background: rgba(255,255,255,.05); border-radius: 999px; height: 4px; overflow: hidden; }
.rank-bar-fill{ height: 4px; border-radius: 999px; }
.rank-val { font-family: 'IBM Plex Mono',monospace; font-size: .72rem; min-width: 38px; text-align: right; }

/* ── 디테일 카드 ── */
.detail-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px;
    margin-bottom: 8px;
}
.dc-name { font-size: .82rem; font-weight: 600; color: var(--text1); margin-bottom: 3px; }
.dc-addr { font-size: .68rem; color: var(--text3); margin-bottom: 8px; }
.dc-gauge-bg   { background: rgba(255,255,255,.05); border-radius: 999px; height: 5px; overflow: hidden; margin-bottom: 4px; }
.dc-gauge-fill { height: 5px; border-radius: 999px; }
.dc-meta { display: flex; justify-content: space-between; font-size: .68rem; }
.dc-rate { font-family: 'IBM Plex Mono',monospace; }
.dc-cap  { color: var(--text3); }

/* ── 선택된 구 상세 ── */
.sel-header { margin-bottom: 14px; }
.sel-name { font-size: 1.05rem; font-weight: 700; color: var(--text1); }
.sel-badge {
    display: inline-block; font-size: .65rem; font-weight: 700;
    padding: 2px 9px; border-radius: 999px; margin-top: 4px; margin-bottom: 12px;
    letter-spacing: .06em;
}
.gauge-main-bg   { background: rgba(255,255,255,.05); border-radius: 999px; height: 8px; overflow: hidden; margin-bottom: 3px; }
.gauge-main-fill { height: 8px; border-radius: 999px; }
.gauge-lbl { font-size: .6rem; color: var(--text3); letter-spacing: .08em; text-transform: uppercase; margin-bottom: 4px; }
.gauge-num { font-family: 'IBM Plex Mono',monospace; font-size: .75rem; color: var(--text2); }

.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 12px 0; }
.stat-box {
    background: rgba(255,255,255,.03); border: 1px solid var(--border);
    border-radius: 7px; padding: 8px 10px;
}
.stat-box-lbl { font-size: .58rem; color: var(--text3); letter-spacing: .08em; text-transform: uppercase; margin-bottom: 3px; }
.stat-box-val { font-family: 'IBM Plex Mono',monospace; font-size: .95rem; color: var(--text1); }

[data-testid="stButton"] > button {
    background: transparent !important; border: none !important;
    padding: 0 !important; color: transparent !important;
    width: 0 !important; height: 0 !important; position: absolute !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 서울 25개 구 좌표
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# 혼잡도 판정
# ─────────────────────────────────────────────────────────────────────────────
def cong(rate: float):
    if rate >= 90:   return "포화",   "#f87171", "255,99,99",   "rgba(248,113,113,.15)"
    elif rate >= 70: return "혼잡",   "#fb923c", "251,146,60",  "rgba(251,146,60,.15)"
    elif rate >= 40: return "보통",   "#fbbf24", "251,191,36",  "rgba(251,191,36,.15)"
    else:            return "여유",   "#22d3a5", "34,211,165",  "rgba(34,211,165,.15)"

def folium_color(rate: float) -> str:
    if rate >= 90:   return "#f87171"
    elif rate >= 70: return "#fb923c"
    elif rate >= 40: return "#fbbf24"
    else:            return "#22d3a5"

# ─────────────────────────────────────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = Path(__file__).parent
    candidates = [
        base / "data" / "서울시_시영주차장_실시간_주차대수_정보.csv",
        base / "서울시_시영주차장_실시간_주차대수_정보.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        st.error("CSV 파일을 찾을 수 없습니다. `data/` 폴더에 넣어주세요.")
        st.stop()

    df = pd.read_csv(path, encoding="cp949")
    df["구"]    = df["주소"].str.extract(r"([가-힣]+구)")
    df["가동률"] = (df["현재 주차 차량수"] / df["총 주차면"] * 100).clip(0, 200).round(1)
    df["잔여"]  = (df["총 주차면"] - df["현재 주차 차량수"]).clip(lower=0)

    gu = df[df["총 주차면"] >= 1].groupby("구").agg(
        주차장수=("주차장명","count"),
        총주차면=("총 주차면","sum"),
        현재차량=("현재 주차 차량수","sum"),
    ).reset_index()
    gu["가동률"] = (gu["현재차량"] / gu["총주차면"] * 100).clip(0, 150).round(1)
    gu["잔여"]  = (gu["총주차면"] - gu["현재차량"]).clip(lower=0).astype(int)
    gu["lat"]   = gu["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[0])
    gu["lon"]   = gu["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[1])
    return df, gu

df, gu = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# 세션 상태
# ─────────────────────────────────────────────────────────────────────────────
if "sel_gu"   not in st.session_state: st.session_state.sel_gu   = None
if "filter"   not in st.session_state: st.session_state.filter   = "전체"

# ─────────────────────────────────────────────────────────────────────────────
# ── 상단 헤더 바
# ─────────────────────────────────────────────────────────────────────────────
total_spaces  = int(df["총 주차면"].sum())
total_cars    = int(df["현재 주차 차량수"].sum())
avg_rate      = total_cars / total_spaces * 100
n_saturated   = int((gu["가동률"] >= 90).sum())
total_avail   = int(df["잔여"].sum())

st.markdown(f"""
<div class="top-bar">
  <div class="logo-wrap">
    <div class="logo-main">Seoul <span>Park</span>Map</div>
    <div class="logo-sub">시영주차장 실시간 현황 · 2026.03.19</div>
  </div>
  <div class="live-pill"><span class="live-dot"></span>LIVE DATA</div>
</div>

<div class="kpi-strip">
  <div class="kpi-cell" style="--accent:#4f8ef7;">
    <div class="kpi-label">총 주차장 수</div>
    <div class="kpi-value">{len(df)}</div>
    <div class="kpi-note">시영 전체</div>
  </div>
  <div class="kpi-cell" style="--accent:#818cf8;">
    <div class="kpi-label">총 주차 공급면</div>
    <div class="kpi-value">{total_spaces:,}</div>
    <div class="kpi-note">면</div>
  </div>
  <div class="kpi-cell" style="--accent:#fbbf24;">
    <div class="kpi-label">현재 주차 차량</div>
    <div class="kpi-value">{total_cars:,}</div>
    <div class="kpi-note">대</div>
  </div>
  <div class="kpi-cell" style="--accent:#22d3a5;">
    <div class="kpi-label">잔여 주차 가능</div>
    <div class="kpi-value">{total_avail:,}</div>
    <div class="kpi-note">면</div>
  </div>
  <div class="kpi-cell" style="--accent:#f87171;">
    <div class="kpi-label">포화 구역</div>
    <div class="kpi-value">{n_saturated}개 구</div>
    <div class="kpi-note">가동률 90%+</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── 바디: 지도 + 사이드 패널
# ─────────────────────────────────────────────────────────────────────────────
col_map, col_side = st.columns([3, 1], gap="small")

# ── 필터 상태 ──
filter_opt = st.session_state.filter
sel_gu     = st.session_state.sel_gu

# 필터링된 개별 주차장 데이터
filter_map = {"전체": None, "여유": (0,40), "보통": (40,70), "혼잡": (70,90), "포화": (90,200)}
frange = filter_map[filter_opt]
if frange:
    df_map = df[(df["가동률"] >= frange[0]) & (df["가동률"] < frange[1])].copy()
else:
    df_map = df.copy()

if sel_gu:
    df_map = df_map[df_map["구"] == sel_gu]

# ─────────────────────────────────────────────────────────────────────────────
# ── 지도 컬럼
# ─────────────────────────────────────────────────────────────────────────────
with col_map:
    # 필터 버튼
    fc = st.columns(5)
    filter_labels = ["전체", "여유", "보통", "혼잡", "포화"]
    filter_colors = ["#4f8ef7", "#22d3a5", "#fbbf24", "#fb923c", "#f87171"]

    for i, (lbl, clr) in enumerate(zip(filter_labels, filter_colors)):
        with fc[i]:
            is_active = filter_opt == lbl
            bg   = f"rgba({','.join(str(int(clr.lstrip('#')[j:j+2],16)) for j in (0,2,4))},.15)" if is_active else "rgba(14,16,23,.92)"
            bord = clr if is_active else "rgba(255,255,255,.07)"
            col  = clr if is_active else "#7b8db0"
            if st.button(lbl, key=f"f_{lbl}"):
                st.session_state.filter = lbl
                st.rerun()
            # 버튼 오버라이드 스타일
            st.markdown(f"""
            <style>
            div:has(> [data-testid="stButton"] > button[data-testid="baseButton-secondary"][kind="secondary"]:focus) {{}}
            div[data-testid="column"]:nth-child({i+1}) [data-testid="stButton"] > button {{
                width: 100% !important; height: auto !important; position: relative !important;
                background: {bg} !important; border: 1px solid {bord} !important;
                color: {col} !important; font-family: 'IBM Plex Mono',monospace !important;
                font-size: .68rem !important; padding: 6px 0 !important; border-radius: 8px !important;
                letter-spacing: .05em !important; text-transform: uppercase !important;
            }}
            </style>""", unsafe_allow_html=True)

    # ── Folium 지도 생성 ──────────────────────────────────────────────────────
    center_lat = GU_COORDS[sel_gu][0] if sel_gu and sel_gu in GU_COORDS else 37.5665
    center_lon = GU_COORDS[sel_gu][1] if sel_gu and sel_gu in GU_COORDS else 126.9780
    zoom_start = 13 if sel_gu else 11

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
    )

    # 다크 타일
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB",
        name="dark",
        max_zoom=19,
    ).add_to(m)

    # 개별 주차장 마커
    for _, row in df_map.iterrows():
        rate  = float(row["가동률"])
        color = folium_color(rate)
        status, _, _, _ = cong(rate)
        fee   = row.get("기본 주차 요금", 0)
        fee_s = f"{int(fee)}원/5분" if pd.notna(fee) and fee > 0 else "무료"

        # 위경도: 주소에서 구 좌표 fallback 사용 (실제 좌표 없으므로)
        gu_name  = row.get("구", "")
        lat_base = GU_COORDS.get(gu_name, (37.5665, 126.9780))[0]
        lon_base = GU_COORDS.get(gu_name, (37.5665, 126.9780))[1]
        # 같은 구 내 주차장을 미세하게 분산
        seed = abs(hash(str(row["주차장명"]))) % 10000
        rng  = np.random.default_rng(seed)
        lat  = lat_base + rng.uniform(-0.012, 0.012)
        lon  = lon_base + rng.uniform(-0.015, 0.015)

        radius = max(5, min(16, float(row["총 주차면"]) * 0.012))

        popup_html = f"""
        <div style="background:#0e1017;border:1px solid rgba(255,255,255,.12);
                    border-radius:10px;padding:12px 14px;font-family:sans-serif;
                    min-width:180px;color:#eef2ff;">
          <div style="font-size:13px;font-weight:700;margin-bottom:6px;">{row['주차장명']}</div>
          <div style="height:1px;background:rgba(255,255,255,.08);margin-bottom:8px;"></div>
          <div style="font-size:11px;color:#7b8db0;margin-bottom:2px;">혼잡도</div>
          <div style="font-size:18px;font-weight:700;color:{color};margin-bottom:8px;">{rate:.1f}% <span style="font-size:11px;">{status}</span></div>
          <div style="font-size:11px;color:#7b8db0;">
            현재: <b style="color:#eef2ff;">{int(row['현재 주차 차량수'])}대</b> /
            총: <b style="color:#eef2ff;">{int(row['총 주차면'])}면</b><br>
            잔여: <b style="color:{color};">{int(row['잔여'])}면</b> · {fee_s}
          </div>
        </div>"""

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.82,
            weight=1.5,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{row['주차장명']} {rate:.0f}%",
        ).add_to(m)

    # 구 중심 레이블 (전체 보기일 때)
    if not sel_gu:
        for _, gr in gu.iterrows():
            rate  = float(gr["가동률"])
            color = folium_color(rate)
            folium.Marker(
                location=[gr["lat"], gr["lon"]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        background:rgba(14,16,23,.88);
                        border:1.5px solid {color};
                        border-radius:6px;padding:3px 7px;
                        font-family:'IBM Plex Mono',monospace;
                        font-size:10px;color:{color};
                        white-space:nowrap;
                        backdrop-filter:blur(4px);
                    ">{gr['구'][:2]} {rate:.0f}%</div>""",
                    icon_size=(70, 24),
                    icon_anchor=(35, 12),
                ),
                tooltip=f"{gr['구']} — 가동률 {rate:.1f}%",
            ).add_to(m)

    st_folium(m, use_container_width=True, height=560, returned_objects=[])

    # 범례
    st.markdown("""
    <div style="display:flex;gap:16px;flex-wrap:wrap;padding:8px 4px 4px;
                border-top:1px solid rgba(255,255,255,.06);">
      <span style="font-size:.68rem;color:#7b8db0;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#22d3a5;display:inline-block;"></span>여유 (~40%)</span>
      <span style="font-size:.68rem;color:#7b8db0;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#fbbf24;display:inline-block;"></span>보통 (40–70%)</span>
      <span style="font-size:.68rem;color:#7b8db0;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#fb923c;display:inline-block;"></span>혼잡 (70–90%)</span>
      <span style="font-size:.68rem;color:#7b8db0;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#f87171;display:inline-block;"></span>포화 (90%+)</span>
      <span style="margin-left:auto;font-size:.62rem;color:#343d52;">마커 크기 = 총 주차면 비례 · 클릭하면 상세 정보</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── 사이드 패널
# ─────────────────────────────────────────────────────────────────────────────
with col_side:
    # ── 구 선택 그리드 ──────────────────────────────────────────────────────────
    st.markdown('<div class="panel-sec-title" style="padding:16px 20px 0;font-family:IBM Plex Mono,monospace;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:#4f8ef7;">구 선택</div>', unsafe_allow_html=True)

    gu_sorted = gu.sort_values("가동률", ascending=False)

    # 구 버튼 (3열 그리드)
    n = len(gu_sorted)
    rows_n = (n + 2) // 3
    for r in range(rows_n):
        row_gus = gu_sorted.iloc[r*3 : r*3+3]
        cols3   = st.columns(3)
        for ci, (_, gr) in enumerate(row_gus.iterrows()):
            rate = float(gr["가동률"])
            _, color, rgb, bgc = cong(rate)
            is_sel = sel_gu == gr["구"]
            bord   = color if is_sel else "rgba(255,255,255,.07)"
            bg     = f"rgba({rgb},.14)" if is_sel else "#141720"
            with cols3[ci]:
                if st.button(
                    f"**{gr['구'][:2]}**\n{rate:.0f}%",
                    key=f"gu_{gr['구']}",
                    help=gr["구"],
                    use_container_width=True,
                ):
                    st.session_state.sel_gu = None if sel_gu == gr["구"] else gr["구"]
                    st.rerun()
                st.markdown(f"""
                <style>
                div:has(> [data-testid="stButton"] > button[title="{gr['구']}"]) > [data-testid="stButton"] > button {{
                    width:100%!important; height:auto!important; position:relative!important;
                    background:{bg}!important; border:1px solid {bord}!important;
                    color:{color if is_sel else '#7b8db0'}!important;
                    font-family:'IBM Plex Mono',monospace!important;
                    font-size:.68rem!important; padding:6px 4px!important;
                    border-radius:7px!important; line-height:1.4!important;
                    white-space:pre-line!important; text-align:center!important;
                }}
                div:has(> [data-testid="stButton"] > button[title="{gr['구']}"]) > [data-testid="stButton"] > button:hover {{
                    border-color:{color}!important; color:{color}!important;
                    background:rgba({rgb},.1)!important;
                }}
                </style>""", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,.07);margin:8px 0;'>", unsafe_allow_html=True)

    # ── 선택된 구 or 전체 순위 ──────────────────────────────────────────────────
    if sel_gu:
        gu_row = gu[gu["구"] == sel_gu].iloc[0]
        rate   = float(gu_row["가동률"])
        status, color, rgb, bgc = cong(rate)

        st.markdown(f"""
        <div style="padding:14px 20px;border-bottom:1px solid rgba(255,255,255,.07);">
          <div style="font-size:1rem;font-weight:700;color:#eef2ff;">{sel_gu}</div>
          <span style="display:inline-block;font-size:.65rem;font-weight:700;padding:2px 9px;
                border-radius:999px;margin-top:4px;margin-bottom:12px;
                background:{bgc};color:{color};letter-spacing:.06em;">{status}</span>
          <div style="font-size:.6rem;color:#343d52;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px;">가동률</div>
          <div style="background:rgba(255,255,255,.05);border-radius:999px;height:8px;overflow:hidden;margin-bottom:3px;">
            <div style="width:{min(rate,100):.1f}%;height:8px;border-radius:999px;background:{color};"></div>
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:.75rem;color:#7b8db0;">{rate:.1f}%</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:12px;">
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:7px;padding:8px 10px;">
              <div style="font-size:.58rem;color:#343d52;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">주차장 수</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:.95rem;color:#eef2ff;">{int(gu_row['주차장수'])}개소</div>
            </div>
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:7px;padding:8px 10px;">
              <div style="font-size:.58rem;color:#343d52;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">총 주차면</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:.95rem;color:#eef2ff;">{int(gu_row['총주차면']):,}</div>
            </div>
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:7px;padding:8px 10px;">
              <div style="font-size:.58rem;color:#343d52;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">현재 차량</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:.95rem;color:#eef2ff;">{int(gu_row['현재차량']):,}대</div>
            </div>
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:7px;padding:8px 10px;">
              <div style="font-size:.58rem;color:#343d52;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">잔여 면수</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:.95rem;color:{color};">{int(gu_row['잔여']):,}면</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 해당 구 주차장 리스트
        st.markdown('<div style="padding:12px 20px 4px;font-family:IBM Plex Mono,monospace;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:#4f8ef7;">주차장 상세</div>', unsafe_allow_html=True)
        lots = df[(df["구"] == sel_gu) & (df["총 주차면"] >= 1)].sort_values("가동률", ascending=False)
        for _, lot in lots.head(10).iterrows():
            lr = float(lot["가동률"])
            _, lc, _, lbg = cong(lr)
            raw_fee = lot.get("기본 주차 요금", 0)
            fee_s   = f"{int(raw_fee)}원" if pd.notna(raw_fee) and raw_fee > 0 else "무료"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.05);
                        border-radius:8px;padding:10px 12px;margin:0 20px 6px;border-left:2px solid {lc};">
              <div style="font-size:.78rem;font-weight:600;color:#eef2ff;margin-bottom:2px;
                          white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{lot['주차장명']}</div>
              <div style="font-size:.67rem;color:#343d52;margin-bottom:7px;">{int(lot['현재 주차 차량수'])}대 / {int(lot['총 주차면'])}면 · {fee_s}</div>
              <div style="background:rgba(255,255,255,.05);border-radius:999px;height:3px;overflow:hidden;margin-bottom:4px;">
                <div style="width:{min(lr,100):.1f}%;height:3px;border-radius:999px;background:{lc};"></div>
              </div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:.67rem;color:{lc};">{lr:.1f}%</div>
            </div>""", unsafe_allow_html=True)

        if st.button("← 전체 보기", key="back"):
            st.session_state.sel_gu = None
            st.rerun()
        st.markdown("""
        <style>
        div:has(> [data-testid="stButton"] > button[title="← 전체 보기"]) > [data-testid="stButton"] > button,
        div:has(> [data-testid="stButton"] > button[kind="secondary"]:last-child) > [data-testid="stButton"] > button[key="back"] {
            width:auto!important; height:auto!important; position:relative!important;
        }
        [data-testid="stButton"][data-key="back"] > button {
            width: calc(100% - 40px) !important; height: auto !important;
            position: relative !important; margin: 8px 20px !important;
            background: rgba(255,255,255,.04) !important;
            border: 1px solid rgba(255,255,255,.1) !important;
            color: #7b8db0 !important; font-size: .72rem !important;
            border-radius: 8px !important; padding: 7px !important;
        }
        </style>""", unsafe_allow_html=True)

    else:
        # 전체 혼잡도 순위
        st.markdown('<div style="padding:12px 20px 8px;font-family:IBM Plex Mono,monospace;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:#4f8ef7;">구별 혼잡도 순위</div>', unsafe_allow_html=True)
        for idx, (_, gr) in enumerate(gu.sort_values("가동률", ascending=False).iterrows(), 1):
            r = float(gr["가동률"])
            _, c, _, _ = cong(r)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:5px 20px;">
              <span style="font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#343d52;width:16px;">{idx:02d}</span>
              <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;font-size:.76rem;margin-bottom:3px;">
                  <span style="color:#eef2ff;">{gr['구']}</span>
                  <span style="font-family:'IBM Plex Mono',monospace;color:{c};">{r:.1f}%</span>
                </div>
                <div style="background:rgba(255,255,255,.05);border-radius:999px;height:4px;overflow:hidden;">
                  <div style="width:{min(r,100):.1f}%;height:4px;border-radius:999px;background:{c};"></div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div style="padding:10px 20px;font-size:.63rem;color:#343d52;">위 버튼을 클릭하면 구별 상세 정보를 볼 수 있습니다.</div>', unsafe_allow_html=True)
