# auto_research/db.py
from __future__ import annotations
from typing import Optional
import json
import datetime as dt
from pathlib import Path

from sqlmodel import SQLModel, Field, create_engine, Session

# DB file lives at repo root, e.g., ./auto_research.db
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "auto_research.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)


# ---------- Models ----------
class Prices(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_time: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    ticker: str
    last_price: Optional[float] = None
    pct_change: Optional[float] = None


class News(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_time: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    published: Optional[dt.datetime] = None
    title: str
    link: str
    tickers_json: str  # JSON-encoded list
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None


# ---------- Setup ----------
def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


# ---------- Inserts (snapshots = last 30 rows per run) ----------
def save_prices_snapshot(df) -> int:
    """
    Insert last 30 rows from the given DataFrame into Prices table.
    Expected cols: ['ticker','last_price','pct_change']
    Returns number of rows inserted.
    """
    if df is None or df.empty:
        return 0
    snap = df.tail(30).copy()
    snap["snapshot_time"] = dt.datetime.utcnow()
    rows = []
    for r in snap.itertuples(index=False):
        rows.append(
            Prices(
                snapshot_time=snap["snapshot_time"].iloc[0],
                ticker=str(getattr(r, "ticker", "")),
                last_price=_to_float(getattr(r, "last_price", None)),
                pct_change=_to_float(getattr(r, "pct_change", None)),
            )
        )
    with Session(engine) as s:
        s.add_all(rows)
        s.commit()
    return len(rows)


def save_news_snapshot(df) -> int:
    """
    Insert last 30 rows from the given DataFrame into News table.
    Expected cols: ['published','title','link','tickers'] and optionally
    ['sentiment','sentiment_score'].
    """
    if df is None or df.empty:
        return 0
    snap = df.tail(30).copy()
    snap["snapshot_time"] = dt.datetime.utcnow()
    rows = []
    for r in snap.itertuples(index=False):
        rows.append(
            News(
                snapshot_time=snap["snapshot_time"].iloc[0],
                published=_to_dt(getattr(r, "published", None)),
                title=str(getattr(r, "title", "")),
                link=str(getattr(r, "link", "")),
                tickers_json=json.dumps(list(getattr(r, "tickers", []) or [])),
                sentiment=str(getattr(r, "sentiment", "")) if hasattr(r, "sentiment") else None,
                sentiment_score=_to_float(getattr(r, "sentiment_score", None)) if hasattr(r, "sentiment_score") else None,
            )
        )
    with Session(engine) as s:
        s.add_all(rows)
        s.commit()
    return len(rows)


# ---------- Utils ----------
def _to_float(x):
    try:
        return float(x) if x is not None else None
    except Exception:
        return None

def _to_dt(x):
    if x is None:
        return None
    if isinstance(x, dt.datetime):
        return x
    try:
        # best-effort parse (assume pandas Timestamp)
        return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None
