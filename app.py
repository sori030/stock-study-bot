import streamlit as st
import google.generativeai as genai
import yfinance as yf
import FinanceDataReader as fdr
import plotly.graph_objects as go
import pandas as pd
import os
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="나의 주식 비서",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .big-title { font-size: 1.8rem; font-weight: bold; color: #1f77b4; }
    .tip-box {
        background: #f0f7ff;
        border-left: 4px solid #1f77b4;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .strategy-box {
        background: #fff8e1;
        border-left: 4px solid #ffa000;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .history-date {
        font-size: 0.75rem;
        color: #999;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── 대화 저장 파일 경로 ────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(messages):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)

def build_gemini_history(messages):
    """저장된 메시지를 Gemini 세션용 형식으로 변환"""
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [{"text": msg["content"]}]})
    return history

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
        ["📚 공부방", "📊 주식 정보", "🎯 나만의 전략"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 대화 내역 요약
    saved = load_history()
    if saved:
        total = len(saved)
        last_time = saved[-1].get("timestamp", "")
        st.markdown("#### 💾 저장된 대화")
        st.caption(f"총 {total}개 메시지")
        if last_time:
            st.caption(f"마지막: {last_time[:16]}")
    else:
        st.markdown("#### 💾 저장된 대화")
        st.caption("아직 대화 내역이 없어요")

    st.markdown("---")
    st.markdown("#### 📌 오늘의 한마디")
    st.info("주식은 단기가 아닌 장기 여정입니다. 꾸준히 공부하는 게 가장 좋은 전략이에요! 💪")

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
    st.session_state.messages = load_history()

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=SYSTEM_PROMPT
    )
    # 저장된 대화가 있으면 Gemini 세션에 이어받기
    gemini_history = build_gemini_history(st.session_state.messages)
    st.session_state.chat_session = model.start_chat(history=gemini_history)

# ── 주식 데이터 함수 ──────────────────────────────────────────
@st.cache_data(ttl=300)
def get_us_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")
        return info, hist
    except Exception:
        return None, None

@st.cache_data(ttl=300)
def get_kr_stock(ticker):
    try:
        end = datetime.today()
        start = end - timedelta(days=90)
        df = fdr.DataReader(ticker, start, end)
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

def add_message(role, content):
    """메시지를 세션과 파일에 동시에 저장"""
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.messages.append(msg)
    save_history(st.session_state.messages)

def ai_analyze(prompt):
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

# ── 페이지 1: 공부방 ──────────────────────────────────────────
if page == "📚 공부방":
    st.markdown('<div class="big-title">📚 공부방 — 무엇이든 물어보세요!</div>', unsafe_allow_html=True)
    st.caption("경제·주식 왕초보 전용 AI 선생님. 모르는 게 있으면 뭐든 물어보세요 😊")

    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("#### 빠른 질문")
        quick_qs = [
            "주식이 뭔가요?",
            "금리가 뭔가요?",
            "ETF가 뭔가요?",
            "PER이 뭔가요?",
            "환율이 주식에 미치는 영향은?",
            "코스피 vs 나스닥 차이는?",
            "인플레이션이 뭔가요?",
            "분산투자가 뭔가요?",
        ]
        for q in quick_qs:
            if st.button(q, use_container_width=True, key=f"quick_{q}"):
                st.session_state.pending_question = q

        st.markdown("---")
        if st.button("🗑️ 대화 내역 전체 삭제", use_container_width=True):
            st.session_state.messages = []
            clear_history()
            model = genai.GenerativeModel("gemini-2.5-flash-lite", system_instruction=SYSTEM_PROMPT)
            st.session_state.chat_session = model.start_chat(history=[])
            st.rerun()

    with col1:
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

        chat_container = st.container(height=450)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg.get("timestamp"):
                        st.markdown(f'<div class="history-date">{msg["timestamp"]}</div>', unsafe_allow_html=True)

        if "pending_question" in st.session_state and st.session_state.pending_question:
            user_input = st.session_state.pending_question
            st.session_state.pending_question = None
            add_message("user", user_input)
            with st.spinner("공부 중...✏️"):
                answer = ai_analyze(user_input)
            add_message("assistant", answer)
            st.rerun()

        user_input = st.chat_input("궁금한 걸 물어보세요! 아무것도 몰라도 괜찮아요 😊")
        if user_input:
            add_message("user", user_input)
            with st.spinner("공부 중...✏️"):
                answer = ai_analyze(user_input)
            add_message("assistant", answer)
            st.rerun()

# ── 페이지 2: 주식 정보 ───────────────────────────────────────
elif page == "📊 주식 정보":
    st.markdown('<div class="big-title">📊 실시간 주식 정보</div>', unsafe_allow_html=True)
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

        col_a, col_b = st.columns([2, 1])
        with col_a:
            us_ticker = st.text_input("티커 입력 (영문)", placeholder="예: AAPL", key="us_input").upper().strip()
        with col_b:
            selected_popular = st.selectbox("인기 종목", ["직접 입력"] + list(popular_us.keys()), key="us_popular")

        if selected_popular != "직접 입력":
            us_ticker = popular_us[selected_popular]

        if us_ticker:
            with st.spinner(f"{us_ticker} 데이터 불러오는 중..."):
                info, hist = get_us_stock(us_ticker)

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

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"],
                    mode="lines", name="종가",
                    line=dict(color="#1f77b4", width=2)
                ))
                fig.update_layout(
                    title=f"{us_ticker} 최근 3개월 주가",
                    xaxis_title="날짜", yaxis_title="가격 (USD)",
                    height=300, margin=dict(t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

                if st.button(f"🤖 AI가 {us_ticker} 쉽게 설명해줘", key="us_explain"):
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

        col_c, col_d = st.columns([2, 1])
        with col_c:
            kr_ticker = st.text_input("종목 코드 입력 (6자리)", placeholder="예: 005930", key="kr_input").strip()
        with col_d:
            selected_kr = st.selectbox("인기 종목", ["직접 입력"] + list(popular_kr.keys()), key="kr_popular")

        if selected_kr != "직접 입력":
            kr_ticker = popular_kr[selected_kr]

        if kr_ticker:
            with st.spinner(f"{kr_ticker} 데이터 불러오는 중..."):
                kr_data = get_kr_stock(kr_ticker)

            if kr_data is not None and len(kr_data) > 1:
                latest_price = float(kr_data["Close"].iloc[-1])
                prev_price = float(kr_data["Close"].iloc[-2])
                change_pct = (latest_price - prev_price) / prev_price * 100
                high_52 = float(kr_data["Close"].max())
                low_52 = float(kr_data["Close"].min())

                st.markdown(f"#### 종목 코드: {kr_ticker}")
                m1, m2, m3 = st.columns(3)
                m1.metric("현재가", f"₩{latest_price:,.0f}", f"{'+' if change_pct>0 else ''}{change_pct:.2f}%")
                m2.metric("3개월 최고", f"₩{high_52:,.0f}")
                m3.metric("3개월 최저", f"₩{low_52:,.0f}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=kr_data.index, y=kr_data["Close"],
                    mode="lines", name="종가",
                    line=dict(color="#e53935", width=2)
                ))
                fig.update_layout(
                    title=f"{kr_ticker} 최근 3개월 주가",
                    xaxis_title="날짜", yaxis_title="가격 (원)",
                    height=300, margin=dict(t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

                if st.button("🤖 AI가 이 종목 쉽게 설명해줘", key="kr_explain"):
                    with st.spinner("AI 분석 중..."):
                        prompt = f"""
한국 주식 종목코드 {kr_ticker}에 대해 주식 왕초보에게 설명해주세요.
현재가: ₩{latest_price:,.0f}, 전일 대비: {change_pct:.2f}%
3개월 범위: ₩{low_52:,.0f} ~ ₩{high_52:,.0f}
1. 현재 주가 상황 (쉽게)
2. 초보자가 한국 주식 볼 때 주의점
"""
                        answer = ai_analyze(prompt)
                    st.markdown(f'<div class="tip-box">{answer}</div>', unsafe_allow_html=True)
            else:
                st.error(f"'{kr_ticker}' 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요.")

# ── 페이지 3: 나만의 전략 ─────────────────────────────────────
elif page == "🎯 나만의 전략":
    st.markdown('<div class="big-title">🎯 나만의 투자 전략 만들기</div>', unsafe_allow_html=True)
    st.caption("내 상황에 맞는 현실적인 초보자 전략을 AI가 제안해드려요")

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
