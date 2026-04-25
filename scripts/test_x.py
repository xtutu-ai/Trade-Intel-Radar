from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.collectors.x_collector import XCollector
from app.pipeline import _flatten_watchlist_accounts, _flatten_watchlist_queries

settings = Settings()
collector = XCollector(
    bearer_token=settings.env("X_BEARER_TOKEN"),
    account_names=_flatten_watchlist_accounts(settings.watchlist),
    keyword_queries=_flatten_watchlist_queries(settings.watchlist),
    max_keyword_queries=2,
    max_results_per_query=10,
    timeout=settings.int_env("HTTP_TIMEOUT_SECONDS", 20),
)
items = collector.collect()
print(f"items={len(items)}")
for item in items[:5]:
    print("-", item.source, item.author, item.title[:120], item.url)
