import streamlit as st
import google.generativeai as genai
import yfinance as yf
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import json
import uuid
import feedparser
import requests
import re
from datetime import datetime, timedelta

@st.cache_resource
def load_knowledge_base():
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def search_knowledge(query, top_k=4):
    kb = load_knowledge_base()
    if not kb:
        return []
    query_words = {w for w in query.replace(",", " ").replace("?", " ").split() if len(w) >= 2}
    if not query_words:
        return []
    scored = []
    for chunk in kb:
        text = chunk.get("text", "")
        score = sum(1 for w in query_words if w in text)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]

st.set_page_config(
    page_title="나의 주식 비서",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');

html, body, p, span, div, h1, h2, h3, h4, h5, h6,
label, li, td, th, caption, input, textarea, select, button {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif !important;
    letter-spacing: -0.03em !important;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #f1f5f9 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 6px 10px;
    border-radius: 8px;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stInfo"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}

/* ── 페이지 헤더 배너 ── */
.page-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1565c0 60%, #1976d2 100%);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(21,101,192,0.25);
}
.page-header .icon { font-size: 2rem; margin-bottom: 6px; }
.page-header h1 {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff !important;
    margin: 0 0 4px 0;
}
.page-header p {
    font-size: 0.88rem;
    color: rgba(255,255,255,0.75) !important;
    margin: 0;
}

/* ── 콘텐츠 카드 ── */
.tip-box {
    background: linear-gradient(135deg, #eff6ff, #f0f9ff);
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    box-shadow: 0 2px 10px rgba(59,130,246,0.1);
    line-height: 1.7;
}
.strategy-box {
    background: linear-gradient(135deg, #fffbeb, #fff7ed);
    border-left: 4px solid #f59e0b;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    box-shadow: 0 2px 10px rgba(245,158,11,0.12);
    line-height: 1.7;
}

/* ── 메트릭 카드 ── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #3b82f6;
    border-radius: 12px;
    padding: 14px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

/* ── 버튼 ── */
.stButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.15) !important;
}

/* ── 탭 ── */
[data-baseweb="tab-list"] { gap: 6px !important; }
[data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
}

/* ── 입력 필드 ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border-radius: 9px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

/* ── 기타 ── */
.big-title {
    font-size: 1.7rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1565c0, #1976d2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.history-date { font-size: 0.75rem; color: #999; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── 세션 ID 기반 대화 저장 ────────────────────────────────────
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "histories")
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_session_id():
    """브라우저별 고유 ID를 URL 파라미터로 관리"""
    params = st.query_params
    if "sid" not in params:
        new_id = str(uuid.uuid4())[:8]
        st.query_params["sid"] = new_id
        return new_id
    return params["sid"]

def get_history_file(session_id):
    return os.path.join(HISTORY_DIR, f"chat_{session_id}.json")

def load_history(session_id):
    path = get_history_file(session_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(session_id, messages):
    try:
        with open(get_history_file(session_id), "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clear_history(session_id):
    path = get_history_file(session_id)
    if os.path.exists(path):
        os.remove(path)

# ── 투자 일지 저장/불러오기 ──────────────────────────────────
def get_journal_file(session_id):
    return os.path.join(HISTORY_DIR, f"journal_{session_id}.json")

def load_journal(session_id):
    path = get_journal_file(session_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_journal(session_id, journal):
    try:
        with open(get_journal_file(session_id), "w", encoding="utf-8") as f:
            json.dump(journal, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def build_gemini_history(messages):
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [{"text": msg["content"]}]})
    return history

# ── 관심 종목 저장/불러오기 ───────────────────────────────────
def get_watchlist_file(session_id):
    return os.path.join(HISTORY_DIR, f"watchlist_{session_id}.json")

def load_watchlist(session_id):
    path = get_watchlist_file(session_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_watchlist(session_id, watchlist):
    try:
        with open(get_watchlist_file(session_id), "w", encoding="utf-8") as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 세션 ID 초기화 ───────────────────────────────────────────
session_id = get_session_id()

# ── API 키 설정 ──────────────────────────────────────────────
try:
    api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

with st.sidebar:
    st.markdown("## 📈 나의 주식 비서")
    st.markdown("---")

    if not api_key:
        st.markdown("### 🔑 API 키 입력")
        api_key = st.text_input("Gemini API 키", type="password")
        st.markdown("[무료 발급받기](https://aistudio.google.com/app/apikey)")
        st.markdown("---")

    page = st.radio(
        "메뉴",
        ["📚 공부방", "📰 경제 뉴스", "📊 주식 정보", "⭐ 관심 종목", "📓 투자 일지", "🎯 나만의 전략"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 대화 내역 요약
    saved = load_history(session_id)
    if saved:
        total = len(saved)
        last_time = saved[-1].get("timestamp", "")
        st.markdown("#### 💾 나의 대화 내역")
        st.caption(f"총 {total}개 메시지")
        if last_time:
            st.caption(f"마지막: {last_time[:16]}")
    else:
        st.markdown("#### 💾 나의 대화 내역")
        st.caption("아직 대화 내역이 없어요")

    st.markdown("---")
    st.markdown("#### 📌 오늘의 한마디")
    st.info("주식은 단기가 아닌 장기 여정입니다. 꾸준히 공부하는 게 가장 좋은 전략이에요! 💪")

    st.markdown("---")
    st.markdown("#### 📖 오늘의 경제용어")
    try:
        _dict_path = os.path.join(os.path.dirname(__file__), "dictionary.json")
        with open(_dict_path, "r", encoding="utf-8") as _f:
            _dict_all = json.load(_f)
        _idx = datetime.today().timetuple().tm_yday % len(_dict_all)
        _today = _dict_all[_idx]
        st.markdown(f"**{_today['term']}**")
        # 첫 문장만 표시
        _body = _today["text"].split(".")[0] + "." if "." in _today["text"] else _today["text"][:80]
        st.caption(_body[:120])
    except Exception:
        pass

if not api_key:
    st.warning("⬅️ 왼쪽 사이드바에서 Gemini API 키를 입력해주세요.")
    st.stop()

genai.configure(api_key=api_key)

# ── AI 모델 초기화 (저장된 대화 이어받기) ────────────────────
SYSTEM_PROMPT = """당신은 '주식 왕초보'를 위한 친절한 경제·주식 선생님 겸 투자 비서입니다.

핵심 원칙:
- 모든 설명은 중학생도 이해하는 쉬운 말로 해주세요
- 어려운 용어는 반드시 괄호 안에 쉬운 설명을 추가하세요
- 친근하고 격려하는 말투를 사용하세요
- 특정 종목 단기 매수/매도 추천은 하지 마세요 (단, 공부 목적 예시는 OK)
- 수익 보장 표현은 절대 사용하지 마세요
- 리스크(위험)를 항상 함께 언급하세요

전략 추천 시:
- 초보자에게는 ETF(여러 주식을 묶은 바구니) 위주로 설명
- 분산투자의 중요성 강조
- 투자 금액은 여유자금으로만 하라고 강조
- 한국/미국 시장 비교 시 장단점 균형있게 설명

답변 형식:
1. 핵심을 한 문장으로 먼저
2. 쉬운 비유나 예시
3. 실전 연결 포인트
4. 주의사항이나 리스크 (짧게)
"""

if "messages" not in st.session_state:
    st.session_state.messages = load_history(session_id)

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=SYSTEM_PROMPT
    )
    gemini_history = build_gemini_history(st.session_state.messages)
    st.session_state.chat_session = model.start_chat(history=gemini_history)

# ── 주식 데이터 함수 ──────────────────────────────────────────
PERIOD_MAP = {
    "1개월":  {"yf": "1mo",  "days": 30},
    "3개월":  {"yf": "3mo",  "days": 90},
    "6개월":  {"yf": "6mo",  "days": 180},
    "1년":   {"yf": "1y",   "days": 365},
    "5년":   {"yf": "5y",   "days": 365*5},
    "10년":  {"yf": "10y",  "days": 365*10},
}

@st.cache_data(ttl=300)
def get_usdkrw():
    """달러/원 환율 조회"""
    try:
        rate = yf.Ticker("USDKRW=X").history(period="1d")
        if rate is not None and len(rate) > 0:
            return float(rate["Close"].iloc[-1])
    except Exception:
        pass
    return 1380.0  # 조회 실패 시 기본값

@st.cache_data(ttl=300)
def get_current_price(ticker, market):
    """현재가 조회 (US: USD, KR: KRW)"""
    try:
        if market == "KR":
            end = datetime.today()
            start = end - timedelta(days=5)
            df = fdr.DataReader(ticker, start, end)
            if df is not None and len(df) > 0:
                return float(df["Close"].iloc[-1])
        else:
            info, hist = get_us_stock(ticker, "5d")
            if info:
                p = info.get("currentPrice") or info.get("regularMarketPrice")
                if p:
                    return float(p)
            if hist is not None and len(hist) > 0:
                return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None

@st.cache_data(ttl=300)
def get_us_stock(ticker, period="6mo"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period=period)
        return info, hist
    except Exception:
        return None, None

@st.cache_data(ttl=300)
def get_us_stock_range(ticker, start_str, end_str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(start=start_str, end=end_str)
        return info, hist
    except Exception:
        return None, None

@st.cache_data(ttl=300)
def get_kr_stock(ticker, days=180):
    try:
        end = datetime.today()
        start = end - timedelta(days=days)
        df = fdr.DataReader(ticker, start, end)
        return df
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_kr_stock_range(ticker, start_str, end_str):
    try:
        df = fdr.DataReader(ticker, start_str, end_str)
        return df
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_index_data():
    indices = {
        "코스피 (KOSPI)": "KS11",
        "코스닥 (KOSDAQ)": "KQ11",
        "S&P 500 (미국)": "^GSPC",
        "나스닥 (NASDAQ)": "^IXIC",
    }
    result = {}
    for name, ticker in indices.items():
        try:
            if ticker.startswith("^"):
                data = yf.Ticker(ticker).history(period="5d")
            else:
                data = fdr.DataReader(ticker, datetime.today() - timedelta(days=7))
            if data is not None and len(data) >= 2:
                latest = float(data["Close"].iloc[-1])
                prev = float(data["Close"].iloc[-2])
                change_pct = (latest - prev) / prev * 100
                result[name] = {"price": latest, "change": change_pct}
        except:
            pass
    return result

# ── 캔들차트 + 거래량 공통 함수 ──────────────────────────────
def make_candle_chart(df, title="", currency="KRW", height=420):
    """OHLCV DataFrame으로 캔들차트 + 거래량 생성 (한국식: 빨간=상승, 파란=하락)"""
    up_color   = "#e53935"  # 상승 빨간
    down_color = "#1565c0"  # 하락 파란

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.03
    )

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color=up_color), fillcolor=up_color),
        decreasing=dict(line=dict(color=down_color), fillcolor=down_color),
        name="주가",
        showlegend=False,
    ), row=1, col=1)

    # 거래량 막대 (상승일=빨간, 하락일=파란)
    vol_colors = [
        up_color if float(c) >= float(o) else down_color
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=vol_colors, opacity=0.75,
        name="거래량", showlegend=False,
    ), row=2, col=1)

    y_label = "USD" if currency == "USD" else "원"
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=height,
        margin=dict(t=30 if title else 10, b=10, l=0, r=0),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        xaxis2=dict(showgrid=False),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#2a2a2a"),
        yaxis2=dict(title="거래량", showgrid=False),
    )
    return fig

def detect_candle_patterns(df):
    """최근 20일 캔들에서 기본 패턴 감지 → Plotly annotation 리스트 반환"""
    annotations = []
    n = min(20, len(df))
    subset = df.tail(n)
    closes = subset["Close"].values
    opens  = subset["Open"].values
    highs  = subset["High"].values
    lows   = subset["Low"].values
    dates  = list(subset.index)

    for i in range(len(subset)):
        o, h, l, c = float(opens[i]), float(highs[i]), float(lows[i]), float(closes[i])
        body = abs(c - o)
        rng  = h - l
        if rng < 0.0001:
            continue
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        pattern = None

        if body / rng < 0.08:                                        # 도지
            pattern = ("도지", "#FFD700")
        elif lower_wick >= 2 * body and upper_wick <= body * 0.4:   # 망치형
            pattern = ("망치형", "#76FF03")
        elif upper_wick >= 2 * body and lower_wick <= body * 0.4:   # 역망치형
            pattern = ("역망치형", "#FF9800")
        elif (i > 0 and c > opens[i-1] and o < closes[i-1]         # 상승장악형
              and closes[i-1] < opens[i-1]):
            pattern = ("상승장악형", "#E91E63")

        if pattern:
            label, color = pattern
            annotations.append(dict(
                x=dates[i], y=h * 1.006,
                text=f"<b>{label}</b>",
                showarrow=True, arrowhead=2, arrowsize=0.8,
                arrowcolor=color,
                font=dict(size=10, color=color),
                bgcolor="rgba(14,17,23,0.85)",
                bordercolor=color, borderwidth=1,
                ax=0, ay=-28,
                xref="x", yref="y",
            ))
    return annotations

def make_annotated_chart(df, title="", currency="KRW", height=520):
    """9일선 / 20일선 + 거래량이 포함된 분석용 차트"""
    up_color   = "#e53935"
    down_color = "#1565c0"

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.03
    )

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color=up_color), fillcolor=up_color),
        decreasing=dict(line=dict(color=down_color), fillcolor=down_color),
        name="주가", showlegend=False,
    ), row=1, col=1)

    # 9일선 (주황)
    if len(df) >= 9:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"].rolling(9).mean(),
            line=dict(color="#FF9800", width=1.8),
            name="9일선",
        ), row=1, col=1)

    # 20일선 (보라)
    if len(df) >= 20:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"].rolling(20).mean(),
            line=dict(color="#CE93D8", width=1.8),
            name="20일선",
        ), row=1, col=1)

    # 거래량
    vol_colors = [up_color if float(c) >= float(o) else down_color
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=vol_colors, opacity=0.75,
        name="거래량", showlegend=False,
    ), row=2, col=1)

    y_label = "USD" if currency == "USD" else "원"
    fig.update_layout(
        title=dict(text=f"{title}  📊 분석 뷰", font=dict(size=13)),
        xaxis_rangeslider_visible=False,
        height=height,
        margin=dict(t=50, b=10, l=0, r=0),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        xaxis2=dict(showgrid=False),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#2a2a2a"),
        yaxis2=dict(title="거래량", showgrid=False),
        legend=dict(orientation="h", y=1.06, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    return fig

def show_chart_tip():
    """캔들차트 읽는 법 팁 (expander)"""
    with st.expander("💡 차트 읽는 법 (처음이라면 클릭!)"):
        st.markdown("""
<div style="line-height:1.9; font-size:0.92rem">

**📊 캔들 하나 = 하루치 주가 요약**

<table style="width:100%; border-collapse:collapse; margin:8px 0; border:1px solid #e0e0e0">
<tr style="background:#f5f5f5; color:#333">
  <th style="padding:8px; text-align:center; border:1px solid #e0e0e0">모양</th>
  <th style="padding:8px; text-align:left; border:1px solid #e0e0e0">부위</th>
  <th style="padding:8px; text-align:left; border:1px solid #e0e0e0">의미</th>
</tr>
<tr style="background:#fff5f5">
  <td rowspan="4" style="padding:12px; text-align:center; font-size:1.6rem; vertical-align:middle; border:1px solid #e0e0e0">
    🕯️
  </td>
  <td style="padding:6px 10px; color:#c62828; font-weight:bold; border:1px solid #e0e0e0">윗 꼬리</td>
  <td style="padding:6px 10px; border:1px solid #e0e0e0">그날 <b>최고가</b> (여기까지 올랐어요)</td>
</tr>
<tr style="background:#fff5f5">
  <td style="padding:6px 10px; color:#c62828; font-weight:bold; border:1px solid #e0e0e0">몸통 위</td>
  <td style="padding:6px 10px; border:1px solid #e0e0e0">🔴 빨간 캔들: <b>종가</b>(마감가) &nbsp;/&nbsp; 🔵 파란 캔들: <b>시가</b>(시작가)</td>
</tr>
<tr style="background:#f5f8ff">
  <td style="padding:6px 10px; color:#1565c0; font-weight:bold; border:1px solid #e0e0e0">몸통 아래</td>
  <td style="padding:6px 10px; border:1px solid #e0e0e0">🔴 빨간 캔들: <b>시가</b>(시작가) &nbsp;/&nbsp; 🔵 파란 캔들: <b>종가</b>(마감가)</td>
</tr>
<tr style="background:#f5f8ff">
  <td style="padding:6px 10px; color:#1565c0; font-weight:bold; border:1px solid #e0e0e0">아랫 꼬리</td>
  <td style="padding:6px 10px; border:1px solid #e0e0e0">그날 <b>최저가</b> (여기까지 내렸어요)</td>
</tr>
</table>

**🎨 색깔 의미 (한국 증권앱 기준)**

| | 의미 | 예시 |
|---|---|---|
| 🔴 **빨간 캔들** | 오늘 **올랐음** (시작보다 마감이 높음) | 10만→11만원 |
| 🔵 **파란 캔들** | 오늘 **내렸음** (시작보다 마감이 낮음) | 10만→9만원 |

> ⚠️ 미국 앱은 반대예요! (초록=상승, 빨강=하락) — 헷갈리지 마세요.

---

**📈 차트로 흐름 읽기**

- **빨간 캔들이 연속** → 상승 추세, 투자자들이 사고 있어요
- **파란 캔들이 연속** → 하락 추세, 투자자들이 팔고 있어요
- **꼬리가 아주 길다** → 그날 주가가 크게 흔들렸다는 신호
- **몸통이 크다** → 시가↔종가 차이가 크다 = 강한 움직임

---

**📊 아래 거래량 막대란?**

막대 높이 = 그날 사고판 주식 수량
막대가 **높을수록** → 그날 많은 사람이 관심을 가진 날
거래량 급증 + 빨간 캔들 = 강한 매수 신호로 보기도 해요

</div>
""", unsafe_allow_html=True)

# ── 관심종목 공통 함수 ────────────────────────────────────────
TAG_COLORS = {
    "ETF":    "#4CAF50",
    "기술주":  "#2196F3",
    "배당주":  "#FF9800",
    "성장주":  "#9C27B0",
    "한국주식": "#F44336",
    "개별주":  "#00BCD4",
    "기타":    "#607D8B",
}

def tag_badge(tag):
    color = TAG_COLORS.get(tag, "#607D8B")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:bold">{tag}</span>'

@st.cache_data(ttl=60)
def search_us_stocks(query):
    """야후 파이낸스 검색 API로 미국 주식·ETF 티커 검색"""
    try:
        url = (
            f"https://query2.finance.yahoo.com/v1/finance/search"
            f"?q={requests.utils.quote(query)}&quotesCount=8&newsCount=0&listsCount=0"
        )
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        results = []
        for q in resp.json().get("quotes", []):
            if q.get("quoteType") in ("EQUITY", "ETF"):
                results.append({
                    "ticker": q.get("symbol", ""),
                    "name": q.get("longname") or q.get("shortname", ""),
                    "exchange": q.get("exchange", ""),
                })
        return results
    except Exception:
        return []

def search_kr_stocks(query, name_map):
    """이름으로 한국 주식 검색 (부분 일치)"""
    query = query.strip()
    if not query:
        return []
    return [
        {"ticker": code, "name": name}
        for code, name in name_map.items()
        if query in name
    ][:10]

@st.cache_data(ttl=86400)
def get_krx_name_map():
    """KOSPI + KOSDAQ + ETF/KR 전체 종목 한글 이름 딕셔너리 (하루 1회 캐시)"""
    name_map = {}
    for market in ['KOSPI', 'KOSDAQ']:
        try:
            df = fdr.StockListing(market)
            for code, name in zip(df['Code'].astype(str), df['Name']):
                name_map[code.zfill(6)] = name
        except:
            pass
    try:
        etf_df = fdr.StockListing('ETF/KR')
        for code, name in zip(etf_df['Symbol'].astype(str), etf_df['Name']):
            name_map[code.zfill(6)] = name
    except:
        pass
    return name_map

def auto_classify_with_name(ticker, market_tag):
    """종목 정보를 가져와서 이름 + 태그 자동 분류 → (name, tag) 반환"""
    try:
        if market_tag == "KR":
            krx_map = get_krx_name_map()
            name = krx_map.get(ticker.zfill(6), ticker)
            etf_name_keywords = ["KODEX", "TIGER", "KBSTAR", "HANARO", "ARIRANG",
                                  "KOSEF", "SOL ", "ACE ", "TIMEFOLIO", "FOCUS", "WOORI",
                                  "PLUS", "TREX", "SMART", "ETF"]
            etf_backup_codes = ["069500","229200","360750","133690","195930","148020",
                                 "114800","252670","102110","251340","kodex","tiger"]
            is_etf = (any(k in name.upper() for k in etf_name_keywords) or
                      (name == ticker and any(k in ticker.lower() for k in etf_backup_codes)))
            tag = "ETF" if is_etf else "한국주식"
            return name, tag
        info = yf.Ticker(ticker).info
        name = info.get("shortName") or info.get("longName") or ticker
        quote_type = info.get("quoteType", "")
        sector = info.get("sector", "")
        div_yield = info.get("dividendYield") or 0
        if quote_type == "ETF":
            tag = "ETF"
        elif sector in ["Technology", "Communication Services"]:
            tag = "기술주"
        elif div_yield >= 0.025:
            tag = "배당주"
        elif sector in ["Consumer Cyclical", "Healthcare", "Industrials",
                        "Consumer Defensive", "Real Estate"]:
            tag = "성장주"
        else:
            tag = "개별주"
        return name, tag
    except:
        return ticker, "기타"

def add_to_watchlist(ticker, market_tag, session_id):
    """관심종목에 추가 (중복 체크 포함). 성공 여부 반환."""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = load_watchlist(session_id)
    existing = [w["ticker"] for w in st.session_state.watchlist]
    if ticker in existing:
        return False, "already"
    name, tag = auto_classify_with_name(ticker, market_tag)
    entry = {"ticker": ticker, "market": market_tag, "tag": tag, "name": name}
    st.session_state.watchlist.append(entry)
    save_watchlist(session_id, st.session_state.watchlist)
    return True, name

def add_message(role, content):
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.messages.append(msg)
    save_history(session_id, st.session_state.messages)

def ai_analyze(prompt, knowledge_context=""):
    if knowledge_context:
        prompt = knowledge_context + "\n\n" + prompt
    try:
        response = st.session_state.chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "exhausted" in err.lower():
            return "⏳ 잠깐! 요청이 너무 많아서 잠시 대기 중이에요. **10~20초 후에 다시 눌러주세요!**\n\n(무료 API는 분당 요청 횟수가 제한돼 있어요 😊)"
        elif "invalid" in err.lower() or "API_KEY" in err:
            return "🔑 API 키가 올바르지 않아요. 사이드바에서 키를 다시 확인해주세요."
        else:
            return f"❌ 오류가 발생했어요. 잠시 후 다시 시도해주세요.\n\n`{err[:100]}`"

# ── 초성 추출 헬퍼 ────────────────────────────────────────────
def get_chosung(char):
    CHOSUNGS = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    if '가' <= char <= '힣':
        return CHOSUNGS[(ord(char) - ord('가')) // 588]
    return char[0].upper() if char else "?"

def extract_term_name(text):
    """청크 텍스트에서 용어명 추출 (짧고 문장이 아닌 첫 줄)"""
    sentence_endings = ('다.', '요.', '니다.', '어요.', '하다.', '이다.', '겠다.', '된다.')
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 2:
            continue
        if len(line) == 1 and 'ㄱ' <= line <= 'ㅎ':
            continue
        # 짧고 문장 어미가 없으면 용어명으로 판단
        if len(line) <= 30 and not any(line.endswith(e) for e in sentence_endings):
            return line
    # 적절한 용어명 없으면 첫 줄 앞부분
    for line in text.split("\n"):
        line = line.strip()
        if len(line) >= 2:
            return line[:20] + "…"
    return "내용 보기"

# ── 페이지 1: 공부방 ──────────────────────────────────────────
if page == "📚 공부방":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📚</div>
        <h1>공부방</h1>
        <p>경제·주식 왕초보 전용 AI 선생님 · 모르는 게 있으면 뭐든 물어보세요 😊</p>
    </div>""", unsafe_allow_html=True)

    tab_chat, tab_dict = st.tabs(["💬 AI 대화", "📖 경제용어 사전"])

    # ══ 탭1: AI 대화 ══════════════════════════════════════════
    with tab_chat:
        quick_qs = [
            "주식이 뭔가요?", "금리가 뭔가요?", "ETF가 뭔가요?", "PER이 뭔가요?",
            "환율이 주식에 미치는 영향은?", "코스피 vs 나스닥 차이는?",
            "인플레이션이 뭔가요?", "분산투자가 뭔가요?",
        ]
        q_cols = st.columns(4)
        for i, q in enumerate(quick_qs):
            with q_cols[i % 4]:
                if st.button(q, use_container_width=True, key=f"quick_{q}"):
                    st.session_state.pending_question = q

        del_col, _ = st.columns([1, 3])
        with del_col:
            if st.button("🗑️ 대화 내역 전체 삭제", use_container_width=True):
                st.session_state.messages = []
                clear_history(session_id)
                model = genai.GenerativeModel("gemini-2.5-flash-lite", system_instruction=SYSTEM_PROMPT)
                st.session_state.chat_session = model.start_chat(history=[])
                st.rerun()

        st.markdown("---")

        if not st.session_state.messages:
            st.markdown("""
            <div class="tip-box">
            💡 <b>이렇게 물어보세요!</b><br>
            • "금리가 오르면 주식이 왜 떨어져요?"<br>
            • "삼성전자 주식은 왜 사람들이 사나요?"<br>
            • "S&P500 ETF가 좋다는데 그게 뭔가요?"<br>
            • "100만원으로 주식 시작하려면 어떻게 해요?"
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("timestamp"):
                    st.markdown(f'<div class="history-date">{msg["timestamp"]}</div>', unsafe_allow_html=True)

        def handle_question(user_input):
            add_message("user", user_input)
            with st.spinner("공부 중...✏️"):
                chunks = search_knowledge(user_input)
                ctx = ""
                if chunks:
                    ctx = "📚 참고 자료 (경제·주식 교육 교재에서 발췌):\n"
                    for c in chunks:
                        ctx += f"\n[출처: {c['source']}]\n{c['text'][:400]}\n"
                    ctx += "\n위 자료를 참고해서 답변해주세요.\n"
                answer = ai_analyze(user_input, knowledge_context=ctx)
            add_message("assistant", answer)
            st.rerun()

        if "pending_question" in st.session_state and st.session_state.pending_question:
            q = st.session_state.pending_question
            st.session_state.pending_question = None
            handle_question(q)

        with st.form(key="chat_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns([6, 1])
            with f_col1:
                user_input = st.text_input("질문 입력",
                                           placeholder="궁금한 걸 물어보세요! 아무것도 몰라도 괜찮아요 😊",
                                           label_visibility="collapsed")
            with f_col2:
                submitted = st.form_submit_button("전송", use_container_width=True, type="primary")
        if submitted and user_input:
            handle_question(user_input)

    # ══ 탭2: 경제용어 사전 ════════════════════════════════════
    with tab_dict:
        st.markdown("### 📖 경제·금융 용어 사전")
        st.caption("한국은행 경제금융용어 800선 — 용어를 클릭하면 설명을 볼 수 있어요")

        @st.cache_resource
        def load_dictionary():
            path = os.path.join(os.path.dirname(__file__), "dictionary.json")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []

        dict_all = load_dictionary()

        # ── 초성 필터
        CHOSUNGS_LIST = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
        if "dict_cho" not in st.session_state:
            st.session_state.dict_cho = "전체"

        cho_cols = st.columns(len(CHOSUNGS_LIST))
        for ci, cho in enumerate(CHOSUNGS_LIST):
            with cho_cols[ci]:
                is_sel = st.session_state.dict_cho == cho
                if st.button(cho, key=f"cho_{cho}", use_container_width=True,
                             type="primary" if is_sel else "secondary"):
                    st.session_state.dict_cho = cho
                    st.rerun()

        cho_filter = st.session_state.dict_cho
        if cho_filter == "전체":
            filtered = dict_all
        else:
            filtered = [t for t in dict_all if get_chosung(t["term"][0]) == cho_filter]

        st.markdown(f"**{len(filtered)}개** 용어")
        st.markdown("---")

        # ── 용어 카드 표시 (초성 전체면 50개씩, 필터 시 전체)
        show_items = filtered if cho_filter != "전체" else filtered[:50]
        if cho_filter == "전체":
            st.caption("💡 초성 버튼을 눌러 원하는 용어를 찾아보세요! (전체 표시 시 50개만 미리보기)")

        for i, item in enumerate(show_items):
            with st.expander(f"**{item['term']}**"):
                st.write(item["text"])
                if st.button("🤖 AI에게 더 쉽게 설명 요청", key=f"dict_ai_{i}"):
                    st.session_state.pending_question = f"{item['term']}이(가) 뭔가요? 왕초보에게 쉽게 설명해주세요."
                    st.rerun()

# ── 페이지 2: 경제 뉴스 ──────────────────────────────────────
elif page == "📰 경제 뉴스":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📰</div>
        <h1>오늘의 경제 뉴스</h1>
        <p>최신 경제 소식을 AI가 왕초보 눈높이로 쉽게 설명해드려요</p>
    </div>""", unsafe_allow_html=True)
    st.caption("최신 경제 뉴스를 왕초보 언어로 쉽게 설명해드려요")

    # 네이버 API 키 확인
    try:
        naver_id = st.secrets.get("NAVER_CLIENT_ID", "")
        naver_secret = st.secrets.get("NAVER_CLIENT_SECRET", "")
    except:
        naver_id, naver_secret = "", ""

    @st.cache_data(ttl=1800)
    def get_naver_news(query, display=5):
        if not naver_id or not naver_secret:
            return []
        try:
            url = "https://openapi.naver.com/v1/search/news.json"
            headers = {
                "X-Naver-Client-Id": naver_id,
                "X-Naver-Client-Secret": naver_secret
            }
            params = {"query": query, "display": display, "sort": "date"}
            res = requests.get(url, headers=headers, params=params, timeout=5)
            items = res.json().get("items", [])
            # HTML 태그 제거
            for item in items:
                item["title"] = re.sub(r"<[^>]+>", "", item["title"])
                item["description"] = re.sub(r"<[^>]+>", "", item["description"])
            return items
        except:
            return []

    US_NEWS_FEEDS = {
        "📈 시장 전체": "https://www.cnbc.com/id/15839069/device/rss/rss.html",
        "💰 경제 지표": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "🏦 금융/투자": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "⚡ 실시간 헤드라인": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    }

    @st.cache_data(ttl=1800)
    def get_us_news(feed_url):
        try:
            feed = feedparser.parse(feed_url)
            return feed.entries[:8]
        except:
            return []

    @st.cache_data(ttl=1800)
    def translate_titles_batch(titles_tuple):
        """뉴스 제목 목록을 한번에 번역 (30분 캐시, API 1회 호출)"""
        try:
            titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles_tuple)])
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content(
                f"다음 미국 경제 뉴스 제목들을 자연스러운 한국어로 번역해주세요.\n"
                f"번호와 번역만 출력하고 다른 설명은 없이 딱 이 형식으로만:\n"
                f"1. 번역된 제목\n2. 번역된 제목\n\n{titles_text}"
            )
            result = {}
            for line in response.text.strip().split("\n"):
                m = re.match(r"(\d+)\.\s+(.+)", line.strip())
                if m:
                    idx = int(m.group(1)) - 1
                    if idx < len(titles_tuple):
                        result[titles_tuple[idx]] = m.group(2).strip()
            return result
        except:
            return {}

    # AI 뉴스 브리핑 버튼
    st.markdown("### 🤖 오늘의 AI 경제 브리핑")
    st.caption("최신 뉴스를 AI가 왕초보 언어로 요약해드려요")

    if st.button("📋 오늘 꼭 알아야 할 경제 뉴스 요약해줘!", use_container_width=True, type="primary"):
        kr_news = get_naver_news("경제 주식 금리", display=5)
        us_news = get_us_news(list(US_NEWS_FEEDS.values())[0])

        kr_titles = "\n".join([f"- {n['title']}" for n in kr_news[:5]]) if kr_news else "뉴스를 불러올 수 없습니다"
        us_titles = "\n".join([f"- {e.get('title','')}" for e in us_news[:5]]) if us_news else "뉴스를 불러올 수 없습니다"

        with st.spinner("AI가 뉴스 읽고 요약 중... ✏️"):
            prompt = f"""
오늘의 경제 뉴스를 주식 왕초보에게 쉽게 설명해주세요.

한국 경제 뉴스:
{kr_titles}

미국 경제 뉴스:
{us_titles}

다음 형식으로 작성해주세요:

## 📌 오늘의 핵심 3줄 요약
(가장 중요한 내용 3가지를 아주 쉽게)

## 🇰🇷 한국 경제 오늘 포인트
(한국 뉴스 중 주식 초보자가 알아야 할 것, 쉽게)

## 🇺🇸 미국 경제 오늘 포인트
(미국 뉴스 중 주식 초보자가 알아야 할 것, 쉽게)

## 💡 초보자를 위한 한마디
(오늘 뉴스를 보고 초보 투자자가 기억할 것 한 가지)

모든 내용은 중학생도 이해하는 말로 써주세요.
"""
            summary = ai_analyze(prompt)
        st.markdown(f'<div class="tip-box">{summary}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 한국/미국 뉴스 탭
    tab_kr, tab_us = st.tabs(["🇰🇷 한국 경제 뉴스", "🇺🇸 미국 경제 뉴스"])

    with tab_kr:
        if not naver_id:
            st.warning("⚠️ 네이버 API 키가 없어요. 아래 안내를 따라 설정해주세요.")
            st.markdown("""
            <div class="tip-box">
            <b>네이버 API 키 설정 방법:</b><br>
            1. <a href="https://developers.naver.com/apps/#/register" target="_blank">네이버 개발자센터</a> 접속<br>
            2. 애플리케이션 등록 → 검색 API 선택<br>
            3. Client ID, Client Secret 복사<br>
            4. Streamlit Cloud → Manage app → Settings → Secrets 에 추가:<br>
            <code>NAVER_CLIENT_ID = "여기에입력"</code><br>
            <code>NAVER_CLIENT_SECRET = "여기에입력"</code>
            </div>
            """, unsafe_allow_html=True)
        else:
            keywords = st.selectbox(
                "뉴스 주제 선택",
                ["경제 주식 금리", "코스피 코스닥", "환율 달러", "삼성전자 반도체", "부동산 금리"]
            )
            with st.spinner("뉴스 불러오는 중..."):
                news_items = get_naver_news(keywords, display=8)

            if news_items:
                for item in news_items:
                    with st.expander(f"📄 {item['title']}"):
                        st.caption(item.get("pubDate", "")[:25])
                        st.write(item.get("description", ""))
                        col_a, col_b = st.columns([1, 3])
                        with col_a:
                            if st.button("🤖 쉽게 설명해줘", key=f"kr_news_{item['title'][:20]}"):
                                with st.spinner("설명 중..."):
                                    answer = ai_analyze(f"다음 뉴스를 주식 왕초보에게 쉽게 설명해주세요:\n제목: {item['title']}\n내용: {item['description']}")
                                st.info(answer)
                        with col_b:
                            st.markdown(f"[원문 보기]({item.get('link', '#')})")
            else:
                st.info("뉴스를 불러올 수 없어요. 잠시 후 다시 시도해주세요.")

    with tab_us:
        # 카테고리 선택
        selected_feed_name = st.radio(
            "카테고리",
            list(US_NEWS_FEEDS.keys()),
            horizontal=True,
            label_visibility="collapsed"
        )
        feed_url = US_NEWS_FEEDS[selected_feed_name]

        with st.spinner("미국 뉴스 불러오는 중..."):
            us_entries = get_us_news(feed_url)

        if us_entries:
            st.caption(f"출처: CNBC / MarketWatch | {selected_feed_name} | 30분마다 업데이트")

            # 제목 전체를 한번에 번역 (캐시됨)
            all_titles = tuple(e.get("title", "") for e in us_entries)
            with st.spinner("제목 번역 중..."):
                translations = translate_titles_batch(all_titles)

            for entry in us_entries:
                title = entry.get("title", "")
                kr_title = translations.get(title, "")
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "#")
                published = entry.get("published", "")[:16] if entry.get("published") else ""

                # HTML 태그 제거
                summary_clean = re.sub(r"<[^>]+>", "", summary)

                with st.expander(f"📄 {title}"):
                    if kr_title:
                        st.markdown(
                            f'<div style="background:#f0f7ff;border-left:3px solid #1f77b4;'
                            f'padding:8px 12px;border-radius:4px;margin-bottom:8px;'
                            f'font-size:0.95rem;font-weight:bold;color:#1a3a5c">🇰🇷 {kr_title}</div>',
                            unsafe_allow_html=True
                        )
                    if published:
                        st.caption(f"🕐 {published}")
                    if summary_clean:
                        st.write(summary_clean[:300] + "..." if len(summary_clean) > 300 else summary_clean)

                    col_a, col_b = st.columns([2, 3])
                    with col_a:
                        if st.button("🤖 한국어로 쉽게 설명해줘", key=f"us_news_{title[:25]}"):
                            with st.spinner("번역 & 설명 중..."):
                                answer = ai_analyze(
                                    f"다음 미국 경제 뉴스를 한국어로 번역하고 주식 왕초보에게 쉽게 설명해주세요:\n"
                                    f"제목: {title}\n내용: {summary_clean[:500]}"
                                )
                            st.info(answer)
                    with col_b:
                        st.markdown(f"[📰 원문 보기 (영어)]({link})")
        else:
            st.info("미국 뉴스를 불러올 수 없어요. 잠시 후 다시 시도해주세요.")

# ── 페이지 3: 관심 종목 ──────────────────────────────────────
elif page == "⭐ 관심 종목":
    st.markdown("""
    <div class="page-header">
        <div class="icon">⭐</div>
        <h1>관심 종목</h1>
        <p>자주 보는 종목을 저장하고 현재가를 한눈에 확인하세요</p>
    </div>""", unsafe_allow_html=True)
    st.caption("자주 보는 종목을 태그별로 분류해서 한눈에 확인하세요")

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = load_watchlist(session_id)
        # 기존 항목 중 tag 없는 것은 기타로 채움
        for item in st.session_state.watchlist:
            if "tag" not in item:
                item["tag"] = "기타"

    # ── 종목 추가 ──
    st.markdown("### ➕ 종목 추가")
    st.caption("종목 코드만 입력하면 ETF·기술주·배당주 등 자동으로 분류돼요!")
    col_add1, col_add2, col_add3 = st.columns([3, 1, 1])
    with col_add1:
        new_ticker = st.text_input("종목 코드", placeholder="미국: AAPL, SPY  /  한국: 005930, 069500", label_visibility="collapsed")
    with col_add2:
        market = st.selectbox("시장", ["🇺🇸 미국", "🇰🇷 한국"], label_visibility="collapsed")
    with col_add3:
        if st.button("추가하기", use_container_width=True, type="primary"):
            if new_ticker:
                ticker = new_ticker.upper().strip() if "미국" in market else new_ticker.strip()
                market_tag = "US" if "미국" in market else "KR"
                existing = [w["ticker"] for w in st.session_state.watchlist]
                if ticker not in existing:
                    with st.spinner(f"{ticker} 정보 가져오는 중..."):
                        stock_name, auto_tag = auto_classify_with_name(ticker, market_tag)
                    entry = {
                        "ticker": ticker,
                        "name": stock_name,
                        "market": market_tag,
                        "tag": auto_tag,
                        "added": datetime.now().strftime("%Y-%m-%d")
                    }
                    st.session_state.watchlist.append(entry)
                    save_watchlist(session_id, st.session_state.watchlist)
                    st.success(f"**{stock_name}** 추가됐어요! 자동 분류: **{auto_tag}**")
                    st.rerun()
                else:
                    st.warning("이미 추가된 종목이에요!")

    st.markdown("---")

    if not st.session_state.watchlist:
        st.markdown("""
        <div class="tip-box">
        💡 <b>이렇게 추가해보세요!</b><br>
        • ETF: SPY (S&P500), QQQ (나스닥), 069500 (KODEX200)<br>
        • 기술주: AAPL (애플), NVDA (엔비디아), 005930 (삼성전자)<br>
        • 배당주: 고배당 ETF, 리츠 등
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── 태그 필터 ──
        filter_options = ["전체"] + list(TAG_COLORS.keys())

        if "selected_filter" not in st.session_state:
            st.session_state.selected_filter = "전체"

        # 태그 필터 버튼 (선택된 것만 primary 강조)
        filter_cols = st.columns(len(filter_options))
        for idx, opt in enumerate(filter_options):
            is_selected = st.session_state.selected_filter == opt
            with filter_cols[idx]:
                btn_label = f"● {opt}" if is_selected else opt
                if st.button(btn_label, key=f"filter_{opt}", use_container_width=True,
                             type="primary" if is_selected else "secondary"):
                    st.session_state.selected_filter = opt
                    st.rerun()

        selected_filter = st.session_state.selected_filter
        st.markdown("---")

        filtered = st.session_state.watchlist if selected_filter == "전체" \
            else [w for w in st.session_state.watchlist if w.get("tag", "기타") == selected_filter]

        st.markdown(f"### 📋 {selected_filter} ({len(filtered)}개)")

        # 헤더 행
        hcol1, hcol2, hcol3, hcol4, hcol5, hcol6 = st.columns([3, 1.2, 1.8, 1.8, 1.5, 1])
        with hcol1:
            st.markdown('<span style="font-size:0.8rem;color:#888;font-weight:bold">종목명</span>', unsafe_allow_html=True)
        with hcol2:
            st.markdown('<span style="font-size:0.8rem;color:#888;font-weight:bold">종목코드</span>', unsafe_allow_html=True)
        with hcol3:
            st.markdown('<span style="font-size:0.8rem;color:#888;font-weight:bold">현재가</span>', unsafe_allow_html=True)
        with hcol4:
            st.markdown('<span style="font-size:0.8rem;color:#888;font-weight:bold">등락률 (오늘)</span>', unsafe_allow_html=True)
        with hcol5:
            st.markdown('<span style="font-size:0.8rem;color:#888;font-weight:bold">분류</span>', unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0 8px 0;border-color:#ddd'>", unsafe_allow_html=True)

        for i, item in enumerate(filtered):
            ticker = item["ticker"]
            market_tag = item["market"]
            tag = item.get("tag", "기타")
            saved_name = item.get("name", "")
            flag = "🇺🇸" if market_tag == "US" else "🇰🇷"

            # KR 종목: KRX 캐시 기반이라 빠름 → 항상 재분류해서 최신 상태 유지
            # US 종목: 이름 없을 때만 yfinance 호출 (느린 API)
            if market_tag == "KR":
                fetched_name, fetched_tag = auto_classify_with_name(ticker, market_tag)
                if fetched_name != saved_name or fetched_tag != tag:
                    item["name"] = fetched_name
                    item["tag"] = fetched_tag
                    save_watchlist(session_id, st.session_state.watchlist)
                saved_name = fetched_name
                tag = fetched_tag
            elif not saved_name or saved_name == ticker:
                fetched_name, fetched_tag = auto_classify_with_name(ticker, market_tag)
                saved_name = fetched_name
                item["name"] = fetched_name
                item["tag"] = fetched_tag
                tag = fetched_tag
                save_watchlist(session_id, st.session_state.watchlist)

            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1.2, 1.8, 1.8, 1.5, 1])

                try:
                    if market_tag == "US":
                        info, hist = get_us_stock(ticker)
                        if info and hist is not None and len(hist) > 0:
                            price = info.get("currentPrice") or info.get("regularMarketPrice") or float(hist["Close"].iloc[-1])
                            prev = info.get("previousClose", float(hist["Close"].iloc[-2]) if len(hist) > 1 else price)
                            change_pct = (price - prev) / prev * 100
                            price_str = f"${price:,.2f}"
                        else:
                            raise Exception()
                    else:
                        end = datetime.today()
                        start = end - timedelta(days=10)
                        kr_data = fdr.DataReader(ticker, start, end)
                        if kr_data is not None and len(kr_data) > 1:
                            price = float(kr_data["Close"].iloc[-1])
                            prev = float(kr_data["Close"].iloc[-2])
                            change_pct = (price - prev) / prev * 100
                            price_str = f"₩{price:,.0f}"
                        else:
                            raise Exception()

                    with col1:
                        st.markdown(f"**{flag} {saved_name}**")
                    with col2:
                        st.caption(ticker)
                    with col3:
                        st.markdown(f"**{price_str}**")
                    with col4:
                        arrow = "▲" if change_pct > 0 else "▼"
                        color_hex = "#e53935" if change_pct > 0 else "#1e88e5"
                        sign = "+" if change_pct > 0 else ""
                        st.markdown(
                            f'<div style="font-size:1rem;font-weight:bold;color:{color_hex};padding-top:4px">'
                            f'{arrow} {sign}{change_pct:.2f}%</div>',
                            unsafe_allow_html=True
                        )
                    with col5:
                        st.markdown(tag_badge(tag), unsafe_allow_html=True)
                    with col6:
                        if st.button("삭제", key=f"del_{ticker}_{i}"):
                            st.session_state.watchlist = [w for w in st.session_state.watchlist if w["ticker"] != ticker]
                            save_watchlist(session_id, st.session_state.watchlist)
                            st.rerun()

                except Exception:
                    with col1:
                        st.markdown(f"**{flag} {saved_name}**")
                    with col2:
                        st.caption(ticker)
                    with col3:
                        st.caption("불러오는 중...")
                    with col5:
                        st.markdown(tag_badge(tag), unsafe_allow_html=True)
                    with col6:
                        if st.button("삭제", key=f"del_{ticker}_{i}"):
                            st.session_state.watchlist = [w for w in st.session_state.watchlist if w["ticker"] != ticker]
                            save_watchlist(session_id, st.session_state.watchlist)
                            st.rerun()

                # 토글 상세보기
                with st.expander(f"📊 {saved_name} 상세보기"):
                    with st.spinner("차트 불러오는 중..."):
                        try:
                            if market_tag == "US":
                                d_info, d_hist = get_us_stock(ticker)
                                if d_info and d_hist is not None and len(d_hist) > 0:
                                    d_price = d_info.get("currentPrice") or float(d_hist["Close"].iloc[-1])
                                    d_prev = d_info.get("previousClose", float(d_hist["Close"].iloc[-2]))
                                    d_chg = (d_price - d_prev) / d_prev * 100
                                    dc1, dc2, dc3, dc4 = st.columns(4)
                                    dc1.metric("현재가", f"${d_price:,.2f}", f"{'+' if d_chg>0 else ''}{d_chg:.2f}%")
                                    dc2.metric("52주 최고", f"${d_info.get('fiftyTwoWeekHigh','N/A')}")
                                    dc3.metric("52주 최저", f"${d_info.get('fiftyTwoWeekLow','N/A')}")
                                    dc4.metric("PER", f"{d_info.get('trailingPE','N/A'):.1f}" if isinstance(d_info.get('trailingPE'), float) else "N/A")
                                    fig = make_candle_chart(d_hist, currency="USD", height=320)
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                d_end = datetime.today()
                                d_start = d_end - timedelta(days=180)
                                d_data = fdr.DataReader(ticker, d_start, d_end)
                                if d_data is not None and len(d_data) > 1:
                                    d_price = float(d_data["Close"].iloc[-1])
                                    d_prev = float(d_data["Close"].iloc[-2])
                                    d_chg = (d_price - d_prev) / d_prev * 100
                                    dc1, dc2, dc3 = st.columns(3)
                                    dc1.metric("현재가", f"₩{d_price:,.0f}", f"{'+' if d_chg>0 else ''}{d_chg:.2f}%")
                                    dc2.metric("3개월 최고", f"₩{float(d_data['Close'].max()):,.0f}")
                                    dc3.metric("3개월 최저", f"₩{float(d_data['Close'].min()):,.0f}")
                                    fig = make_candle_chart(d_data, currency="KRW", height=320)
                                    st.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            st.caption("데이터를 불러올 수 없어요.")

                st.divider()

        if st.button("🔄 전체 가격 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ── 페이지 4: 주식 정보 ──────────────────────────────────────
elif page == "📊 주식 정보":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📊</div>
        <h1>실시간 주식 정보</h1>
        <p>미국·한국 주식 차트 조회 · AI 차트 해석 · 매수·손절·익절 가이드</p>
    </div>""", unsafe_allow_html=True)
    st.caption("실제 주식 데이터를 보면서 공부해요. 데이터는 Yahoo Finance / FinanceDataReader 제공 (무료)")

    st.markdown("### 🌍 주요 시장 지수")
    with st.spinner("시장 데이터 불러오는 중..."):
        indices = get_index_data()

    if indices:
        cols = st.columns(len(indices))
        for i, (name, data) in enumerate(indices.items()):
            with cols[i]:
                sign = "+" if data["change"] > 0 else ""
                st.metric(
                    label=name,
                    value=f"{data['price']:,.2f}",
                    delta=f"{sign}{data['change']:.2f}%"
                )
    else:
        st.warning("시장 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")

    st.markdown("---")

    tab1, tab2 = st.tabs(["🇺🇸 미국 주식", "🇰🇷 한국 주식"])

    with tab1:
        st.markdown("#### 미국 주식 검색")
        st.caption("예시: AAPL(애플), MSFT(마이크로소프트), TSLA(테슬라), SPY(S&P500 ETF), QQQ(나스닥 ETF)")

        popular_us = {
            "SPY (S&P500 ETF)": "SPY",
            "QQQ (나스닥 ETF)": "QQQ",
            "AAPL (애플)": "AAPL",
            "MSFT (마이크로소프트)": "MSFT",
            "TSLA (테슬라)": "TSLA",
            "NVDA (엔비디아)": "NVDA",
        }

        with st.expander("🔍 회사 이름으로 검색"):
            us_name_q = st.text_input("회사 이름 입력", placeholder="예: apple, 테슬라, nvidia", key="us_name_q")
            if us_name_q and len(us_name_q) >= 2:
                with st.spinner("검색 중..."):
                    us_results = search_us_stocks(us_name_q)
                if us_results:
                    st.caption("아래 종목을 클릭하면 바로 조회돼요")
                    rc1, rc2 = st.columns(2)
                    for i, r in enumerate(us_results[:6]):
                        with (rc1 if i % 2 == 0 else rc2):
                            label = f"**{r['ticker']}** — {r['name'][:24]}"
                            if st.button(label, key=f"us_sr_{i}", use_container_width=True):
                                st.session_state["us_input"] = r["ticker"]
                                st.rerun()
                else:
                    st.caption("검색 결과가 없어요. 영어로 다시 시도해보세요.")

        col_a, col_b = st.columns([2, 1])
        with col_a:
            us_ticker = st.text_input("티커 직접 입력 (영문)", placeholder="예: AAPL", key="us_input").upper().strip()
        with col_b:
            selected_popular = st.selectbox("인기 종목", ["직접 입력"] + list(popular_us.keys()), key="us_popular")

        if selected_popular != "직접 입력":
            us_ticker = popular_us[selected_popular]

        if us_ticker:
            # ── 기간 버튼
            us_period_key = f"us_period_{us_ticker}"
            if us_period_key not in st.session_state:
                st.session_state[us_period_key] = "6개월"
            period_cols = st.columns(len(PERIOD_MAP))
            for pi, pname in enumerate(PERIOD_MAP):
                with period_cols[pi]:
                    is_sel = st.session_state[us_period_key] == pname
                    if st.button(pname, key=f"us_p_{pname}",
                                 type="primary" if is_sel else "secondary",
                                 use_container_width=True):
                        st.session_state[us_period_key] = pname
                        st.session_state.pop(f"us_custom_{us_ticker}", None)
                        st.rerun()

            # ── 날짜 직접 선택
            with st.expander("📅 날짜 직접 선택"):
                dc1, dc2, dc3 = st.columns([2, 2, 1])
                with dc1:
                    us_start = st.date_input("시작일", value=datetime.today() - timedelta(days=180),
                                             min_value=datetime(2000, 1, 1), max_value=datetime.today(),
                                             key=f"us_start_{us_ticker}")
                with dc2:
                    us_end = st.date_input("종료일", value=datetime.today(),
                                           min_value=datetime(2000, 1, 1), max_value=datetime.today(),
                                           key=f"us_end_{us_ticker}")
                with dc3:
                    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                    if st.button("조회", key=f"us_custom_btn_{us_ticker}", type="primary", use_container_width=True):
                        st.session_state[f"us_custom_{us_ticker}"] = (str(us_start), str(us_end))
                        st.rerun()

            # 커스텀 기간 vs 버튼 기간
            us_custom = st.session_state.get(f"us_custom_{us_ticker}")
            if us_custom:
                us_period_label = f"{us_custom[0]} ~ {us_custom[1]}"
                with st.spinner(f"{us_ticker} 데이터 불러오는 중..."):
                    info, hist = get_us_stock_range(us_ticker, us_custom[0], us_custom[1])
            else:
                us_yf_period = PERIOD_MAP[st.session_state[us_period_key]]["yf"]
                us_period_label = st.session_state[us_period_key]
                with st.spinner(f"{us_ticker} 데이터 불러오는 중..."):
                    info, hist = get_us_stock(us_ticker, us_yf_period)

            if info and hist is not None and len(hist) > 0:
                name = info.get("longName", us_ticker)
                price = info.get("currentPrice") or info.get("regularMarketPrice") or float(hist["Close"].iloc[-1])
                prev_close = info.get("previousClose", float(hist["Close"].iloc[-2]) if len(hist) > 1 else price)
                change_pct = (price - prev_close) / prev_close * 100

                st.markdown(f"#### {name} ({us_ticker})")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("현재가", f"${price:,.2f}", f"{'+' if change_pct>0 else ''}{change_pct:.2f}%")
                m2.metric("52주 최고", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")
                m3.metric("52주 최저", f"${info.get('fiftyTwoWeekLow', 'N/A')}")
                m4.metric("PER", f"{info.get('trailingPE', 'N/A'):.1f}" if isinstance(info.get('trailingPE'), float) else "N/A")

                us_annotated_key = f"us_annotated_{us_ticker}"
                us_chart_text_key = f"us_chart_text_{us_ticker}"
                if st.session_state.get(us_annotated_key):
                    fig = make_annotated_chart(hist, title=f"{us_ticker} ({us_period_label})", currency="USD")
                else:
                    fig = make_candle_chart(hist, title=f"{us_ticker} ({us_period_label})", currency="USD", height=450)
                st.plotly_chart(fig, use_container_width=True)

                if st.session_state.get(us_annotated_key):
                    st.caption("🟠 9일선 (단기 추세)  &nbsp;|&nbsp; 🟣 20일선 (중기 추세)  &nbsp;|&nbsp; 거래량은 상승일=빨강, 하락일=파랑")
                    if st.button("✖ 원래 차트로", key="us_chart_reset", use_container_width=False):
                        st.session_state[us_annotated_key] = False
                        st.session_state.pop(us_chart_text_key, None)
                        st.rerun()
                    if st.session_state.get(us_chart_text_key):
                        st.markdown(f'<div class="tip-box">{st.session_state[us_chart_text_key]}</div>', unsafe_allow_html=True)
                else:
                    show_chart_tip()

                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if st.button(f"🤖 AI가 {us_ticker} 쉽게 설명해줘", key="us_explain", use_container_width=True):
                        with st.spinner("AI 분석 중..."):
                            prompt = f"""
미국 주식 {name}({us_ticker})에 대해 주식 왕초보에게 설명해주세요.
현재가: ${price:.2f}, 전일 대비: {change_pct:.2f}%
PER: {info.get('trailingPE', 'N/A')}
52주 범위: ${info.get('fiftyTwoWeekLow', '?')} ~ ${info.get('fiftyTwoWeekHigh', '?')}
업종: {info.get('sector', '알 수 없음')}
1. 이 회사가 무엇을 하는 회사인지 (2-3줄)
2. 현재 주가가 어떤 상황인지 (쉽게)
3. 초보자가 알아야 할 주의사항
"""
                            answer = ai_analyze(prompt)
                        st.markdown(f'<div class="tip-box">{answer}</div>', unsafe_allow_html=True)
                with btn_col2:
                    existing_tickers = [w["ticker"] for w in st.session_state.get("watchlist", load_watchlist(session_id))]
                    if us_ticker in existing_tickers:
                        st.button("⭐ 관심종목에 추가됨", key="us_watch_add", disabled=True, use_container_width=True)
                    elif st.button("☆ 관심종목에 추가", key="us_watch_add", type="primary", use_container_width=True):
                        with st.spinner("추가 중..."):
                            ok, result = add_to_watchlist(us_ticker, "US", session_id)
                        if ok:
                            st.success(f"✅ {result} 관심종목에 추가됐어요!")
                            st.rerun()
                        else:
                            st.info("이미 관심종목에 있어요!")

                if st.button("📈 차트 패턴 AI 해석", key="us_chart_ai", use_container_width=True, type="primary"):
                    with st.spinner("차트 패턴 분석 중..."):
                        recent = hist.tail(20)
                        ohlcv_lines = [
                            f"{str(d)[:10]}: 시가={r['Open']:.2f}, 고가={r['High']:.2f}, 저가={r['Low']:.2f}, 종가={r['Close']:.2f}, 거래량={int(r['Volume'])}"
                            for d, r in recent.iterrows()
                        ]
                        ohlcv_str = "\n".join(ohlcv_lines)
                        chart_prompt = f"""다음은 미국 주식 {name}({us_ticker})의 최근 {len(recent)}일 캔들 데이터입니다 (USD):

{ohlcv_str}

위 데이터를 바탕으로 주식 왕초보에게 차트 패턴을 쉽게 설명해주세요:
1. 현재 추세 — 상승/하락/횡보 중 어디인지, 왜 그렇게 보이는지
2. 눈에 띄는 캔들 패턴 — 망치형, 도지, 장악형 등 최근에 나타난 패턴
3. 지지선과 저항선 — 어떤 가격대에서 자주 멈추는지
4. 거래량 흐름 — 거래량이 많은 날과 가격 변화의 관계
5. 초보자 한마디 — 이 차트를 보고 주의해야 할 점 한 가지
어려운 용어는 꼭 쉬운 말로 풀어서 설명해주세요."""
                        chart_answer = ai_analyze(chart_prompt)
                    st.session_state[us_annotated_key] = True
                    st.session_state[us_chart_text_key] = chart_answer
                    st.rerun()

                # ── 🎯 매수·손절·익절 가이드
                st.markdown("---")
                st.markdown("#### 🎯 매수·손절·익절 가이드")
                st.caption("⚠️ 아래 가격은 참고용이에요. 실제 투자 결정은 본인이 직접 하세요.")

                g1, g2 = st.columns(2)
                with g1:
                    st.markdown("**🔴 손절 기준가 (Stop Loss)**")
                    for pct in [5, 10, 15]:
                        sl = price * (1 - pct / 100)
                        st.markdown(f"- **-{pct}%** → `${sl:.2f}`")
                with g2:
                    st.markdown("**🟢 익절 목표가 (Take Profit)**")
                    for pct in [10, 20, 30]:
                        tp = price * (1 + pct / 100)
                        st.markdown(f"- **+{pct}%** → `${tp:.2f}`")

                if st.button("🤖 지금 이 종목 사도 될까? AI 판단", key="us_entry_ai", use_container_width=True):
                    with st.spinner("AI가 매수 시점을 분석하는 중..."):
                        recent20 = hist.tail(20)
                        price_5d_ago = float(hist["Close"].iloc[-6]) if len(hist) >= 6 else price
                        trend_5d = (price - price_5d_ago) / price_5d_ago * 100
                        ohlcv_lines2 = [
                            f"{str(d)[:10]}: 종가={r['Close']:.2f}, 거래량={int(r['Volume'])}"
                            for d, r in recent20.iterrows()
                        ]
                        entry_prompt = f"""미국 주식 {name}({us_ticker}) 매수 시점 분석을 요청합니다.

[현재 데이터]
현재가: ${price:.2f}
5일 등락: {'+' if trend_5d >= 0 else ''}{trend_5d:.2f}%
52주 고가: ${info.get('fiftyTwoWeekHigh', '?')}  /  52주 저가: ${info.get('fiftyTwoWeekLow', '?')}
PER: {info.get('trailingPE', 'N/A')}

[최근 20일 종가·거래량]
{chr(10).join(ohlcv_lines2)}

주식 왕초보를 위해 다음을 쉽게 설명해주세요:
1. 지금 이 시점이 매수하기 좋은가, 나쁜가, 애매한가? (이유 포함)
2. 만약 산다면 어느 가격대에서 손절할지 (구체적 가격 제시)
3. 목표 익절가 시나리오 1~2개 (구체적 가격 제시)
4. 초보자가 이 종목 살 때 특히 주의할 점
주의: 이건 교육 목적 참고 의견이고 실제 투자 결정은 본인이 해야 한다고 꼭 언급해주세요."""
                        entry_answer = ai_analyze(entry_prompt)
                    st.markdown(f'<div class="strategy-box">{entry_answer}</div>', unsafe_allow_html=True)
            else:
                st.error(f"'{us_ticker}' 데이터를 찾을 수 없어요. 티커를 다시 확인해주세요.")

    with tab2:
        st.markdown("#### 한국 주식 검색")
        st.caption("예시: 005930(삼성전자), 000660(SK하이닉스), 035420(NAVER), 069500(KODEX200 ETF)")

        popular_kr = {
            "삼성전자 (005930)": "005930",
            "SK하이닉스 (000660)": "000660",
            "NAVER (035420)": "035420",
            "카카오 (035720)": "035720",
            "KODEX200 ETF (069500)": "069500",
            "TIGER미국S&P500 ETF (360750)": "360750",
        }

        with st.expander("🔍 회사 이름으로 검색"):
            kr_name_q = st.text_input("회사 이름 입력", placeholder="예: 삼성, 카카오, TIGER", key="kr_name_q")
            if kr_name_q and len(kr_name_q) >= 2:
                with st.spinner("검색 중..."):
                    kr_name_map = get_krx_name_map()
                    kr_results = search_kr_stocks(kr_name_q, kr_name_map)
                if kr_results:
                    st.caption("아래 종목을 클릭하면 바로 조회돼요")
                    krc1, krc2 = st.columns(2)
                    for i, r in enumerate(kr_results):
                        with (krc1 if i % 2 == 0 else krc2):
                            if st.button(f"**{r['ticker']}** — {r['name']}", key=f"kr_sr_{i}", use_container_width=True):
                                st.session_state["kr_input"] = r["ticker"]
                                st.rerun()
                else:
                    st.caption("검색 결과가 없어요. 다른 키워드로 시도해보세요.")

        col_c, col_d = st.columns([2, 1])
        with col_c:
            kr_ticker = st.text_input("종목 코드 직접 입력 (6자리)", placeholder="예: 005930", key="kr_input").strip()
        with col_d:
            selected_kr = st.selectbox("인기 종목", ["직접 입력"] + list(popular_kr.keys()), key="kr_popular")

        if selected_kr != "직접 입력":
            kr_ticker = popular_kr[selected_kr]

        if kr_ticker:
            # ── 기간 버튼
            kr_period_key = f"kr_period_{kr_ticker}"
            if kr_period_key not in st.session_state:
                st.session_state[kr_period_key] = "6개월"
            period_cols = st.columns(len(PERIOD_MAP))
            for pi, pname in enumerate(PERIOD_MAP):
                with period_cols[pi]:
                    is_sel = st.session_state[kr_period_key] == pname
                    if st.button(pname, key=f"kr_p_{pname}",
                                 type="primary" if is_sel else "secondary",
                                 use_container_width=True):
                        st.session_state[kr_period_key] = pname
                        st.session_state.pop(f"kr_custom_{kr_ticker}", None)
                        st.rerun()

            # ── 날짜 직접 선택
            with st.expander("📅 날짜 직접 선택"):
                dc1, dc2, dc3 = st.columns([2, 2, 1])
                with dc1:
                    kr_start = st.date_input("시작일", value=datetime.today() - timedelta(days=180),
                                             min_value=datetime(2000, 1, 1), max_value=datetime.today(),
                                             key=f"kr_start_{kr_ticker}")
                with dc2:
                    kr_end = st.date_input("종료일", value=datetime.today(),
                                           min_value=datetime(2000, 1, 1), max_value=datetime.today(),
                                           key=f"kr_end_{kr_ticker}")
                with dc3:
                    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                    if st.button("조회", key=f"kr_custom_btn_{kr_ticker}", type="primary", use_container_width=True):
                        st.session_state[f"kr_custom_{kr_ticker}"] = (str(kr_start), str(kr_end))
                        st.rerun()

            # 커스텀 기간 vs 버튼 기간
            custom_range = st.session_state.get(f"kr_custom_{kr_ticker}")
            if custom_range:
                period_label = f"{custom_range[0]} ~ {custom_range[1]}"
                with st.spinner(f"{kr_ticker} 데이터 불러오는 중..."):
                    kr_data = get_kr_stock_range(kr_ticker, custom_range[0], custom_range[1])
            else:
                kr_days = PERIOD_MAP[st.session_state[kr_period_key]]["days"]
                period_label = st.session_state[kr_period_key]
                with st.spinner(f"{kr_ticker} 데이터 불러오는 중..."):
                    kr_data = get_kr_stock(kr_ticker, kr_days)

            if kr_data is not None and len(kr_data) > 1:
                kr_name = get_krx_name_map().get(kr_ticker.zfill(6), kr_ticker)
                latest_price = float(kr_data["Close"].iloc[-1])
                prev_price = float(kr_data["Close"].iloc[-2])
                change_pct = (latest_price - prev_price) / prev_price * 100
                high_52 = float(kr_data["Close"].max())
                low_52 = float(kr_data["Close"].min())

                st.markdown(f"#### {kr_name} ({kr_ticker})")
                m1, m2, m3 = st.columns(3)
                m1.metric("현재가", f"₩{latest_price:,.0f}", f"{'+' if change_pct>0 else ''}{change_pct:.2f}%")
                m2.metric("기간 최고", f"₩{high_52:,.0f}")
                m3.metric("기간 최저", f"₩{low_52:,.0f}")

                kr_annotated_key = f"kr_annotated_{kr_ticker}"
                kr_chart_text_key = f"kr_chart_text_{kr_ticker}"
                if st.session_state.get(kr_annotated_key):
                    fig = make_annotated_chart(kr_data, title=f"{kr_name} ({period_label})", currency="KRW")
                else:
                    fig = make_candle_chart(kr_data, title=f"{kr_name} ({period_label})", currency="KRW", height=450)
                st.plotly_chart(fig, use_container_width=True)

                if st.session_state.get(kr_annotated_key):
                    st.caption("🟠 9일선 (단기 추세)  &nbsp;|&nbsp; 🟣 20일선 (중기 추세)  &nbsp;|&nbsp; 거래량은 상승일=빨강, 하락일=파랑")
                    if st.button("✖ 원래 차트로", key="kr_chart_reset", use_container_width=False):
                        st.session_state[kr_annotated_key] = False
                        st.session_state.pop(kr_chart_text_key, None)
                        st.rerun()
                    if st.session_state.get(kr_chart_text_key):
                        st.markdown(f'<div class="tip-box">{st.session_state[kr_chart_text_key]}</div>', unsafe_allow_html=True)
                else:
                    show_chart_tip()

                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if st.button("🤖 AI가 이 종목 쉽게 설명해줘", key="kr_explain", use_container_width=True):
                        with st.spinner("AI 분석 중..."):
                            prompt = f"""
한국 주식 {kr_name}({kr_ticker})에 대해 주식 왕초보에게 설명해주세요.
현재가: ₩{latest_price:,.0f}, 전일 대비: {change_pct:.2f}%
3개월 범위: ₩{low_52:,.0f} ~ ₩{high_52:,.0f}
1. 현재 주가 상황 (쉽게)
2. 초보자가 한국 주식 볼 때 주의점
"""
                            answer = ai_analyze(prompt)
                        st.markdown(f'<div class="tip-box">{answer}</div>', unsafe_allow_html=True)
                with btn_col2:
                    existing_tickers = [w["ticker"] for w in st.session_state.get("watchlist", load_watchlist(session_id))]
                    if kr_ticker in existing_tickers:
                        st.button("⭐ 관심종목에 추가됨", key="kr_watch_add", disabled=True, use_container_width=True)
                    elif st.button("☆ 관심종목에 추가", key="kr_watch_add", type="primary", use_container_width=True):
                        with st.spinner("추가 중..."):
                            ok, result = add_to_watchlist(kr_ticker, "KR", session_id)
                        if ok:
                            st.success(f"✅ {result} 관심종목에 추가됐어요!")
                            st.rerun()
                        else:
                            st.info("이미 관심종목에 있어요!")

                if st.button("📈 차트 패턴 AI 해석", key="kr_chart_ai", use_container_width=True, type="primary"):
                    with st.spinner("차트 패턴 분석 중..."):
                        recent = kr_data.tail(20)
                        ohlcv_lines = [
                            f"{str(d)[:10]}: 시가={r['Open']:,.0f}, 고가={r['High']:,.0f}, 저가={r['Low']:,.0f}, 종가={r['Close']:,.0f}, 거래량={int(r['Volume'])}"
                            for d, r in recent.iterrows()
                        ]
                        ohlcv_str = "\n".join(ohlcv_lines)
                        chart_prompt = f"""다음은 한국 주식 {kr_name}({kr_ticker})의 최근 {len(recent)}일 캔들 데이터입니다 (KRW):

{ohlcv_str}

위 데이터를 바탕으로 주식 왕초보에게 차트 패턴을 쉽게 설명해주세요:
1. 현재 추세 — 상승/하락/횡보 중 어디인지, 왜 그렇게 보이는지
2. 눈에 띄는 캔들 패턴 — 망치형, 도지, 장악형 등 최근에 나타난 패턴
3. 지지선과 저항선 — 어떤 가격대에서 자주 멈추는지
4. 거래량 흐름 — 거래량이 많은 날과 가격 변화의 관계
5. 초보자 한마디 — 이 차트를 보고 주의해야 할 점 한 가지
어려운 용어는 꼭 쉬운 말로 풀어서 설명해주세요."""
                        chart_answer = ai_analyze(chart_prompt)
                    st.session_state[kr_annotated_key] = True
                    st.session_state[kr_chart_text_key] = chart_answer
                    st.rerun()

                # ── 🎯 매수·손절·익절 가이드
                st.markdown("---")
                st.markdown("#### 🎯 매수·손절·익절 가이드")
                st.caption("⚠️ 아래 가격은 참고용이에요. 실제 투자 결정은 본인이 직접 하세요.")

                g1, g2 = st.columns(2)
                with g1:
                    st.markdown("**🔴 손절 기준가 (Stop Loss)**")
                    for pct in [5, 10, 15]:
                        sl = latest_price * (1 - pct / 100)
                        st.markdown(f"- **-{pct}%** → `₩{sl:,.0f}`")
                with g2:
                    st.markdown("**🟢 익절 목표가 (Take Profit)**")
                    for pct in [10, 20, 30]:
                        tp = latest_price * (1 + pct / 100)
                        st.markdown(f"- **+{pct}%** → `₩{tp:,.0f}`")

                if st.button("🤖 지금 이 종목 사도 될까? AI 판단", key="kr_entry_ai", use_container_width=True):
                    with st.spinner("AI가 매수 시점을 분석하는 중..."):
                        price_5d_ago = float(kr_data["Close"].iloc[-6]) if len(kr_data) >= 6 else latest_price
                        trend_5d = (latest_price - price_5d_ago) / price_5d_ago * 100
                        recent20 = kr_data.tail(20)
                        ohlcv_lines_kr = [
                            f"{str(d)[:10]}: 종가={r['Close']:,.0f}, 거래량={int(r['Volume'])}"
                            for d, r in recent20.iterrows()
                        ]
                        entry_prompt_kr = f"""한국 주식 {kr_name}({kr_ticker}) 매수 시점 분석을 요청합니다.

[현재 데이터]
현재가: ₩{latest_price:,.0f}
5일 등락: {'+' if trend_5d >= 0 else ''}{trend_5d:.2f}%
기간 고가: ₩{high_52:,.0f}  /  기간 저가: ₩{low_52:,.0f}

[최근 20일 종가·거래량]
{chr(10).join(ohlcv_lines_kr)}

주식 왕초보를 위해 다음을 쉽게 설명해주세요:
1. 지금 이 시점이 매수하기 좋은가, 나쁜가, 애매한가? (이유 포함)
2. 만약 산다면 어느 가격대에서 손절할지 (구체적 가격 제시)
3. 목표 익절가 시나리오 1~2개 (구체적 가격 제시)
4. 초보자가 이 종목 살 때 특히 주의할 점
주의: 이건 교육 목적 참고 의견이고 실제 투자 결정은 본인이 해야 한다고 꼭 언급해주세요."""
                        entry_answer_kr = ai_analyze(entry_prompt_kr)
                    st.markdown(f'<div class="strategy-box">{entry_answer_kr}</div>', unsafe_allow_html=True)
            else:
                st.error(f"'{kr_ticker}' 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요.")

# ── 페이지 5: 투자 일지 ──────────────────────────────────────
elif page == "📓 투자 일지":
    st.markdown("""
    <div class="page-header">
        <div class="icon">📓</div>
        <h1>나의 투자 일지</h1>
        <p>매수·매도 기록을 남기고 실시간 손익 · AI 패턴 분석까지</p>
    </div>""", unsafe_allow_html=True)

    if "journal" not in st.session_state:
        st.session_state.journal = load_journal(session_id)

    # ── 거래 입력 폼 ──
    st.markdown("### ✏️ 거래 기록 추가")
    with st.form(key="journal_form", clear_on_submit=True):
        jc1, jc2, jc3 = st.columns([2, 1, 1])
        with jc1:
            j_ticker = st.text_input("종목 코드", placeholder="예: 005930, AAPL")
        with jc2:
            j_market = st.selectbox("시장", ["🇰🇷 한국", "🇺🇸 미국"])
        with jc3:
            j_type = st.selectbox("거래 유형", ["매수", "매도"])

        jc4, jc5, jc6 = st.columns([2, 1, 1])
        with jc4:
            j_date = st.date_input("거래일", value=datetime.today())
        with jc5:
            j_price = st.number_input("거래 가격", min_value=0.0, step=0.01, format="%.2f")
        with jc6:
            j_qty = st.number_input("수량 (주)", min_value=1, step=1, value=1)

        j_memo = st.text_input("메모 (선택)", placeholder="예: 실적 발표 전 매수, 목표가 도달 매도")
        j_submitted = st.form_submit_button("기록 추가", use_container_width=True, type="primary")

    if j_submitted and j_ticker and j_price > 0:
        market_tag = "KR" if "한국" in j_market else "US"
        ticker = j_ticker.strip().upper() if market_tag == "US" else j_ticker.strip()
        # 종목명 조회
        if market_tag == "KR":
            name = get_krx_name_map().get(ticker.zfill(6), ticker)
        else:
            try:
                name = yf.Ticker(ticker).info.get("shortName", ticker)
            except Exception:
                name = ticker
        entry = {
            "id": str(uuid.uuid4())[:8],
            "ticker": ticker,
            "name": name,
            "market": market_tag,
            "type": j_type,
            "date": str(j_date),
            "price": j_price,
            "quantity": int(j_qty),
            "amount": round(j_price * j_qty, 2),
            "memo": j_memo,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        st.session_state.journal.insert(0, entry)
        save_journal(session_id, st.session_state.journal)
        flag = "🇰🇷" if market_tag == "KR" else "🇺🇸"
        currency = "₩" if market_tag == "KR" else "$"
        st.success(f"✅ {flag} {name} {j_type} {j_qty}주 @ {currency}{j_price:,.2f} 기록됐어요!")
        st.rerun()

    st.markdown("---")

    if not st.session_state.journal:
        st.markdown("""
        <div class="tip-box">
        💡 <b>이렇게 사용해보세요!</b><br>
        • 매수할 때마다 기록 → 평균 매수가 자동 계산<br>
        • 매도 후 기록 → 수익률 자동 계산<br>
        • AI 분석 → 내 투자 패턴의 장단점 피드백
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── 요약 통계 ──
        st.markdown("### 📊 거래 요약")
        total_trades = len(st.session_state.journal)
        buy_trades = [t for t in st.session_state.journal if t["type"] == "매수"]
        sell_trades = [t for t in st.session_state.journal if t["type"] == "매도"]
        total_invested = sum(t["amount"] for t in buy_trades)
        total_sold = sum(t["amount"] for t in sell_trades)

        # 달러/원 분리 계산
        us_invested  = sum(t["amount"] for t in buy_trades if t["market"] == "US")
        kr_invested  = sum(t["amount"] for t in buy_trades if t["market"] == "KR")
        _usdkrw      = get_usdkrw()
        total_krw    = kr_invested + us_invested * _usdkrw

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("총 거래 횟수", f"{total_trades}회")
        sc2.metric("매수 횟수", f"{len(buy_trades)}회")
        sc3.metric("매도 횟수", f"{len(sell_trades)}회")
        with sc4:
            st.metric("총 매수금액 (원화 합산)", f"₩{total_krw:,.0f}")
            parts = []
            if us_invested > 0:
                parts.append(f"🇺🇸 ${us_invested:,.2f}")
            if kr_invested > 0:
                parts.append(f"🇰🇷 ₩{kr_invested:,.0f}")
            if parts:
                st.caption("  +  ".join(parts) + f"  (환율 ₩{_usdkrw:,.0f})")

        st.markdown("---")

        # ── AI 분석 버튼 ──
        if st.button("🤖 내 투자 기록 AI 분석해줘", use_container_width=True, type="primary"):
            with st.spinner("AI가 투자 패턴 분석 중..."):
                records_text = "\n".join([
                    f"- {t['date']} | {t['name']}({t['ticker']}) | {t['type']} | "
                    f"{'₩' if t['market']=='KR' else '$'}{t['price']:,.2f} × {t['quantity']}주 "
                    f"| 메모: {t['memo'] or '없음'}"
                    for t in st.session_state.journal
                ])
                analysis_prompt = f"""
다음은 주식 왕초보의 실제 매수·매도 기록이에요. 분석해주세요.

거래 내역:
{records_text}

다음 항목으로 분석해주세요:
## 📌 투자 성향 분석
(어떤 종목을 선호하는지, 단기/장기 성향 등)

## ✅ 잘한 점
(좋아 보이는 결정이나 패턴)

## 💡 개선할 점
(아쉬운 점이나 초보자가 주의할 것들)

## 🎯 앞으로의 제안
(이 투자 패턴에서 발전할 수 있는 방향)

모든 설명은 왕초보도 이해하는 쉬운 말로, 격려하는 톤으로 써주세요.
"""
                analysis = ai_analyze(analysis_prompt)
            st.markdown(f'<div class="strategy-box">{analysis}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📋 거래 내역")

        tab_all, tab_grouped = st.tabs(["📄 전체 내역", "📦 종목별 묶음"])

        if "editing_id" not in st.session_state:
            st.session_state.editing_id = None
        if "split_ticker" not in st.session_state:
            st.session_state.split_ticker = None

        # ══ 전체 내역 탭 ══════════════════════════════════════
        with tab_all:

            hj1,hj2,hj3,hj4,hj5,hj6,hj7 = st.columns([1.2,2,1,1.5,1,2,1.2])
            for col, label in zip([hj1,hj2,hj3,hj4,hj5,hj6,hj7],
                                   ["날짜","종목","구분","가격","수량","메모",""]):
                col.markdown(f'<span style="font-size:0.78rem;color:#888;font-weight:bold">{label}</span>',
                             unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 8px 0;border-color:#ddd'>", unsafe_allow_html=True)

            for idx, trade in enumerate(st.session_state.journal):
                flag = "🇰🇷" if trade["market"] == "KR" else "🇺🇸"
                currency = "₩" if trade["market"] == "KR" else "$"
                type_color = "#e53935" if trade["type"] == "매수" else "#1565c0"
                tid = trade["id"]

                # ── 수정 모드
                if st.session_state.editing_id == tid:
                    with st.form(key=f"edit_form_{tid}"):
                        ec1, ec2, ec3 = st.columns([2, 1, 1])
                        with ec1:
                            e_date = st.date_input("거래일", value=datetime.strptime(trade["date"], "%Y-%m-%d"))
                        with ec2:
                            e_price = st.number_input("가격", value=float(trade["price"]), min_value=0.0, step=0.01, format="%.2f")
                        with ec3:
                            e_qty = st.number_input("수량", value=int(trade["quantity"]), min_value=1, step=1)
                        e_type = st.selectbox("구분", ["매수", "매도"], index=0 if trade["type"] == "매수" else 1)
                        e_memo = st.text_input("메모", value=trade.get("memo", ""))
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            save_btn = st.form_submit_button("💾 저장", use_container_width=True, type="primary")
                        with cancel_col:
                            cancel_btn = st.form_submit_button("취소", use_container_width=True)

                    if save_btn:
                        for t in st.session_state.journal:
                            if t["id"] == tid:
                                t["date"] = str(e_date)
                                t["price"] = e_price
                                t["quantity"] = int(e_qty)
                                t["amount"] = round(e_price * e_qty, 2)
                                t["type"] = e_type
                                t["memo"] = e_memo
                        save_journal(session_id, st.session_state.journal)
                        st.session_state.editing_id = None
                        st.rerun()
                    if cancel_btn:
                        st.session_state.editing_id = None
                        st.rerun()

                else:
                    c1,c2,c3,c4,c5,c6,c7 = st.columns([1.2,2,1,1.5,1,2,1.2])
                    c1.caption(trade["date"])
                    c2.markdown(f"**{flag} {trade['name']}**")
                    c3.markdown(f'<span style="color:{type_color};font-weight:bold">{trade["type"]}</span>', unsafe_allow_html=True)
                    c4.markdown(f"`{currency}{trade['price']:,.2f}`")
                    c5.caption(f"{trade['quantity']}주")
                    c6.caption(trade.get("memo") or "-")
                    with c7:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button("수정", key=f"edit_{tid}_{idx}", use_container_width=True):
                                st.session_state.editing_id = tid
                                st.rerun()
                        with btn_c2:
                            if st.button("삭제", key=f"del_{tid}_{idx}", use_container_width=True):
                                st.session_state.journal = [t for t in st.session_state.journal if t["id"] != tid]
                                save_journal(session_id, st.session_state.journal)
                                st.rerun()

        # ══ 종목별 묶음 탭 ════════════════════════════════════
        with tab_grouped:
            usdkrw = get_usdkrw()
            st.caption(f"💱 현재 환율: $1 = ₩{usdkrw:,.0f}  |  현재가 기준 평가손익")

            ticker_order = list(dict.fromkeys(t["ticker"] for t in st.session_state.journal))
            for tk in ticker_order:
                tk_trades = [t for t in st.session_state.journal if t["ticker"] == tk]
                buys  = [t for t in tk_trades if t["type"] == "매수"]
                sells = [t for t in tk_trades if t["type"] == "매도"]
                market = tk_trades[0]["market"]
                flag     = "🇰🇷" if market == "KR" else "🇺🇸"
                currency = "₩" if market == "KR" else "$"
                name = tk_trades[0]["name"]

                total_buy_qty  = sum(t["quantity"] for t in buys)
                total_sell_qty = sum(t["quantity"] for t in sells)
                hold_qty = total_buy_qty - total_sell_qty
                avg_buy = (sum(t["price"] * t["quantity"] for t in buys) / total_buy_qty) if buys else 0
                total_invested = avg_buy * total_buy_qty

                # 현재가 & 평가손익
                cur_price = get_current_price(tk, market)
                if cur_price and hold_qty > 0:
                    eval_val_native = cur_price * hold_qty          # 현재 평가금액 (원화 or USD)
                    cost_native     = avg_buy * hold_qty            # 매수금액
                    pnl_native      = eval_val_native - cost_native # 평가손익
                    pnl_pct         = pnl_native / cost_native * 100 if cost_native else 0
                    # 원화 환산 (미국주식)
                    if market == "US":
                        eval_val_krw = eval_val_native * usdkrw
                        pnl_krw      = pnl_native * usdkrw
                    else:
                        eval_val_krw = eval_val_native
                        pnl_krw      = pnl_native
                    sign = "+" if pnl_pct >= 0 else ""
                    price_str = f"{currency}{cur_price:,.2f}"
                    pnl_emoji = "🔺" if pnl_pct >= 0 else "🔻"
                    pnl_badge = f"{pnl_emoji} {sign}{pnl_pct:.2f}%"
                else:
                    eval_val_krw = pnl_krw = pnl_pct = None
                    price_str = "조회 중..."
                    pnl_badge = ""

                label = f"{flag} {name} ({tk})  |  현재가 {price_str}  {pnl_badge}"
                with st.expander(label, expanded=False):
                    # ── 핵심 지표 카드
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("평균 매수가", f"{currency}{avg_buy:,.2f}")
                    m2.metric("보유 수량", f"{hold_qty}주")
                    if cur_price and hold_qty > 0:
                        m3.metric("평가금액 (원화)", f"₩{eval_val_krw:,.0f}")
                        delta_str = f"{sign}{pnl_pct:.2f}% (₩{pnl_krw:+,.0f})"
                        m4.metric("평가손익", f"₩{pnl_krw:,.0f}", delta=delta_str)
                    else:
                        m3.metric("평가금액", "-")
                        m4.metric("평가손익", "-")

                    # ── 실현 손익 (매도 있을 때)
                    if sells:
                        avg_sell = sum(t["price"]*t["quantity"] for t in sells) / sum(t["quantity"] for t in sells)
                        realized_pnl = (avg_sell - avg_buy) * total_sell_qty
                        realized_pct = realized_pnl / (avg_buy * total_sell_qty) * 100
                        r_color = "#e53935" if realized_pnl >= 0 else "#1565c0"
                        r_sign  = "+" if realized_pnl >= 0 else ""
                        realized_krw = realized_pnl * usdkrw if market == "US" else realized_pnl
                        st.markdown(
                            f'💰 **실현손익** (매도 {total_sell_qty}주): '
                            f'<span style="color:{r_color};font-weight:bold">'
                            f'{r_sign}{realized_pct:.2f}% (₩{realized_krw:+,.0f})</span>',
                            unsafe_allow_html=True
                        )

                    st.markdown("---")
                    st.markdown("**거래 상세**")
                    for t in sorted(tk_trades, key=lambda x: x["date"]):
                        ttype_color = "#e53935" if t["type"] == "매수" else "#1565c0"
                        memo_str = f" — {t['memo']}" if t.get("memo") else ""
                        st.markdown(
                            f"- {t['date']} &nbsp; "
                            f'<span style="color:{ttype_color};font-weight:bold">{t["type"]}</span>'
                            f" &nbsp; {currency}{t['price']:,.2f} × {t['quantity']}주"
                            f" = {currency}{t['amount']:,.2f}{memo_str}",
                            unsafe_allow_html=True
                        )

                    # ── 주식 병합(리버스 스플릿) 처리
                    st.markdown("---")
                    if st.session_state.split_ticker == tk:
                        st.markdown("**⚙️ 주식 병합 처리**")
                        st.caption("병합 후 실제 수량과 평균단가를 입력하면 기존 매수 기록이 하나로 통합됩니다.")
                        with st.form(key=f"split_form_{tk}"):
                            sp1, sp2 = st.columns(2)
                            with sp1:
                                new_qty = st.number_input("병합 후 수량 (주)", min_value=1, step=1, value=1)
                            with sp2:
                                new_price = st.number_input(f"병합 후 평균단가 ({currency})", min_value=0.0001, step=0.01, format="%.4f", value=1.0)
                            sp_save_col, sp_cancel_col = st.columns(2)
                            with sp_save_col:
                                sp_submit = st.form_submit_button("✅ 적용", type="primary", use_container_width=True)
                            with sp_cancel_col:
                                sp_cancel_btn = st.form_submit_button("취소", use_container_width=True)
                        if sp_submit:
                            first_buy = buys[0] if buys else tk_trades[0]
                            new_record = {
                                "id": str(uuid.uuid4())[:8],
                                "date": first_buy["date"],
                                "ticker": tk,
                                "name": first_buy["name"],
                                "market": first_buy["market"],
                                "type": "매수",
                                "price": round(float(new_price), 4),
                                "quantity": int(new_qty),
                                "amount": round(float(new_price) * int(new_qty), 2),
                                "memo": "주식 병합 후 통합 기록"
                            }
                            st.session_state.journal = [
                                t for t in st.session_state.journal
                                if not (t["ticker"] == tk and t["type"] == "매수")
                            ]
                            st.session_state.journal.append(new_record)
                            save_journal(session_id, st.session_state.journal)
                            st.session_state.split_ticker = None
                            st.rerun()
                        if sp_cancel_btn:
                            st.session_state.split_ticker = None
                            st.rerun()
                    else:
                        if st.button("⚙️ 주식 병합 처리", key=f"split_btn_{tk}",
                                     help="리버스 스플릿(주식 병합) 발생 시 클릭"):
                            st.session_state.split_ticker = tk
                            st.rerun()

# ── 페이지 3: 나만의 전략 ─────────────────────────────────────
elif page == "🎯 나만의 전략":
    st.markdown("""
    <div class="page-header">
        <div class="icon">🎯</div>
        <h1>나만의 투자 전략</h1>
        <p>내 상황에 맞는 현실적인 초보자 전략을 AI가 제안해드려요</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="strategy-box">
    ⚠️ <b>꼭 읽어주세요!</b><br>
    아래 전략은 <b>교육 목적</b>의 참고 자료입니다. 실제 투자 결정은 본인이 직접 판단하세요.
    주식 투자에는 원금 손실 위험이 있으며, 투자 금액은 <b>잃어도 괜찮은 여유자금</b>으로만 하세요.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📝 나의 투자 상황 입력")

    col1, col2 = st.columns(2)
    with col1:
        invest_amount = st.selectbox(
            "💰 월 투자 가능 금액",
            ["10만원 이하", "10~30만원", "30~50만원", "50~100만원", "100만원 이상"]
        )
        invest_goal = st.selectbox(
            "🎯 투자 목표",
            ["노후 준비 (10년 이상)", "목돈 마련 (3~10년)", "단기 수익 (1~3년)", "경험 쌓기 (지금은 소액)"]
        )
        market_pref = st.multiselect(
            "🌍 관심 시장",
            ["한국 주식 (코스피/코스닥)", "미국 주식", "둘 다"],
            default=["둘 다"]
        )

    with col2:
        risk_level = st.select_slider(
            "⚡ 리스크(위험) 감수 정도",
            options=["매우 낮게 (안전 최우선)", "낮게", "보통", "높게", "매우 높게 (수익 최우선)"],
            value="낮게"
        )
        invest_knowledge = st.selectbox(
            "📚 현재 나의 주식 지식 수준",
            ["완전 초보 (아무것도 모름)", "기초 조금 앎 (주식이 뭔지는 앎)", "중급 (PER, ETF 정도는 앎)"]
        )
        worry = st.text_input("😟 가장 걱정되는 것 (선택)", placeholder="예: 잃을까봐 무서워요, 언제 팔아야 할지 모르겠어요")

    st.markdown("---")

    if st.button("🤖 나만의 전략 만들어줘!", use_container_width=True, type="primary"):
        with st.spinner("AI가 맞춤 전략을 작성 중이에요... (10~20초 걸려요)"):
            prompt = f"""
주식 왕초보를 위한 맞춤형 현실적 투자 전략을 작성해주세요.

사용자 정보:
- 월 투자 가능 금액: {invest_amount}
- 투자 목표: {invest_goal}
- 관심 시장: {', '.join(market_pref)}
- 리스크 감수 수준: {risk_level}
- 현재 지식 수준: {invest_knowledge}
- 가장 걱정되는 것: {worry if worry else '없음'}

## 🌟 한줄 요약
## 📌 추천 투자 방식
## 💼 추천 투자 대상 (예시)
## ⚠️ 이것만은 꼭!
## 📅 3개월 공부 로드맵

모든 내용은 왕초보도 이해하는 쉬운 말로 써주세요.
투자 원금 손실 가능성을 반드시 언급하고, 여유자금 투자를 강조해주세요.
"""
            strategy = ai_analyze(prompt)

        st.markdown(f'<div class="strategy-box">{strategy}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 💬 전략에 대해 더 물어보기")
        follow_up = st.chat_input("전략에 대해 궁금한 점을 물어보세요!")
        if follow_up:
            with st.spinner("답변 중..."):
                answer = ai_analyze(follow_up)
            st.markdown(f'<div class="tip-box">{answer}</div>', unsafe_allow_html=True)
