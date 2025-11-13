# X Scraping Algo Trading Bot

This repository contains a reference implementation for an algo-trading bot that
monitors predefined X (Twitter) accounts, parses BUY/SELL signals from their
tweets, and routes simulated orders to the Alpaca brokerage API. The system is
designed to operate in paper-trading mode by default with a clear separation of
responsibilities across modules:

* `config.py` – Runtime configuration values (usernames, risk settings, polling
  interval, file paths).
* `x_client.py` – Lightweight wrapper around the X API v2 for looking up users
  and fetching their recent tweets.
* `signals.py` – Signal extraction logic based on tweet content, supporting
  ticker detection and keyword-based sentiment (BUY/SELL).
* `trade_engine.py` – Data model and rules for managing open trades including
  hard stop-loss and trailing-stop calculations.
* `broker.py` – Minimal Alpaca client with helpers for market data lookups,
  order submission, and position sizing utilities.
* `storage.py` – Persistence helpers for bot state and CSV-based signal/trade
  logging.
* `live_trader.py` – The continuous service loop that ties together data
  ingestion, signal processing, order placement, and risk management.

## Quick start

1. Install dependencies: `pip install -r requirements.txt` (create the file as
   needed with `requests` and optional tooling).
2. Export required environment variables:

   ```bash
   export X_BEARER_TOKEN=...
   export ALPACA_API_KEY=...
   export ALPACA_SECRET_KEY=...
   # Optional: export ALPACA_PAPER=false  # to switch to live trading
   ```

3. Run the live trader loop:

   ```bash
   python -m live_trader
   ```

The bot will create/update `state.json`, `signals.csv`, and `trades.csv` in the
repository root as it observes signals and manages trades. Review and tweak the
parameters in `config.py` before enabling live trading.

