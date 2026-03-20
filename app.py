import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="서울 시영주차장 현황",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0b1120 !important;
    color: #dde6f5;
    font-family: 'Noto Sans KR', sans-serif;
}
[data-testid="stSidebar"]  { background: #0e1628 !important; }
[data-testid="stHeader"]   { background: transparent !important; }
#MainMenu, footer          { display: none !important; }
.block-container           { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; }

.hdr { border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 14px; margin-bottom: 18px; }
.hdr-title { font-size: 1.3rem; font-weight: 700; color: #f0f6ff; }
.hdr-sub   { font-size: 0.72rem; color: #3d5070; letter-spacing: .07em; text-transform: uppercase; margin-top: 2px; }

.kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 18px; }
.kpi  {
    background: #0f1a2e; border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 13px 15px; position: relative; overflow: hidden;
}
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--c); }
.kpi-l { font-size:.62rem; color:#3d5070; letter-spacing:.09em; text-transform:uppercase; margin-bottom:5px; }
.kpi-v { font-family:'IBM Plex Mono',monospace; font-size:1.45rem; font-weight:600; color:#f0f6ff; line-height:1.1; }
.kpi-n { font-size:.64rem; color:#3d5070; margin-top:4px; }

.panel {
    background:#0f1a2e; border:1px solid rgba(255,255,255,0.07);
    border-radius:12px; overflow:hidden;
}
.ph  { padding:11px 15px; border-bottom:1px solid rgba(255,255,255,0.07); }
.pt  { font-family:'IBM Plex Mono',monospace; font-size:.66rem; letter-spacing:.1em; text-transform:uppercase; color:#5577aa; }
.pb  { padding:14px 15px; }

.gu-name  { font-size:1.1rem; font-weight:700; color:#f0f6ff; }
.gu-badge { display:inline-block; font-size:.66rem; font-weight:700; letter-spacing:.07em;
            padding:2px 9px; border-radius:999px; margin-top:4px; margin-bottom:12px; }
.gauge-lbl { font-size:.6rem; color:#3d5070; letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px; }
.gauge-bg  { background:rgba(255,255,255,0.06); border-radius:999px; height:7px; overflow:hidden; margin-bottom:3px; }
.gauge-fill{ height:7px; border-radius:999px; }
.gauge-num { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:#5577aa; }

.srow { display:flex; justify-content:space-between; padding:6px 0;
        border-bottom:1px solid rgba(255,255,255,0.04); font-size:.77rem; }
.srow:last-child { border-bottom:none; }
.sk { color:#3d5070; }
.sv { font-family:'IBM Plex Mono',monospace; color:#8899bb; }

.lc  { background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.05);
        border-radius:8px; padding:9px 11px; margin-bottom:5px; }
.ln  { font-size:.78rem; font-weight:600; color:#dde6f5; margin-bottom:2px; }
.lm  { font-size:.67rem; color:#3d5070; }
.lb-bg  { background:rgba(255,255,255,0.06); border-radius:999px; height:3px; margin-top:6px; overflow:hidden; }
.lb-fill{ height:3px; border-radius:999px; }
.lr  { font-family:'IBM Plex Mono',monospace; font-size:.66rem; margin-top:3px; }

.ri  { margin-bottom:9px; }
.rr  { display:flex; justify-content:space-between; font-size:.76rem; margin-bottom:3px; }
.rn  { color:#dde6f5; }
.rv  { font-family:'IBM Plex Mono',monospace; }
.rb-bg  { background:rgba(255,255,255,0.05); border-radius:999px; height:4px; overflow:hidden; }
.rb-fill{ height:4px; border-radius:999px; }

.sec { font-family:'IBM Plex Mono',monospace; font-size:.6rem; letter-spacing:.13em;
       text-transform:uppercase; color:#3b82f6; margin:12px 0 7px; }

[data-testid="stDataFrame"] { border-radius:10px!important; border:1px solid rgba(255,255,255,0.07)!important; }
[data-testid="stButton"] > button {
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:.7rem !important; border-radius:7px !important; padding:4px 9px !important;
    background:rgba(255,255,255,0.03) !important; border:1px solid rgba(255,255,255,0.09) !important;
    color:#8899bb !important; transition:all .15s !important; white-space:pre-line !important; line-height:1.4 !important;
}
[data-testid="stButton"] > button:hover { background:rgba(255,255,255,0.08) !important; color:#f0f6ff !important; }
</style>
""", unsafe_allow_html=True)

# ── 좌표 ─────────────────────────────────────────────────────────────────────
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

def cong(rate):
    if rate >= 90:   return "포화","#ef4444","rgba(239,68,68,.15)","color:#ef4444;"
    elif rate >= 70: return "혼잡","#f97316","rgba(249,115,22,.15)","color:#f97316;"
    elif rate >= 40: return "보통","#f59e0b","rgba(245,158,11,.15)","color:#f59e0b;"
    else:            return "여유","#10b981","rgba(16,185,129,.15)","color:#10b981;"

# ── 데이터 ───────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_csv("서울시_시영주차장_실시간_주차대수_정보.csv", encoding="cp949")
    df["구"] = df["주소"].str.extract(r"([가-힣]+구)")
    df["가동률"] = (df["현재 주차 차량수"] / df["총 주차면"] * 100).clip(0, 200).round(1)
    df["잔여"] = (df["총 주차면"] - df["현재 주차 차량수"]).clip(lower=0)

    gu = df[df["총 주차면"] >= 1].groupby("구").agg(
        주차장수=("주차장명","count"),
        총주차면=("총 주차면","sum"),
        현재차량=("현재 주차 차량수","sum"),
    ).reset_index()
    gu["가동률"] = (gu["현재차량"] / gu["총주차면"] * 100).clip(0, 150).round(1)
    gu["잔여"] = (gu["총주차면"] - gu["현재차량"]).clip(lower=0)
    gu["lat"] = gu["구"].map(lambda x: GU_COORDS.get(x,(37.55,126.98))[0])
    gu["lon"] = gu["구"].map(lambda x: GU_COORDS.get(x,(37.55,126.98))[1])
    gu["색상"] = gu["가동률"].apply(lambda r: cong(r)[1])
    gu["상태"] = gu["가동률"].apply(lambda r: cong(r)[0])
    return df, gu

df, gu = load()

if "sel" not in st.session_state:
    st.session_state.sel = None

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <div class="hdr-title">🚗 서울시 시영주차장 실시간 현황</div>
  <div class="hdr-sub">Seoul City-Managed Parking · Static Snapshot · 2026.03.19</div>
</div>
""", unsafe_allow_html=True)

# ── KPI ──────────────────────────────────────────────────────────────────────
total_spaces = int(df["총 주차면"].sum())
total_cars   = int(df["현재 주차 차량수"].sum())
avg_rate     = total_cars / total_spaces * 100
n_busy       = int((gu["가동률"] >= 90).sum())

st.markdown(f"""
<div class="kpis">
  <div class="kpi" style="--c:#3b82f6;">
    <div class="kpi-l">주차장 수</div><div class="kpi-v">{len(df)}</div><div class="kpi-n">시영 전체</div>
  </div>
  <div class="kpi" style="--c:#8b5cf6;">
    <div class="kpi-l">총 주차면</div><div class="kpi-v">{total_spaces:,}</div><div class="kpi-n">공급 가능</div>
  </div>
  <div class="kpi" style="--c:#f59e0b;">
    <div class="kpi-l">현재 주차 차량</div><div class="kpi-v">{total_cars:,}</div><div class="kpi-n">대</div>
  </div>
  <div class="kpi" style="--c:#10b981;">
    <div class="kpi-l">전체 평균 가동률</div><div class="kpi-v">{avg_rate:.1f}%</div><div class="kpi-n">시영 기준</div>
  </div>
  <div class="kpi" style="--c:#ef4444;">
    <div class="kpi-l">포화 구역 수</div><div class="kpi-v">{n_busy}개 구</div><div class="kpi-n">가동률 90%+</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 구 선택 버튼 ──────────────────────────────────────────────────────────────
gu_sorted = gu.sort_values("가동률", ascending=False)
st.markdown('<div class="sec">구 선택 (클릭 → 우측에 상세 정보 표시)</div>', unsafe_allow_html=True)

btn_cols = st.columns(len(gu_sorted))
for i, (_, row) in enumerate(gu_sorted.iterrows()):
    with btn_cols[i]:
        if st.button(f"{row['구'][:2]}\n{row['가동률']:.0f}%", key=f"gb_{row['구']}", help=row["구"]):
            st.session_state.sel = None if st.session_state.sel == row["구"] else row["구"]
            st.rerun()

# 선택 버튼 하이라이트
if st.session_state.sel:
    rv = gu[gu["구"] == st.session_state.sel]["가동률"].values
    if len(rv):
        _, hc, _, _ = cong(float(rv[0]))
        st.markdown(f"""<style>
        div:has(> [data-testid="stButton"] > button[title="{st.session_state.sel}"]) > [data-testid="stButton"] > button
        {{ border-color:{hc}!important; color:{hc}!important; background:rgba(255,255,255,0.07)!important; }}
        </style>""", unsafe_allow_html=True)

# ── 지도 + 상세 ───────────────────────────────────────────────────────────────
col_map, col_detail = st.columns([2.4, 1], gap="medium")

with col_map:
    sel = st.session_state.sel
    fig = go.Figure()

    for _, row in gu.iterrows():
        _, color, _, _ = cong(float(row["가동률"]))
        size = max(20, min(52, float(row["총주차면"]) * 0.026))
        is_sel = sel == row["구"]

        # 본체 마커
        fig.add_trace(go.Scattermapbox(
            lat=[row["lat"]], lon=[row["lon"]],
            mode="markers+text",
            marker=dict(size=size, color=color, opacity=0.9 if is_sel else 0.78, sizemode="diameter"),
            text=[f"{row['구'][:2]}\n{row['가동률']:.0f}%"],
            textfont=dict(size=9, color="white", family="IBM Plex Mono"),
            textposition="middle center",
            hovertext=[
                f"<b>{row['구']}</b><br>"
                f"상태: {row['상태']}<br>"
                f"가동률: {row['가동률']:.1f}%<br>"
                f"주차면: {int(row['총주차면']):,}면<br>"
                f"현재차량: {int(row['현재차량']):,}대<br>"
                f"잔여: {int(row['잔여']):,}면"
            ],
            hoverinfo="text", showlegend=False,
        ))
        # 선택 강조 링
        if is_sel:
            fig.add_trace(go.Scattermapbox(
                lat=[row["lat"]], lon=[row["lon"]],
                mode="markers",
                marker=dict(size=size+18, color="rgba(0,0,0,0)", sizemode="diameter",
                            line=dict(width=2.5, color=color)),
                hoverinfo="skip", showlegend=False,
            ))

    center_lat = GU_COORDS[sel][0] if sel and sel in GU_COORDS else 37.5665
    center_lon = GU_COORDS[sel][1] if sel and sel in GU_COORDS else 126.9780
    zoom = 12.8 if sel else 10.8

    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0),
        height=490,
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#0f1a2e", font_size=12, font_family="Noto Sans KR",
                        bordercolor="rgba(255,255,255,0.15)"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 범례
    st.markdown("""
    <div style="display:flex;gap:16px;flex-wrap:wrap;padding:7px 2px 0;border-top:1px solid rgba(255,255,255,0.07);">
      <span style="font-size:.7rem;color:#5577aa;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#10b981;display:inline-block;"></span>여유 (~40%)</span>
      <span style="font-size:.7rem;color:#5577aa;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#f59e0b;display:inline-block;"></span>보통 (40–70%)</span>
      <span style="font-size:.7rem;color:#5577aa;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#f97316;display:inline-block;"></span>혼잡 (70–90%)</span>
      <span style="font-size:.7rem;color:#5577aa;display:flex;align-items:center;gap:5px;">
        <span style="width:9px;height:9px;border-radius:50%;background:#ef4444;display:inline-block;"></span>포화 (90%+)</span>
      <span style="margin-left:auto;font-size:.63rem;color:#3d5070;">원 크기 = 총 주차면 비례</span>
    </div>
    """, unsafe_allow_html=True)

# ── 상세 패널 ─────────────────────────────────────────────────────────────────
with col_detail:
    if sel:
        row = gu[gu["구"] == sel]
        if not row.empty:
            row = row.iloc[0]
            rate = float(row["가동률"])
            status, color, bgc, tc = cong(rate)

            st.markdown(f"""
            <div class="panel">
              <div class="ph"><div class="pt">📍 지역 상세</div></div>
              <div class="pb">
                <div class="gu-name">{sel}</div>
                <span class="gu-badge" style="background:{bgc};{tc}">{status}</span>
                <div class="gauge-lbl">가동률</div>
                <div class="gauge-bg">
                  <div class="gauge-fill" style="width:{min(rate,100):.1f}%;background:{color};"></div>
                </div>
                <div class="gauge-num">{rate:.1f}%</div>
                <div style="height:10px;"></div>
                <div class="srow"><span class="sk">주차장 수</span><span class="sv">{int(row['주차장수'])}개소</span></div>
                <div class="srow"><span class="sk">총 주차면</span><span class="sv">{int(row['총주차면']):,}면</span></div>
                <div class="srow"><span class="sk">현재 차량</span><span class="sv">{int(row['현재차량']):,}대</span></div>
                <div class="srow"><span class="sk">잔여 면수</span>
                  <span class="sv" style="{tc}">{int(row['잔여']):,}면</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            lots = df[(df["구"] == sel) & (df["총 주차면"] >= 1)].sort_values("가동률", ascending=False)
            st.markdown('<div class="sec">주차장별 현황</div>', unsafe_allow_html=True)
            for _, lot in lots.head(8).iterrows():
                lr = float(lot["가동률"])
                _, lc, _, ltc = cong(lr)
                fee = f"{int(lot['기본 주차 요금'])}원/5분" if lot.get("기본 주차 요금", 0) > 0 else "무료"
                st.markdown(f"""
                <div class="lc">
                  <div class="ln">{lot['주차장명']}</div>
                  <div class="lm">{int(lot['현재 주차 차량수'])}대 / {int(lot['총 주차면'])}면 · {fee}</div>
                  <div class="lb-bg"><div class="lb-fill" style="width:{min(lr,100):.1f}%;background:{lc};"></div></div>
                  <div class="lr" style="{ltc}">{lr:.1f}%</div>
                </div>""", unsafe_allow_html=True)

            if st.button("✕ 선택 해제", key="desel"):
                st.session_state.sel = None
                st.rerun()
    else:
        st.markdown("""
        <div class="panel">
          <div class="ph"><div class="pt">📊 구별 혼잡도 순위</div></div>
          <div class="pb">
        """, unsafe_allow_html=True)
        for _, row in gu.sort_values("가동률", ascending=False).iterrows():
            r = float(row["가동률"])
            _, c, _, _ = cong(r)
            st.markdown(f"""
            <div class="ri">
              <div class="rr"><span class="rn">{row['구']}</span>
                <span class="rv" style="color:{c};">{r:.1f}%</span></div>
              <div class="rb-bg"><div class="rb-fill" style="width:{min(r,100):.1f}%;background:{c};"></div></div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:.65rem;color:#3d5070;margin-top:6px;">상단 버튼을 클릭하면 구별 상세 정보를 볼 수 있습니다.</div>', unsafe_allow_html=True)

# ── 하단 테이블 ───────────────────────────────────────────────────────────────
st.markdown('<div class="sec" style="margin-top:20px;">전체 구별 현황</div>', unsafe_allow_html=True)

disp = gu[["구","주차장수","총주차면","현재차량","잔여","가동률","상태"]].copy()
disp.columns = ["자치구","주차장(개소)","총 주차면","현재 차량","잔여 면수","가동률(%)","상태"]
disp = disp.sort_values("가동률(%)", ascending=False).reset_index(drop=True)
disp.index += 1

st.dataframe(
    disp, use_container_width=True, height=280,
    column_config={
        "가동률(%)": st.column_config.ProgressColumn("가동률(%)", min_value=0, max_value=150, format="%.1f%%"),
        "총 주차면":  st.column_config.NumberColumn(format="%d 면"),
        "현재 차량":  st.column_config.NumberColumn(format="%d 대"),
        "잔여 면수":  st.column_config.NumberColumn(format="%d 면"),
    }
)
