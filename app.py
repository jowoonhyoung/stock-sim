from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="멀티 계좌 주식 모의투자 시뮬레이터", page_icon="📈", layout="wide"
)

DATA_FILE = "multi_portfolio_data.json"


# 데이터 불러오기 함수
def load_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      pass
  return {
      "accounts": {
          "계좌 1 (삼성증권)": {
              "cash": 10000000.0,
              "initial_cash": 10000000.0,
              "portfolio": {},
              "history": [],
          }
      },
      "active_account": "계좌 1 (삼성증권)",
  }


# 데이터 저장하기 함수
def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# 세션 초기화
if "app_data" not in st.session_state:
  st.session_state.app_data = load_data()

if "accounts" not in st.session_state.app_data:
  st.session_state.app_data["accounts"] = {
      "계좌 1 (삼성증권)": {
          "cash": 10000000.0,
          "initial_cash": 10000000.0,
          "portfolio": {},
          "history": [],
      }
  }
if "active_account" not in st.session_state.app_data or st.session_state.app_data[
    "active_account"
] not in st.session_state.app_data["accounts"]:
  st.session_state.app_data["active_account"] = list(
      st.session_state.app_data["accounts"].keys()
  )[0]

current_acc_name = st.session_state.app_data["active_account"]
acc_dict = st.session_state.app_data["accounts"][current_acc_name]


# 한글 금액 변환 유틸리티 함수
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
      return df["Close"].iloc[-1]
  except:
    pass
  return 1350.0


st.title("📈 멀티 계좌 주식 재무제표 및 모의투자 시뮬레이터")
st.markdown(
    f"현재 조회 및 거래 중인 활성 계좌: **[{current_acc_name}]** | 증권사별로"
    " 계좌를 자유롭게 추가하고 분리 관리하세요!"
)

# --- 사이드바: 멀티 계좌 관리 센터 ---
st.sidebar.header("🏦 계좌 관리 센터")

account_list = list(st.session_state.app_data["accounts"].keys())
selected_active = st.sidebar.selectbox(
    "조회/거래할 계좌 선택 (활성 계좌)",
    account_list,
    index=account_list.index(current_acc_name),
)
if selected_active != current_acc_name:
  st.session_state.app_data["active_account"] = selected_active
  save_data(st.session_state.app_data)
  st.rerun()

with st.sidebar.expander("➕ 새 증권사 계좌 추가하기", expanded=False):
  new_acc_title = st.text_input(
      "계좌 이름/증권사 입력", value="계좌 2 (미래에셋증권)"
  ).strip()
  new_acc_init_cash = st.number_input(
      "초기 자본금 (원)", value=10000000, step=1000000
  )
  if st.button("계좌 생성하기"):
    if new_acc_title in st.session_state.app_data["accounts"]:
      st.sidebar.error("이미 존재하는 계좌 이름입니다.")
    elif not new_acc_title:
      st.sidebar.error("계좌 이름을 입력해 주세요.")
    else:
      st.session_state.app_data["accounts"][new_acc_title] = {
          "cash": float(new_acc_init_cash),
          "initial_cash": float(new_acc_init_cash),
          "portfolio": {},
          "history": [],
      }
      st.session_state.app_data["active_account"] = new_acc_title
      save_data(st.session_state.app_data)
      st.sidebar.success(
          f"'{new_acc_title}' 계좌가 생성되고 활성화되었습니다!"
      )
      st.rerun()

with st.sidebar.expander(
    f"🛠️ [{current_acc_name}] 자산 설정", expanded=False
):
  cur_init = acc_dict["initial_cash"]
  new_initial = st.number_input(
      "현재 계좌 초기 자본금 수정 (원)", value=int(cur_init), step=1000000
  )
  if st.button("초기 자본금 적용"):
    diff = new_initial - acc_dict["initial_cash"]
    acc_dict["initial_cash"] = float(new_initial)
    acc_dict["cash"] += diff
    if acc_dict["cash"] < 0:
      acc_dict["cash"] = 0.0
    save_data(st.session_state.app_data)
    st.success("적용되었습니다!")
    st.rerun()

  add_amount = st.number_input(
      "현재 계좌에 목돈 추가 (원)", value=5000000, step=1000000
  )
  if st.button("현금 추가 반영"):
    acc_dict["cash"] += float(add_amount)
    acc_dict["initial_cash"] += float(add_amount)
    save_data(st.session_state.app_data)
    st.success(f"{add_amount:,.0f}원이 추가되었습니다!")
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button(f"🚨 현재 계좌 [{current_acc_name}] 초기화"):
  acc_dict["cash"] = 10000000.0
  acc_dict["initial_cash"] = 10000000.0
  acc_dict["portfolio"] = {}
  acc_dict["history"] = []
  save_data(st.session_state.app_data)
  st.success("현재 계좌가 초기화되었습니다!")
  st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **멀티 계좌 안내:**
* 사이드바 상단에서 증권사별 계좌를 원하는 만큼 추가할 수 있습니다.
* 각 계좌별로 독립된 예수금과 보유 종목 리스트가 유지됩니다.
""")

tab1, tab2, tab3 = st.tabs(
    ["💰 자산 및 포트폴리오", "🛒 주식 매수/매도", "📜 거래 및 투자 노트 복기"]
)

# --- 탭 1: 포트폴리오 현황 ---
with tab1:
  st.header(f"📊 [{current_acc_name}] 계좌 현황")

  total_stock_value = 0.0
  portfolio_data = []
  usd_krw = get_usd_krw_rate()

  if acc_dict["portfolio"]:
    for ticker, info in acc_dict["portfolio"].items():
      name = info.get("name", "알 수 없음")
      shares = info["shares"]
      avg_price = info["avg_price"]
      memo = info["memo"]
      is_us = not ticker.endswith((".KS", ".KQ"))

      try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")["Close"].iloc[-1]
      except:
        current_price = avg_price

      eval_value = shares * current_price
      buy_total_value = shares * avg_price

      if is_us:
        eval_value_krw = eval_value * usd_krw
        buy_total_krw = buy_total_value * usd_krw
        total_stock_value += eval_value_krw
        profit_loss_krw = eval_value_krw - buy_total_krw
      else:
        eval_value_krw = eval_value
        buy_total_krw = buy_total_value
        total_stock_value += eval_value
        profit_loss_krw = eval_value - buy_total_value

      profit_loss_pct = (
          ((current_price - avg_price) / avg_price) * 100
          if avg_price > 0
          else 0
      )

      portfolio_data.append({
          "종목이름": name,
          "종목코드": ticker,
          "보유수량": shares,
          "매입단가": f"{avg_price:,.2f}" + (" USD" if is_us else " 원"),
          "총 매수금액": (
              f"{buy_total_krw:,.0f} 원"
              if is_us
              else f"{buy_total_value:,.0f} 원"
          ),
          "현재주가": f"{current_price:,.2f}" + (" USD" if is_us else " 원"),
          "평가금액": format_krw(eval_value_krw),
          "손익": f"{profit_loss_krw:+,.0f} 원 ({profit_loss_pct:+.2f}%)",
          "투자메모": memo,
      })

  total_assets = acc_dict["cash"] + total_stock_value
  total_profit = total_assets - acc_dict["initial_cash"]
  total_profit_pct = (
      (total_profit / acc_dict["initial_cash"]) * 100
      if acc_dict["initial_cash"] > 0
      else 0
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("총 자산", format_krw(total_assets), f"{total_profit_pct:+.2f}%")
  col2.metric("보유 현금", format_krw(acc_dict["cash"]))
  col3.metric("주식 평가금", format_krw(total_stock_value))
  col4.metric("총 누적 손익", format_krw(total_profit))

  st.markdown("---")
  st.subheader(f"[{current_acc_name}] 보유 종목 상세 리스트")
  if portfolio_data:
    df_portfolio = pd.DataFrame(portfolio_data)
    st.dataframe(df_portfolio, use_container_width=True)
  else:
    st.info(
        "현재 이 계좌에 매수한 종목이 없습니다. [주식 매수/매도] 탭에서 종목을"
        " 추가해 보세요!"
    )

# --- 탭 2: 매수/매도 ---
with tab2:
  st.header(f"🛒 주식 거래소 ({current_acc_name})")

  trade_type = st.radio(
      "거래 유형 선택", ["매수 (Buy)", "매도 (Sell)"], horizontal=True
  )
  usd_krw = get_usd_krw_rate()

  if trade_type == "매수 (Buy)":
    st.subheader(
        f"🚀 주식 매수하기 [{current_acc_name}] (신규, 물타기 및 자유 가격 입력"
        " 지원)"
    )

    buy_mode = st.radio(
        "매수 방식 선택",
        [
            "신규 종목 매수 (실시간 연동)",
            "보유 종목 추가 매수 (실시간 연동)",
            "🛠️ 자유 가격 입력 매수 (수동/강제 연습용)",
        ],
        horizontal=True,
    )

    target_ticker = ""
    stock_name_input = ""
    current_price = 0.0
    is_us = False

    if buy_mode == "🛠️ 자유 가격 입력 매수 (수동/강제 연습용)":
      st.info(
          "💡 실시간 주가 조회 없이 원하는 가격을 자유롭게 입력하여 물타기"
          " 연습을 할 수 있는 모드입니다."
      )

      manual_market_choice = st.radio(
          "시장 구분 선택 (통화 단위 결정)",
          [
              "🇰🇷 국내 주식 - 코스피 (원화 단가)",
              "🇰🇷 국내 주식 - 코스닥 (원화 단가)",
              "🇺🇸 해외 주식 (달러 단가)",
          ],
          horizontal=True,
      )

      stock_name_input = st.text_input(
          "🏷️ 연습할 종목 이름 (예: 삼성전자)", value="삼성전자"
      ).strip()
      raw_manual_ticker = st.text_input(
          "🔍 종목 코드 또는 티커 임의 입력 (예: 005930)", value="005930"
      ).strip()

      if "코스피" in manual_market_choice:
        target_ticker = (
            raw_manual_ticker + ".KS"
            if raw_manual_ticker.isdigit()
            else raw_manual_ticker.upper()
        )
        is_us = False
      elif "코스닥" in manual_market_choice:
        target_ticker = (
            raw_manual_ticker + ".KQ"
            if raw_manual_ticker.isdigit()
            else raw_manual_ticker.upper()
        )
        is_us = False
      else:
        target_ticker = raw_manual_ticker.upper()
        is_us = True

      manual_price = st.number_input(
          (
              "🎯 강제 지정 매수 가격 입력 (원)"
              if not is_us
              else "🎯 강제 지정 매수 가격 입력 (USD)"
          ),
          min_value=0.01,
          value=320000.0 if not is_us else 100.0,
          step=100.0 if not is_us else 1.0,
      )
      execution_price = manual_price

      execution_cost_krw = execution_price * usd_krw if is_us else execution_price

      if target_ticker in acc_dict["portfolio"]:
        p_info = acc_dict["portfolio"][target_ticker]
        st.warning(
            f"⚠️ 이 계좌에 이미 있는 종목입니다. (현재 보유: {p_info['shares']}주"
            f" / 기존 평단가: {p_info['avg_price']:,.2f}"
            f" {'USD' if is_us else '원'})"
        )

      max_buyable = (
          int(acc_dict["cash"] // execution_cost_krw)
          if execution_cost_krw > 0
          else 0
      )
      shares_to_buy = st.number_input(
          "매수 수량", min_value=1, max_value=max(1, max_buyable), value=1
      )
      memo_input = st.text_area(
          "📝 물타기 투자 아이디어 및 매수 사유 메모", "자유 가격 입력 물타기 연습"
      )

      total_cost_krw = shares_to_buy * execution_cost_krw
      st.info(
          f"필요한 매수 총액: **{total_cost_krw:,.2f} 원"
          f" ({format_krw(total_cost_krw)})** (현재 계좌 현금:"
          f" {format_krw(acc_dict['cash'])})"
      )

      if st.button("🚀 자유 가격 매수/물타기 확정"):
        if acc_dict["cash"] >= total_cost_krw:
          acc_dict["cash"] -= total_cost_krw

          if target_ticker in acc_dict["portfolio"]:
            old_shares = acc_dict["portfolio"][target_ticker]["shares"]
            old_avg = acc_dict["portfolio"][target_ticker]["avg_price"]
            new_shares = old_shares + shares_to_buy
            new_avg = (
                (old_shares * old_avg) + (shares_to_buy * execution_price)
            ) / new_shares

            acc_dict["portfolio"][target_ticker]["shares"] = new_shares
            acc_dict["portfolio"][target_ticker]["avg_price"] = new_avg
            if memo_input:
              acc_dict["portfolio"][target_ticker]["memo"] += f" | {memo_input}"
          else:
            acc_dict["portfolio"][target_ticker] = {
                "name": stock_name_input,
                "shares": shares_to_buy,
                "avg_price": execution_price,
                "memo": memo_input,
            }

          acc_dict["history"].append({
              "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "유형": "자유가격매수(물타기)",
              "종목명": stock_name_input,
              "종목코드": target_ticker,
              "수량": shares_to_buy,
              "가격": execution_price,
              "통화": "USD" if is_us else "KRW",
              "메모": memo_input,
          })
          save_data(st.session_state.app_data)
          st.success(
              f"[{current_acc_name}] [{stock_name_input}] 가격"
              f" {execution_price:,.2f}"
              f" {'USD' if is_us else '원'}으로 {shares_to_buy}주 매수 완료!"
          )
          st.rerun()
        else:
          st.error("현재 계좌의 현금이 부족합니다!")

    else:
      if buy_mode == "신규 종목 매수 (실시간 연동)":
        market_choice = st.radio(
            "시장 구분 선택",
            [
                "🇰🇷 국내 주식 - 코스피 (KS)",
                "🇰🇷 국내 주식 - 코스닥 (KQ)",
                "🇺🇸 해외 주식 (영문 티커)",
            ],
            horizontal=True,
        )

        stock_name_input = st.text_input(
            "🏷️ 종목 이름 입력 (예: 삼성전자)", value=""
        ).strip()
        raw_ticker_input = st.text_input(
            "🔍 종목 코드 또는 티커 입력 (예: '005930')", value=""
        ).strip()

        if "코스피" in market_choice:
          target_ticker = (
              raw_ticker_input + ".KS"
              if raw_ticker_input.isdigit()
              else raw_ticker_input.upper()
          )
        elif "코스닥" in market_choice:
          target_ticker = (
              raw_ticker_input + ".KQ"
              if raw_ticker_input.isdigit()
              else raw_ticker_input.upper()
          )
        else:
          target_ticker = raw_ticker_input.upper()
          is_us = True

      else:  # 보유 종목 추가 매수
        if acc_dict["portfolio"]:
          portfolio_options = {
              f"{info['name']} ({ticker})": ticker
              for ticker, info in acc_dict["portfolio"].items()
          }
          selected_display = st.selectbox(
              "추가 매수할 보유 종목 선택", list(portfolio_options.keys())
          )
          target_ticker = portfolio_options[selected_display]
          stock_name_input = acc_dict["portfolio"][target_ticker]["name"]
          is_us = not target_ticker.endswith((".KS", ".KQ"))
        else:
          st.warning(
              "이 계좌에 보유 중인 종목이 없습니다. 신규 매수나 [자유 가격 입력"
              " 매수]를 이용해 주세요."
          )
          target_ticker = ""

      if target_ticker and stock_name_input:
        try:
          stock = yf.Ticker(target_ticker)
          hist = stock.history(period="1d")
          if not hist.empty:
            current_price = hist["Close"].iloc[-1]

            if is_us:
              price_krw = current_price * usd_krw
              price_str = (
                  f"{current_price:,.2f} USD ({format_krw(price_krw)})"
              )
              unit_cost_for_cash = price_krw
            else:
              price_str = (
                  f"{current_price:,.2f} 원 ({format_krw(current_price)})"
              )
              unit_cost_for_cash = current_price

            st.success(
                f"조회된 종목: **{stock_name_input} ({target_ticker})** | 현재"
                f" 실시간 주가: **{price_str}**"
            )

            order_type = st.radio(
                "매수 주문 유형",
                ["시장가 (즉시 매수)", "지정가 (목표가 도달 시 예약 매수)"],
                horizontal=True,
            )
            execution_price = current_price
            if "지정가" in order_type:
              execution_price = st.number_input(
                  "🎯 희망 매수 가격 입력",
                  min_value=0.01,
                  value=float(current_price),
                  step=100.0 if not is_us else 1.0,
              )
              execution_cost_krw = (
                  execution_price * usd_krw if is_us else execution_price
              )
            else:
              execution_cost_krw = unit_cost_for_cash

            max_buyable = (
                int(acc_dict["cash"] // execution_cost_krw)
                if execution_cost_krw > 0
                else 0
            )
            shares_to_buy = st.number_input(
                "매수 수량", min_value=1, max_value=max(1, max_buyable), value=1
            )
            memo_input = st.text_area("📝 투자 아이디어 & 추가 매수 사유 메모", "")

            total_cost_krw = shares_to_buy * execution_cost_krw
            st.info(
                f"필요한 매수 총액: **{total_cost_krw:,.2f} 원"
                f" ({format_krw(total_cost_krw)})** (현재 계좌 현금:"
                f" {format_krw(acc_dict['cash'])})"
            )

            if st.button("🚀 매수 확정"):
              if acc_dict["cash"] >= total_cost_krw:
                acc_dict["cash"] -= total_cost_krw

                if target_ticker in acc_dict["portfolio"]:
                  old_shares = acc_dict["portfolio"][target_ticker]["shares"]
                  old_avg = acc_dict["portfolio"][target_ticker]["avg_price"]
                  new_shares = old_shares + shares_to_buy
                  new_avg = (
                      (old_shares * old_avg) + (shares_to_buy * execution_price)
                  ) / new_shares

                  acc_dict["portfolio"][target_ticker]["shares"] = new_shares
                  acc_dict["portfolio"][target_ticker]["avg_price"] = new_avg
                  if memo_input:
                    acc_dict["portfolio"][target_ticker][
                        "memo"
                    ] += f" | {memo_input}"
                else:
                  acc_dict["portfolio"][target_ticker] = {
                      "name": stock_name_input,
                      "shares": shares_to_buy,
                      "avg_price": execution_price,
                      "memo": memo_input,
                  }

                acc_dict["history"].append({
                    "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "유형": (
                        "추가매수" if buy_mode != "신규 종목 매수" else "매수"
                    ),
                    "종목명": stock_name_input,
                    "종목코드": target_ticker,
                    "수량": shares_to_buy,
                    "가격": execution_price,
                    "메모": memo_input,
                })
                save_data(st.session_state.app_data)
                st.success(f"[{stock_name_input}] {shares_to_buy}주 매수 완료!")
                st.rerun()
              else:
                st.error("현금이 부족합니다!")
          else:
            st.error("해당 종목의 주가 데이터를 찾을 수 없습니다.")
        except Exception as e:
          st.error(f"주가 조회 중 오류 발생: {e}")

  else:  # 매도
    st.subheader(f"📉 주식 매도하기 [{current_acc_name}]")

    if acc_dict["portfolio"]:
      portfolio_options = {
          f"{info['name']} ({ticker})": ticker
          for ticker, info in acc_dict["portfolio"].items()
      }
      selected_display = st.selectbox(
          "보유 종목 선택하기", list(portfolio_options.keys())
      )

      ticker_input = portfolio_options[selected_display]
      owned_info = acc_dict["portfolio"][ticker_input]
      owned_shares = owned_info["shares"]
      stock_name = owned_info["name"]
      avg_price = owned_info["avg_price"]
      is_us = not ticker_input.endswith((".KS", ".KQ"))

      try:
        stock = yf.Ticker(ticker_input)
        current_price = stock.history(period="1d")["Close"].iloc[-1]
      except:
        current_price = avg_price

      cur_str = (
          f"{current_price:,.2f} USD ({format_krw(current_price * usd_krw)})"
          if is_us
          else f"{current_price:,.2f} 원 ({format_krw(current_price)})"
      )
      avg_str = f"{avg_price:,.2f} USD" if is_us else f"{format_krw(avg_price)}"

      st.info(
          f"📌 선택한 종목: **{stock_name} ({ticker_input})** | 보유 수량:"
          f" **{owned_shares}주** | 평균 매입가: **{avg_str}** | 현재 주가:"
          f" **{cur_str}**"
      )

      sell_mode = st.radio(
          "매도 주문 방식",
          ["시장가 (즉시 현재가 매도)", "지정가 (목표가 도달 시 예약 매도)"],
          horizontal=True,
      )
      shares_to_sell = st.number_input(
          "매도 수량", min_value=1, max_value=owned_shares, value=1
      )

      target_price = current_price
      if "지정가" in sell_mode:
        target_price = st.number_input(
            "🎯 희망 매도 가격 입력",
            min_value=0.01,
            value=float(current_price),
            step=100.0 if not is_us else 1.0,
        )

      if st.button("📉 매도 확정 (주문 실행)"):
        execution_price = (
            target_price if "지정가" in sell_mode else current_price
        )
        multiplier = usd_krw if is_us else 1.0

        sale_revenue_krw = shares_to_sell * execution_price * multiplier
        acc_dict["cash"] += sale_revenue_krw
        acc_dict["portfolio"][ticker_input]["shares"] -= shares_to_sell

        profit_per_share = execution_price - avg_price
        total_profit_trade_krw = profit_per_share * shares_to_sell * multiplier

        if acc_dict["portfolio"][ticker_input]["shares"] == 0:
          del acc_dict["portfolio"][ticker_input]

        acc_dict["history"].append({
            "시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "유형": "매수/매도 복기",
            "종목명": stock_name,
            "종목코드": ticker_input,
            "수량": shares_to_sell,
            "가격": execution_price,
            "메모": (
                "매도 청산 (실현 손익:"
                f" {total_profit_trade_krw:+,.0f}원)"
            ),
        })
        save_data(st.session_state.app_data)
        st.success(
            f"[{stock_name}] {shares_to_sell}주 매도 완료! (실현 손익:"
            f" {format_krw(total_profit_trade_krw)})"
        )
        st.rerun()
    else:
      st.info("현재 계좌에 보유 중인 종목이 없습니다.")

# --- 탭 3: 거래 및 투자 노트 복기 ---
with tab3:
  st.header(f"📜 [{current_acc_name}] 거래 내역 및 투자 복기")
  if acc_dict["history"]:
    df_history = pd.DataFrame(acc_dict["history"])
    st.dataframe(df_history, use_container_width=True)
  else:
    st.info("아직 거래 내역이 없습니다.")
