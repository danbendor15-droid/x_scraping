"""Configuration values for the X-based algo trading bot."""

from pathlib import Path


# ---- Twitter / X configuration -------------------------------------------------

# Accounts that will be monitored for trading signals.
USERNAMES = [
    "TheTranscript_",
    "earnings_guy",
    "fundstrat",
    "elonmusk",
    "StockMKTNewz",
    "eWhispers",
    "realDonaldTrump",
]


# ---- Risk management -----------------------------------------------------------

# Hard stop percentage (e.g. 0.05 -> 5%).
HARD_STOP_PCT = 0.05

# Trailing stop percentage below the highest recorded price.
TRAILING_STOP_PCT = 0.03

# Portfolio configuration used for position sizing.
EQUITY = 10_000.0

# Maximum portfolio percentage risked per trade.
RISK_PER_TRADE_PCT = 0.01


# ---- Runtime behaviour ---------------------------------------------------------

# Delay between polling iterations when running live_trader.
POLL_INTERVAL_SECONDS = 15


# ---- Persisted resources -------------------------------------------------------

STATE_FILE = Path("state.json")
SIGNALS_CSV = Path("signals.csv")
TRADES_CSV = Path("trades.csv")

