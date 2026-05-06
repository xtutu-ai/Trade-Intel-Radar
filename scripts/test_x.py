from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.collectors.x_collector import XCollector


def configured_accounts(watchlist: dict) -> list[str]:
    out: list[str] = []
    for person in (watchlist.get("people") or {}).values():
        out.extend(person.get("accounts", []) or [])
    return list(dict.fromkeys([str(x).strip().lstrip("@") for x in out if str(x).strip()]))


settings = Settings()
accounts = configured_accounts(settings.watchlist)
print(f"configured_accounts={accounts}")

collector = XCollector(
    bearer_token=settings.env("X_BEARER_TOKEN"),
    account_names=accounts,
    keyword_queries=[],
    max_keyword_queries=0,
    max_results_per_query=10,
    max_posts_per_account=20,
    max_accounts=len(accounts),
    timeout=settings.int_env("HTTP_TIMEOUT_SECONDS", 20),
)
items = collector.collect()
print(f"items={len(items)}")
for item in items[:20]:
    print("-", item.source, item.author, item.published_at, item.title[:160], item.url)
