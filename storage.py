"""Persistence helpers for state and logs."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional

from config import SIGNALS_CSV, STATE_FILE, TRADES_CSV


def load_state(path: Path = STATE_FILE) -> Dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state: Mapping[str, dict], path: Path = STATE_FILE) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def append_signal_log(
    *,
    timestamp: str,
    username: str,
    tweet_id: str,
    text: str,
    action: str,
    tickers: Iterable[str],
    likes: Optional[int],
    retweets: Optional[int],
    source: str = "X",
    path: Path = SIGNALS_CSV,
) -> None:
    headers = [
        "timestamp",
        "username",
        "tweet_id",
        "text",
        "action",
        "tickers",
        "likes",
        "retweets",
        "source",
    ]
    needs_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if needs_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": timestamp,
                "username": username,
                "tweet_id": tweet_id,
                "text": text,
                "action": action,
                "tickers": ",".join(tickers),
                "likes": likes if likes is not None else "",
                "retweets": retweets if retweets is not None else "",
                "source": source,
            }
        )


def append_trade_log(
    *,
    timestamp_open: str,
    timestamp_close: str,
    ticker: str,
    qty: int,
    entry_price: float,
    exit_price: float,
    pnl_abs: float,
    pnl_pct: float,
    reason_exit: str,
    order_id_open: Optional[str],
    order_id_close: Optional[str],
    path: Path = TRADES_CSV,
) -> None:
    headers = [
        "timestamp_open",
        "timestamp_close",
        "ticker",
        "qty",
        "entry_price",
        "exit_price",
        "pnl_abs",
        "pnl_pct",
        "reason_exit",
        "order_id_open",
        "order_id_close",
    ]
    needs_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if needs_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_open": timestamp_open,
                "timestamp_close": timestamp_close,
                "ticker": ticker,
                "qty": qty,
                "entry_price": f"{entry_price:.2f}",
                "exit_price": f"{exit_price:.2f}",
                "pnl_abs": f"{pnl_abs:.2f}",
                "pnl_pct": f"{pnl_pct:.4f}",
                "reason_exit": reason_exit,
                "order_id_open": order_id_open or "",
                "order_id_close": order_id_close or "",
            }
        )


def iso_timestamp() -> str:
    return datetime.utcnow().isoformat()


__all__ = ["load_state", "save_state", "append_signal_log", "append_trade_log", "iso_timestamp"]

