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
st.markdown("재무제표를 분석하고 단기/중장기 투자 관점을 기록하며 실력을 키워보세요! (종목명 지원 및 지정가 예약 매도 기능 포함)")

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
💡 **사용 안내:**
* **매수 시**: 종목이름(예: 삼성전자)과 종목코드(예: 005930)를 각각 입력하여 나만의 리스트를 만드세요.
* **매도 시**: 보유 중인 종목을 목록에서 선택하고, **현재가 매도** 혹은 원하는 가격에 파는 **지정가(예약) 매도**를 선택할 수 있습니다.
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
            name = info.get("name", "알 수 없음") # 종목 이름
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
                "종목이름": name,
                "종목코드": ticker,
                "보유수량": shares,
                "매입단가": f"{avg_price:,.0f} 원",
                "현재주가": f"{current_price:,.0f} 원",
                "평가금액": f"{eval_value:,.0f} 원",
                "손익": f"{profit_loss:,.0f} 원 ({profit_loss_pct:+.2f}%)",
                "투자메모": memo
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
    
    if trade_type == "매수 (Buy)":
        st.subheader("🚀 주식 매수하기")
        market_choice = st.radio(
            "시장 구분 선택", 
            ["🇰🇷 국내 주식 - 코스피 (KS)", "🇰🇷 국내 주식 - 코스닥 (KQ)", "🇺🇸 해외 주식 (영문 티커)"], 
            horizontal=True
        )
        
        # 사용자가 직접 입력하는 종목 이름
        stock_name_input = st.text_input("🏷️ 종목 이름 입력 (예: 삼성전자, 애플)", value="").strip()
        raw_ticker_input = st.text_input("🔍 종목 코드 또는 티커 입력 (예: 코스피는 '005930', 해외는 'AAPL')", value="").strip()
        
        if "코스피" in market_choice:
            ticker_input = raw_ticker_input + ".KS" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
        elif "코스닥" in market_choice:
            ticker_input = raw_ticker_input + ".KQ" if raw_ticker_input.isdigit() else raw_ticker_input.upper()
        else:
            ticker_input = raw_ticker_input.upper()
        
        if raw_ticker_input and stock_name_input:
            try:
                stock = yf.Ticker(ticker_input)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    st.success(f"조회된 종목: **{stock_name_input} ({ticker_input})** | 현재 실시간 주가: **{current_price:,.2f}**")
                    
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
                                    "name": stock_name_input,
                                    "shares": shares_to_buy,
                                    "avg_price": current_price,
                                    "memo": memo_input
                                }
                            
                            st.session_state.history.append({
                                "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "유형": "매수",
                                "종목명": stock_name_input,
                                "종목코드": ticker_input,
                                "수량": shares_to_buy,
                                "가격": current_price,
                                "메모": memo_input
                            })
                            save_data() 
                            st.success(f"[{stock_name_input}] {shares_to_buy}주 매수 완료!")
                            st.rerun()
                        else:
                            st.error("현금이 부족합니다!")
                else:
                    st.error("해당 종목의 주가 데이터를 찾을 수 없습니다. 코드를 확인해 주세요.")
            except Exception as e:
                st.error(f"주가 조회 중 오류 발생: {e}")
        elif raw_ticker_input and not stock_name_input:
            st.warning("⚠️ 종목 이름을 입력해 주세요! (예: 삼성전자)")

    else:  # 매도 (보유 종목 불러오기 & 지정가 예약 매도 기능)
        st.subheader("📉 주식 매도하기 (예약/지정가 지원)")
        
        if st.session_state.portfolio:
            # 사용자가 보유한 종목들을 깔끔하게 셀렉트박스로 불러옴 (종목이름과 코드 동시 표시)
            portfolio_options = {f"{info['name']} ({ticker})": ticker for ticker, info in st.session_state.portfolio.items()}
            selected_display = st.selectbox("보유 종목 선택하기", list(portfolio_options.keys()))
            
            ticker_input = portfolio_options[selected_display]
            owned_info = st.session_state.portfolio[ticker_input]
            owned_shares = owned_info["shares"]
            stock_name = owned_info["name"]
            avg_price = owned_info["avg_price"]
            
            # 실시간 주가 조회
            try:
                stock = yf.Ticker(ticker_input)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = avg_price

            st.info(f"📌 선택한 종목: **{stock_name} ({ticker_input})** | 보유 수량: **{owned_shares}주** | 평균 매입가: **{avg_price:,.0f}원** | 현재 실시간 주가: **{current_price:,.2f}원**")
            
            # 매도 방식 선택 (현재가 vs 지정가 예약)
            sell_mode = st.radio("매도 주문 방식", ["시장가 (즉시 현재가 매도)", "지정가 (목표가 도달 시 또는 예약 매도)"], horizontal=True)
            
            shares_to_sell = st.number_input("매도 수량", min_value=1, max_value=owned_shares, value=1)
            
            target_price = current_price # 기본값
            if "지정가" in sell_mode:
                target_price = st.number_input("🎯 희망 매도 가격 (지정가/예약가 입력)", min_value=1.0, value=float(current_price), step=100.0)
                st.caption("💡 지정가 매도는 현재 주가보다 높게 설정하여 목표가에 도달했을 때 수익을 실현하는 '예약 매도' 개념입니다.")

            if st.button("📉 매도 확정 (주문 실행)"):
                # 지정가 매도 검증 로직
                if "지정가" in sell_mode and target_price > current_price:
                    # 현재가보다 높은 가격에 예약 걸어둔 경우 (목표가 미도달 상태 시뮬레이션 안내)
                    st.warning(f"⚠️ 현재 주가({current_price:,.0f}원)보다 희망 매도 가격({target_price:,.0f}원)이 더 높습니다! 목표가에 도달할 때까지 예약 상태로 대기하거나, 혹은 즉시 체결 가격을 현재가 기준으로 처리할 수 있습니다.")
                    # 사용자의 편의를 위해 모의투자상에서 지정가 도달 시뮬레이션을 위해 즉시 체결 또는 대기 선택을 줄 수 있으나, 여기서는 지정가 가격으로 즉시 수익을 확정하는 방식으로 반영합니다.
                
                # 매도 체결 가격 결정 (지정가 혹은 현재가)
                execution_price = target_price if "지정가" in sell_mode else current_price
                
                sale_revenue = shares_to_sell * execution_price
                st.session_state.cash += sale_revenue
                st.session_state.portfolio[ticker_input]["shares"] -= shares_to_sell
                
                # 수익금 계산
                profit_per_share = execution_price - avg_price
                total_profit_trade = profit_per_share * shares_to_sell
                
                if st.session_state.portfolio[ticker_input]["shares"] == 0:
                    del st.session_state.portfolio[ticker_input]
                    
                st.session_state.history.append({
                    "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "유형": "매도",
                    "종목명": stock_name,
                    "종목코드": ticker_input,
                    "수량": shares_to_sell,
                    "가격": execution_price,
                    "메모": f"매도 청산 (실현 손익: {total_profit_trade:+,.0f}원)"
                })
                save_data() 
                st.success(f"[{stock_name}] {shares_to_sell}주 매도 완료! (체결가: {execution_price:,.0f}원 / 실현 손익: {total_profit_trade:+,.0f}원)")
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
