"""Signal extraction logic for tweets pulled from X (Twitter)."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


TICKER_REGEX = re.compile(r"\$[A-Z]{1,5}")

POSITIVE_KEYWORDS = {
    "buy",
    "accumulate",
    "bullish",
    "upgrade",
    "long",
    "adding",
    "added",
}

NEGATIVE_KEYWORDS = {
    "sell",
    "downgrade",
    "bearish",
    "short",
    "trim",
    "reduce",
    "cut",
}


def _extract_tickers(text: str) -> List[str]:
    tickers = {match.group()[1:] for match in TICKER_REGEX.finditer(text)}
    return sorted(tickers)


def parse_signal_from_tweet(text: str) -> Optional[Dict[str, object]]:
    """Parse a trading signal from tweet text.

    Returns:
        None: If the tweet does not contain a clear actionable signal.
        dict: With keys ``action`` and ``tickers`` when a signal is identified.
    """

    if not text:
        return None

    tickers = _extract_tickers(text)
    if not tickers:
        return None

    lowercase_text = text.lower()

    has_positive = any(keyword in lowercase_text for keyword in POSITIVE_KEYWORDS)
    has_negative = any(keyword in lowercase_text for keyword in NEGATIVE_KEYWORDS)

    if has_positive and not has_negative:
        return {"action": "BUY", "tickers": tickers}
    if has_negative and not has_positive:
        return {"action": "SELL", "tickers": tickers}

    return None


__all__ = ["parse_signal_from_tweet"]

