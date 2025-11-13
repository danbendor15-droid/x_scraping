"""Alpaca broker client helpers."""

from __future__ import annotations

import os

import requests


ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() != "false"

TRADING_BASE_URL = "https://paper-api.alpaca.markets" if ALPACA_PAPER else "https://api.alpaca.markets"
MARKET_DATA_URL = "https://data.alpaca.markets/v2"


def _require_credentials() -> None:
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise EnvironmentError("Alpaca API credentials are not configured")


def _auth_headers() -> dict:
    _require_credentials()
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    }


def get_last_price(symbol: str) -> float:
    url = f"{MARKET_DATA_URL}/stocks/{symbol}/trades/latest"
    response = requests.get(url, headers=_auth_headers(), timeout=10)
    response.raise_for_status()
    data = response.json()
    return float(data["trade"]["p"])


def submit_market_order(symbol: str, qty: int, side: str) -> str:
    if side.lower() not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side.lower(),
        "type": "market",
        "time_in_force": "gtc",
    }

    headers = {"Content-Type": "application/json", **_auth_headers()}
    response = requests.post(f"{TRADING_BASE_URL}/v2/orders", json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    return str(data["id"])


def decide_qty(
    ticker: str,
    price: float,
    equity: float = 10_000,
    risk_per_trade_pct: float = 0.01,
    stop_loss_pct: float = 0.05,
) -> int:
    if price <= 0:
        raise ValueError("price must be positive")
    risk_amount = equity * risk_per_trade_pct
    position_size = risk_amount / (price * stop_loss_pct)
    return max(int(position_size), 0)


__all__ = ["get_last_price", "submit_market_order", "decide_qty"]

