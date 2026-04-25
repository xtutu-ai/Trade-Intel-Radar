from __future__ import annotations

import logging

import requests

from app.collectors.base import Collector
from app.models import IntelItem

log = logging.getLogger(__name__)


class XCollector(Collector):
    """Small-budget X API collector using official X API v2 recent search."""

    name = "x"

    def __init__(self, bearer_token: str, account_names: list[str], keyword_queries: list[str], max_keyword_queries: int = 10, max_results_per_query: int = 10, timeout: int = 20):
        self.bearer_token = bearer_token.strip()
        self.account_names = account_names
        self.keyword_queries = keyword_queries
        self.max_keyword_queries = max_keyword_queries
        self.max_results_per_query = max_results_per_query
        self.timeout = timeout

    def collect(self) -> list[IntelItem]:
        if not self.bearer_token:
            log.info("X_BEARER_TOKEN is empty; skipping X collector")
            return []
        items: list[IntelItem] = []
        queries = list(self.keyword_queries[: self.max_keyword_queries])
        if self.account_names:
            account_clause = " OR ".join([f"from:{x}" for x in self.account_names[:20]])
            queries.insert(0, f"({account_clause}) -is:retweet")
        for query in queries[: self.max_keyword_queries + 1]:
            items.extend(self._recent_search(query))
        return items

    def _recent_search(self, query: str) -> list[IntelItem]:
        url = "https://api.x.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max(10, min(100, self.max_results_per_query)),
            "tweet.fields": "created_at,author_id,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            if resp.status_code >= 400:
                log.warning("X API failed %s: %s", resp.status_code, resp.text[:300])
                return []
            data = resp.json()
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            out: list[IntelItem] = []
            for tweet in data.get("data", []) or []:
                user = users.get(tweet.get("author_id", ""), {})
                username = user.get("username", tweet.get("author_id", ""))
                tid = tweet.get("id", "")
                out.append(IntelItem(source="x.com", title=tweet.get("text", "")[:180], url=f"https://x.com/{username}/status/{tid}" if username and tid else "", content=tweet.get("text", ""), published_at=tweet.get("created_at", ""), author=username, raw={"query": query, "metrics": tweet.get("public_metrics", {})}))
            return out
        except Exception as exc:
            log.warning("X recent search failed for query=%r: %s", query, exc)
            return []
