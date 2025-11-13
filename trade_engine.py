"""Trade management logic, including hard and trailing stop updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from config import HARD_STOP_PCT, TRAILING_STOP_PCT


@dataclass
class Trade:
    ticker: str
    direction: str
    entry_price: float
    hard_stop: float
    trailing_stop: float
    highest_price: float
    qty: int
    opened_at: str
    is_open: bool = True
    broker_order_id_open: Optional[str] = None
    broker_order_id_close: Optional[str] = None


def open_long_trade(ticker: str, entry_price: float, qty: int, opened_at: str) -> Trade:
    hard_stop = entry_price * (1 - HARD_STOP_PCT)
    trailing_stop = hard_stop
    return Trade(
        ticker=ticker,
        direction="LONG",
        entry_price=entry_price,
        hard_stop=hard_stop,
        trailing_stop=trailing_stop,
        highest_price=entry_price,
        qty=qty,
        opened_at=opened_at,
    )


def update_trade_with_price(trade: Trade, current_price: float) -> bool:
    if not trade.is_open:
        return False

    if current_price > trade.highest_price:
        trade.highest_price = current_price
        new_trailing = trade.highest_price * (1 - TRAILING_STOP_PCT)
        trade.trailing_stop = max(new_trailing, trade.hard_stop)

    effective_stop = max(trade.hard_stop, trade.trailing_stop)
    if current_price <= effective_stop:
        trade.is_open = False
        return True

    return False


__all__ = ["Trade", "open_long_trade", "update_trade_with_price"]

