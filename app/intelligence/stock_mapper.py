from __future__ import annotations

from app.models import IntelItem


def map_stocks(items: list[IntelItem], watchlist: dict) -> dict:
    cn: dict[str, list[str]] = {}
    us: dict[str, list[str]] = {}
    text_all = "\n".join([i.text() for i in items]).lower()
    for theme_name, theme in (watchlist.get("themes") or {}).items():
        theme_keywords = [str(x).lower() for x in theme.get("keywords", [])]
        if not any(k in text_all for k in theme_keywords):
            continue
        for stock in theme.get("cn_stocks", []) or []:
            cn.setdefault(str(stock), []).append(theme_name)
        for stock in theme.get("us_stocks", []) or []:
            us.setdefault(str(stock), []).append(theme_name)
    return {"cn": cn, "us": us}
