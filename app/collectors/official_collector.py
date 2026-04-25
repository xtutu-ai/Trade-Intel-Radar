from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.collectors.base import Collector
from app.models import IntelItem

log = logging.getLogger(__name__)


class OfficialPageCollector(Collector):
    name = "official_pages"

    def __init__(self, pages: list[dict], timeout: int = 20):
        self.pages = pages
        self.timeout = timeout

    def collect(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        headers = {"User-Agent": "trade-intel-radar/0.1 personal-use"}
        for page in self.pages:
            try:
                resp = requests.get(page["url"], timeout=self.timeout, headers=headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                seen: set[str] = set()
                for a in soup.select("a")[:120]:
                    title = a.get_text(" ", strip=True)
                    href = a.get("href") or ""
                    if len(title) < 12 or not href:
                        continue
                    key = title.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(IntelItem(source=page.get("name", "official"), title=title, url=urljoin(page["url"], href)))
                    if len(items) >= 80:
                        break
            except Exception as exc:
                log.warning("Official page collector failed for %s: %s", page.get("url"), exc)
        return items
