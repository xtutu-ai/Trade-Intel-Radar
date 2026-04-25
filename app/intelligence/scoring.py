from __future__ import annotations

from urllib.parse import urlparse

from app.models import IntelItem


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def score_items(items: list[IntelItem], scoring_cfg: dict) -> list[IntelItem]:
    source_weights = scoring_cfg.get("source_weights", {}) or {}
    keyword_weights = scoring_cfg.get("keyword_weights", {}) or {}
    for item in items:
        text = item.text().lower()
        score = 0.0
        domain = _domain(item.url)
        for source_key, weight in source_weights.items():
            if source_key.lower() in item.source.lower() or source_key.lower() in domain:
                score += float(weight)
        matched = []
        for kw, weight in keyword_weights.items():
            if kw.lower() in text:
                score += float(weight)
                matched.append(kw)
        metrics = item.raw.get("metrics") if isinstance(item.raw, dict) else None
        if metrics:
            likes = metrics.get("like_count", 0) or 0
            reposts = metrics.get("retweet_count", 0) or metrics.get("repost_count", 0) or 0
            replies = metrics.get("reply_count", 0) or 0
            score += min(10, (likes + reposts * 2 + replies) / 1000)
        item.score = round(score, 2)
        item.matched_keywords = matched
    return sorted(items, key=lambda x: x.score, reverse=True)


def dedup_items(items: list[IntelItem]) -> list[IntelItem]:
    seen: set[str] = set()
    out: list[IntelItem] = []
    for item in items:
        key = item.stable_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
