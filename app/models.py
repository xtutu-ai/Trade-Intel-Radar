from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IntelItem:
    source: str
    title: str
    url: str = ""
    content: str = ""
    published_at: str = ""
    author: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    matched_keywords: list[str] = field(default_factory=list)

    def stable_key(self) -> str:
        base = self.url or f"{self.source}:{self.title}:{self.published_at}"
        return base.strip().lower()

    def text(self) -> str:
        return f"{self.title}\n{self.content}".strip()


@dataclass
class DailyReport:
    date: str
    items: list[IntelItem]
    analysis: dict[str, Any]
    html: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
