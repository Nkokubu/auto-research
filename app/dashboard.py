import streamlit as st
from auto_research.config import FRED_API_KEY
from auto_research.prices import latest_prices
import pandas as pd

st.set_page_config(page_title="Auto Research", layout="wide")
st.title("Auto Research – Dashboard")

tabs = st.tabs(["Overview", "Prices"])

with st.sidebar:
    st.header("Settings")
    st.text_input(
        "FRED API Key",
        value=("•••" if FRED_API_KEY else ""),
        type="password",
        disabled=True,
        key="fred_api_key_display",   # ✅ unique key
    )
    st.caption("Tip: put keys in your .env (see .env.example).")

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
    st.json({"FRED_API_KEY_present": bool(FRED_API_KEY)})

with tabs[0]:
    st.success("Environment OK 🎉")
    st.write("This stub proves Streamlit + Poetry are wired up.")

    with st.sidebar:
        st.header("Settings")
        st.text_input("FRED API Key", value=("•••" if FRED_API_KEY else ""), type="password", disabled=True)
        st.caption("Tip: put keys in your .env (see .env.example).")

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
        st.json({"FRED_API_KEY_present": bool(FRED_API_KEY)})

with tabs[1]:
    st.subheader("📈 Stock Price Fetcher")
    tickers_text = st.text_input(
        "Tickers (comma-separated):",
        value="TSLA,AAPL,F",
        key="tickers_input",          # ✅ unique key
    )
    symbols = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    run = st.button("Fetch latest prices", key="fetch_prices_btn")  # (optional) unique key

    if run and symbols:
        try:
            df = latest_prices(symbols)
            if df.empty:
                st.info("No data returned. Try different tickers.")
            else:
                # Ensure column order & types look right
                expected_cols = ["ticker", "last_price", "pct_change"]
                df = df[[c for c in expected_cols if c in df.columns]]
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching prices: {e}")