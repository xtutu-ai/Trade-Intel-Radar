from __future__ import annotations

from collections import Counter

from app.models import IntelItem


def build_theme_snapshot(items: list[IntelItem], watchlist: dict) -> dict:
    theme_counts: dict[str, Counter] = {}
    stock_hits: Counter = Counter()
    for theme_name, theme in (watchlist.get("themes") or {}).items():
        keywords = theme.get("keywords", []) or []
        counter: Counter = Counter()
        for item in items:
            text = item.text().lower()
            for kw in keywords:
                hits = text.count(str(kw).lower())
                if hits:
                    counter[str(kw)] += hits
        theme_counts[theme_name] = counter
        for stock in (theme.get("cn_stocks", []) or []) + (theme.get("us_stocks", []) or []):
            st = str(stock).lower()
            for item in items:
                if st in item.text().lower():
                    stock_hits[str(stock)] += 1
    return {"themes": {k: dict(v.most_common()) for k, v in theme_counts.items()}, "stock_hits": dict(stock_hits.most_common(30))}


def compare_theme_shift(current: dict, recent_snapshots: list[dict]) -> dict:
    if not recent_snapshots:
        return {"alerts": [], "note": "No historical theme snapshots yet."}
    alerts = []
    prev_totals: Counter = Counter()
    for snap in recent_snapshots:
        for theme, counts in (snap.get("theme", {}).get("themes", {}) or {}).items():
            for kw, count in counts.items():
                prev_totals[f"{theme}:{kw}"] += count
    current_totals: Counter = Counter()
    for theme, counts in (current.get("themes", {}) or {}).items():
        for kw, count in counts.items():
            current_totals[f"{theme}:{kw}"] += count
    for key, cur in current_totals.most_common(20):
        prev_avg = prev_totals.get(key, 0) / max(1, len(recent_snapshots))
        if cur >= 2 and cur >= prev_avg * 2 + 1:
            alerts.append({"signal": key, "current_count": cur, "recent_avg": round(prev_avg, 2), "type": "rising_theme"})
    return {"alerts": alerts[:10]}
