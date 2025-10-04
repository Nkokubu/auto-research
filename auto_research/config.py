# auto_research/config.py
import os
from pathlib import Path

# Optional: support .streamlit/secrets.toml (Streamlit Cloud or local secrets)
try:
    import streamlit as st
    _secrets = getattr(st, "secrets", {})
except Exception:
    _secrets = {}

# Load .env from repo root
try:
    from dotenv import load_dotenv
    ROOT = Path(__file__).resolve().parents[1]  # repo root (one level above package)
    load_dotenv(ROOT / ".env")
except Exception:
    pass  # python-dotenv not installed or other non-fatal issue

def _get_env(name: str, default: str = "") -> str:
    # priority: Streamlit secrets → OS env → default
    val = (_secrets.get(name) if isinstance(_secrets, dict) else None) or os.getenv(name, default)
    # normalize whitespace/quotes that sometimes sneak in on Windows
    if isinstance(val, str):
        val = val.strip().strip('"').strip("'")
    return val

FRED_API_KEY = _get_env("FRED_API_KEY", "")

# Optional: WATCHLIST with empty default
WATCHLIST = [
    s.strip().upper()
    for s in _get_env("WATCHLIST", "").split(",")
    if s.strip()
]

