import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="서울 환경·보건 대시보드",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 글로벌 CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 폰트 임포트 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Space+Mono:wght@400;700&display=swap');

/* 전체 배경 */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0e1a;
    color: #e2e8f0;
    font-family: 'Noto Sans KR', sans-serif;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #0f1525;
    border-right: 1px solid #1e2d45;
}
[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}

/* 헤더 숨기기 */
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* 타이틀 */
.dash-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f1f5f9;
    padding: 0.2rem 0 0.1rem;
    border-left: 3px solid #38bdf8;
    padding-left: 0.8rem;
    margin-bottom: 0.2rem;
}
.dash-sub {
    font-size: 0.82rem;
    color: #64748b;
    padding-left: 1.1rem;
    margin-bottom: 1.5rem;
    letter-spacing: 0.03em;
}

/* KPI 카드 */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
}
.kpi-label {
    font-size: 0.72rem;
    color: #64748b;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
}
.kpi-delta {
    font-size: 0.72rem;
    margin-top: 0.35rem;
}
.kpi-delta.down { color: #34d399; }
.kpi-delta.up   { color: #f87171; }
.kpi-delta.neutral { color: #64748b; }

/* 섹션 제목 */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #38bdf8;
    margin: 1.6rem 0 0.8rem;
}

/* 데이터프레임 래퍼 */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    overflow: hidden;
}

/* 셀렉트박스 / 라디오 */
[data-testid="stSelectbox"] > div > div {
    background-color: #111827;
    border: 1px solid #1e2d45;
    border-radius: 6px;
    color: #e2e8f0;
}

/* 구분선 */
hr { border-color: #1e2d45; }

/* 정책 배지 */
.policy-badge {
    display: inline-block;
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    margin-bottom: 0.8rem;
}

/* 인사이트 박스 */
.insight-box {
    background: #111827;
    border: 1px solid #1e2d45;
    border-left: 3px solid #38bdf8;
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
    color: #cbd5e1;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ── 데이터 생성 ───────────────────────────────────────────────────────────────
SEOUL_DISTRICTS = [
    "종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구",
    "강북구","도봉구","노원구","은평구","서대문구","마포구","양천구","강서구",
    "구로구","금천구","영등포구","동작구","관악구","서초구","강남구","송파구",
    "강동구","강남A","강남B","마포A","서초A","용산A",
    "종로A","중구A","성동A","광진A","동대문A","중랑A","성북A","강북A",
    "도봉A","노원A","은평A","서대문A","양천A","강서A","구로A","금천A",
    "영등포A","동작A","관악A","송파A",
]

@st.cache_data
def load_data():
    np.random.seed(42)
    n = 50
    lat_c, lon_c = 37.5665, 126.9780
    df = pd.DataFrame({
        "지역": SEOUL_DISTRICTS[:n],
        "lat": lat_c + np.random.uniform(-0.07, 0.07, n),
        "lon": lon_c + np.random.uniform(-0.09, 0.09, n),
        "자가용이용률": np.random.uniform(40, 90, n),
        "인구밀도": np.random.uniform(5000, 20000, n),
    })
    df["NOx"] = 0.02 * df["자가용이용률"] + 0.0005 * df["인구밀도"]
    df["폐질환지수"] = 18 * df["NOx"]
    return df

df_base = load_data()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 대시보드 설정")
    st.markdown("---")

    policy = st.selectbox(
        "🏛️ 정책 시나리오",
        ["기본 상태", "대중교통 인센티브", "저배출구역 (LEZ)", "통합 정책"],
    )

    st.markdown("---")
    map_metric = st.radio(
        "🗺️ 지도 표시 지표",
        ["폐질환지수", "NOx", "자가용이용률"],
    )

    st.markdown("---")
    top_n = st.slider("🔥 핫스팟 표시 수", 5, 20, 10)

    st.markdown("---")
    st.markdown(
        "<span style='font-size:0.72rem;color:#334155;'>데이터: 서울 모의 환경-보건 시뮬레이션</span>",
        unsafe_allow_html=True,
    )

# ── 정책 시뮬레이션 ───────────────────────────────────────────────────────────
df = df_base.copy()

if policy == "대중교통 인센티브":
    df["자가용이용률"] *= 0.90
elif policy == "저배출구역 (LEZ)":
    df["NOx"] *= 0.80
elif policy == "통합 정책":
    df["자가용이용률"] *= 0.85
    df["NOx"] *= 0.70

df["NOx"] = 0.02 * df["자가용이용률"] + 0.0005 * df["인구밀도"]
df["폐질환지수"] = 18 * df["NOx"]

# 기준 대비 변화율
nox_delta = (df["NOx"].mean() - df_base["NOx"].mean()) / df_base["NOx"].mean() * 100
lung_delta = (df["폐질환지수"].mean() - df_base["폐질환지수"].mean()) / df_base["폐질환지수"].mean() * 100
car_delta  = (df["자가용이용률"].mean() - df_base["자가용이용률"].mean()) / df_base["자가용이용률"].mean() * 100

# ── 레이아웃 ──────────────────────────────────────────────────────────────────
st.markdown('<div class="dash-title">서울 환경·보건 정책 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-sub">자가용 이용률 → NOx → 폐질환 구조의 공간 시각화</div>', unsafe_allow_html=True)

# KPI
def fmt_delta(val, positive_is_bad=True):
    if abs(val) < 0.01:
        cls, sym = "neutral", "±0.0%"
    elif val < 0:
        cls = "down" if positive_is_bad else "up"
        sym = f"▼ {abs(val):.1f}%"
    else:
        cls = "up" if positive_is_bad else "down"
        sym = f"▲ {abs(val):.1f}%"
    return cls, sym

nc, ns = fmt_delta(nox_delta)
lc, ls = fmt_delta(lung_delta)
cc, cs = fmt_delta(car_delta)

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">평균 NOx</div>
    <div class="kpi-value">{df['NOx'].mean():.2f}</div>
    <div class="kpi-delta {nc}">{ns} vs 기본</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">평균 폐질환 지수</div>
    <div class="kpi-value">{df['폐질환지수'].mean():.2f}</div>
    <div class="kpi-delta {lc}">{ls} vs 기본</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">평균 자가용 이용률</div>
    <div class="kpi-value">{df['자가용이용률'].mean():.1f}%</div>
    <div class="kpi-delta {cc}">{cs} vs 기본</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">고위험 지역 수 (상위 20%)</div>
    <div class="kpi-value">{int(len(df) * 0.2)}</div>
    <div class="kpi-delta neutral">— 전체 {len(df)}개 구역</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 지도 ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">공간 위험도 지도</div>', unsafe_allow_html=True)

# 색상 스케일: 파랑(낮음) → 주황 → 빨강(높음)
col_min = df[map_metric].min()
col_max = df[map_metric].max()

def make_color(val):
    t = (val - col_min) / (col_max - col_min + 1e-9)
    r = int(50  + 205 * t)
    g = int(120 - 120 * t)
    b = int(200 - 160 * t)
    return [r, g, b, 180]

df["_color"] = df[map_metric].apply(make_color)
df["_radius"] = df[map_metric] * (60 if map_metric == "폐질환지수" else 45 if map_metric == "NOx" else 20)

layer = pdk.Layer(
    "ScatterplotLayer",
    df,
    get_position="[lon, lat]",
    get_radius="_radius",
    get_fill_color="_color",
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(latitude=37.5665, longitude=126.9780, zoom=10.5, pitch=30)

tooltip = {
    "html": """
    <div style="background:#0f1525;border:1px solid #1e2d45;border-radius:8px;
                padding:10px 14px;font-family:sans-serif;font-size:12px;color:#e2e8f0;">
      <b style="color:#38bdf8;font-size:13px;">{지역}</b><br/>
      <hr style="border-color:#1e2d45;margin:6px 0;">
      🚗 자가용 이용률: <b>{자가용이용률:.1f}%</b><br/>
      💨 NOx: <b>{NOx:.3f}</b><br/>
      🫁 폐질환 지수: <b>{폐질환지수:.2f}</b>
    </div>
    """,
    "style": {"background": "transparent", "border": "none"},
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style="mapbox://styles/mapbox/dark-v10",
)

st.pydeck_chart(deck, use_container_width=True)

# ── 핫스팟 & 인사이트 ─────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(f'<div class="section-title">🔥 위험 구역 Top {top_n}</div>', unsafe_allow_html=True)
    top_df = (
        df[["지역", "자가용이용률", "NOx", "폐질환지수", "인구밀도"]]
        .sort_values("폐질환지수", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    top_df.index += 1
    top_df["자가용이용률"] = top_df["자가용이용률"].map("{:.1f}%".format)
    top_df["NOx"] = top_df["NOx"].map("{:.3f}".format)
    top_df["폐질환지수"] = top_df["폐질환지수"].map("{:.2f}".format)
    top_df["인구밀도"] = top_df["인구밀도"].map("{:,.0f}".format)
    st.dataframe(top_df, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">🧠 정책 인사이트</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="policy-badge">현재 시나리오: {policy}</div>', unsafe_allow_html=True)

    insights = {
        "기본 상태": [
            "현재 서울 평균 NOx는 <b>{:.3f}</b> 수준입니다.".format(df["NOx"].mean()),
            "자가용 이용률이 높은 구역일수록 폐질환 위험이 집중됩니다.",
            "고밀도·고이용률 지역이 핫스팟의 주요 원인입니다.",
        ],
        "대중교통 인센티브": [
            "자가용 이용률 10% 감소 → NOx <b>{:.1f}%</b> 개선.".format(abs(nox_delta)),
            "인센티브 효과는 대중교통 인프라가 좋은 구역에서 극대화됩니다.",
            "단기적으로 시행 가능한 정책 중 비용 대비 효과가 높습니다.",
        ],
        "저배출구역 (LEZ)": [
            "NOx 직접 저감 20% 적용 → 폐질환 지수 <b>{:.1f}%</b> 감소.".format(abs(lung_delta)),
            "구역 지정 범위와 차량 기준 설정이 효과의 핵심 변수입니다.",
            "고밀도 상업지구 중심으로 먼저 적용 시 효율적입니다.",
        ],
        "통합 정책": [
            "이동 감소 + 배출 저감 동시 적용으로 가장 큰 효과를 냅니다.",
            "폐질환 지수 <b>{:.1f}%</b> 개선으로 모든 시나리오 중 최적.".format(abs(lung_delta)),
            "예산·행정 부담이 크지만 장기적 공중보건 편익이 명확합니다.",
        ],
    }

    for txt in insights.get(policy, []):
        st.markdown(f'<div class="insight-box">• {txt}</div>', unsafe_allow_html=True)
