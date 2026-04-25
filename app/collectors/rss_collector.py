from __future__ import annotations

import logging

import feedparser
from bs4 import BeautifulSoup

from app.collectors.base import Collector
from app.models import IntelItem

log = logging.getLogger(__name__)


def _clean_html(value: str) -> str:
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


class RSSCollector(Collector):
    name = "rss"

    def __init__(self, feeds: list[dict], max_entries_per_feed: int = 12):
        self.feeds = feeds
        self.max_entries = max_entries_per_feed

    def collect(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for feed in self.feeds:
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[: self.max_entries]:
                    items.append(
                        IntelItem(
                            source=feed.get("name", "rss"),
                            title=_clean_html(getattr(entry, "title", "")),
                            url=getattr(entry, "link", ""),
                            content=_clean_html(getattr(entry, "summary", "")),
                            published_at=getattr(entry, "published", "") or getattr(entry, "updated", ""),
                            raw={"feed": feed.get("url")},
                        )
                    )
            except Exception as exc:
                log.warning("RSS collector failed for %s: %s", feed.get("url"), exc)
        return items
