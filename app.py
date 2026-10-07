import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="나만의 주식 모의투자 시뮬레이터", page_icon="📈", layout="wide")

DATA_FILE = "portfolio_data.json"

# 데이터 불러오기 함수
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

# 데이터 저장하기 함수
def save_data():
    data = {
        "cash": st.session_state.cash,
        "initial_cash": st.session_state.initial_cash,
        "portfolio": st.session_state.portfolio,
        "history": st.session_state.history
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 세션 초기화
saved_data = load_data()

if "cash" not in st.session_state:
    if saved_data:
        st.session_state.cash = saved_data.get("cash", 10000000.0)
        st.session_state.initial_cash = saved_data.get("initial_cash", 10000000.0)
        st.session_state.portfolio = saved_data.get("portfolio", {})
        st.session_state.history = saved_data.get("history", [])
    else:
        st.session_state.cash = 10000000.0
        st.session_state.initial_cash = 10000000.0
        st.session_state.portfolio = {}
        st.session_state.history = []

# 한글 금액 변환 유틸리티 함수 (예: 1604000 -> "160만 4,000원")
def format_krw(amount):
    try:
        amount = float(amount)
    except:
        return f"{amount}"
    
    if amount < 0:
        sign = "-"
        amount = abs(amount)
    else:
        sign = ""

    man = 10000
    eok = 100000000

    if amount >= eok:
        eok_part = int(amount // eok)
        rem_part = int((amount % eok) // man)
        if rem_part > 0:
            return f"{sign}{eok_part}억 {rem_part:,}원"
        else:
            return f"{sign}{eok_part}억원"
    elif amount >= man:
        man_part = int(amount // man)
        rem_part = int(amount % man)
        if rem_part > 0:
            return f"{sign}{man_part}만 {rem_part:,.0f}원"
        else:
            return f"{sign}{man_part}만원"
    else:
        return f"{sign}{amount:,.0f}원"

# 실시간 환율 조회 함수 (USD to KRW)
@st.cache_data(ttl=600)
def get_usd_krw_rate():
    try:
        ticker = yf.Ticker("USDKRW=X")
        df = ticker.history(period="1d")
        if not df.empty:
            return df['Close'].iloc[-1]
    except:
        pass
    return 1350.0  # 기본 Fallback 환율

st.title("📈 주식 재무제표 및 모의투자 연습 시뮬레이터")
st.markdown("재무제표를 분석하고 물타기/불타기 및 지정가 예약 매매 기능을 지원하는 업그레이드 시뮬레이터입니다!")

# 사이드바 설정 (자본금 셋팅, 추가, 리셋 분리)
st.sidebar.header("⚙️ 자산 설정 및 관리")

with st.sidebar.expander("🛠️ 초기 자본금 셋팅", expanded=False):
    new_initial = st.number_input("초기 자본금 설정 (원)", value=int(st.session_state.initial_cash), step=1000000)
    if st.button("초기 자본금 적용"):
        diff = new_initial - st.session_state.initial_cash
        st.session_state.initial_cash = float(new_initial)
        st.session_state.cash += diff # 기존 현금 잔액에도 차이 반영
        if st.session_state.cash < 0: 
            st.session_state.cash = 0.0
        save_data()
        st.success("초기 자본금이 설정되었습니다!")
        st.rerun()

with st.sidebar.expander("➕ 자본금 더 추가하기", expanded=False):
    add_amount = st.number_input("추가할 목돈 입력 (원)", value=10000000, step=1000000)
    if st.button("자본금 추가 반영"):
        st.session_state.cash += float(add_amount)
        st.session_state.initial_cash += float(add_amount) # 총 투입 원금도 함께 증가
        save_data()
        st.success(f"{add_amount:,.0f}원이 추가되었습니다!")
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🚨 계좌 전체 리셋 (초기화)"):
    st.session_state.cash = 10000000.0
    st.session_state.initial_cash = 10000000.0
    st.session_state.portfolio = {}
    st.session_state.history = []
    save_data()
    st.success("계좌가 완전히 초기화되었습니다!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **사용 안내:**
* **매수 시**: 신규 매수 또는 보유 종목 추가 매수(물타기/불타기), 지정가 매수를 지원합니다.
* **매도 시**: 현재가 또는 지정가(예약) 매도가 가능합니다.
""")

# 탭 메뉴 구성
tab1, tab2, tab3 = st.tabs(["💰 자산 및 포트폴리오", "🛒 주식 매수/매도", "📜 거래 및 투자 노트 복기"])

# --- 탭 1: 포트폴리오 현황 ---
with tab1:
    st.header("📊 내 계좌 현황")
    
    total_stock_value = 0.0
    portfolio_data = []
    usd_krw = get_usd_krw_rate()

    if st.session_state.portfolio:
        for ticker, info in st.session_state.portfolio.items():
            name = info.get("name", "알 수 없음")
            shares = info["shares"]
            avg_price = info["avg_price"]
            memo = info["memo"]
            is_us = not ticker.endswith(('.KS', '.KQ'))
            
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = avg_price  
                
            eval_value = shares * current_price
            if is_us:
                eval_value_krw = eval_value * usd_krw
                total_stock_value += eval_value_krw
                profit_loss_krw = eval_value_krw - (shares * avg_price * usd_krw)
            else:
                total_stock_value += eval_value
                profit_loss_krw = eval_value - (shares * avg_price)

            profit_loss_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
            
            portfolio_data.append({
                "종목이름": name,
                "종목코드": ticker,
                "보유수량": shares,
                "매입단가": f"{avg_price:,.2f}" + (" USD" if is_us else " 원"),
                "현재주가": f"{current_price:,.2f}" + (" USD" if is_us else " 원"),
                "평가금액": format_krw(eval_value_krw if is_us else eval_value),
                "손익": f"{profit_loss_krw:+,.0f} 원 ({profit_loss_pct:+.2f}%)",
                "투자메모": memo
            })

    total_assets = st.session_state.cash + total_stock_value
    total_profit = total_assets - st.session_state.initial_cash
    total_profit_pct = (total_profit / st.session_state.initial_cash) * 100 if st.session_state.initial_cash > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 자산", format_krw(total_assets), f"{total_profit_pct:+.2f}%")
    col2.metric("보유 현금", format_krw(st.session_state.cash))
    col3.metric("주식 평가금", format_krw(total_stock_value))
    col4.metric("총 누적 손익", format_krw(total_profit))

    st.markdown("---")
    st.subheader("보유 종목 상세 리스트")
    if portfolio_data:
        df_portfolio = pd.DataFrame(portfolio_data)
        st.dataframe(df_portfolio, use_container_width=True)
    else:
        st.info("아직 매수한 종목이 없습니다. [주식 매수/매도] 탭에서 첫 종목을 담아보세요!")

# --- 탭 2: 매수/매도 ---
with tab2:
    st.header("🛒 주식 거래소")
    
    trade_type = st.radio("거래 유형 선택", ["매수 (Buy)", "매도 (Sell)"], horizontal=True)
    usd_krw = get_usd_krw_rate()
    
    if trade_type == "매수 (Buy)":
        st.subheader("🚀 주식 매수하기 (신규 및 물타기/불타기 지원)")
        
        buy_mode = st.radio("매수 방식 선택", ["신규 종목 매수", "보유 종목 추가 매수 (물타기/불타기)"], horizontal=True)
        
        target_ticker = ""
        stock_name_input = ""
        current_price = 0.0
        is_us = False
        
        if buy_mode == "신규 종목 매수":
            market_choice = st.radio(
                "시장 구분 선택", 
                ["🇰🇷 국내 주식 - 코스피 (KS)", "🇰🇷 국내 주식 - 코스닥 (KQ)", "🇺🇸 해외 주식 (영문 티커)"], 
                horizontal=True
            )
            
            stock_name_input = st.text_input("🏷️ 종목 이름 입력 (예: 삼성전자, 애플)", value="").strip()
            raw_ticker_input = st.text_input("🔍 종목 코드 또는 티커 입력 (예: 코스피는 '005930', 해외는 'AAPL')", value="").strip()
            
            if "코스피" in market_choice:
                target_ticker = raw_ticker_input + ".KS" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
            elif "코스닥" in market_choice:
                target_ticker = raw_ticker_input + ".KQ" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
            else:
                target_ticker = raw_ticker_input.upper()
                is_us = True
                
        else: # 보유 종목 추가 매수
            if st.session_state.portfolio:
                portfolio_options = {f"{info['name']} ({ticker})": ticker for ticker, info in st.session_state.portfolio.items()}
                selected_display = st.selectbox("추가 매수할 보유 종목 선택", list(portfolio_options.keys()))
                target_ticker = portfolio_options[selected_display]
                stock_name_input = st.session_state.portfolio[target_ticker]["name"]
                is_us = not target_ticker.endswith(('.KS', '.KQ'))
            else:
                st.warning("보유 중인 종목이 없습니다. 먼저 신규 매수를 진행해 주세요.")
                target_ticker = ""
        
        if target_ticker and stock_name_input:
            try:
                stock = yf.Ticker(target_ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # 가격 및 단위 표시 준비
                    if is_us:
                        price_krw = current_price * usd_krw
                        price_str = f"{current_price:,.2f} USD ({format_krw(price_krw)})"
                        unit_cost_for_cash = price_krw
                    else:
                        price_str = f"{current_price:,.2f} 원 ({format_krw(current_price)})"
                        unit_cost_for_cash = current_price
                        
                    st.success(f"조회된 종목: **{stock_name_input} ({target_ticker})** | 현재 실시간 주가: **{price_str}**")
                    
                    # 지정가 매수 옵션
                    order_type = st.radio("매수 주문 유형", ["시장가 (즉시 매수)", "지정가 (목표가 도달 시 예약 매수)"], horizontal=True)
                    execution_price = current_price
                    if "지정가" in order_type:
                        execution_price = st.number_input("🎯 희망 매수 가격 입력", min_value=0.01, value=float(current_price), step=100.0 if not is_us else 1.0)
                        execution_cost_krw = execution_price * usd_krw if is_us else execution_price
                    else:
                        execution_cost_krw = unit_cost_for_cash
                        
                    max_buyable = int(st.session_state.cash // execution_cost_krw) if execution_cost_krw > 0 else 0
                    shares_to_buy = st.number_input("매수 수량", min_value=1, max_value=max(1, max_buyable), value=1)
                    memo_input = st.text_area("📝 투자 아이디어 & 추가 매수(물타기/불타기) 사유 메모", "")
                    
                    total_cost_krw = shares_to_buy * execution_cost_krw
                    st.info(f"필요한 매수 총액: **{total_cost_krw:,.2f} 원 ({format_krw(total_cost_krw)})** (보유 현금: {format_krw(st.session_state.cash)})")
                    
                    if st.button("🚀 매수 확정"):
                        if st.session_state.cash >= total_cost_krw:
                            st.session_state.cash -= total_cost_krw
                            
                            # 포트폴리오 반영 (평단가 재계산)
                            if target_ticker in st.session_state.portfolio:
                                old_shares = st.session_state.portfolio[target_ticker]["shares"]
                                old_avg = st.session_state.portfolio[target_ticker]["avg_price"]
                                new_shares = old_shares + shares_to_buy
                                new_avg = ((old_shares * old_avg) + (shares_to_buy * execution_price)) / new_shares
                                
                                st.session_state.portfolio[target_ticker]["shares"] = new_shares
                                st.session_state.portfolio[target_ticker]["avg_price"] = new_avg
                                if memo_input:
                                    st.session_state.portfolio[target_ticker]["memo"] += f" | {memo_input}"
                            else:
                                st.session_state.portfolio[target_ticker] = {
                                    "name": stock_name_input,
                                    "shares": shares_to_buy,
                                    "avg_price": execution_price,
                                    "memo": memo_input
                                }
                            
                            st.session_state.history.append({
                                "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "유형": "추가매수" if buy_mode != "신규 종목 매수" else "매수",
                                "종목명": stock_name_input,
                                "종목코드": target_ticker,
                                "수량": shares_to_buy,
                                "가격": execution_price,
                                "메모": memo_input
                            })
                            save_data() 
                            st.success(f"[{stock_name_input}] {shares_to_buy}주 매수 완료!")
                            st.rerun()
                        else:
                            st.error("현금이 부족합니다!")
                else:
                    st.error("해당 종목의 주가 데이터를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"주가 조회 중 오류 발생: {e}")

    else:  # 매도 (보유 종목 불러오기 & 지정가 예약 매도)
        st.subheader("📉 주식 매도하기 (예약/지정가 지원)")
        
        if st.session_state.portfolio:
            portfolio_options = {f"{info['name']} ({ticker})": ticker for ticker, info in st.session_state.portfolio.items()}
            selected_display = st.selectbox("보유 종목 선택하기", list(portfolio_options.keys()))
            
            ticker_input = portfolio_options[selected_display]
            owned_info = st.session_state.portfolio[ticker_input]
            owned_shares = owned_info["shares"]
            stock_name = owned_info["name"]
            avg_price = owned_info["avg_price"]
            is_us = not ticker_input.endswith(('.KS', '.KQ'))
            
            try:
                stock = yf.Ticker(ticker_input)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = avg_price

            cur_str = f"{current_price:,.2f} USD ({format_krw(current_price * usd_krw)})" if is_us else f"{current_price:,.2f} 원 ({format_krw(current_price)})"
            avg_str = f"{avg_price:,.2f} USD" if is_us else f"{format_krw(avg_price)}"
            
            st.info(f"📌 선택한 종목: **{stock_name} ({ticker_input})** | 보유 수량: **{owned_shares}주** | 평균 매입가: **{avg_str}** | 현재 주가: **{cur_str}**")
            
            sell_mode = st.radio("매도 주문 방식", ["시장가 (즉시 현재가 매도)", "지정가 (목표가 도달 시 예약 매도)"], horizontal=True)
            shares_to_sell = st.number_input("매도 수량", min_value=1, max_value=owned_shares, value=1)
            
            target_price = current_price
            if "지정가" in sell_mode:
                target_price = st.number_input("🎯 희망 매도 가격 입력", min_value=0.01, value=float(current_price), step=100.0 if not is_us else 1.0)

            if st.button("📉 매도 확정 (주문 실행)"):
                execution_price = target_price if "지정가" in sell_mode else current_price
                multiplier = usd_krw if is_us else 1.0
                
                sale_revenue_krw = shares_to_sell * execution_price * multiplier
                st.session_state.cash += sale_revenue_krw
                st.session_state.portfolio[ticker_input]["shares"] -= shares_to_sell
                
                profit_per_share = execution_price - avg_price
                total_profit_trade_krw = profit_per_share * shares_to_sell * multiplier
                
                if st.session_state.portfolio[ticker_input]["shares"] == 0:
                    del st.session_state.portfolio[ticker_input]
                    
                st.session_state.history.append({
                    "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "유형": "매도",
                    "종목명": stock_name,
                    "종목코드": ticker_input,
                    "수량": shares_to_sell,
                    "가격": execution_price,
                    "메모": f"매도 청산 (실현 손익: {total_profit_trade_krw:+,.0f}원)"
                })
                save_data() 
                st.success(f"[{stock_name}] {shares_to_sell}주 매도 완료! (실현 손익: {format_krw(total_profit_trade_krw)})")
                st.rerun()
        else:
            st.info("현재 보유 중인 종목이 없습니다. 먼저 주식을 매수해 보세요!")

# --- 탭 3: 거래 및 투자 노트 복기 ---
with tab3:
    st.header("📜 거래 내역 및 투자 복기")
    if st.session_state.history:
        df_history = pd.DataFrame(st.session_state.history)
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("아직 거래 내역이 없습니다.")
