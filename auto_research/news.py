# auto_research/news.py
from __future__ import annotations
from typing import Dict, Iterable, List, Optional
import re
import datetime as dt
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import feedparser
feedparser.USER_AGENT = "AutoResearch/0.1 (+https://github.com/Nkokubu/auto-research)"
import pandas as pd
from dateutil import parser as dtparse

# Sensible defaults (you can pass your own feed list to the function too)
DEFAULT_FEEDS = {
    "reuters_top": "https://feeds.reuters.com/reuters/topNews",
    "reuters_business": "https://feeds.reuters.com/reuters/businessNews",
    "wsj_markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "cnbc_top": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "ap_top": "https://apnews.com/hub/ap-top-news?utm_source=rss",  # alternate RSS-ish URL
}


def _clean_url(url: str) -> str:
    """Strip tracking params like utm_* to reduce duplicate links."""
    try:
        p = urlparse(url)
        qs = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
        return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(qs), p.fragment))
    except Exception:
        return url


def _parse_published(entry) -> Optional[dt.datetime]:
    """Parse datetime from common RSS/Atom fields; return naive UTC."""
    for key in ("published", "updated", "created", "issued"):
        val = entry.get(key)
        if val:
            try:
                d = dtparse.parse(val)
                if d.tzinfo:
                    d = d.astimezone(dt.timezone.utc).replace(tzinfo=None)
                return d
            except Exception:
                pass

    # Fallback to *_parsed tuples
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                d = dt.datetime(*t[:6], tzinfo=dt.timezone.utc).replace(tzinfo=None)
                return d
            except Exception:
                pass
    return None


def _match_tickers(text: str, ticker_map: Dict[str, Iterable[str]]) -> List[str]:
    """Return list of tickers whose keyword list matches the text (word-boundary)."""
    text_l = text.lower()
    hits: List[str] = []
    for ticker, keywords in ticker_map.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(str(kw).lower())}\b", text_l):
                hits.append(ticker.upper())
                break
    return sorted(set(hits))

#the fetch helper
def _fetch(url: str):
    """Fetch a feed with a defined User-Agent; quick retry if empty."""
    parsed = feedparser.parse(url, request_headers={"User-Agent": feedparser.USER_AGENT})
    if not getattr(parsed, "entries", None):
        # Gentle second attempt
        parsed = feedparser.parse(url, request_headers={"User-Agent": feedparser.USER_AGENT})
    return parsed


def top_headlines(
    ticker_map: Dict[str, Iterable[str]],
    feeds: Optional[Iterable[str]] = None,
    max_items: int = 100,
    hours_lookback: int = 48,
) -> pd.DataFrame:
    """
    Pull top headlines from RSS/Atom feeds and tag them by ticker keywords.

    Parameters
    ----------
    ticker_map : dict
        Mapping like {"AAPL": ["Apple", "iPhone"], "TSLA": ["Tesla", "Elon Musk"]}.
        Case-insensitive; word-boundary matching to avoid false positives.
    feeds : iterable of str, optional
        List of feed URLs. Defaults to Reuters/WSJ/AP in DEFAULT_FEEDS.
    max_items : int
        Limit returned rows after sorting/newest-first.
    hours_lookback : int
        Only include stories newer than now - hours_lookback.

    Returns
    -------
    pandas.DataFrame with columns:
        - published (datetime, naive UTC)
        - title (str)
        - link (str, tracking params removed)
        - tickers (list[str])
    """
    urls = list(feeds) if feeds else list(DEFAULT_FEEDS.values())
    now = dt.datetime.utcnow()
    cutoff = now - dt.timedelta(hours=hours_lookback)

    rows: List[dict] = []
    for url in urls:
        parsed = _fetch(url)  # NEW: uses UA + retry
        for e in getattr(parsed, "entries", []):
            title = (e.get("title") or "").strip()
            link = _clean_url(e.get("link") or "")
            published = _parse_published(e) or now

            # Filter by time window
            if published < cutoff:
                continue

            # Build a matchable text blob
            text = " ".join([title, e.get("summary", "") or "", link])

            tickers = _match_tickers(text, ticker_map)
            rows.append(
                {
                    "published": published,
                    "title": title,
                    "link": link,
                    "tickers": tickers,
                }
            )

    if not rows:
        return pd.DataFrame(columns=["published", "title", "link", "tickers"])

    df = pd.DataFrame(rows)
    # Deduplicate by link/title, keep newest
    df = df.sort_values("published", ascending=False).drop_duplicates(subset=["link", "title"], keep="first")
    if max_items:
        df = df.head(max_items)
    return df.reset_index(drop=True)
