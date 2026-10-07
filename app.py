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

st.title("📈 주식 재무제표 및 모의투자 연습 시뮬레이터")
st.markdown("재무제표를 분석하고 단기/중장기 투자 관점을 기록하며 실력을 키워보세요! (데이터 자동 저장 & 코스피/코스닥 선택 지원)")

# 사이드바 설정
st.sidebar.header("⚙️ 자산 설정 및 초기화")
new_initial = st.sidebar.number_input("초기 자본금 설정 (원)", value=int(st.session_state.initial_cash), step=1000000)
if st.sidebar.button("자본금 및 계좌 리셋"):
    st.session_state.cash = float(new_initial)
    st.session_state.initial_cash = float(new_initial)
    st.session_state.portfolio = {}
    st.session_state.history = []
    save_data()
    st.success("계좌가 초기화되었습니다!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **입력 팁:**
* **국내 주식**: 시장 구분(코스피/코스닥)을 선택하고 6자리 숫자를 입력하세요. (자동으로 `.KS` 또는 `.KQ`가 붙습니다.)
* **해외 주식**: 시장 구분을 '해외 주식(미국 등)'으로 선택하고 영문 티커를 입력하세요. (예: `AAPL`, `SOXL`)
""")

# 탭 메뉴 구성
tab1, tab2, tab3 = st.tabs(["💰 자산 및 포트폴리오", "🛒 주식 매수/매도", "📜 거래 및 투자 노트 복기"])

# --- 탭 1: 포트폴리오 현황 ---
with tab1:
    st.header("📊 내 계좌 현황")
    
    total_stock_value = 0.0
    portfolio_data = []

    if st.session_state.portfolio:
        for ticker, info in st.session_state.portfolio.items():
            shares = info["shares"]
            avg_price = info["avg_price"]
            memo = info["memo"]
            
            # 실시간 주가 조회
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = avg_price  
                
            eval_value = shares * current_price
            total_stock_value += eval_value
            profit_loss = eval_value - (shares * avg_price)
            profit_loss_pct = (profit_loss / (shares * avg_price)) * 100 if (shares * avg_price) > 0 else 0
            
            portfolio_data.append({
                "종목(티커)": ticker,
                "보유 수량": shares,
                "매입 단가": f"{avg_price:,.0f} 원",
                "현재 주가": f"{current_price:,.0f} 원",
                "평가 금액": f"{eval_value:,.0f} 원",
                "손익": f"{profit_loss:,.0f} 원 ({profit_loss_pct:+.2f}%)",
                "투자 메모": memo
            })

    total_assets = st.session_state.cash + total_stock_value
    total_profit = total_assets - st.session_state.initial_cash
    total_profit_pct = (total_profit / st.session_state.initial_cash) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 자산", f"{total_assets:,.0f} 원", f"{total_profit_pct:+.2f}%")
    col2.metric("보유 현금", f"{st.session_state.cash:,.0f} 원")
    col3.metric("주식 평가금", f"{total_stock_value:,.0f} 원")
    col4.metric("총 누적 손익", f"{total_profit:,.0f} 원")

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
    
    # 시장 선택 버튼 (기본값: 코스피)
    market_choice = st.radio(
        "시장 구분 선택", 
        ["🇰🇷 국내 주식 - 코스피 (KS)", "🇰🇷 국내 주식 - 코스닥 (KQ)", "🇺🇸 해외 주식 (영문 티커)"], 
        horizontal=True
    )
    
    raw_ticker_input = st.text_input("종목 코드 또는 티커 입력 (예: 코스피는 '005930', 해외는 'AAPL')", value="").strip()
    
    # 선택한 시장에 따라 자동으로 접미사 붙이기
    if "코스피" in market_choice:
        ticker_input = raw_ticker_input + ".KS" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
    elif "코스닥" in market_choice:
        ticker_input = raw_ticker_input + ".KQ" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
    else:
        ticker_input = raw_ticker_input.upper()
    
    if raw_ticker_input:
        try:
            stock = yf.Ticker(ticker_input)
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                st.success(f"조회된 종목: **{ticker_input}** | 현재 실시간 주가: **{current_price:,.2f}**")
                
                if trade_type == "매수 (Buy)":
                    max_buyable = int(st.session_state.cash // current_price) if current_price > 0 else 0
                    shares_to_buy = st.number_input("매수 수량", min_value=1, max_value=max(1, max_buyable), value=1)
                    memo_input = st.text_area("📝 투자 아이디어 & 재무제표 분석 메모", "")
                    
                    total_cost = shares_to_buy * current_price
                    st.info(f"필요한 매수 총액: **{total_cost:,.2f}** (보유 현금: {st.session_state.cash:,.0f} 원)")
                    
                    if st.button("🚀 매수 확정"):
                        if st.session_state.cash >= total_cost:
                            st.session_state.cash -= total_cost
                            if ticker_input in st.session_state.portfolio:
                                old_shares = st.session_state.portfolio[ticker_input]["shares"]
                                old_avg = st.session_state.portfolio[ticker_input]["avg_price"]
                                new_shares = old_shares + shares_to_buy
                                new_avg = ((old_shares * old_avg) + total_cost) / new_shares
                                st.session_state.portfolio[ticker_input]["shares"] = new_shares
                                st.session_state.portfolio[ticker_input]["avg_price"] = new_avg
                                if memo_input:
                                    st.session_state.portfolio[ticker_input]["memo"] += f" | {memo_input}"
                            else:
                                st.session_state.portfolio[ticker_input] = {
                                    "shares": shares_to_buy,
                                    "avg_price": current_price,
                                    "memo": memo_input
                                }
                            
                            st.session_state.history.append({
                                "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "유형": "매수",
                                "종목": ticker_input,
                                "수량": shares_to_buy,
                                "가격": current_price,
                                "메모": memo_input
                            })
                            save_data() 
                            st.success(f"{ticker_input} {shares_to_buy}주 매수 완료!")
                            st.rerun()
                        else:
                            st.error("현금이 부족합니다!")

                else:  # 매도
                    if ticker_input in st.session_state.portfolio:
                        owned_shares = st.session_state.portfolio[ticker_input]["shares"]
                        shares_to_sell = st.number_input("매도 수량", min_value=1, max_value=owned_shares, value=1)
                        
                        if st.button("📉 매도 확정"):
                            sale_revenue = shares_to_sell * current_price
                            st.session_state.cash += sale_revenue
                            st.session_state.portfolio[ticker_input]["shares"] -= shares_to_sell
                            
                            if st.session_state.portfolio[ticker_input]["shares"] == 0:
                                del st.session_state.portfolio[ticker_input]
                                
                            st.session_state.history.append({
                                "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "유형": "매도",
                                "종목": ticker_input,
                                "수량": shares_to_sell,
                                "가격": current_price,
                                "메모": "매도 청산"
                            })
                            save_data() 
                            st.success(f"{ticker_input} {shares_to_sell}주 매도 완료!")
                            st.rerun()
                    else:
                        st.warning("현재 보유 중이지 않은 종목입니다.")
            else:
                st.error("해당 종목의 주가 데이터를 찾을 수 없습니다. 시장 구분(코스피/코스닥)이나 코드를 다시 확인해 주세요.")
        except Exception as e:
            st.error(f"주가 조회 중 오류 발생: {e}")

# --- 탭 3: 거래 및 투자 노트 복기 ---
with tab3:
    st.header("📜 거래 내역 및 투자 복기")
    if st.session_state.history:
        df_history = pd.DataFrame(st.session_state.history)
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("아직 거래 내역이 없습니다.")