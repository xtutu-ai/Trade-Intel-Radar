from __future__ import annotations

import json

from app.models import IntelItem


def build_daily_messages(items: list[IntelItem], watchlist: dict, stock_map: dict, theme_shift: dict) -> list[dict[str, str]]:
    payload_items = []
    for idx, it in enumerate(items, start=1):
        payload_items.append({
            "id": idx,
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
4. 所有分析、标题改写、翻译、摘要都必须使用中文。
5. 对英文原文不要逐字硬翻，要翻成适合中文交易者阅读的自然表达。
6. 输出必须是合法 JSON，不要 Markdown。
""".strip()
    user = {
        "task": "生成每日交易情报邮件分析 JSON，并为重要英文信息提供中文翻译/中文摘要",
        "translation_rules": [
            "对 top 20 条高分 item 生成中文翻译或中文摘要。",
            "如果原文是英文，翻译标题并用1-2句话解释核心含义。",
            "如果原文已经是中文，则改写成更清楚的中文摘要。",
            "不要添加输入中没有的事实；可以明确写‘推断’。"
        ],
        "required_schema": {
            "one_sentence_conclusion": "一句话核心结论，中文",
            "top_intel": [{"title": "中文情报标题", "source": "来源", "why_it_matters": "为什么重要，中文", "market_impact": "对A股/美股/行业链影响，中文", "already_priced_in_risk": "是否可能已被市场提前交易，中文", "related_assets": ["股票/板块/资产"]}],
            "translated_items": [{"id": 1, "source": "来源", "original_title": "原始标题", "chinese_title": "中文标题", "chinese_summary": "中文摘要，1-2句话", "trading_relevance": "对交易的相关性，中文"}],
            "theme_shift_alerts": ["主线变化提醒，中文"],
            "trump_policy_watch": ["Trump/政策风险要点，中文"],
            "musk_ai_tesla_watch": ["Musk/Tesla/xAI要点，中文"],
            "institution_watch": ["机构观点变化，中文"],
            "cn_stock_watchlist": ["A股观察清单和理由，中文"],
            "us_stock_watchlist": ["美股观察清单和理由，中文"],
            "tomorrow_observation": ["明日观察点，中文"],
            "risks": ["风险提示，中文"]
        },
        "theme_shift_by_rules": theme_shift,
        "stock_mapping_by_rules": stock_map,
        "watchlist": watchlist,
        "items": payload_items,
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]
