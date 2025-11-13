"""Simple client for interacting with the X (Twitter) API v2."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests


API_BASE_URL = "https://api.twitter.com/2"


def _auth_headers() -> Dict[str, str]:
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        raise EnvironmentError("X_BEARER_TOKEN environment variable is not set")
    return {"Authorization": f"Bearer {bearer_token}"}


def get_user_id(username: str) -> str:
    url = f"{API_BASE_URL}/users/by/username/{username}"
    response = requests.get(url, headers=_auth_headers(), timeout=10)
    response.raise_for_status()
    data = response.json()
    return str(data["data"]["id"])


def get_recent_tweets(
    user_id: str,
    *,
    max_results: int = 10,
    since_id: Optional[str] = None,
) -> List[Dict]:
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
    }
    if since_id:
        params["since_id"] = since_id

    url = f"{API_BASE_URL}/users/{user_id}/tweets"
    response = requests.get(url, headers=_auth_headers(), params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


__all__ = ["get_user_id", "get_recent_tweets"]

