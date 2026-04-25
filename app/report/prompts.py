from __future__ import annotations

import json

from app.models import IntelItem


def build_daily_messages(items: list[IntelItem], watchlist: dict, stock_map: dict, theme_shift: dict) -> list[dict[str, str]]:
    payload_items = []
    for it in items:
        payload_items.append({
            "source": it.source,
            "title": it.title,
            "url": it.url,
            "content": it.content[:1200],
            "published_at": it.published_at,
            "author": it.author,
            "score": it.score,
            "matched_keywords": it.matched_keywords,
        })
    system = """
你是一名谨慎、专业的交易情报分析师。任务不是泛泛总结新闻，而是识别政策、机构观点、科技主线是否发生变化，并映射到A股/美股观察方向。
要求：
1. 不要编造未在输入中出现的信息。
2. 明确区分：事实、推断、交易观察。
3. 不给绝对买卖指令，只给观察清单、风险、可能受益链条。
4. 输出必须是合法 JSON，不要 Markdown。
""".strip()
    user = {
        "task": "生成每日交易情报邮件分析 JSON",
        "required_schema": {
            "one_sentence_conclusion": "一句话核心结论",
            "top_intel": [{"title": "情报标题", "source": "来源", "why_it_matters": "为什么重要", "market_impact": "对A股/美股/行业链影响", "already_priced_in_risk": "是否可能已被市场提前交易", "related_assets": ["股票/板块/资产"]}],
            "theme_shift_alerts": ["主线变化提醒"],
            "trump_policy_watch": ["Trump/政策风险要点"],
            "musk_ai_tesla_watch": ["Musk/Tesla/xAI要点"],
            "institution_watch": ["机构观点变化"],
            "cn_stock_watchlist": ["A股观察清单和理由"],
            "us_stock_watchlist": ["美股观察清单和理由"],
            "tomorrow_observation": ["明日观察点"],
            "risks": ["风险提示"]
        },
        "theme_shift_by_rules": theme_shift,
        "stock_mapping_by_rules": stock_map,
        "watchlist": watchlist,
        "items": payload_items,
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]
