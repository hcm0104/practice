import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import folium
from folium.plugins import MiniMap
from streamlit_folium import st_folium
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="서울시 공영주차장 현황",
    page_icon="🅿️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #f0f4f8; }
[data-testid="stSidebar"] { background: #1b2a4a; }
[data-testid="stSidebar"] * { color: #d0d9ea !important; }
.page-title { font-size: 26px; font-weight: 700; color: #1b2a4a; padding: 4px 0 2px; }
.page-sub   { font-size: 13px; color: #6b7a99; margin-bottom: 18px; }
.kpi-wrap   { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }
.kpi        { background:#fff; border-radius:12px; padding:16px 18px;
               border-left:4px solid var(--ac); box-shadow:0 1px 6px rgba(0,0,0,.06); }
.kpi-label  { font-size:11px; color:#8a94a6; text-transform:uppercase; letter-spacing:.8px; margin-bottom:6px; }
.kpi-value  { font-size:26px; font-weight:700; color:#1b2a4a; line-height:1; }
.kpi-sub    { font-size:12px; color:#8a94a6; margin-top:4px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 서울 25개 구 중심 좌표
# ─────────────────────────────────────────
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


# ─────────────────────────────────────────
# 혼잡도 색상
# ─────────────────────────────────────────
STATUS_COLOR = {"여유": "#2ecc71", "보통": "#3498db", "혼잡": "#f39c12", "만차": "#e74c3c"}

def get_congestion_color(rate: float) -> str:
    if rate >= 95: return "#e74c3c"
    elif rate >= 70: return "#f39c12"
    elif rate >= 30: return "#3498db"
    else: return "#2ecc71"

def get_congestion_label(rate: float) -> str:
    if rate >= 95: return "만차"
    elif rate >= 70: return "혼잡"
    elif rate >= 30: return "보통"
    else: return "여유"


# ─────────────────────────────────────────
# API 호출 (서울 열린데이터광장 GetParkInfo)
# ─────────────────────────────────────────
def fetch_parking_api(api_key: str) -> list:
    """전체 페이지 순회하여 공영주차장 데이터 수집"""
    all_rows = []
    page_size = 1000
    for page in range(1, 7):           # 최대 6,000건
        start = (page - 1) * page_size + 1
        end   = page * page_size
        url   = f"http://openapi.seoul.go.kr:8088/{api_key}/json/GetParkInfo/{start}/{end}/"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("GetParkInfo", {}).get("row", [])
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < page_size:  # 마지막 페이지
                break
        except Exception:
            break
    return all_rows


@st.cache_data(ttl=300, show_spinner=False)   # 5분 캐시
def load_data(api_key: str):
    rows = fetch_parking_api(api_key)
    if not rows:
        return None, None, None, None, "-"

    raw = pd.DataFrame(rows)

    # ── 컬럼명 한글 통일 ──
    col_map = {
        "PKLT_CD":          "주차장코드",
        "PARKING_NAME":     "주차장명",
        "ADDR":             "주소",
        "PARKING_TYPE_NM":  "주차장 종류명",
        "OPER_SE_NM":       "운영구분명",
        "CAPACITY":         "총 주차면",
        "CUR_PARKING":      "현재 주차 차량수",
        "PAY_YN_NM":        "유무료구분명",
        "RATES":            "기본 주차 요금",
        "TIME_RATE":        "기본 주차 시간(분 단위)",
        "ADD_RATES":        "추가 단위 요금",
        "ADD_TIME_RATE":    "추가 단위 시간(분 단위)",
        "DAY_MAXIMUM":      "일 최대 요금",
        "MONTHLY_TICKET_GIFT": "월 정기권 금액",
        "LAT":              "위도",
        "LNG":              "경도",
        "TEL":              "전화번호",
        "QUERY_DATE":       "현재 주차 차량수 업데이트시간",
    }
    raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns}, inplace=True)

    raw["구"] = raw["주소"].str.extract(r"([가-힣]+구)")

    for col in ["총 주차면", "현재 주차 차량수", "기본 주차 요금",
                "기본 주차 시간(분 단위)", "추가 단위 요금", "추가 단위 시간(분 단위)",
                "일 최대 요금", "월 정기권 금액", "위도", "경도"]:
        if col in raw.columns:
            raw[col] = pd.to_numeric(raw[col], errors="coerce").fillna(0)

    # info : 전체 주차장 (정적 정보)
    info = raw.copy()

    # rt : 이상치 제거 후 실시간 현황
    rt = raw[raw["총 주차면"] > 10].copy()
    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0, 100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)
    rt["혼잡도"] = pd.cut(
        rt["이용률"],
        bins=[-1, 30, 70, 95, 100],
        labels=["여유", "보통", "혼잡", "만차"],
    ).astype(str)

    # 구별 실시간 집계
    gu_rt = (
        rt.groupby("구")
        .agg(주차장수=("주차장코드", "count"),
             총주차면=("총 주차면",   "sum"),
             현재차량=("현재 주차 차량수", "sum"),
             가용면=("가용면", "sum"))
        .reset_index()
    )
    gu_rt["이용률"] = (gu_rt["현재차량"] / gu_rt["총주차면"] * 100).round(1)
    gu_rt["lat"]   = gu_rt["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[0])
    gu_rt["lon"]   = gu_rt["구"].map(lambda x: GU_COORDS.get(x, (37.55, 126.98))[1])

    # 구별 전체 집계
    gu_info = (
        info.groupby("구")
        .agg(전체주차장수=("주차장코드", "count"),
             전체주차면=("총 주차면",   "sum"))
        .reset_index()
    )

    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return info, rt, gu_rt, gu_info, update_time


# ─────────────────────────────────────────
# API 키 확인 (secrets.toml 또는 사이드바)
# ─────────────────────────────────────────
try:
    _secret_key = st.secrets.get("SEOUL_API_KEY", "")
except Exception:
    _secret_key = ""

# 사이드바보다 먼저 선언 (사이드바에서 덮어씀)
if "api_key" not in st.session_state:
    st.session_state.api_key = _secret_key
PLOT_BASE    = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.9)",
    font=dict(family="Noto Sans KR, sans-serif", size=12, color="#4a5568"),
    margin=dict(l=10, r=10, t=36, b=10),
)


# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🅿️ Seoul ParkMap")
    st.markdown("---")

    # ── API 키 입력 ──
    api_key_input = st.text_input(
        "🔑 서울 열린데이터광장 API 키",
        value=st.session_state.api_key,
        type="password",
        placeholder="발급받은 인증키 입력",
        help="data.seoul.go.kr → 로그인 → 마이페이지 → 인증키 발급",
    )
    if api_key_input:
        st.session_state.api_key = api_key_input.strip()

    if st.button("🔄 데이터 새로고침", use_container_width=True):
        load_data.clear()
        st.rerun()

    st.markdown("---")
    view = st.radio(
        "화면",
        ["📊 전체 현황", "🗺️ 구별 현황", "📋 주차장 목록"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**필터**")

    # 필터는 데이터 로드 후 채움
    gu_ph   = st.empty()
    kind_ph = st.empty()
    fee_ph  = st.empty()

    st.markdown("---")


# ─────────────────────────────────────────
# API 키 없을 때 안내
# ─────────────────────────────────────────
if not st.session_state.api_key:
    st.markdown('<div class="page-title">🅿️ Seoul ParkMap — 실시간 공영주차장 현황</div>', unsafe_allow_html=True)
    st.info(
        "**좌측 사이드바에 API 키를 입력하면 실시간 데이터가 로드됩니다.**\n\n"
        "**API 키 발급 방법:**\n"
        "1. [data.seoul.go.kr](https://data.seoul.go.kr) 접속 → 회원가입\n"
        "2. 로그인 → 마이페이지 → **인증키 발급**\n"
        "3. 발급된 키를 사이드바 입력란에 붙여넣기\n\n"
        "**또는** `.streamlit/secrets.toml` 파일에 저장:\n"
        "```toml\n"
        "SEOUL_API_KEY = \"발급받은_키\"\n"
        "```\n\n"
        "사용 API: `GetParkInfo` (공영주차장 안내정보, 5분 갱신)"
    )
    st.stop()


# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
with st.spinner("실시간 주차 데이터를 불러오는 중..."):
    info, rt, gu_rt, gu_info, UPDATE_TIME = load_data(st.session_state.api_key)

if info is None:
    st.error(
        "데이터를 불러오지 못했습니다.\n\n"
        "- API 키가 올바른지 확인해 주세요.\n"
        "- [data.seoul.go.kr](https://data.seoul.go.kr)에서 `GetParkInfo` 서비스 신청 여부를 확인해 주세요."
    )
    st.stop()

GU_LIST = sorted(info["구"].dropna().unique().tolist())

# 필터 채우기
with gu_ph:
    sel_gu   = st.multiselect("자치구", GU_LIST, placeholder="전체", key="f_gu")
with kind_ph:
    KIND_LIST = rt["주차장 종류명"].dropna().unique().tolist() if "주차장 종류명" in rt.columns else []
    sel_kind  = st.multiselect("주차장 종류", KIND_LIST, placeholder="전체", key="f_kind")
with fee_ph:
    FEE_LIST = rt["유무료구분명"].dropna().unique().tolist() if "유무료구분명" in rt.columns else []
    sel_fee  = st.multiselect("유무료", FEE_LIST, placeholder="전체", key="f_fee")

with st.sidebar:
    st.caption(f"📡 마지막 갱신: {UPDATE_TIME}")
    st.caption("출처: 서울 열린데이터광장")


def filt(df):
    d = df.copy()
    if sel_gu   and "구"            in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_kind and "주차장 종류명" in d.columns: d = d[d["주차장 종류명"].isin(sel_kind)]
    if sel_fee  and "유무료구분명"  in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    return d


# ─────────────────────────────────────────────────────────────────────────────
# ① 전체 현황  (원본 그대로)
# ─────────────────────────────────────────────────────────────────────────────
if "전체 현황" in view:
    st.markdown('<div class="page-title">📊 서울시 공영주차장 전체 현황</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">실시간 기준: {UPDATE_TIME} &nbsp;|&nbsp; 총 주차면 10면 이하 이상치 제거 &nbsp;|&nbsp; 5분 자동 갱신</div>', unsafe_allow_html=True)

    fi = filt(info)
    fr = filt(rt)

    total_lots  = len(fi)
    total_spots = int(fi["총 주차면"].sum())
    rt_spots    = int(fr["총 주차면"].sum())
    rt_curr     = int(fr["현재 주차 차량수"].sum())
    rt_avail    = int(fr["가용면"].sum())
    rt_rate     = round(rt_curr / rt_spots * 100, 1) if rt_spots > 0 else 0

    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi" style="--ac:#1a6fc4">
        <div class="kpi-label">총 공영주차장</div>
        <div class="kpi-value">{total_lots:,}</div>
        <div class="kpi-sub">개소</div>
      </div>
      <div class="kpi" style="--ac:#0f7b6c">
        <div class="kpi-label">총 주차면</div>
        <div class="kpi-value">{total_spots:,}</div>
        <div class="kpi-sub">면</div>
      </div>
      <div class="kpi" style="--ac:#d35400">
        <div class="kpi-label">전체 이용률 (실시간)</div>
        <div class="kpi-value">{rt_rate}%</div>
        <div class="kpi-sub">실시간 연계 {len(fr)}개소 기준</div>
      </div>
      <div class="kpi" style="--ac:#2ecc71">
        <div class="kpi-label">현재 가용 면수</div>
        <div class="kpi-value">{rt_avail:,}</div>
        <div class="kpi-sub">면 여유</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 혼잡도 분포")
        cnt = fr["혼잡도"].value_counts().reindex(["여유", "보통", "혼잡", "만차"], fill_value=0)
        fig = go.Figure(go.Bar(
            x=cnt.index, y=cnt.values,
            marker_color=[STATUS_COLOR.get(k, "#aaa") for k in cnt.index],
            marker_line_width=0,
            text=cnt.values, textposition="outside",
        ))
        fig.update_layout(**PLOT_BASE, height=280, showlegend=False,
                          yaxis=dict(gridcolor="#f0f0f0"))
        fig.update_traces(width=0.5)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 주차장 종류 비율")
        vc = fi["주차장 종류명"].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=vc.index, values=vc.values, hole=0.45,
            marker=dict(colors=["#1a6fc4", "#0f7b6c", "#d35400", "#8e44ad", "#2ecc71"]),
            textinfo="label+percent",
        ))
        fig2.update_layout(**PLOT_BASE, height=280, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns([2, 1])

    with col3:
        st.markdown("#### 자치구별 실시간 이용률")
        f_gu   = gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy()
        f_gu_s = f_gu.sort_values("이용률", ascending=True)
        bar_colors = [
            "#e74c3c" if v >= 95 else
            "#f39c12" if v >= 70 else
            "#3498db" if v >= 30 else "#2ecc71"
            for v in f_gu_s["이용률"]
        ]
        fig3 = go.Figure(go.Bar(
            x=f_gu_s["이용률"], y=f_gu_s["구"], orientation="h",
            marker_color=bar_colors, marker_line_width=0,
            text=f_gu_s["이용률"].map(lambda v: f"{v}%"), textposition="outside",
        ))
        fig3.update_layout(**PLOT_BASE, height=max(300, len(f_gu_s) * 28 + 60),
                           xaxis=dict(range=[0, 115], gridcolor="#f0f0f0"),
                           yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### 유무료 현황")
        vc2 = fi["유무료구분명"].value_counts()
        fig4 = go.Figure(go.Pie(
            labels=vc2.index, values=vc2.values, hole=0.5,
            marker=dict(colors=["#1a6fc4", "#2ecc71"]),
            textinfo="label+value",
        ))
        fig4.update_layout(**PLOT_BASE, height=240, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("#### 운영 구분 Top 5")
        for nm, c in fi["운영구분명"].value_counts().head(5).items():
            pct = round(c / max(len(fi), 1) * 100, 1)
            st.markdown(f"**{nm}** `{c:,}개` {pct}%")


# ─────────────────────────────────────────────────────────────────────────────
# ② 구별 현황  (원본 테이블·차트 유지 + 지도 추가)
# ─────────────────────────────────────────────────────────────────────────────
elif "구별 현황" in view:
    st.markdown('<div class="page-title">🗺️ 자치구별 주차 현황</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">전체 공영주차장 인프라 및 실시간 이용 현황 비교 &nbsp;|&nbsp; 기준: {UPDATE_TIME}</div>', unsafe_allow_html=True)

    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"] / r["총주차면"] * 100, 1) if r["총주차면"] > 0 else 0.0,
        axis=1,
    )
    if sel_gu:
        merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("전체주차장수", ascending=False)

    # ── 지도 + 우측 테이블 ─────────────────────────────────────────────────────
    st.markdown("#### 🗺️ 구별 혼잡도 지도")
    st.caption("마커를 클릭하면 해당 구의 상세 정보를 볼 수 있습니다.")

    map_col, info_col = st.columns([3, 2], gap="medium")

    with map_col:
        # Folium 지도 생성
        m = folium.Map(
            location=[37.5665, 126.9780],
            zoom_start=11,
            tiles=None,
        )
        # 밝은 카토 타일 (원본 앱 밝은 테마와 어울리도록)
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            attr="CartoDB",
            max_zoom=19,
        ).add_to(m)

        # 구별 버블 마커
        map_data = gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy()

        for _, row in map_data.iterrows():
            rate   = float(row["이용률"])
            color  = get_congestion_color(rate)
            label  = get_congestion_label(rate)
            avail  = int(row["가용면"])
            size   = max(28, min(65, float(row["총주차면"]) * 0.034))

            # 버블 아이콘
            bubble_html = f"""
            <div style="
                width:{size:.0f}px; height:{size:.0f}px; border-radius:50%;
                background:{color}; border:3px solid white;
                box-shadow:0 3px 10px rgba(0,0,0,0.2);
                display:flex; flex-direction:column;
                align-items:center; justify-content:center;
            ">
              <span style="font-size:{max(9,size*0.24):.0f}px;font-weight:800;color:white;line-height:1.1;">{rate:.0f}%</span>
              <span style="font-size:{max(7,size*0.17):.0f}px;font-weight:600;color:rgba(255,255,255,.9);line-height:1.1;">{row['구'][:2]}</span>
            </div>"""

            # 팝업
            popup_html = f"""
            <div style="font-family:'Noto Sans KR',sans-serif;min-width:190px;padding:6px 2px;">
              <div style="font-size:15px;font-weight:700;color:#1b2a4a;margin-bottom:8px;">{row['구']}</div>
              <div style="display:inline-block;background:{color};color:white;font-size:11px;
                          font-weight:700;padding:2px 9px;border-radius:999px;margin-bottom:10px;">{label}</div>
              <div style="font-size:12px;color:#8a94a6;margin-bottom:2px;">실시간 이용률</div>
              <div style="font-size:24px;font-weight:800;color:{color};margin-bottom:8px;">{rate:.1f}%</div>
              <hr style="border:none;border-top:1px solid #eee;margin:8px 0;">
              <table style="width:100%;font-size:12px;color:#6b7a99;border-collapse:collapse;">
                <tr style="border-bottom:1px solid #f5f5f5;">
                  <td style="padding:4px 0;">주차장 수</td>
                  <td style="text-align:right;font-weight:700;color:#1b2a4a;">{int(row['주차장수'])}개소</td>
                </tr>
                <tr style="border-bottom:1px solid #f5f5f5;">
                  <td style="padding:4px 0;">총 주차면</td>
                  <td style="text-align:right;font-weight:700;color:#1b2a4a;">{int(row['총주차면']):,}면</td>
                </tr>
                <tr style="border-bottom:1px solid #f5f5f5;">
                  <td style="padding:4px 0;">현재 차량</td>
                  <td style="text-align:right;font-weight:700;color:#1b2a4a;">{int(row['현재차량']):,}대</td>
                </tr>
                <tr>
                  <td style="padding:4px 0;">잔여 면수</td>
                  <td style="text-align:right;font-weight:700;color:{color};">{avail:,}면</td>
                </tr>
              </table>
            </div>"""

            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=folium.DivIcon(
                    html=bubble_html,
                    icon_size=(size, size),
                    icon_anchor=(size / 2, size / 2),
                ),
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{row['구']} — {rate:.1f}% ({label})",
            ).add_to(m)

        # 범례
        legend_html = """
        <div style="
            position:fixed; bottom:20px; left:20px; z-index:9999;
            background:white; border:1px solid #dde3ec; border-radius:12px;
            padding:12px 14px; box-shadow:0 2px 10px rgba(0,0,0,.1);
            font-family:'Noto Sans KR',sans-serif;
        ">
          <div style="font-size:11px;font-weight:700;color:#1b2a4a;margin-bottom:8px;">혼잡도 기준</div>
          <div style="font-size:12px;color:#6b7a99;line-height:2;">
            <span style="color:#2ecc71;font-weight:700;">●</span> 여유 &nbsp;(~30%)<br>
            <span style="color:#3498db;font-weight:700;">●</span> 보통 &nbsp;(30–70%)<br>
            <span style="color:#f39c12;font-weight:700;">●</span> 혼잡 &nbsp;(70–95%)<br>
            <span style="color:#e74c3c;font-weight:700;">●</span> 만차 &nbsp;(95%+)
          </div>
          <div style="margin-top:7px;font-size:10px;color:#b0bac9;">버블 크기 = 총 주차면 비례</div>
        </div>"""
        m.get_root().html.add_child(folium.Element(legend_html))

        MiniMap(toggle_display=True, zoom_level_offset=-5).add_to(m)

        st_folium(m, use_container_width=True, height=500, returned_objects=[])

    with info_col:
        # 혼잡도 순위 카드
        st.markdown("#### 구별 혼잡도 순위")
        rank_df = map_data.sort_values("이용률", ascending=False)
        for i, (_, row) in enumerate(rank_df.iterrows(), 1):
            rate  = float(row["이용률"])
            color = get_congestion_color(rate)
            label = get_congestion_label(rate)
            bar_w = min(rate, 100)
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:10px 14px;
                        margin-bottom:7px;box-shadow:0 1px 4px rgba(0,0,0,.06);
                        border-left:4px solid {color};">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                <div>
                  <span style="font-size:11px;color:#8a94a6;margin-right:6px;">#{i:02d}</span>
                  <span style="font-size:14px;font-weight:700;color:#1b2a4a;">{row['구']}</span>
                  <span style="display:inline-block;background:{color};color:white;
                               font-size:10px;font-weight:700;padding:1px 7px;
                               border-radius:999px;margin-left:6px;">{label}</span>
                </div>
                <span style="font-size:16px;font-weight:800;color:{color};">{rate:.1f}%</span>
              </div>
              <div style="height:5px;background:#f0f4f8;border-radius:3px;overflow:hidden;">
                <div style="height:5px;background:{color};border-radius:3px;width:{bar_w:.1f}%;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:11px;color:#8a94a6;">
                <span>{int(row['주차장수'])}개소 · {int(row['총주차면']):,}면</span>
                <span>잔여 <b style="color:{color};">{int(row['가용면']):,}면</b></span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── 원본 테이블 ───────────────────────────────────────────────────────────
    st.markdown("#### 구별 종합 현황 테이블")
    disp = merged[[
        "구", "전체주차장수", "전체주차면", "주차장수", "총주차면", "현재차량", "가용면", "실시간이용률"
    ]].copy()
    disp.columns = ["자치구", "전체 주차장", "전체 주차면", "실시간 연계", "연계 주차면", "현재 차량", "가용 면수", "이용률(%)"]
    st.dataframe(
        disp.style
            .background_gradient(subset=["이용률(%)"], cmap="RdYlGn_r", vmin=0, vmax=100)
            .format({"전체 주차장": "{:,.0f}", "전체 주차면": "{:,.0f}", "실시간 연계": "{:,.0f}",
                     "연계 주차면": "{:,.0f}", "현재 차량": "{:,.0f}", "가용 면수": "{:,.0f}", "이용률(%)": "{:.1f}"}),
        use_container_width=True, height=460, hide_index=True,
    )

    st.markdown("---")

    # ── 원본 차트 2개 ─────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 구별 전체 주차면")
        srt = merged.sort_values("전체주차면", ascending=True)
        fig = go.Figure(go.Bar(
            x=srt["전체주차면"], y=srt["구"], orientation="h",
            marker_color="#1a6fc4", marker_line_width=0,
            text=srt["전체주차면"].map(lambda v: f"{int(v):,}면"), textposition="outside",
        ))
        fig.update_layout(**PLOT_BASE, height=max(340, len(srt) * 28 + 60),
                          xaxis=dict(gridcolor="#f0f0f0"),
                          yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 구별 실시간 이용률")
        srt2 = merged.sort_values("실시간이용률", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=srt2["실시간이용률"], y=srt2["구"], orientation="h",
            marker_color=[
                "#e74c3c" if v >= 95 else "#f39c12" if v >= 70 else "#3498db" if v >= 30 else "#2ecc71"
                for v in srt2["실시간이용률"]
            ],
            marker_line_width=0,
            text=srt2["실시간이용률"].map(lambda v: f"{v:.1f}%"), textposition="outside",
        ))
        fig2.update_layout(**PLOT_BASE, height=max(340, len(srt2) * 28 + 60),
                           xaxis=dict(range=[0, 115], gridcolor="#f0f0f0"),
                           yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ③ 주차장 목록  (원본 그대로)
# ─────────────────────────────────────────────────────────────────────────────
elif "주차장 목록" in view:
    st.markdown('<div class="page-title">📋 주차장 목록 조회</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">API 실시간 데이터 &nbsp;|&nbsp; 기준: {UPDATE_TIME} &nbsp;|&nbsp; 5분 자동 갱신</div>', unsafe_allow_html=True)

    fr2 = filt(rt)

    col_s1, col_s2 = st.columns([2, 2])
    with col_s1:
        sort_opt = st.selectbox(
            "정렬", ["이용률 높은 순", "이용률 낮은 순", "가용면 많은 순", "가용면 적은 순"], key="s1"
        )
    with col_s2:
        search = st.text_input("주차장명 검색", placeholder="예: 세종로, 강남...", key="search")
        if search:
            fr2 = fr2[fr2["주차장명"].str.contains(search, na=False)]

    sm = {
        "이용률 높은 순": ("이용률", False), "이용률 낮은 순": ("이용률", True),
        "가용면 많은 순": ("가용면", False), "가용면 적은 순": ("가용면", True),
    }
    sc, asc = sm[sort_opt]
    fr2 = fr2.sort_values(sc, ascending=asc)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("조회 주차장", f"{len(fr2):,}개소")
    c2.metric("총 주차면",   f"{int(fr2['총 주차면'].sum()):,}면")
    c3.metric("현재 차량",   f"{int(fr2['현재 주차 차량수'].sum()):,}대")
    c4.metric("가용 면수",   f"{int(fr2['가용면'].sum()):,}면")

    # 표시할 컬럼 구성 (API에 있는 것만)
    base_cols = ["구", "주차장명", "주소", "총 주차면", "현재 주차 차량수", "가용면", "이용률", "혼잡도"]
    opt_cols  = ["주차장 종류명", "유무료구분명", "기본 주차 요금",
                 "기본 주차 시간(분 단위)", "일 최대 요금", "월 정기권 금액", "전화번호"]
    show_cols = base_cols + [c for c in opt_cols if c in fr2.columns]
    disp_rt   = fr2[show_cols].copy()

    rename_map = {
        "현재 주차 차량수":      "현재 차량",
        "이용률":               "이용률(%)",
        "주차장 종류명":         "종류",
        "유무료구분명":          "유무료",
        "기본 주차 요금":        "기본요금(원)",
        "기본 주차 시간(분 단위)":"기본시간(분)",
        "일 최대 요금":          "일최대요금(원)",
        "월 정기권 금액":        "월정기권(원)",
    }
    disp_rt.rename(columns=rename_map, inplace=True)

    fmt = {"총 주차면": "{:,.0f}", "현재 차량": "{:,.0f}",
           "가용면": "{:,.0f}", "이용률(%)": "{:.1f}"}
    for c in ["기본요금(원)", "기본시간(분)", "일최대요금(원)", "월정기권(원)"]:
        if c in disp_rt.columns:
            fmt[c] = "{:,.0f}"

    st.dataframe(
        disp_rt.style
            .background_gradient(subset=["이용률(%)"], cmap="RdYlGn_r", vmin=0, vmax=100)
            .format(fmt),
        use_container_width=True, height=500, hide_index=True,
    )
    st.download_button(
        "📥 CSV 다운로드",
        disp_rt.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"실시간_주차현황_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
