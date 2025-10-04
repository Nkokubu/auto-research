# auto_research/macro.py
from __future__ import annotations
from typing import Dict, Iterable, List, Optional
import datetime as dt
import requests
import pandas as pd

from auto_research.config import FRED_API_KEY

_FRED_SERIES_URL = "https://api.stlouisfed.org/fred/series/observations"

def _fred_request(series_id: str, start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch a single FRED series as a DataFrame with columns: date (datetime64[ns]), value (float).
    Missing values are coerced to NaN. Dates are naive (UTC-like).
    """
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY is not set. Put it in your .env")

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
    }
    if end:
        params["observation_end"] = end

    r = requests.get(_FRED_SERIES_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("observations", [])

    if not data:
        return pd.DataFrame(columns=["date", "value"])

    df = pd.DataFrame(data)[["date", "value"]].copy()
    df["date"] = pd.to_datetime(df["date"], utc=False)
    # FRED uses "." for missing; coerce to float
    df["value"] = pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce")
    return df

def macro_dataframe(series_ids: Iterable[str] = ("TOTALSA", "INDPRO"),
                    start: str = "2000-01-01",
                    end: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch multiple FRED series and return a *wide* DataFrame indexed by date,
    with one column per series_id.
    """
    frames: List[pd.DataFrame] = []
    for sid in series_ids:
        df = _fred_request(sid, start=start, end=end)
        if not df.empty:
            df = df.rename(columns={"value": sid}).set_index("date")
            frames.append(df[[sid]])
    if not frames:
        return pd.DataFrame(columns=list(series_ids))
    out = pd.concat(frames, axis=1).sort_index()
    return out
