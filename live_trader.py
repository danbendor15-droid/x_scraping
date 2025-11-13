"""Main loop orchestrating the X-driven algo trading workflow."""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List

from broker import decide_qty, get_last_price, submit_market_order
from config import EQUITY, HARD_STOP_PCT, POLL_INTERVAL_SECONDS, RISK_PER_TRADE_PCT, USERNAMES
from signals import parse_signal_from_tweet
from storage import append_signal_log, append_trade_log, iso_timestamp, load_state, save_state
from trade_engine import Trade, open_long_trade, update_trade_with_price
from x_client import get_recent_tweets, get_user_id


logger = logging.getLogger(__name__)


OPEN_TRADES: Dict[str, Trade] = {}
USER_STATE: Dict[str, dict] = {}


def _ensure_logging_configured() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _initialise_user_state() -> None:
    global USER_STATE
    USER_STATE = load_state()
    state_changed = False
    for username in USERNAMES:
        user_entry = USER_STATE.get(username, {})
        if "user_id" not in user_entry:
            user_id = get_user_id(username)
            user_entry["user_id"] = user_id
            state_changed = True
            logger.info("Initialised user_id for %s", username)
        user_entry.setdefault("last_tweet_id", None)
        USER_STATE[username] = user_entry
    if state_changed:
        save_state(USER_STATE)


def _update_last_tweet_id(username: str, tweets: Iterable[dict]) -> None:
    tweet_ids = [tweet["id"] for tweet in tweets if "id" in tweet]
    if not tweet_ids:
        return
    last_id = max(tweet_ids, key=int)
    USER_STATE[username]["last_tweet_id"] = last_id
    save_state(USER_STATE)


def _handle_signal(username: str, tweet: dict, signal: dict) -> None:
    action = signal["action"]
    tickers: List[str] = signal["tickers"]
    tweet_id = tweet["id"]
    metrics = tweet.get("public_metrics", {})
    append_signal_log(
        timestamp=tweet.get("created_at", iso_timestamp()),
        username=username,
        tweet_id=tweet_id,
        text=tweet.get("text", ""),
        action=action,
        tickers=tickers,
        likes=metrics.get("like_count"),
        retweets=metrics.get("retweet_count"),
    )

    if action == "BUY":
        for ticker in tickers:
            if ticker in OPEN_TRADES:
                logger.info("Skipping BUY for %s - position already open", ticker)
                continue
            _open_trade_for_signal(ticker)
    elif action == "SELL":
        for ticker in tickers:
            if ticker not in OPEN_TRADES:
                logger.info("Skipping SELL for %s - no open position", ticker)
                continue
            _close_trade(ticker, reason="SELL_SIGNAL")


def _open_trade_for_signal(ticker: str) -> None:
    try:
        price = get_last_price(ticker)
    except Exception as exc:  # pragma: no cover - network call
        logger.error("Failed to fetch price for %s: %s", ticker, exc)
        return

    qty = decide_qty(ticker, price, equity=EQUITY, risk_per_trade_pct=RISK_PER_TRADE_PCT, stop_loss_pct=HARD_STOP_PCT)
    if qty <= 0:
        logger.info("Position size for %s resolved to zero; skipping", ticker)
        return

    try:
        order_id = submit_market_order(ticker, qty, side="buy")
    except Exception as exc:  # pragma: no cover - network call
        logger.error("Failed to submit BUY order for %s: %s", ticker, exc)
        return

    opened_at = iso_timestamp()
    trade = open_long_trade(ticker, entry_price=price, qty=qty, opened_at=opened_at)
    trade.broker_order_id_open = order_id
    OPEN_TRADES[ticker] = trade
    logger.info("Opened trade for %s qty=%s entry=%.2f", ticker, qty, price)


def _close_trade(ticker: str, reason: str) -> None:
    trade = OPEN_TRADES.get(ticker)
    if not trade:
        return

    try:
        price = get_last_price(ticker)
    except Exception as exc:  # pragma: no cover - network call
        logger.error("Failed to fetch price while closing %s: %s", ticker, exc)
        return

    try:
        order_id = submit_market_order(ticker, trade.qty, side="sell")
    except Exception as exc:  # pragma: no cover - network call
        logger.error("Failed to submit SELL order for %s: %s", ticker, exc)
        return

    trade.broker_order_id_close = order_id
    trade.is_open = False
    del OPEN_TRADES[ticker]

    pnl_abs = (price - trade.entry_price) * trade.qty
    pnl_pct = (price / trade.entry_price) - 1 if trade.entry_price else 0.0
    append_trade_log(
        timestamp_open=trade.opened_at,
        timestamp_close=iso_timestamp(),
        ticker=ticker,
        qty=trade.qty,
        entry_price=trade.entry_price,
        exit_price=price,
        pnl_abs=pnl_abs,
        pnl_pct=pnl_pct,
        reason_exit=reason,
        order_id_open=trade.broker_order_id_open,
        order_id_close=trade.broker_order_id_close,
    )
    logger.info("Closed trade for %s reason=%s exit=%.2f", ticker, reason, price)


def _poll_signals() -> None:
    for username in USERNAMES:
        state = USER_STATE.get(username, {})
        user_id = state.get("user_id")
        if not user_id:
            logger.warning("Missing user_id for %s", username)
            continue
        since_id = state.get("last_tweet_id")
        try:
            tweets = get_recent_tweets(user_id, since_id=since_id)
        except Exception as exc:  # pragma: no cover - network call
            logger.error("Failed to fetch tweets for %s: %s", username, exc)
            continue

        if not tweets:
            continue

        # Process oldest to newest to keep order deterministic.
        tweets_sorted = sorted(tweets, key=lambda t: int(t["id"]))
        for tweet in tweets_sorted:
            signal = parse_signal_from_tweet(tweet.get("text", ""))
            if signal:
                logger.info("[SIGNAL] %s %s %s", username, signal["action"], signal["tickers"])
                _handle_signal(username, tweet, signal)

        _update_last_tweet_id(username, tweets_sorted)


def _manage_open_trades() -> None:
    tickers = list(OPEN_TRADES.keys())
    for ticker in tickers:
        trade = OPEN_TRADES.get(ticker)
        if not trade or not trade.is_open:
            continue
        try:
            price = get_last_price(ticker)
        except Exception as exc:  # pragma: no cover - network call
            logger.error("Failed to update price for %s: %s", ticker, exc)
            continue

        should_close = update_trade_with_price(trade, price)
        if should_close:
            logger.info("Stop triggered for %s", ticker)
            _close_trade(ticker, reason="STOP")


def run() -> None:
    _ensure_logging_configured()
    _initialise_user_state()
    logger.info("Starting live trader loop for %d users", len(USERNAMES))
    while True:
        _poll_signals()
        _manage_open_trades()
        time.sleep(POLL_INTERVAL_SECONDS)


__all__ = ["run", "OPEN_TRADES", "USER_STATE"]

