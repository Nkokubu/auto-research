#accepts list of ticker
from __future__ import annotations
from typing import Iterable, List
import math
import pandas as pd
import yfinance as yf


def latest_prices(tickers: Iterable[str]) -> pd.DataFrame:
    """
    Fetch latest close and day-over-day percent change for each ticker.

    Parameters
    ----------
    tickers : Iterable[str]
        A list (or any iterable) of ticker symbols, e.g. ["AAPL", "TSLA"].

    Returns
    -------
    pandas.DataFrame
        Columns:
          - ticker (str)
          - last_price (float)
          - pct_change (float, % change from previous trading day; NaN if unavailable)
    """
    # Normalize & de-duplicate symbols
    symbols: List[str] = sorted({t.strip().upper() for t in tickers if str(t).strip()})
    if not symbols:
        return pd.DataFrame(columns=["ticker", "last_price", "pct_change"])

    rows = []
    for sym in symbols:
        try:
            # Pull up to 7 calendar days to ensure we get two trading days (weekends/holidays safe)
            hist = yf.Ticker(sym).history(period="7d", interval="1d", auto_adjust=False)
            closes = hist.get("Close", pd.Series(dtype=float)).dropna()

            if closes.empty:
                rows.append({"ticker": sym, "last_price": math.nan, "pct_change": math.nan})
                continue

            last_price = float(closes.iloc[-1])

            if len(closes) >= 2:
                prev = float(closes.iloc[-2])
                pct_change = ((last_price - prev) / prev * 100.0) if prev != 0 else math.nan
            else:
                pct_change = math.nan

            rows.append(
                {
                    "ticker": sym,
                    "last_price": round(last_price, 4),
                    "pct_change": round(pct_change, 4) if pd.notna(pct_change) else math.nan,
                }
            )
        except Exception:
            # If yfinance or network hiccups, keep the row but with NaNs so the UI doesn't crash
            rows.append({"ticker": sym, "last_price": math.nan, "pct_change": math.nan})

    return pd.DataFrame(rows, columns=["ticker", "last_price", "pct_change"])
