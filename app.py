import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
import plotly.graph_objects as go
from pathlib import Path
import glob

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seoul ParkMap",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — 카카오맵 톤앤매너: 밝고 선명한 지도, 청명한 UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg:       #f5f6f8;
  --surface:  #ffffff;
  --surface2: #f0f2f5;
  --border:   #e4e7ed;
  --text1:    #191f28;
  --text2:    #6b7684;
  --text3:    #b0b8c1;
  --kakao:    #fee500;
  --kakao-d:  #d4ac00;
  --blue:     #246bfd;
  --green:    #05c072;
  --orange:   #ff6b00;
  --red:      #ff3b3b;
  --yellow:   #ffb400;
  --shadow:   0 2px 12px rgba(0,0,0,0.08);
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg) !important;
    font-family: 'Noto Sans KR', sans-serif;
}
[data-testid="stHeader"]   { background: transparent !important; box-shadow: none !important; }
[data-testid="stSidebar"]  { background: #1a1d27 !important; }
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── 네비게이션 바 ── */
.nav {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 28px;
    display: flex; align-items: center;
    height: 56px; gap: 0;
    box-shadow: var(--shadow);
    position: sticky; top: 0; z-index: 100;
}
.nav-logo {
    display: flex; align-items: center; gap: 8px;
    margin-right: 40px; cursor: pointer; text-decoration: none;
}
.nav-logo-icon {
    width: 34px; height: 34px; border-radius: 10px;
    background: var(--kakao);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
}
.nav-logo-text {
    font-size: 16px; font-weight: 800;
    color: var(--text1); letter-spacing: -0.02em;
}
.nav-logo-text span { color: var(--blue); }
.nav-tab {
    padding: 0 18px; height: 56px; display: flex; align-items: center;
    font-size: 14px; font-weight: 500; color: var(--text2);
    border-bottom: 2px solid transparent; cursor: pointer;
    transition: all .15s; white-space: nowrap;
}
.nav-tab:hover  { color: var(--text1); }
.nav-tab.active { color: var(--blue); border-bottom-color: var(--blue); font-weight: 700; }
.nav-right {
    margin-left: auto; display: flex; align-items: center; gap: 12px;
}
.live-chip {
    display: inline-flex; align-items: center; gap: 5px;
    background: #e8f5e9; border: 1px solid #c8e6c9;
    border-radius: 999px; padding: 4px 11px;
    font-size: 11px; color: #2e7d32; font-weight: 600; letter-spacing: .03em;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #43a047;
             animation: blink 1.8s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }

/* ── KPI 스트립 ── */
.kpi-strip {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: grid; grid-template-columns: repeat(5,1fr);
}
.kpi-cell {
    padding: 14px 24px; position: relative;
    border-right: 1px solid var(--border);
    transition: background .15s;
}
.kpi-cell:last-child { border-right: none; }
.kpi-cell:hover { background: var(--surface2); }
.kpi-l { font-size: 11px; color: var(--text2); letter-spacing: .06em; text-transform: uppercase; margin-bottom: 4px; }
.kpi-v { font-family: 'IBM Plex Mono',monospace; font-size: 22px; font-weight: 700; color: var(--text1); line-height: 1.1; }
.kpi-n { font-size: 11px; color: var(--text3); margin-top: 3px; }
.kpi-bar { height: 3px; background: var(--border); border-radius: 2px; margin-top: 8px; overflow: hidden; }
.kpi-bar-fill { height: 3px; border-radius: 2px; background: var(--c,var(--blue)); }

/* ── 본문 레이아웃 ── */
.body { display: flex; height: calc(100vh - 108px); overflow: hidden; }

/* ── 좌측 패널 ── */
.left-panel {
    width: 340px; min-width: 340px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    overflow: hidden;
}
.panel-head {
    padding: 16px 18px 12px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
}
.panel-head-title { font-size: 14px; font-weight: 700; color: var(--text1); margin-bottom: 10px; }
.search-box {
    display: flex; align-items: center; gap: 8px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px 13px;
    font-size: 13px; color: var(--text2);
}
.panel-scroll { flex: 1; overflow-y: auto; padding: 10px 0; }
.panel-scroll::-webkit-scrollbar { width: 4px; }
.panel-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

/* ── 구 카드 ── */
.gu-card {
    display: flex; align-items: center; gap: 12px;
    padding: 11px 18px; cursor: pointer;
    transition: background .12s; border-bottom: 1px solid var(--border);
}
.gu-card:hover  { background: var(--surface2); }
.gu-card.active { background: #eef3ff; border-left: 3px solid var(--blue); padding-left: 15px; }
.gu-icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; color: white; flex-shrink: 0;
}
.gu-info { flex: 1; min-width: 0; }
.gu-name { font-size: 13px; font-weight: 700; color: var(--text1); margin-bottom: 3px; }
.gu-meta { font-size: 11px; color: var(--text2); }
.gu-rate-wrap { text-align: right; flex-shrink: 0; }
.gu-rate-num { font-family:'IBM Plex Mono',monospace; font-size: 16px; font-weight: 700; }
.gu-rate-label { font-size: 10px; color: var(--text3); }
.mini-bar { height: 4px; border-radius: 2px; background: var(--border); overflow: hidden; margin-top: 4px; width: 60px; }
.mini-bar-fill { height: 4px; border-radius: 2px; }

/* ── 상세 패널 ── */
.detail-back {
    display: flex; align-items: center; gap: 6px; padding: 12px 18px;
    border-bottom: 1px solid var(--border); cursor: pointer;
    font-size: 13px; color: var(--blue); font-weight: 600;
}
.detail-head {
    padding: 16px 18px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.detail-gu-name { font-size: 18px; font-weight: 800; color: var(--text1); margin-bottom: 4px; }
.status-badge {
    display: inline-block; font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 999px; letter-spacing: .04em;
}
.gauge-wrap { padding: 14px 18px; border-bottom: 1px solid var(--border); }
.gauge-label { font-size: 11px; color: var(--text2); letter-spacing: .06em; text-transform: uppercase; margin-bottom: 6px; }
.gauge-track { height: 10px; background: var(--border); border-radius: 5px; overflow: hidden; margin-bottom: 5px; }
.gauge-fill  { height: 10px; border-radius: 5px; }
.gauge-num { font-family:'IBM Plex Mono',monospace; font-size: 13px; color: var(--text2); }
.stat-grid-2 { display: grid; grid-template-columns:1fr 1fr; gap: 1px; background: var(--border); }
.stat-cell { background:var(--surface); padding:12px 16px; }
.stat-cell-l { font-size:10px; color:var(--text3); text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; }
.stat-cell-v { font-family:'IBM Plex Mono',monospace; font-size:15px; font-weight:600; color:var(--text1); }

/* ── 개별 주차장 카드 ── */
.lot-item {
    padding: 11px 18px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px;
    transition: background .12s; cursor: default;
}
.lot-item:hover { background: var(--surface2); }
.lot-cong-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.lot-info { flex: 1; min-width: 0; }
.lot-name { font-size: 13px; font-weight: 600; color: var(--text1);
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
.lot-sub  { font-size: 11px; color: var(--text2); }
.lot-right { text-align: right; flex-shrink: 0; }
.lot-rate  { font-family:'IBM Plex Mono',monospace; font-size: 14px; font-weight: 700; }
.lot-cap   { font-size: 10px; color: var(--text3); margin-top: 1px; }

/* ── 지도 영역 ── */
.map-area { flex: 1; position: relative; overflow: hidden; }

/* ── Streamlit 버튼 숨김 (커스텀 HTML 버튼 사용) ── */
[data-testid="stButton"] > button {
    display: none !important;
}
/* 단, desel 버튼만 표시 */
[data-testid="stButton"][key="__desel__"] > button { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 서울 25개 구 중심 좌표
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
    """(상태명, hex색, 배경색, 텍스트색) 반환"""
    if rate >= 90:
        return "포화",  "#ff3b3b", "#fff0f0", "#cc0000"
    elif rate >= 70:
        return "혼잡",  "#ff6b00", "#fff4ed", "#cc4400"
    elif rate >= 40:
        return "보통",  "#ffb400", "#fffaed", "#996800"
    else:
        return "여유",  "#05c072", "#edfff7", "#027a48"

# ─────────────────────────────────────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = Path(__file__).parent
    csv_files = list(base.glob("*.csv")) + list((base / "data").glob("*.csv") if (base/"data").exists() else [])

    info_path = next((f for f in csv_files if "공영" in f.name or "안내" in f.name), None)
    rt_path   = next((f for f in csv_files if "시영" in f.name or "실시간" in f.name), None)

    if not info_path or not rt_path:
        st.error(
            "**CSV 파일을 찾을 수 없습니다.**\n\n"
            "아래 두 파일을 `app.py`와 **같은 폴더**에 넣어주세요.\n\n"
            "- `서울시 공영주차장 안내 정보.csv`\n"
            "- `서울시 시영주차장 실시간 주차대수 정보.csv`\n\n"
            f"현재 탐색 경로: `{base}`"
        )
        st.stop()

    info = pd.read_csv(info_path, encoding="euc-kr")
    rt   = pd.read_csv(rt_path,   encoding="euc-kr")

    # 구 추출
    info["구"] = info["주소"].str.extract(r"([가-힣]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([가-힣]+구)")

    # 수치 정리
    for col in ["총 주차면", "기본 주차 요금", "일 최대 요금", "월 정기권 금액"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce").fillna(0)
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    # 이상치 제거 (총주차면 ≤ 10)
    rt = rt[rt["총 주차면"] > 10].copy()
    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).clip(0, 100).round(1)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)

    # 구별 실시간 집계
    gu = rt.groupby("구").agg(
        주차장수=("주차장명", "count"),
        총주차면=("총 주차면",     "sum"),
        현재차량=("현재 주차 차량수", "sum"),
        가용면=("가용면",       "sum"),
    ).reset_index()
    gu["이용률"] = (gu["현재차량"] / gu["총주차면"] * 100).clip(0, 150).round(1)
    gu["잔여"]   = gu["가용면"].astype(int)
    gu["lat"]    = gu["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[0])
    gu["lon"]    = gu["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[1])

    # 공영주차장 좌표 있는 것만
    info_coord = info.dropna(subset=["위도", "경도"]).copy()
    info_coord["위도"] = pd.to_numeric(info_coord["위도"], errors="coerce")
    info_coord["경도"] = pd.to_numeric(info_coord["경도"], errors="coerce")
    info_coord = info_coord.dropna(subset=["위도", "경도"])

    update_time = rt["현재 주차 차량수 업데이트시간"].iloc[0][:16] if len(rt) > 0 else "-"
    return info, rt, gu, info_coord, update_time

info, rt, gu, info_coord, update_time = load_data()

# 세션 상태
if "sel_gu" not in st.session_state:
    st.session_state.sel_gu = None

# ─────────────────────────────────────────────────────────────────────────────
# 전체 KPI
# ─────────────────────────────────────────────────────────────────────────────
total_info_lots  = len(info)
total_info_spots = int(info["총 주차면"].sum())
rt_curr   = int(rt["현재 주차 차량수"].sum())
rt_spots  = int(rt["총 주차면"].sum())
rt_avail  = int(rt["가용면"].sum())
rt_rate   = round(rt_curr / rt_spots * 100, 1) if rt_spots > 0 else 0
n_sat     = int((gu["이용률"] >= 90).sum())

# ─────────────────────────────────────────────────────────────────────────────
# ── 네비게이션 바
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="nav">
  <div class="nav-logo">
    <div class="nav-logo-icon">🅿️</div>
    <div class="nav-logo-text">Seoul <span>Park</span>Map</div>
  </div>
  <div class="nav-right">
    <div class="live-chip">
      <span class="live-dot"></span>
      LIVE · {update_time}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── KPI 스트립
# ─────────────────────────────────────────────────────────────────────────────
rate_pct = min(rt_rate, 100)
sat_pct  = round(n_sat / 25 * 100)

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-cell">
    <div class="kpi-l">공영주차장 총 개소</div>
    <div class="kpi-v">{total_info_lots:,}</div>
    <div class="kpi-n">서울시 전체</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:100%;--c:#246bfd;"></div></div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-l">총 공급 주차면</div>
    <div class="kpi-v">{total_info_spots:,}</div>
    <div class="kpi-n">면</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:100%;--c:#246bfd;"></div></div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-l">현재 주차 차량 (실시간)</div>
    <div class="kpi-v">{rt_curr:,}</div>
    <div class="kpi-n">{len(rt)}개소 기준</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{rate_pct:.0f}%;--c:#ffb400;"></div></div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-l">평균 이용률</div>
    <div class="kpi-v" style="color:{'#ff3b3b' if rt_rate>=90 else '#ff6b00' if rt_rate>=70 else '#ffb400' if rt_rate>=40 else '#05c072'};">{rt_rate:.1f}%</div>
    <div class="kpi-n">실시간 기준</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{rate_pct:.0f}%;--c:{'#ff3b3b' if rt_rate>=90 else '#ffb400'};"></div></div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-l">포화 구역 수</div>
    <div class="kpi-v" style="color:#ff3b3b;">{n_sat}개 구</div>
    <div class="kpi-n">이용률 90% 이상</div>
    <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{sat_pct:.0f}%;--c:#ff3b3b;"></div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ── 본문: 좌측 패널 + 지도
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_map = st.columns([1, 3], gap="small")

sel = st.session_state.sel_gu

# ────────────────────────────────────────────
# 좌측 패널
# ────────────────────────────────────────────
with col_left:
    if sel:
        # ── 구 상세 뷰 ──
        sel_row = gu[gu["구"] == sel]
        if not sel_row.empty:
            sr     = sel_row.iloc[0]
            rate   = float(sr["이용률"])
            status, color, bgc, tc = cong(rate)

            # 뒤로가기 버튼
            if st.button("← 전체 목록", key="back_btn"):
                st.session_state.sel_gu = None
                st.rerun()
            st.markdown(f"""
            <style>
            [data-testid="stButton"][key="back_btn"] > button {{
                display: flex !important; align-items: center; gap: 6px;
                width: 100% !important; padding: 10px 18px !important;
                background: transparent !important; border: none !important;
                border-bottom: 1px solid var(--border) !important;
                color: #246bfd !important; font-size: 13px !important;
                font-weight: 600 !important; cursor: pointer !important;
                border-radius: 0 !important; font-family: 'Noto Sans KR',sans-serif !important;
            }}
            [data-testid="stButton"][key="back_btn"] > button:hover {{
                background: #eef3ff !important;
            }}
            </style>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="padding:16px 18px;border-bottom:1px solid var(--border);">
              <div style="font-size:20px;font-weight:800;color:var(--text1);margin-bottom:6px;">{sel}</div>
              <span style="display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;
                    border-radius:999px;background:{bgc};color:{tc};letter-spacing:.04em;">{status}</span>
            </div>

            <div style="padding:14px 18px;border-bottom:1px solid var(--border);">
              <div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.06em;margin-bottom:7px;">실시간 이용률</div>
              <div style="height:12px;background:var(--border);border-radius:6px;overflow:hidden;margin-bottom:6px;">
                <div style="height:12px;border-radius:6px;background:{color};width:{min(rate,100):.1f}%;transition:width .5s;"></div>
              </div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:{color};">{rate:.1f}%</div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);">
              <div style="background:white;padding:12px 16px;">
                <div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">주차장 수</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:var(--text1);">{int(sr['주차장수'])}개소</div>
              </div>
              <div style="background:white;padding:12px 16px;">
                <div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">총 주차면</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:var(--text1);">{int(sr['총주차면']):,}면</div>
              </div>
              <div style="background:white;padding:12px 16px;">
                <div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">현재 차량</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:var(--text1);">{int(sr['현재차량']):,}대</div>
              </div>
              <div style="background:white;padding:12px 16px;">
                <div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">잔여 면수</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:{color};">{int(sr['잔여']):,}면</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # 주차장 목록
            st.markdown("""
            <div style="padding:10px 18px 6px;border-top:1px solid var(--border);
                        font-size:11px;font-weight:700;color:var(--text2);
                        text-transform:uppercase;letter-spacing:.08em;">
              주차장 상세
            </div>""", unsafe_allow_html=True)

            lots = rt[(rt["구"] == sel)].sort_values("이용률", ascending=False)
            for _, lot in lots.iterrows():
                lr = float(lot["이용률"])
                _, lc, lbg, ltc = cong(lr)
                raw_fee = lot.get("기본 주차 요금", 0)
                fee_s   = f"{int(raw_fee)}원/5분" if pd.notna(raw_fee) and raw_fee > 0 else "무료"
                avail   = int(lot["가용면"])
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 18px;
                            border-bottom:1px solid var(--border);transition:background .1s;"
                     onmouseover="this.style.background='#f5f6f8'"
                     onmouseout="this.style.background='white'">
                  <div style="width:10px;height:10px;border-radius:50%;background:{lc};flex-shrink:0;"></div>
                  <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:600;color:var(--text1);
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px;">
                      {lot['주차장명']}
                    </div>
                    <div style="font-size:11px;color:var(--text2);">
                      {int(lot['현재 주차 차량수'])}대 / {int(lot['총 주차면'])}면 · {fee_s}
                    </div>
                    <div style="height:3px;background:var(--border);border-radius:2px;margin-top:5px;overflow:hidden;">
                      <div style="height:3px;border-radius:2px;background:{lc};width:{min(lr,100):.1f}%;"></div>
                    </div>
                  </div>
                  <div style="text-align:right;flex-shrink:0;">
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;color:{lc};">{lr:.0f}%</div>
                    <div style="font-size:10px;color:var(--text3);">잔여 {avail}면</div>
                  </div>
                </div>""", unsafe_allow_html=True)

    else:
        # ── 전체 구 목록 ──
        st.markdown("""
        <div style="padding:14px 18px 10px;border-bottom:1px solid var(--border);">
          <div style="font-size:14px;font-weight:700;color:var(--text1);margin-bottom:8px;">구 선택</div>
          <div style="display:flex;align-items:center;gap:7px;background:#f5f6f8;
                      border:1px solid var(--border);border-radius:10px;padding:8px 12px;
                      font-size:13px;color:var(--text3);">
            🔍 자치구를 선택하면 상세 정보를 볼 수 있어요
          </div>
        </div>
        """, unsafe_allow_html=True)

        gu_sorted = gu.sort_values("이용률", ascending=False)
        for _, gr in gu_sorted.iterrows():
            r = float(gr["이용률"])
            status, color, bgc, tc = cong(r)
            is_sel = sel == gr["구"]
            bar_w  = min(r, 100)

            # 버튼 (보이지 않지만 클릭 감지용으로 유지)
            btn_key = f"gu__{gr['구']}"
            if st.button(gr["구"], key=btn_key):
                st.session_state.sel_gu = gr["구"]
                st.rerun()

            st.markdown(f"""
            <style>
            [data-testid="stButton"][key="{btn_key}"] > button {{
                display: none !important;
            }}
            </style>
            <div onclick="
                var buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(function(b) {{
                    if(b.innerText.trim() === '{gr['구']}') b.click();
                }});
            "
            style="display:flex;align-items:center;gap:12px;padding:11px 18px;
                   cursor:pointer;border-bottom:1px solid var(--border);
                   background:{'#eef3ff' if is_sel else 'white'};
                   border-left:{'3px solid #246bfd' if is_sel else '3px solid transparent'};
                   transition:background .12s;"
            onmouseover="this.style.background='#f5f6f8'"
            onmouseout="this.style.background='{'#eef3ff' if is_sel else 'white'}'">

              <div style="width:38px;height:38px;border-radius:10px;
                          background:{color};display:flex;align-items:center;
                          justify-content:center;font-size:13px;font-weight:700;
                          color:white;flex-shrink:0;">
                {gr['구'][:1]}
              </div>

              <div style="flex:1;min-width:0;">
                <div style="font-size:13px;font-weight:700;color:var(--text1);margin-bottom:2px;">{gr['구']}</div>
                <div style="font-size:11px;color:var(--text2);">
                  {int(gr['주차장수'])}개소 · {int(gr['총주차면']):,}면
                </div>
                <div style="height:4px;background:var(--border);border-radius:2px;margin-top:5px;overflow:hidden;">
                  <div style="height:4px;border-radius:2px;background:{color};width:{bar_w:.1f}%;"></div>
                </div>
              </div>

              <div style="text-align:right;flex-shrink:0;">
                <div style="font-family:'IBM Plex Mono',monospace;font-size:17px;font-weight:700;color:{color};">{r:.0f}%</div>
                <div style="font-size:10px;color:var(--text3);margin-top:1px;">{status}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────
# 지도 컬럼
# ────────────────────────────────────────────
with col_map:
    # 중심·줌 결정
    if sel and sel in GU_COORDS:
        clat, clon, czoom = GU_COORDS[sel][0], GU_COORDS[sel][1], 14
    else:
        clat, clon, czoom = 37.5665, 126.9780, 11

    # ── Folium 지도 생성 ──
    m = folium.Map(
        location=[clat, clon],
        zoom_start=czoom,
        tiles=None,
        prefer_canvas=True,
    )

    # 카카오맵 느낌의 밝은 타일
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="CartoDB Voyager",
        name="지도",
        max_zoom=19,
    ).add_to(m)

    # ── 구별 버블 마커 (전체 보기 시) ──────────────────────
    if not sel:
        for _, gr in gu.iterrows():
            r = float(gr["이용률"])
            status, color, bgc, tc = cong(r)
            size = max(28, min(70, float(gr["총주차면"]) * 0.035))

            # 원형 버블 DivIcon
            bubble_html = f"""
            <div style="
                width:{size:.0f}px; height:{size:.0f}px;
                border-radius:50%;
                background:{color};
                border: 3px solid white;
                box-shadow: 0 3px 12px rgba(0,0,0,0.25);
                display:flex; flex-direction:column;
                align-items:center; justify-content:center;
                cursor:pointer;
                transition: transform .15s;
            "
            onmouseover="this.style.transform='scale(1.12)'"
            onmouseout="this.style.transform='scale(1)'">
              <span style="font-size:{max(9, size*0.22):.0f}px;font-weight:800;color:white;line-height:1.1;">{r:.0f}%</span>
              <span style="font-size:{max(7, size*0.16):.0f}px;font-weight:600;color:rgba(255,255,255,.88);line-height:1.1;">{gr['구'][:2]}</span>
            </div>"""

            popup_html = f"""
            <div style="font-family:'Noto Sans KR',sans-serif;min-width:190px;padding:4px;">
              <div style="font-size:15px;font-weight:800;color:#191f28;margin-bottom:8px;">{gr['구']}</div>
              <div style="display:inline-block;font-size:11px;font-weight:700;padding:2px 9px;
                          border-radius:999px;background:{bgc};color:{tc};margin-bottom:10px;">{status}</div>
              <div style="font-size:12px;color:#6b7684;margin-bottom:2px;">이용률</div>
              <div style="font-size:22px;font-weight:800;color:{color};margin-bottom:8px;">{r:.1f}%</div>
              <hr style="border:none;border-top:1px solid #e4e7ed;margin:8px 0;">
              <table style="width:100%;font-size:12px;color:#6b7684;border-collapse:collapse;">
                <tr><td>주차장 수</td><td style="text-align:right;font-weight:700;color:#191f28;">{int(gr['주차장수'])}개소</td></tr>
                <tr><td>총 주차면</td><td style="text-align:right;font-weight:700;color:#191f28;">{int(gr['총주차면']):,}면</td></tr>
                <tr><td>현재 차량</td><td style="text-align:right;font-weight:700;color:#191f28;">{int(gr['현재차량']):,}대</td></tr>
                <tr><td>잔여 면수</td><td style="text-align:right;font-weight:700;color:{color};">{int(gr['잔여']):,}면</td></tr>
              </table>
            </div>"""

            folium.Marker(
                location=[gr["lat"], gr["lon"]],
                icon=folium.DivIcon(
                    html=bubble_html,
                    icon_size=(size, size),
                    icon_anchor=(size/2, size/2),
                ),
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{gr['구']} — {r:.1f}% ({status})",
            ).add_to(m)

    # ── 선택된 구: 개별 주차장 마커 ──────────────────────────
    else:
        lots = rt[rt["구"] == sel]
        sel_coord = GU_COORDS.get(sel, (37.5665, 126.9780))

        for _, lot in lots.iterrows():
            lr = float(lot["이용률"])
            _, lc, lbg, ltc = cong(lr)
            raw_fee = lot.get("기본 주차 요금", 0)
            fee_s   = f"{int(raw_fee)}원/5분" if pd.notna(raw_fee) and raw_fee > 0 else "무료"

            # 구 중심에서 미세 분산 (좌표 없으므로)
            seed = abs(hash(str(lot["주차장명"]))) % 99999
            rng  = np.random.default_rng(seed)
            lat  = sel_coord[0] + rng.uniform(-0.018, 0.018)
            lon  = sel_coord[1] + rng.uniform(-0.022, 0.022)

            dot_size = max(14, min(36, float(lot["총 주차면"]) * 0.055))

            icon_html = f"""
            <div style="
                width:{dot_size:.0f}px; height:{dot_size:.0f}px; border-radius:50%;
                background:{lc}; border:2.5px solid white;
                box-shadow:0 2px 8px rgba(0,0,0,.22);
                display:flex;align-items:center;justify-content:center;
            ">
              <span style="font-size:{max(7,dot_size*0.32):.0f}px;font-weight:800;color:white;">{lr:.0f}</span>
            </div>"""

            popup_html = f"""
            <div style="font-family:'Noto Sans KR',sans-serif;min-width:200px;padding:4px;">
              <div style="font-size:14px;font-weight:800;color:#191f28;margin-bottom:6px;">{lot['주차장명']}</div>
              <div style="font-size:11px;color:#6b7684;margin-bottom:1px;">{lot['주소']}</div>
              <hr style="border:none;border-top:1px solid #e4e7ed;margin:8px 0;">
              <div style="font-size:11px;color:#6b7684;margin-bottom:2px;">이용률</div>
              <div style="font-size:24px;font-weight:800;color:{lc};margin-bottom:8px;">{lr:.1f}%</div>
              <div style="height:8px;background:#f0f2f5;border-radius:4px;overflow:hidden;margin-bottom:10px;">
                <div style="height:8px;background:{lc};border-radius:4px;width:{min(lr,100):.1f}%;"></div>
              </div>
              <table style="width:100%;font-size:12px;color:#6b7684;border-collapse:collapse;">
                <tr><td>현재 차량</td><td style="text-align:right;font-weight:700;color:#191f28;">{int(lot['현재 주차 차량수'])}대</td></tr>
                <tr><td>총 주차면</td><td style="text-align:right;font-weight:700;color:#191f28;">{int(lot['총 주차면'])}면</td></tr>
                <tr><td>가용 면수</td><td style="text-align:right;font-weight:700;color:{lc};">{int(lot['가용면'])}면</td></tr>
                <tr><td>기본 요금</td><td style="text-align:right;font-weight:700;color:#191f28;">{fee_s}</td></tr>
              </table>
            </div>"""

            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html=icon_html,
                    icon_size=(dot_size, dot_size),
                    icon_anchor=(dot_size/2, dot_size/2),
                ),
                popup=folium.Popup(popup_html, max_width=230),
                tooltip=f"{lot['주차장명']} {lr:.0f}%",
            ).add_to(m)

    # ── 공영주차장 좌표 핀 (전체 보기 시 배경으로) ─────────────
    if not sel and len(info_coord) > 0:
        sample = info_coord.sample(min(80, len(info_coord)), random_state=42)
        for _, row in sample.iterrows():
            folium.CircleMarker(
                location=[float(row["위도"]), float(row["경도"])],
                radius=3,
                color="#246bfd",
                fill=True,
                fill_color="#246bfd",
                fill_opacity=0.4,
                weight=1,
                tooltip=f"{row['주차장명']}",
            ).add_to(m)

    # ── 범례 오버레이 ────────────────────────────────────────────
    legend_html = """
    <div style="
        position:fixed; bottom:24px; right:16px; z-index:9999;
        background:white; border:1px solid #e4e7ed; border-radius:12px;
        padding:12px 15px; box-shadow:0 4px 16px rgba(0,0,0,0.12);
        font-family:'Noto Sans KR',sans-serif;
    ">
      <div style="font-size:11px;font-weight:700;color:#191f28;margin-bottom:8px;letter-spacing:.04em;">혼잡도 기준</div>
      <div style="display:flex;flex-direction:column;gap:5px;">
        <div style="display:flex;align-items:center;gap:7px;font-size:12px;color:#6b7684;">
          <span style="width:12px;height:12px;border-radius:50%;background:#05c072;display:inline-block;flex-shrink:0;"></span>여유 &nbsp;<span style="color:#b0b8c1;font-size:10px;">~40%</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;font-size:12px;color:#6b7684;">
          <span style="width:12px;height:12px;border-radius:50%;background:#ffb400;display:inline-block;flex-shrink:0;"></span>보통 &nbsp;<span style="color:#b0b8c1;font-size:10px;">40–70%</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;font-size:12px;color:#6b7684;">
          <span style="width:12px;height:12px;border-radius:50%;background:#ff6b00;display:inline-block;flex-shrink:0;"></span>혼잡 &nbsp;<span style="color:#b0b8c1;font-size:10px;">70–90%</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;font-size:12px;color:#6b7684;">
          <span style="width:12px;height:12px;border-radius:50%;background:#ff3b3b;display:inline-block;flex-shrink:0;"></span>포화 &nbsp;<span style="color:#b0b8c1;font-size:10px;">90%+</span>
        </div>
      </div>
      <div style="margin-top:8px;padding-top:8px;border-top:1px solid #f0f2f5;font-size:10px;color:#b0b8c1;">
        버블 크기 = 총 주차면 비례<br>마커 클릭 시 상세 정보
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    # 미니맵
    MiniMap(toggle_display=True, tile_layer="CartoDB.Positron", zoom_level_offset=-5).add_to(m)

    # 지도 출력
    map_height = 620 if not sel else 640
    st_folium(m, use_container_width=True, height=map_height, returned_objects=[])
