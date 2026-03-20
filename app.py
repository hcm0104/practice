import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
# CSV 경로 탐색 — 언더바 / 띄어쓰기 둘 다 찾음
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent

def find_csv(name_underscore: str) -> Path:
    """
    언더바 버전과 띄어쓰기 버전을 순서대로 탐색해서
    존재하는 파일 경로를 반환. 둘 다 없으면 None 반환.
    """
    name_space = name_underscore.replace("_", " ")
    for name in [name_underscore, name_space]:
        p = BASE_DIR / name
        if p.exists():
            return p
    return None


INFO_CSV = find_csv("서울시_공영주차장_안내_정보.csv")
RT_CSV   = find_csv("서울시_시영주차장_실시간_주차대수_정보.csv")


# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    # 파일 존재 여부 체크
    if INFO_CSV is None:
        st.error(
            "**CSV 파일을 찾을 수 없습니다.**\n\n"
            "아래 두 파일을 `app.py`와 **같은 폴더**에 넣어주세요.\n\n"
            "- `서울시 공영주차장 안내 정보.csv`\n"
            "- `서울시 시영주차장 실시간 주차대수 정보.csv`\n\n"
            f"현재 탐색 경로: `{BASE_DIR}`"
        )
        st.stop()
    if RT_CSV is None:
        st.error(
            "**CSV 파일을 찾을 수 없습니다.**\n\n"
            "`서울시 시영주차장 실시간 주차대수 정보.csv` 파일을 "
            "`app.py`와 **같은 폴더**에 넣어주세요.\n\n"
            f"현재 탐색 경로: `{BASE_DIR}`"
        )
        st.stop()

    info = pd.read_csv(INFO_CSV, encoding="euc-kr")
    rt   = pd.read_csv(RT_CSV,   encoding="euc-kr")

    # 구 추출
    info["구"] = info["주소"].str.extract(r"([\w]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([\w]+구)")

    # info 숫자 컬럼 NaN → 0
    for col in ["총 주차면", "기본 주차 요금", "기본 주차 시간(분 단위)",
                "추가 단위 요금", "추가 단위 시간(분 단위)",
                "일 최대 요금", "월 정기권 금액"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce").fillna(0)

    # 이상치 제거 (총 주차면 10 이하)
    rt = rt[rt["총 주차면"] > 10].copy()

    # rt 숫자 컬럼 NaN → 0
    for col in ["기본 주차 요금", "일 최대 요금"]:
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    # 파생 컬럼
    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0, 100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)

    # Categorical → str (Streamlit Arrow 직렬화 오류 방지)
    rt["혼잡도"] = pd.cut(
        rt["이용률"],
        bins=[-1, 30, 70, 95, 100],
        labels=["여유", "보통", "혼잡", "만차"],
    ).astype(str)

    # 구별 집계 — 실시간
    gu_rt = (
        rt.groupby("구")
        .agg(주차장수=("주차장코드", "count"),
             총주차면=("총 주차면",   "sum"),
             현재차량=("현재 주차 차량수", "sum"),
             가용면=("가용면", "sum"))
        .reset_index()
    )
    gu_rt["이용률"] = (gu_rt["현재차량"] / gu_rt["총주차면"] * 100).round(1)

    # 구별 집계 — 전체 공영
    gu_info = (
        info.groupby("구")
        .agg(전체주차장수=("주차장코드", "count"),
             전체주차면=("총 주차면",   "sum"))
        .reset_index()
    )

    return info, rt, gu_rt, gu_info


info, rt, gu_rt, gu_info = load_data()

GU_LIST      = sorted(info["구"].dropna().unique().tolist())
UPDATE_TIME  = rt["현재 주차 차량수 업데이트시간"].iloc[0] if len(rt) > 0 else "-"
STATUS_COLOR = {"여유": "#2ecc71", "보통": "#3498db", "혼잡": "#f39c12", "만차": "#e74c3c"}
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
    view = st.radio(
        "화면",
        ["📊 전체 현황", "🗺️ 구별 현황", "📋 주차장 목록"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**필터**")
    sel_gu   = st.multiselect("자치구",    GU_LIST,                                        placeholder="전체")
    sel_kind = st.multiselect("주차장 종류", info["주차장 종류명"].dropna().unique().tolist(), placeholder="전체")
    sel_fee  = st.multiselect("유무료",    ["유료", "무료"],                                placeholder="전체")
    st.markdown("---")
    st.caption(f"📡 데이터 기준: {UPDATE_TIME[:16]}")
    st.caption("출처: 서울 열린데이터 광장")


def filt(df):
    d = df.copy()
    if sel_gu   and "구"            in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_kind and "주차장 종류명" in d.columns: d = d[d["주차장 종류명"].isin(sel_kind)]
    if sel_fee  and "유무료구분명"  in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    return d


# ─────────────────────────────────────────
# ① 전체 현황
# ─────────────────────────────────────────
if "전체 현황" in view:
    st.markdown('<div class="page-title">📊 서울시 공영주차장 전체 현황</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">실시간 기준: {UPDATE_TIME[:16]} &nbsp;|&nbsp; 총 주차면 10면 이하 이상치 제거</div>', unsafe_allow_html=True)

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


# ─────────────────────────────────────────
# ② 구별 현황
# ─────────────────────────────────────────
elif "구별 현황" in view:
    st.markdown('<div class="page-title">🗺️ 자치구별 주차 현황</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">전체 공영주차장 인프라 및 실시간 이용 현황 비교</div>', unsafe_allow_html=True)

    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"] / r["총주차면"] * 100, 1) if r["총주차면"] > 0 else 0.0,
        axis=1,
    )
    if sel_gu:
        merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("전체주차장수", ascending=False)

    st.markdown("#### 구별 종합 현황 테이블")
    disp = merged[["구", "전체주차장수", "전체주차면", "주차장수", "총주차면", "현재차량", "가용면", "실시간이용률"]].copy()
    disp.columns = ["자치구", "전체 주차장", "전체 주차면", "실시간 연계", "연계 주차면", "현재 차량", "가용 면수", "이용률(%)"]
    st.dataframe(
        disp.style
            .background_gradient(subset=["이용률(%)"], cmap="RdYlGn_r", vmin=0, vmax=100)
            .format({"전체 주차장": "{:,.0f}", "전체 주차면": "{:,.0f}", "실시간 연계": "{:,.0f}",
                     "연계 주차면": "{:,.0f}", "현재 차량": "{:,.0f}", "가용 면수": "{:,.0f}", "이용률(%)": "{:.1f}"}),
        use_container_width=True, height=460, hide_index=True,
    )

    st.markdown("---")
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


# ─────────────────────────────────────────
# ③ 주차장 목록
# ─────────────────────────────────────────
elif "주차장 목록" in view:
    st.markdown('<div class="page-title">📋 주차장 목록 조회</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">실시간 데이터(시영 180개소) + 전체 공영주차장(2,579개소) 통합 조회</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔴 실시간 현황 (180개소)", "📁 전체 공영주차장 (2,579개소)"])

    with tab1:
        fr2 = filt(rt)

        sort_opt = st.selectbox(
            "정렬", ["이용률 높은 순", "이용률 낮은 순", "가용면 많은 순", "가용면 적은 순"], key="s1"
        )
        sm = {
            "이용률 높은 순": ("이용률", False), "이용률 낮은 순": ("이용률", True),
            "가용면 많은 순": ("가용면", False), "가용면 적은 순": ("가용면", True),
        }
        sc, asc = sm[sort_opt]
        fr2 = fr2.sort_values(sc, ascending=asc)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("조회 주차장", f"{len(fr2)}개소")
        c2.metric("총 주차면",   f"{int(fr2['총 주차면'].sum()):,}면")
        c3.metric("현재 차량",   f"{int(fr2['현재 주차 차량수'].sum()):,}대")
        c4.metric("가용 면수",   f"{int(fr2['가용면'].sum()):,}면")

        cols_rt = ["구", "주차장명", "주소", "총 주차면", "현재 주차 차량수",
                   "가용면", "이용률", "혼잡도", "기본 주차 요금", "일 최대 요금"]
        disp_rt = fr2[cols_rt].copy()
        disp_rt.columns = ["구", "주차장명", "주소", "총 주차면", "현재 차량",
                            "가용면", "이용률(%)", "혼잡도", "기본요금(원)", "일최대요금(원)"]

        st.dataframe(
            disp_rt.style
                .background_gradient(subset=["이용률(%)"], cmap="RdYlGn_r", vmin=0, vmax=100)
                .format({"총 주차면": "{:,.0f}", "현재 차량": "{:,.0f}", "가용면": "{:,.0f}",
                         "이용률(%)": "{:.1f}", "기본요금(원)": "{:,.0f}", "일최대요금(원)": "{:,.0f}"}),
            use_container_width=True, height=460, hide_index=True,
        )
        st.download_button(
            "📥 CSV 다운로드",
            disp_rt.to_csv(index=False, encoding="utf-8-sig"),
            file_name="실시간_주차현황.csv", mime="text/csv",
        )

    with tab2:
        fi2 = filt(info)

        search = st.text_input("주차장명 검색", placeholder="예: 세종로, 종로...")
        if search:
            fi2 = fi2[fi2["주차장명"].str.contains(search, na=False)]

        sort_opt2 = st.selectbox("정렬", ["주차면 많은 순", "기본요금 낮은 순", "기본요금 높은 순"], key="s2")
        if sort_opt2 == "주차면 많은 순":
            fi2 = fi2.sort_values("총 주차면", ascending=False)
        elif sort_opt2 == "기본요금 낮은 순":
            fi2 = fi2.sort_values("기본 주차 요금")
        elif sort_opt2 == "기본요금 높은 순":
            fi2 = fi2.sort_values("기본 주차 요금", ascending=False)

        c1, c2, c3 = st.columns(3)
        c1.metric("조회 주차장", f"{len(fi2):,}개소")
        c2.metric("총 주차면",   f"{int(fi2['총 주차면'].sum()):,}면")
        c3.metric("유료 비율",   f"{round(len(fi2[fi2['유무료구분명']=='유료']) / max(len(fi2), 1) * 100, 1)}%")

        cols_info = ["구", "주차장명", "주소", "주차장 종류명", "운영구분명",
                     "총 주차면", "유무료구분명", "기본 주차 요금", "기본 주차 시간(분 단위)",
                     "일 최대 요금", "월 정기권 금액", "전화번호"]
        disp_info = fi2[cols_info].copy()
        disp_info.columns = ["구", "주차장명", "주소", "종류", "운영구분",
                              "총 주차면", "유무료", "기본요금(원)", "기본시간(분)",
                              "일최대요금(원)", "월정기권(원)", "전화번호"]

        st.dataframe(
            disp_info.style.format({
                "총 주차면":      "{:,.0f}",
                "기본요금(원)":   "{:,.0f}",
                "기본시간(분)":   "{:,.0f}",
                "일최대요금(원)": "{:,.0f}",
                "월정기권(원)":   "{:,.0f}",
            }),
            use_container_width=True, height=460, hide_index=True,
        )
        st.download_button(
            "📥 CSV 다운로드",
            disp_info.to_csv(index=False, encoding="utf-8-sig"),
            file_name="공영주차장_전체목록.csv", mime="text/csv",
        )
