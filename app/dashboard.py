import streamlit as st
from auto_research.config import FRED_API_KEY, WATCHLIST
from auto_research.prices import latest_prices
from auto_research.news import top_headlines
from auto_research.macro import macro_dataframe
import datetime as dt
import ast
import re

st.set_page_config(page_title="Auto Research", layout="wide")
st.title("Auto Research – Dashboard")

def _clean_symbols(csv_text: str) -> list[str]:
    raw = [t.strip().upper() for t in (csv_text or "").split(",")]
    # keep only letters/numbers/.- (common for tickers)
    return [re.sub(r"[^A-Z0-9\.\-]", "", t) for t in raw if re.sub(r"[^A-Z0-9\.\-]", "", t)]


# ---------- SINGLE SIDEBAR (define once) ----------
with st.sidebar:
    st.header("Settings")
    st.text_input(
        "FRED API Key",
        value=("•••" if FRED_API_KEY else ""),
        type="password",
        disabled=True,
        key="fred_api_key_display",
    )
    st.text_input(
        "Watchlist (comma-separated)",
        value=",".join(WATCHLIST),   # if empty, the field is blank
        key="watchlist_input",
        help="Add tickers like: TSLA,AAPL,NVDA",
    )
    st.caption("Tip: put keys in your .env (see .env.example).")

# ---------- TABS ----------
tabs = st.tabs(["Overview", "📈 Prices", "🗞️ Top News", "📊 Macro"])

with tabs[0]:
    st.success("Environment OK 🎉")
    st.write("This stub proves Streamlit + Poetry are wired up.")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Next steps")
        st.markdown(
            "- Add modules in `auto_research/` (prices, news, etc.)\n"
            "- Wire UI panels here\n"
            "- Commit to git\n"
        )
    with col2:
        st.subheader("Env check")
        st.json({"FRED_API_KEY_present": bool(FRED_API_KEY), "WATCHLIST": WATCHLIST})

with tabs[1]:
    st.subheader("📈 Prices – Watchlist")
    wl_text = st.session_state.get("watchlist_input", ",".join(WATCHLIST))
    symbols = _clean_symbols(wl_text)

    if not symbols:
        st.info("No tickers yet. Add symbols in the sidebar (e.g., TSLA) and click the button.")
    run_prices = st.button("Fetch latest prices", key="fetch_prices_btn")

    if run_prices and symbols:
        try:
            df_prices = latest_prices(symbols)
            if df_prices.empty:
                st.info("No data returned. Try different tickers or check your internet.")
            else:
                st.dataframe(df_prices, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching prices: {e}")

with tabs[2]:
    st.subheader("🗞️ Top News – Tagged by Ticker")

    # Read current watchlist
    wl_text = st.session_state.get("watchlist_input", ",".join(WATCHLIST))
    watchlist = [t.strip().upper() for t in wl_text.split(",") if t.strip()]

    # Starter map: each ticker only matches itself (no defaults)
    starter_map = {t: [t] for t in watchlist}

    # Refill the text area only when the watchlist changes
    wl_key = ",".join(watchlist)
    if (
        "news_ticker_map" not in st.session_state
        or st.session_state.get("news_ticker_map_autofill_source") != wl_key
    ):
        st.session_state["news_ticker_map"] = (str(starter_map) if starter_map else "{}")
        st.session_state["news_ticker_map_autofill_source"] = wl_key

    st.caption("Add keywords if you like (e.g., {'TSLA': ['TSLA','Tesla','Elon Musk']}).")
    mapping_text = st.text_area(
        "Ticker → Keywords map (Python dict)",
        value=st.session_state["news_ticker_map"],
        height=140,
        key="news_ticker_map",
    )

    lookback = st.slider("Lookback (hours)", 6, 336, 48, 6, key="news_lookback")
    run_news = st.button("Fetch headlines", key="fetch_news_btn")

    if not watchlist:
        st.info("No tickers yet. Add at least one in the sidebar (e.g., TSLA).")

    if run_news:
        try:
            import ast
            ticker_map = ast.literal_eval(mapping_text) if mapping_text.strip() else {}
            if not ticker_map:
                st.warning("Your ticker→keywords map is empty. Add at least one ticker, e.g., {'TSLA':['TSLA']}.")
            else:
                df_news = top_headlines(ticker_map, hours_lookback=lookback, max_items=50)
                
                if df_news.empty:
                     df_news = df_news[df_news["tickers"].map(lambda ts: bool(ts))]
                     wl_set = set(watchlist)
                     df_news = df_news[
                          df_news["tickers"].map(lambda ts: bool(wl_set.intersection(set(ts))))
                     ]
                
                if df_news.empty:
                    st.info("No tagged headlines for your tickers. Increase lookback or add broader keywords (e.g., 'Tesla').")
                else:
                    st.dataframe(df_news, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ...existing tabs[0], tabs[1], tabs[2]...

with tabs[3]:
    st.subheader("📊 Macro – FRED")
    st.caption("US Light Vehicle Sales (SAAR): TOTALSA • Industrial Production Index: INDPRO")

    colm1, colm2 = st.columns([1, 3])
    with colm1:
        start = st.date_input("Start date", value=dt.date(2000, 1, 1), key="macro_start")
        run_macro = st.button("Fetch macro data", key="fetch_macro_btn")
    with colm2:
        st.info("Uses your FRED API key from .env. Lines will appear after fetch.")

    if run_macro:
        try:
            df_macro = macro_dataframe(["TOTALSA", "INDPRO"], start=start.isoformat())
            if df_macro.empty:
                st.warning("No data returned. Check your FRED API key or try a wider date range.")
            else:
                st.dataframe(df_macro.tail(12), use_container_width=True)
                st.line_chart(df_macro)  # Streamlit draws both series on one chart
        except Exception as e:
            st.error(f"Error fetching FRED data: {e}")
