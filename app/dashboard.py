import streamlit as st
from auto_research.config import FRED_API_KEY

st.set_page_config(page_title="Auto Research", layout="wide")
st.title("Auto Research – Dashboard")

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
