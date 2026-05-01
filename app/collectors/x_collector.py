from __future__ import annotations

import logging
import time

import requests

from app.collectors.base import Collector
from app.models import IntelItem

log = logging.getLogger(__name__)


class XCollector(Collector):
    """Small-budget X API collector.

    Strategy:
    1. Pull fixed-account timelines for watch accounts, such as Elon Musk, WhiteHouse, Tesla, xAI.
    2. Run a small number of recent-search keyword queries.

    Both calls use official X API v2 and are skipped when X_BEARER_TOKEN is empty.
    """

    name = "x"

    def __init__(
        self,
        bearer_token: str,
        account_names: list[str],
        keyword_queries: list[str],
        max_keyword_queries: int = 10,
        max_results_per_query: int = 10,
        max_posts_per_account: int = 8,
        max_accounts: int = 20,
        timeout: int = 20,
        sleep_seconds: float = 0.2,
    ):
        self.bearer_token = bearer_token.strip()
        self.account_names = list(dict.fromkeys([x.strip().lstrip("@") for x in account_names if x.strip()]))
        self.keyword_queries = list(dict.fromkeys([x.strip() for x in keyword_queries if x.strip()]))
        self.max_keyword_queries = max_keyword_queries
        self.max_results_per_query = max_results_per_query
        self.max_posts_per_account = max_posts_per_account
        self.max_accounts = max_accounts
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds

    def collect(self) -> list[IntelItem]:
        if not self.bearer_token:
            log.info("X_BEARER_TOKEN is empty; skipping X collector")
            return []
        items: list[IntelItem] = []
        for username in self.account_names[: self.max_accounts]:
            items.extend(self._user_timeline(username))
            time.sleep(self.sleep_seconds)
        for query in self.keyword_queries[: self.max_keyword_queries]:
            items.extend(self._recent_search(query))
            time.sleep(self.sleep_seconds)
        return items

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def _get_user_id(self, username: str) -> str:
        url = f"https://api.x.com/2/users/by/username/{username}"
        params = {"user.fields": "username,name"}
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            if resp.status_code >= 400:
                log.warning("X user lookup failed username=%s status=%s body=%s", username, resp.status_code, resp.text[:300])
                return ""
            return str((resp.json().get("data") or {}).get("id") or "")
        except Exception as exc:
            log.warning("X user lookup exception username=%s: %s", username, exc)
            return ""

    def _user_timeline(self, username: str) -> list[IntelItem]:
        user_id = self._get_user_id(username)
        if not user_id:
            return []
        url = f"https://api.x.com/2/users/{user_id}/tweets"
        params = {
            "max_results": max(5, min(100, self.max_posts_per_account)),
            "tweet.fields": "created_at,author_id,public_metrics,lang,referenced_tweets",
            "exclude": "retweets,replies",
        }
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            if resp.status_code >= 400:
                log.warning("X timeline failed username=%s status=%s body=%s", username, resp.status_code, resp.text[:300])
                return []
            data = resp.json()
            out: list[IntelItem] = []
            for tweet in data.get("data", []) or []:
                tid = tweet.get("id", "")
                text = tweet.get("text", "")
                out.append(
                    IntelItem(
                        source="x.com",
                        title=text[:180],
                        url=f"https://x.com/{username}/status/{tid}" if tid else "",
                        content=text,
                        published_at=tweet.get("created_at", ""),
                        author=username,
                        raw={"mode": "user_timeline", "metrics": tweet.get("public_metrics", {})},
                    )
                )
            return out
        except Exception as exc:
            log.warning("X timeline exception username=%s: %s", username, exc)
            return []

    def _recent_search(self, query: str) -> list[IntelItem]:
        url = "https://api.x.com/2/tweets/search/recent"
        params = {
            "query": f"({query}) -is:retweet",
            "max_results": max(10, min(100, self.max_results_per_query)),
            "tweet.fields": "created_at,author_id,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            if resp.status_code >= 400:
                log.warning("X recent search failed query=%r status=%s body=%s", query, resp.status_code, resp.text[:300])
                return []
            data = resp.json()
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            out: list[IntelItem] = []
            for tweet in data.get("data", []) or []:
                user = users.get(tweet.get("author_id", ""), {})
                username = user.get("username", tweet.get("author_id", ""))
                tid = tweet.get("id", "")
                text = tweet.get("text", "")
                out.append(
                    IntelItem(
                        source="x.com",
                        title=text[:180],
                        url=f"https://x.com/{username}/status/{tid}" if username and tid else "",
                        content=text,
                        published_at=tweet.get("created_at", ""),
                        author=username,
                        raw={"mode": "recent_search", "query": query, "metrics": tweet.get("public_metrics", {})},
                    )
                )
            return out
        except Exception as exc:
            log.warning("X recent search exception query=%r: %s", query, exc)
            return []
