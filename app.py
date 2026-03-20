import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import requests
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# ══════════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Seoul ParkMap",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
  --bg0:#060c18; --bg1:#0b1525; --bg2:#101e32; --bg3:#182840;
  --cyan:#00d4ff; --green:#00e87a; --amber:#ffb300; --red:#ff4554;
  --muted:#3d5470; --text:#b8d0e8; --text2:#6a8aaa;
  --border:rgba(0,212,255,0.10); --border2:rgba(0,212,255,0.20);
  --mono:'JetBrains Mono',monospace;
  --sans:'Noto Sans KR',sans-serif;
}

html, body, [class*="css"], .stApp {
  font-family: var(--sans) !important;
  background: var(--bg0) !important;
  color: var(--text) !important;
}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg1)}
::-webkit-scrollbar-thumb{background:rgba(0,212,255,.15);border-radius:2px}

/* 사이드바 */
[data-testid="stSidebar"]{background:var(--bg1)!important;border-right:1px solid var(--border2)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}
[data-testid="stSidebar"] hr{border-color:var(--border2)!important;margin:10px 0}
[data-testid="stSidebar"] .stRadio label{font-family:var(--mono);font-size:12px;letter-spacing:.5px}

/* 메인 패딩 제거 */
.main .block-container{padding-top:0!important;padding-bottom:40px!important;max-width:100%!important}

/* 헤더 */
.pk-header{
  background:linear-gradient(135deg,var(--bg2) 0%,var(--bg1) 100%);
  border-bottom:1px solid var(--border2);
  padding:14px 28px;
  display:flex;align-items:center;gap:20px;
  margin-bottom:0;
}
.pk-logo{font-family:var(--mono);font-size:18px;font-weight:700;color:var(--cyan);letter-spacing:3px}
.pk-logo span{color:var(--text);font-weight:300}
.pk-sep{width:1px;height:20px;background:var(--border2)}
.pk-live{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;color:var(--green);letter-spacing:1.5px}
.pk-live::before{content:'';width:6px;height:6px;background:var(--green);border-radius:50%;box-shadow:0 0 6px var(--green);animation:blink 1.4s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.pk-time{font-family:var(--mono);font-size:11px;color:var(--muted);margin-left:auto}

/* KPI 띠 */
.kpi-strip{display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid var(--border);background:var(--bg1)}
.kpi-cell{padding:13px 20px;border-right:1px solid var(--border);position:relative;overflow:hidden}
.kpi-cell:last-child{border-right:none}
.kpi-cell::after{content:'';position:absolute;bottom:0;left:0;width:100%;height:2px;background:var(--ac,var(--cyan));transform:scaleX(0);transform-origin:left;transition:transform .3s}
.kpi-cell:hover::after{transform:scaleX(1)}
.kl{font-family:var(--mono);font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px}
.kv{font-family:var(--mono);font-size:20px;font-weight:700;color:var(--text);line-height:1}
.kv span{font-size:10px;font-weight:400;color:var(--text2);margin-left:2px}
.ks{font-size:10px;color:var(--text2);margin-top:2px}

/* 범례 */
.legend-wrap{display:flex;gap:8px;flex-wrap:wrap;padding:10px 0 8px}
.leg{display:flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10px;color:var(--text2);letter-spacing:.5px}
.led{width:8px;height:8px;border-radius:50%;flex-shrink:0}

/* TOP 리스트 */
.top-row{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border)}
.top-row:last-child{border-bottom:none}
.top-n{font-family:var(--mono);font-size:9px;color:var(--muted);width:14px;flex-shrink:0}
.top-nm{font-size:11px;color:var(--text);flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top-bd{font-family:var(--mono);font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;flex-shrink:0}

/* 구별 바 */
.gbar-row{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.gbar-lb{font-size:10px;color:var(--text2);width:54px;text-align:right;flex-shrink:0}
.gbar-tr{flex:1;height:4px;background:var(--bg3);border-radius:2px;overflow:hidden}
.gbar-fl{height:100%;border-radius:2px}
.gbar-vl{font-family:var(--mono);font-size:9px;width:30px;text-align:right;flex-shrink:0}

/* 카드 */
.card{background:var(--bg2);border:1px solid var(--border2);border-radius:10px;padding:16px 18px;margin-bottom:14px}
.card-title{font-family:var(--mono);font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}

/* 메트릭 */
[data-testid="stMetric"]{background:var(--bg2);border:1px solid var(--border2);border-radius:8px;padding:10px 14px}
[data-testid="stMetricLabel"] p{font-family:var(--mono)!important;font-size:9px!important;color:var(--muted)!important;letter-spacing:1px}
[data-testid="stMetricValue"]{font-family:var(--mono)!important;font-size:18px!important;color:var(--text)!important}

/* 데이터프레임 */
[data-testid="stDataFrame"] thead th{background:var(--bg3)!important;color:var(--text2)!important;font-family:var(--mono)!important;font-size:10px!important;letter-spacing:.8px}

/* 버튼 */
.stButton>button{background:transparent!important;border:1px solid var(--border2)!important;color:var(--cyan)!important;border-radius:8px!important;font-family:var(--mono)!important;font-size:10px!important;letter-spacing:1px!important}
.stButton>button:hover{background:rgba(0,212,255,.08)!important;border-color:var(--cyan)!important}
.stDownloadButton>button{background:transparent!important;border:1px solid var(--border)!important;color:var(--text2)!important;font-size:11px!important;border-radius:6px!important}

/* 탭 */
[data-baseweb="tab-list"]{background:var(--bg2)!important;border-radius:8px!important;padding:2px!important;gap:2px!important}
[data-baseweb="tab"]{color:var(--muted)!important;border-radius:6px!important;font-family:var(--mono)!important;font-size:11px!important}
[aria-selected="true"][data-baseweb="tab"]{background:var(--bg3)!important;color:var(--cyan)!important}

/* 인풋 */
.stTextInput input{background:var(--bg2)!important;border:1px solid var(--border2)!important;border-radius:8px!important;color:var(--text)!important;font-family:var(--sans)!important}
.stTextInput input:focus{border-color:var(--cyan)!important;box-shadow:0 0 0 2px rgba(0,212,255,.1)!important}
[data-baseweb="select"] div{background:var(--bg2)!important;border-color:var(--border2)!important;color:var(--text)!important}

/* 사이드바 라디오 */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label{
  padding:8px 12px;border-radius:8px;margin-bottom:2px;display:flex;align-items:center;gap:8px;
  transition:background .15s;cursor:pointer;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover{background:rgba(0,212,255,.06)}

/* 알림 */
[data-testid="stAlert"]{background:rgba(255,179,0,.05)!important;border:1px solid rgba(255,179,0,.2)!important;border-radius:8px!important}

/* 반응형 */
@media(max-width:900px){.kpi-strip{grid-template-columns:repeat(2,1fr)}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════
try:
    API_KEY = st.secrets["SEOUL_API_KEY"]
except Exception:
    API_KEY = "584a546d737470643333744569725a"

BASE_URL = "http://openAPI.seoul.go.kr:8088"

GU_COORDS = {
    '강남구':(37.5172,127.0473),'강동구':(37.5301,127.1238),'강북구':(37.6396,127.0255),
    '강서구':(37.5509,126.8495),'관악구':(37.4784,126.9516),'광진구':(37.5385,127.0823),
    '구로구':(37.4954,126.8874),'금천구':(37.4602,126.9002),'노원구':(37.6542,127.0568),
    '도봉구':(37.6688,127.0471),'동대문구':(37.5744,127.0396),'동작구':(37.5124,126.9393),
    '마포구':(37.5663,126.9014),'서대문구':(37.5791,126.9368),'서초구':(37.4837,127.0324),
    '성동구':(37.5633,127.0365),'성북구':(37.5894,127.0167),'송파구':(37.5145,127.1059),
    '양천구':(37.5172,126.8664),'영등포구':(37.5264,126.8963),'용산구':(37.5324,126.9906),
    '은평구':(37.6026,126.9291),'종로구':(37.5735,126.9788),'중구':(37.5640,126.9975),
    '중랑구':(37.6063,127.0927),
}

COMMON_MAP = {
    "ADDR":"주소","PKLT_CD":"주차장코드","PKLT_NM":"주차장명",
    "PKLT_TYPE":"주차장 종류","PRK_TYPE_NM":"주차장 종류명",
    "PKLT_KND":"주차장 종류","PKLT_KND_NM":"주차장 종류명",
    "OPER_SE":"운영구분","OPER_SE_NM":"운영구분명","TELNO":"전화번호",
    "TPKCT":"총 주차면","CAPACITY":"총 주차면",
    "NOW_PRK_VHCL_CNT":"현재 주차 차량수","NOW_PRK_VHCL_UPDT_TM":"현재 주차 차량수 업데이트시간",
    "CUR_PARKING":"현재 주차 차량수","CUR_PARKING_TIME":"현재 주차 차량수 업데이트시간",
    "PAY_YN":"유무료구분","PAY_YN_NM":"유무료구분명",
    "CHGD_FREE_SE":"유무료구분","CHGD_FREE_NM":"유무료구분명",
    "PRK_STTS_YN":"유무료구분","PRK_STTS_NM":"유무료구분명",
    "NGHT_PAY_YN":"야간무료개방여부","NGHT_PAY_YN_NM":"야간무료개방여부명",
    "NGHT_FREE_OPN_YN":"야간무료개방여부","NGHT_FREE_OPN_YN_NAME":"야간무료개방여부명",
    "WD_OPER_BGNG_TM":"평일 운영 시작시각(HHMM)","WD_OPER_END_TM":"평일 운영 종료시각(HHMM)",
    "WE_OPER_BGNG_TM":"주말 운영 시작시각(HHMM)","WE_OPER_END_TM":"주말 운영 종료시각(HHMM)",
    "LHLDY_OPER_BGNG_TM":"공휴일 운영 시작시각(HHMM)","LHLDY_OPER_END_TM":"공휴일 운영 종료시각(HHMM)",
    "LHLDY_BGNG":"공휴일 운영 시작시각(HHMM)","LHLDY":"공휴일 운영 종료시각(HHMM)",
    "LAST_DATA_SYNC_TM":"최종데이터 동기화 시간",
    "SAT_CHGD_FREE_SE":"토요일 유,무료 구분","SAT_CHGD_FREE_NM":"토요일 유,무료 구분명",
    "LHLDY_CHGD_FREE_SE":"공휴일 유,무료 구분","LHLDY_CHGD_FREE_SE_NAME":"공휴일 유,무료 구분명",
    "LHLDY_YN":"공휴일 유,무료 구분","LHLDY_NM":"공휴일 유,무료 구분명",
    "BSC_PRK_CRG":"기본 주차 요금","BSC_PRK_HR":"기본 주차 시간(분 단위)",
    "ADD_PRK_CRG":"추가 단위 요금","ADD_PRK_HR":"추가 단위 시간(분 단위)",
    "ADD_CRG":"추가 단위 요금","ADD_UNIT_TM_MNT":"추가 단위 시간(분 단위)",
    "PRK_CRG":"기본 주차 요금","PRK_HM":"기본 주차 시간(분 단위)",
    "BUS_BSC_PRK_CRG":"버스 기본 주차 요금","BUS_BSC_PRK_HR":"버스 기본 주차 시간(분 단위)",
    "BUS_ADD_PRK_HR":"버스 추가 단위 시간(분 단위)","BUS_ADD_PRK_CRG":"버스 추가 단위 요금",
    "BUS_PRK_CRG":"버스 기본 주차 요금","BUS_PRK_HM":"버스 기본 주차 시간(분 단위)",
    "BUS_PRK_ADD_HM":"버스 추가 단위 시간(분 단위)","BUS_PRK_ADD_CRG":"버스 추가 단위 요금",
    "DAY_MAX_CRG":"일 최대 요금","DLY_MAX_CRG":"일 최대 요금",
    "PRD_AMT":"월 정기권 금액","MNTL_CMUT_CRG":"월 정기권 금액",
    "STRT_PKLT_MNG_NO":"노상 주차장 관리그룹번호","CRB_PKLT_MNG_GROUP_NO":"노상 주차장 관리그룹번호",
    "SHRN_PKLT_MNG_NM":"공유 주차장 관리업체명","SHRN_PKLT_MNG_URL":"공유 주차장 관리업체 링크",
    "SHRN_PKLT_YN":"공유 주차장 여부","SHRN_PKLT_ETC":"공유 주차장 기타사항",
    "LAT":"위도","LOT":"경도",
}


# ══════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════
def fetch_all(service, total_hint=3000):
    rows, start = [], 1
    while True:
        end = start + 999
        url = f"{BASE_URL}/{API_KEY}/json/{service}/{start}/{end}/"
        try:
            data = requests.get(url, timeout=15).json()
        except Exception as e:
            st.warning(f"API 오류 ({service}): {e}"); break
        if "RESULT" in data:
            if data["RESULT"].get("CODE") != "INFO-000":
                st.warning(f"API: {data['RESULT'].get('MESSAGE','')}")
            break
        svc = data.get(service, {})
        rows.extend(svc.get("row", []))
        if end >= svc.get("list_total_count", 0): break
        start += 1000
    return rows


# ══════════════════════════════════════════════════════
# 데이터 로드 (5분 캐시)
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M (KST)")

    info_rows = fetch_all("GetParkInfo", 3000)
    if not info_rows: st.error("공영주차장 API 실패"); st.stop()
    info = pd.DataFrame(info_rows).rename(columns=COMMON_MAP)

    rt_rows = fetch_all("GetParkingInfo", 300)
    if not rt_rows: st.error("실시간 API 실패"); st.stop()
    rt = pd.DataFrame(rt_rows).rename(columns=COMMON_MAP)

    if "주차장코드" not in info.columns: info["주차장코드"] = info.get("주차장명", "")
    if "주차장코드" not in rt.columns:   rt["주차장코드"]   = rt.get("주차장명", "")

    for req in ["주소", "총 주차면"]:
        if req not in info.columns:
            st.error(f"GetParkInfo '{req}' 없음. 컬럼: {info.columns.tolist()}"); st.stop()
    for req in ["주소", "총 주차면", "현재 주차 차량수"]:
        if req not in rt.columns:
            st.error(f"GetParkingInfo '{req}' 없음. 컬럼: {rt.columns.tolist()}"); st.stop()

    info["구"] = info["주소"].str.extract(r"([\w]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([\w]+구)")

    # 숫자 변환
    for col in ["총 주차면","기본 주차 요금","일 최대 요금","월 정기권 금액","위도","경도"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce")
    for col in ["기본 주차 요금","일 최대 요금","월 정기권 금액"]:
        if col in info.columns: info[col] = info[col].fillna(0)
    if "총 주차면" in info.columns: info["총 주차면"] = info["총 주차면"].fillna(0)

    for col in ["총 주차면","현재 주차 차량수","기본 주차 요금","일 최대 요금"]:
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    rt = rt[rt["총 주차면"] > 10].copy()
    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0, 100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)
    rt["혼잡도"] = pd.cut(rt["이용률"], bins=[-1,30,70,95,100],
                          labels=["여유","보통","혼잡","만차"]).astype(str)

    # 위경도 조인
    coord_map = info.dropna(subset=["위도","경도"])[["주차장코드","위도","경도"]]
    rt = rt.merge(coord_map, on="주차장코드", how="left")
    rng = np.random.default_rng(42)
    for idx, row in rt[rt["위도"].isna()].iterrows():
        gu = row["구"]
        if gu in GU_COORDS:
            b = GU_COORDS[gu]
            rt.at[idx,"위도"] = b[0] + rng.uniform(-0.018, 0.018)
            rt.at[idx,"경도"] = b[1] + rng.uniform(-0.018, 0.018)
        else:
            rt.at[idx,"위도"], rt.at[idx,"경도"] = 37.5665, 126.9780

    # 운영시간
    def fmt_t(v):
        try: v=int(float(v)); return f"{v//100:02d}:{v%100:02d}"
        except: return "-"

    for df in [rt, info]:
        if "평일 운영 시작시각(HHMM)" in df.columns:
            df["평일운영"] = df.apply(
                lambda r: f"{fmt_t(r.get('평일 운영 시작시각(HHMM)',0))} ~ {fmt_t(r.get('평일 운영 종료시각(HHMM)',2400))}",
                axis=1)
        else:
            df["평일운영"] = "-"

    # 구별 집계
    gu_rt = rt.groupby("구").agg(
        주차장수=("주차장코드","count"),
        총주차면=("총 주차면","sum"),
        현재차량=("현재 주차 차량수","sum"),
        가용면=("가용면","sum")
    ).reset_index()
    gu_rt["이용률"] = (gu_rt["현재차량"] / gu_rt["총주차면"] * 100).round(1)

    gu_info = info.groupby("구").agg(
        전체주차장수=("주차장코드","count"),
        전체주차면=("총 주차면","sum")
    ).reset_index()

    return info, rt, gu_rt, gu_info, now


# ══════════════════════════════════════════════════════
# 색상 / 스타일
# ══════════════════════════════════════════════════════
def sc(rate):
    if rate >= 95: return "#ff4554", "만차"
    if rate >= 70: return "#ffb300", "혼잡"
    if rate >= 30: return "#00d4ff", "보통"
    return "#00e87a", "여유"

def color_util(val):
    try: v = float(val)
    except: return ""
    if v >= 95: return "background:#3a0c10;color:#ff4554;"
    if v >= 70: return "background:#2a1e00;color:#ffb300;"
    if v >= 30: return "background:#001f2e;color:#00d4ff;"
    return "background:#002a1a;color:#00e87a;"

def style_util(df, col="이용률(%)"):
    s = pd.DataFrame("", index=df.index, columns=df.columns)
    if col in df.columns: s[col] = df[col].map(color_util)
    return s

PLOT_CFG = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(11,21,37,0.7)",
    font=dict(family="JetBrains Mono, monospace", size=11, color="#3d5470"),
    margin=dict(l=8, r=12, t=30, b=8),
)


# ══════════════════════════════════════════════════════
# 지도 생성
# ══════════════════════════════════════════════════════
def make_map(rt_df, show_clusters, sel_gu):
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11,
                   tiles="CartoDB dark_matter", control_scale=True)
    MiniMap(tile_layer="CartoDB dark_matter", position="bottomright",
            width=110, height=80).add_to(m)

    df = rt_df[rt_df["구"].isin(sel_gu)] if sel_gu else rt_df.copy()

    if show_clusters:
        cluster = MarkerCluster(options={"maxClusterRadius":60,"disableClusteringAtZoom":14})
        cluster.add_to(m)
        rt_target = cluster
    else:
        rt_target = m

    # 실시간 핀
    for _, row in df.iterrows():
        try: lat, lng = float(row["위도"]), float(row["경도"])
        except: continue

        rate  = float(row.get("이용률", 0))
        avail = int(row.get("가용면", 0))
        total = int(row.get("총 주차면", 0))
        curr  = int(row.get("현재 주차 차량수", 0))
        color, status = sc(rate)
        fee   = int(row.get("기본 주차 요금", 0))
        mfee  = int(row.get("일 최대 요금", 0))
        name  = str(row.get("주차장명", ""))
        addr  = str(row.get("주소", ""))
        paid  = str(row.get("유무료구분명", "-"))
        phone = str(row.get("전화번호", "-"))
        kind  = str(row.get("주차장 종류명", "-"))
        ops   = str(row.get("평일운영", "-"))
        upd   = str(row.get("현재 주차 차량수 업데이트시간", ""))[:16]
        bw    = min(int(rate), 100)

        popup_html = f"""
<div style="font-family:'Noto Sans KR',sans-serif;width:268px;background:#060c18;
  border:1px solid {color}44;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.6);">
  <div style="background:linear-gradient(135deg,{color}18 0%,#060c18 100%);
    border-bottom:1px solid {color}33;padding:13px 15px;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
      <div style="flex:1;min-width:0;">
        <div style="font-size:13px;font-weight:600;color:#b8d0e8;
          white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
        <div style="font-size:10px;color:#3d5470;margin-top:2px;">{addr}</div>
      </div>
      <div style="margin-left:10px;text-align:right;flex-shrink:0;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:22px;
          font-weight:700;color:{color};line-height:1;">{rate:.0f}%</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
          color:{color};letter-spacing:1px;">{status}</div>
      </div>
    </div>
    <div style="background:rgba(0,0,0,.3);border-radius:3px;height:4px;overflow:hidden;">
      <div style="width:{bw}%;height:100%;background:{color};
        box-shadow:0 0 6px {color};border-radius:3px;"></div>
    </div>
  </div>
  <div style="padding:12px 15px;">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:12px;">
      <div style="background:#0b1525;border:1px solid #182840;border-radius:6px;
        padding:7px;text-align:center;">
        <div style="font-size:8px;color:#3d5470;letter-spacing:1px;margin-bottom:2px;">전체</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:15px;
          font-weight:700;color:#6a8aaa;">{total}</div>
      </div>
      <div style="background:#0b1525;border:1px solid #182840;border-radius:6px;
        padding:7px;text-align:center;">
        <div style="font-size:8px;color:#3d5470;letter-spacing:1px;margin-bottom:2px;">현재</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:15px;
          font-weight:700;color:{color};">{curr}</div>
      </div>
      <div style="background:#0b1525;border:1px solid #182840;border-radius:6px;
        padding:7px;text-align:center;">
        <div style="font-size:8px;color:#3d5470;letter-spacing:1px;margin-bottom:2px;">가용</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:15px;
          font-weight:700;color:#00e87a;">{avail}</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:60px 1fr;gap:3px 8px;
      font-size:11px;align-items:center;">
      <span style="color:#3d5470;">⏰ 운영</span>
      <span style="color:#6a8aaa;">{ops}</span>
      <span style="color:#3d5470;">💰 기본</span>
      <span style="color:#6a8aaa;">{f"{fee:,}원/5분" if fee>0 else "무료"}</span>
      <span style="color:#3d5470;">📅 최대</span>
      <span style="color:#6a8aaa;">{f"{mfee:,}원" if mfee>0 else "-"}</span>
      <span style="color:#3d5470;">📞 전화</span>
      <span style="color:#6a8aaa;">{phone if phone not in ("nan","") else "-"}</span>
    </div>
    <div style="margin-top:10px;padding-top:8px;border-top:1px solid #182840;
      display:flex;gap:5px;flex-wrap:wrap;align-items:center;">
      <span style="background:{color}18;color:{color};border:1px solid {color}33;
        border-radius:4px;padding:2px 7px;font-family:'JetBrains Mono',monospace;
        font-size:8px;letter-spacing:1px;">{status}</span>
      <span style="background:#0b1525;color:#3d5470;border:1px solid #182840;
        border-radius:4px;padding:2px 7px;font-size:9px;">{kind}</span>
      <span style="background:#0b1525;color:#3d5470;border:1px solid #182840;
        border-radius:4px;padding:2px 7px;font-size:9px;">{paid}</span>
      <span style="margin-left:auto;font-family:'JetBrains Mono',monospace;
        font-size:8px;color:#1f3048;">{upd}</span>
    </div>
  </div>
</div>"""

        icon_html = f"""
<div style="position:relative;width:34px;height:34px;">
  <div style="position:absolute;inset:0;background:{color};
    border-radius:50% 50% 50% 0;transform:rotate(-45deg);
    border:2px solid rgba(255,255,255,.15);
    box-shadow:0 0 10px {color}88,0 2px 8px rgba(0,0,0,.7);"></div>
  <div style="position:absolute;inset:0;display:flex;
    align-items:center;justify-content:center;">
    <span style="font-family:'JetBrains Mono',monospace;font-weight:700;
      font-size:11px;color:#060c18;transform:translateY(-2px);">
      {"P" if avail > 0 else "×"}
    </span>
  </div>
</div>"""

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"<b>{name}</b><br><span style='color:{color}'>{rate:.0f}%</span> | 가용 {avail}면",
            icon=folium.DivIcon(html=icon_html, icon_size=(34,34), icon_anchor=(17,34)),
        ).add_to(rt_target)


    return m


# ══════════════════════════════════════════════════════
# 데이터 로드 실행
# ══════════════════════════════════════════════════════
with st.spinner("🔄 서울시 실시간 주차 데이터 수신 중..."):
    info, rt, gu_rt, gu_info, last_updated = load_data()

GU_LIST = sorted(info["구"].dropna().unique().tolist())


# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;">
      <div style="font-size:16px;font-weight:700;color:#00d4ff;letter-spacing:3px;margin-bottom:2px;">
        PARKMAP
      </div>
      <div style="font-size:9px;color:#3d5470;letter-spacing:1px;">SEOUL REALTIME</div>
      <div style="font-size:10px;color:#3d5470;margin-top:6px;">{last_updated}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 데이터 새로고침", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.markdown("---")

    # ★ st.radio — 안정적인 페이지 전환 (st.button 대신)
    page = st.radio(
        "화면 선택",
        ["🗺️  실시간 지도", "📊  통계 대시보드", "📋  주차장 목록"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:#3d5470;letter-spacing:2px;margin-bottom:8px;">FILTER</div>', unsafe_allow_html=True)
    sel_gu     = st.multiselect("자치구",  GU_LIST,              placeholder="전체")
    sel_status = st.multiselect("혼잡도",  ["여유","보통","혼잡","만차"], placeholder="전체")
    sel_fee    = []  # 유무료 필터 제거

    if "🗺️" in page:
        st.markdown("---")
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:#3d5470;letter-spacing:2px;margin-bottom:8px;">MAP</div>', unsafe_allow_html=True)
        show_clusters = st.toggle("마커 클러스터링", value=True)
    else:
        show_clusters = True

    st.markdown("---")
    st.caption("서울 열린데이터 광장 · 5분 자동 갱신")


# ══════════════════════════════════════════════════════
# 필터 함수
# ══════════════════════════════════════════════════════
def filt(df):
    d = df.copy()
    if sel_gu     and "구"           in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_fee    and "유무료구분명" in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    if sel_status and "혼잡도"       in d.columns: d = d[d["혼잡도"].isin(sel_status)]
    return d

fi = filt(info)
fr = filt(rt)

rt_spots = int(fr["총 주차면"].sum())
rt_curr  = int(fr["현재 주차 차량수"].sum())
rt_avail = int(fr["가용면"].sum())
rt_rate  = round(rt_curr / rt_spots * 100, 1) if rt_spots > 0 else 0
rt_color, rt_status = sc(rt_rate)
avail_color = "#00e87a" if rt_avail > 500 else "#ffb300" if rt_avail > 100 else "#ff4554"
full_cnt = int((fr["이용률"] >= 95).sum())
free_cnt = int((fr["이용률"] < 30).sum())


# ══════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div class="pk-header">
  <div class="pk-logo">SEOUL<span> PARKMAP</span></div>
  <div class="pk-sep"></div>
  <div class="pk-live">LIVE</div>
  <div class="pk-sep"></div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#3d5470;">
    실시간 <b style="color:#00d4ff">{len(fr)}</b>개소 연계 &nbsp;|&nbsp;
    전체 <b style="color:#6a8aaa">{len(fi):,}</b>개소
  </div>
  <div class="pk-time">{last_updated}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# KPI 띠
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-cell" style="--ac:#00d4ff">
    <div class="kl">공영주차장</div>
    <div class="kv">{len(fi):,}<span>개소</span></div>
    <div class="ks">서울시 전체</div>
  </div>
  <div class="kpi-cell" style="--ac:{avail_color}">
    <div class="kl">현재 가용</div>
    <div class="kv" style="color:{avail_color}">{rt_avail:,}<span>면</span></div>
    <div class="ks">즉시 주차 가능</div>
  </div>
  <div class="kpi-cell" style="--ac:{rt_color}">
    <div class="kl">전체 이용률</div>
    <div class="kv" style="color:{rt_color}">{rt_rate}<span>%</span></div>
    <div class="ks">{rt_status} · 실시간 기준</div>
  </div>
  <div class="kpi-cell" style="--ac:#ff4554">
    <div class="kl">만차</div>
    <div class="kv" style="color:#ff4554">{full_cnt}<span>개소</span></div>
    <div class="ks">이용률 95% 이상</div>
  </div>
  <div class="kpi-cell" style="--ac:#00e87a">
    <div class="kl">여유</div>
    <div class="kv" style="color:#00e87a">{free_cnt}<span>개소</span></div>
    <div class="ks">이용률 30% 미만</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="padding:0 24px">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ① 실시간 지도
# ══════════════════════════════════════════════════════
if "🗺️" in page:
    # 범례
    st.markdown("""
    <div class="legend-wrap">
      <div class="leg"><div class="led" style="background:#00e87a;box-shadow:0 0 4px #00e87a55"></div>여유 &lt;30%</div>
      <div class="leg"><div class="led" style="background:#00d4ff;box-shadow:0 0 4px #00d4ff55"></div>보통 30~70%</div>
      <div class="leg"><div class="led" style="background:#ffb300;box-shadow:0 0 4px #ffb30055"></div>혼잡 70~95%</div>
      <div class="leg"><div class="led" style="background:#ff4554;box-shadow:0 0 4px #ff455455"></div>만차 95%+</div>
      <div class="leg"><div class="led" style="background:#182840"></div>실시간 미연계</div>
      <div class="leg" style="margin-left:auto;color:#1f3048">📍 핀 클릭 → 상세정보</div>
    </div>
    """, unsafe_allow_html=True)

    map_col, side_col = st.columns([3, 1])

    with map_col:
        m = make_map(fr, show_clusters, sel_gu)
        st_folium(m, width="100%", height=580, returned_objects=[], key="pk_map")

    with side_col:
        # 구별 이용률 바
        f_gu = (gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy())
        f_gu_s = f_gu.sort_values("이용률", ascending=False)

        bars = ""
        for _, r in f_gu_s.iterrows():
            v = float(r["이용률"])
            c, _ = sc(v)
            w = min(v, 100)
            bars += f"""
<div class="gbar-row">
  <div class="gbar-lb">{r['구']}</div>
  <div class="gbar-tr"><div class="gbar-fl" style="width:{w}%;background:{c};box-shadow:0 0 4px {c}44"></div></div>
  <div class="gbar-vl" style="color:{c}">{v:.0f}%</div>
</div>"""

        st.markdown(f'<div class="card" style="margin-bottom:12px"><div class="card-title">구별 이용률</div>{bars}</div>',
                    unsafe_allow_html=True)

        # 혼잡 TOP5
        top5 = fr.nlargest(5, "이용률")
        tops = ""
        for i, (_, r) in enumerate(top5.iterrows(), 1):
            v = float(r["이용률"])
            c, s = sc(v)
            tops += f"""<div class="top-row">
  <div class="top-n">{i:02d}</div>
  <div class="top-nm">{r['주차장명']}</div>
  <div class="top-bd" style="background:{c}18;color:{c};border:1px solid {c}33">{v:.0f}%</div>
</div>"""
        st.markdown(f'<div class="card" style="margin-bottom:12px"><div class="card-title">🔴 혼잡 TOP 5</div>{tops}</div>',
                    unsafe_allow_html=True)

        # 여유 TOP5
        free5 = fr[fr["이용률"] < 100].nsmallest(5, "이용률")
        frees = ""
        for i, (_, r) in enumerate(free5.iterrows(), 1):
            v = float(r["이용률"])
            c, _ = sc(v)
            frees += f"""<div class="top-row">
  <div class="top-n">{i:02d}</div>
  <div class="top-nm">{r['주차장명']}</div>
  <div class="top-bd" style="background:{c}18;color:{c};border:1px solid {c}33">{int(r['가용면'])}면</div>
</div>"""
        st.markdown(f'<div class="card"><div class="card-title">🟢 여유 TOP 5</div>{frees}</div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ② 통계 대시보드
# ══════════════════════════════════════════════════════
elif "📊" in page:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">혼잡도 분포</div>', unsafe_allow_html=True)
        cnt = fr["혼잡도"].value_counts().reindex(["여유","보통","혼잡","만차"], fill_value=0)
        fig = go.Figure(go.Bar(
            x=cnt.index, y=cnt.values,
            marker_color=["#00e87a","#00d4ff","#ffb300","#ff4554"],
            marker_line_width=0,
            text=cnt.values, textposition="outside",
            textfont=dict(color="#6a8aaa", family="JetBrains Mono"),
        ))
        fig.update_layout(**PLOT_CFG, height=240, showlegend=False,
                          xaxis=dict(tickfont=dict(color="#6a8aaa",size=11),gridcolor="rgba(0,212,255,.04)"),
                          yaxis=dict(gridcolor="rgba(0,212,255,.04)",zeroline=False,showticklabels=False))
        fig.update_traces(width=0.5)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">주차장 종류 비율</div>', unsafe_allow_html=True)
        vc = fi["주차장 종류명"].value_counts() if "주차장 종류명" in fi.columns else pd.Series(dtype=int)
        fig2 = go.Figure(go.Pie(
            labels=vc.index, values=vc.values, hole=0.58,
            marker=dict(colors=["#00d4ff","#00e87a","#ffb300","#ff4554","#6a8aaa"],
                        line=dict(color="#060c18", width=2)),
            textinfo="percent", textfont=dict(family="JetBrains Mono", size=10, color="#b8d0e8"),
        ))
        fig2.update_layout(**PLOT_CFG, height=240,
                           legend=dict(font=dict(family="JetBrains Mono",size=10,color="#6a8aaa"),
                                       bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    # 구별 종합 테이블
    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"]/r["총주차면"]*100,1) if r["총주차면"]>0 else 0.0, axis=1)
    if sel_gu: merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("실시간이용률", ascending=False)
    disp = merged[["구","전체주차장수","전체주차면","주차장수","총주차면","현재차량","가용면","실시간이용률"]].copy()
    disp.columns = ["자치구","전체 주차장","전체 주차면","실시간 연계","연계 주차면","현재 차량","가용 면수","이용률(%)"]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">자치구별 종합 현황</div>', unsafe_allow_html=True)
    st.dataframe(
        disp.style.apply(style_util, axis=None)
            .format({"전체 주차장":"{:,.0f}","전체 주차면":"{:,.0f}","실시간 연계":"{:,.0f}",
                     "연계 주차면":"{:,.0f}","현재 차량":"{:,.0f}","가용 면수":"{:,.0f}","이용률(%)":"{:.1f}"}),
        use_container_width=True, height=400, hide_index=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">구별 전체 주차면</div>', unsafe_allow_html=True)
        srt = disp.sort_values("전체 주차면", ascending=True)
        fig3 = go.Figure(go.Bar(
            x=srt["전체 주차면"], y=srt["자치구"], orientation="h",
            marker=dict(color=srt["전체 주차면"],
                        colorscale=[[0,"#0b1525"],[1,"#00d4ff"]]),
            marker_line_width=0,
            text=srt["전체 주차면"].map(lambda v: f"{int(v):,}"),
            textposition="outside", textfont=dict(size=9,color="#3d5470",family="JetBrains Mono"),
        ))
        fig3.update_layout(**PLOT_CFG, height=max(300, len(srt)*22+40),
                           xaxis=dict(gridcolor="rgba(0,212,255,.04)",showticklabels=False,zeroline=False),
                           yaxis=dict(tickfont=dict(size=10,color="#6a8aaa"),gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">구별 실시간 이용률</div>', unsafe_allow_html=True)
        srt2 = disp.sort_values("이용률(%)", ascending=True)
        fig4 = go.Figure(go.Bar(
            x=srt2["이용률(%)"], y=srt2["자치구"], orientation="h",
            marker_color=[sc(v)[0] for v in srt2["이용률(%)"]],
            marker_line_width=0,
            text=srt2["이용률(%)"].map(lambda v: f"{v:.1f}%"),
            textposition="outside", textfont=dict(size=9,color="#3d5470",family="JetBrains Mono"),
        ))
        fig4.update_layout(**PLOT_CFG, height=max(300, len(srt2)*22+40),
                           xaxis=dict(range=[0,115],gridcolor="rgba(0,212,255,.04)",
                                      showticklabels=False,zeroline=False),
                           yaxis=dict(tickfont=dict(size=10,color="#6a8aaa"),gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ③ 주차장 목록
# ══════════════════════════════════════════════════════
elif "📋" in page:
    tab1, tab2 = st.tabs(["  🔴  실시간 현황  ","  📁  전체 공영주차장  "])

    with tab1:
        fr2 = filt(rt)
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            srch = st.text_input("", placeholder="🔍 주차장명 검색...", label_visibility="collapsed")
            if srch: fr2 = fr2[fr2["주차장명"].str.contains(srch, na=False)]
        with c2:
            sopt = st.selectbox("", ["이용률 높은 순","이용률 낮은 순","가용면 많은 순","가용면 적은 순"],
                                label_visibility="collapsed")
        with c3:
            st.download_button("↓ CSV", fr2.to_csv(index=False, encoding="utf-8-sig"),
                               file_name="실시간_주차현황.csv", mime="text/csv", use_container_width=True)

        sm = {"이용률 높은 순":("이용률",False),"이용률 낮은 순":("이용률",True),
              "가용면 많은 순":("가용면",False),"가용면 적은 순":("가용면",True)}
        sc_col, asc_v = sm[sopt]
        fr2 = fr2.sort_values(by=sc_col, ascending=asc_v)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("조회",     f"{len(fr2)}개소")
        mc2.metric("총 주차면", f"{int(fr2['총 주차면'].sum()):,}면")
        mc3.metric("현재 차량", f"{int(fr2['현재 주차 차량수'].sum()):,}대")
        mc4.metric("가용면",   f"{int(fr2['가용면'].sum()):,}면")

        cols_want = [
            ("구","구"),("주차장명","주차장명"),("주소","주소"),
            ("총 주차면","전체"),("현재 주차 차량수","현재"),("가용면","가용"),
            ("이용률","이용률(%)"),("혼잡도","혼잡도"),
            ("기본 주차 요금","기본요금(원)"),("일 최대 요금","일최대(원)"),
            ("평일운영","평일운영"),("현재 주차 차량수 업데이트시간","업데이트"),
        ]
        cols_use = [c for c,_ in cols_want if c in fr2.columns]
        cols_ren = [r for c,r in cols_want if c in fr2.columns]
        missing  = [c for c,_ in cols_want if c not in fr2.columns]
        if missing: st.caption(f"미포함: {missing}")

        disp_rt = fr2[cols_use].copy()
        disp_rt.columns = cols_ren
        fmt = {k:v for k,v in {"전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}",
                                "이용률(%)":"{:.1f}","기본요금(원)":"{:,.0f}","일최대(원)":"{:,.0f}"
                               }.items() if k in disp_rt.columns}
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.dataframe(
            disp_rt.style.apply(style_util, axis=None).format(fmt),
            use_container_width=True, height=520, hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        fi2 = filt(info)
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            srch2 = st.text_input("", placeholder="🔍 주차장명 검색...",
                                  label_visibility="collapsed", key="s2")
            if srch2: fi2 = fi2[fi2["주차장명"].str.contains(srch2, na=False)]
        with c2:
            sopt2 = st.selectbox("", ["주차면 많은 순","기본요금 낮은 순","기본요금 높은 순"],
                                 label_visibility="collapsed", key="so2")
        with c3:
            st.download_button("↓ CSV", fi2.to_csv(index=False, encoding="utf-8-sig"),
                               file_name="공영주차장_목록.csv", mime="text/csv", use_container_width=True)

        if sopt2 == "주차면 많은 순":    fi2 = fi2.sort_values("총 주차면", ascending=False)
        elif sopt2 == "기본요금 낮은 순": fi2 = fi2.sort_values("기본 주차 요금")
        else:                            fi2 = fi2.sort_values("기본 주차 요금", ascending=False)

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("조회",     f"{len(fi2):,}개소")
        mc2.metric("총 주차면", f"{int(fi2['총 주차면'].sum()):,}면")
        mc3.metric("유료 비율", f"{round(len(fi2[fi2['유무료구분명']=='유료'])/max(len(fi2),1)*100,1)}%")

        ci = ["구","주차장명","주소","주차장 종류명","운영구분명","총 주차면",
              "유무료구분명","기본 주차 요금","일 최대 요금","월 정기권 금액","전화번호"]
        ci2 = [c for c in ci if c in fi2.columns]
        disp_i = fi2[ci2].copy().rename(columns={
            "주차장 종류명":"종류","운영구분명":"운영구분","유무료구분명":"유무료",
            "기본 주차 요금":"기본요금(원)","일 최대 요금":"일최대(원)","월 정기권 금액":"월정기권(원)"})
        fmt_i = {k:v for k,v in {"총 주차면":"{:,.0f}","기본요금(원)":"{:,.0f}",
                                  "일최대(원)":"{:,.0f}","월정기권(원)":"{:,.0f}"
                                 }.items() if k in disp_i.columns}
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.dataframe(disp_i.style.format(fmt_i),
                     use_container_width=True, height=520, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
