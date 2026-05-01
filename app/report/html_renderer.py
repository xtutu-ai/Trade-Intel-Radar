from __future__ import annotations

from datetime import datetime
from jinja2 import Template

from app.models import IntelItem

_TEMPLATE = Template("""
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; color:#1f2937; line-height:1.55; }
.container { max-width: 920px; margin: 0 auto; padding: 20px; }
h1 { font-size: 24px; margin-bottom: 6px; }
h2 { border-left: 4px solid #2563eb; padding-left: 10px; margin-top: 28px; font-size: 18px; }
.card { border:1px solid #e5e7eb; border-radius: 10px; padding: 14px; margin: 12px 0; background:#fff; }
.translation { border-left: 3px solid #16a34a; background:#f0fdf4; }
.original { color:#6b7280; font-size: 13px; margin-top: 6px; }
.muted { color:#6b7280; font-size: 13px; }
.badge { display:inline-block; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; margin-right:6px; }
.badge-green { background:#dcfce7; color:#166534; }
.risk { color:#b45309; }
.footer { margin-top: 30px; color:#6b7280; font-size:12px; }
a { color:#2563eb; text-decoration:none; }
</style>
</head>
<body>
<div class="container">
<h1>每日交易情报 - {{ date }}</h1>
<div class="muted">由 Trade-Intel-Radar 自动生成。仅作信息整理与观察，不构成投资建议。</div>
<h2>一句话结论</h2>
<div class="card"><strong>{{ analysis.get('one_sentence_conclusion', 'LLM 未返回结论，以下为规则筛选结果。') }}</strong></div>
<h2>今日 Top 情报</h2>
{% for x in analysis.get('top_intel', []) %}
<div class="card">
  <div><span class="badge">{{ x.get('source','') }}</span><strong>{{ x.get('title','') }}</strong></div>
  <p>{{ x.get('why_it_matters','') }}</p>
  <p><strong>影响：</strong>{{ x.get('market_impact','') }}</p>
  <p class="risk"><strong>兑现风险：</strong>{{ x.get('already_priced_in_risk','') }}</p>
  <div class="muted">相关：{{ ', '.join(x.get('related_assets', [])) }}</div>
</div>
{% endfor %}
<h2>重点英文信息中文翻译/摘要</h2>
{% for x in analysis.get('translated_items', []) %}
<div class="card translation">
  <div><span class="badge badge-green">中文翻译</span><span class="badge">{{ x.get('source','') }}</span><strong>{{ x.get('chinese_title','') }}</strong></div>
  <div class="original">原文：{{ x.get('original_title','') }}</div>
  <p>{{ x.get('chinese_summary','') }}</p>
  <p><strong>交易相关性：</strong>{{ x.get('trading_relevance','') }}</p>
</div>
{% else %}
<div class="card muted">LLM 未返回 translated_items；如果已经配置 OpenRouter，请检查模型是否支持 JSON 输出。</div>
{% endfor %}
<h2>主线变化预警</h2>
<ul>{% for x in analysis.get('theme_shift_alerts', []) %}<li>{{ x }}</li>{% else %}<li>暂无明显主线迁移信号，需继续积累历史样本。</li>{% endfor %}</ul>
<h2>Trump / 政策风险</h2>
<ul>{% for x in analysis.get('trump_policy_watch', []) %}<li>{{ x }}</li>{% else %}<li>暂无高权重政策信号。</li>{% endfor %}</ul>
<h2>Musk / Tesla / xAI</h2>
<ul>{% for x in analysis.get('musk_ai_tesla_watch', []) %}<li>{{ x }}</li>{% else %}<li>暂无高权重 Musk/Tesla/xAI 信号。</li>{% endfor %}</ul>
<h2>机构观点观察</h2>
<ul>{% for x in analysis.get('institution_watch', []) %}<li>{{ x }}</li>{% else %}<li>暂无明确机构观点变化。</li>{% endfor %}</ul>
<h2>A股观察清单</h2>
<ul>{% for x in analysis.get('cn_stock_watchlist', []) %}<li>{{ x }}</li>{% else %}<li>暂无。</li>{% endfor %}</ul>
<h2>美股观察清单</h2>
<ul>{% for x in analysis.get('us_stock_watchlist', []) %}<li>{{ x }}</li>{% else %}<li>暂无。</li>{% endfor %}</ul>
<h2>明日观察点</h2>
<ul>{% for x in analysis.get('tomorrow_observation', []) %}<li>{{ x }}</li>{% else %}<li>观察高权重主题在竞价、板块强度和成交额上的确认。</li>{% endfor %}</ul>
<h2>风险提示</h2>
<ul>{% for x in analysis.get('risks', []) %}<li>{{ x }}</li>{% else %}<li>信息可能滞后或已被市场提前交易；需要结合实际盘面确认。</li>{% endfor %}</ul>
<h2>规则筛选原始 Top 项</h2>
{% for item in items[:30] %}
<div class="card">
  <div><span class="badge">score {{ item.score }}</span><span class="badge">{{ item.source }}</span><strong>{{ item.title }}</strong></div>
  {% if item.url %}<div class="muted"><a href="{{ item.url }}">打开来源</a> ｜ {{ item.published_at }}</div>{% endif %}
  <p>{{ item.content[:350] }}</p>
  <div class="muted">命中关键词：{{ ', '.join(item.matched_keywords) }}</div>
</div>
{% endfor %}
<div class="footer">Generated at {{ generated_at }}. This email is informational only.</div>
</div>
</body>
</html>
""")


def fallback_analysis(items: list[IntelItem], theme_shift: dict, stock_map: dict) -> dict:
    top = []
    translated = []
    for idx, it in enumerate(items[:8], start=1):
        top.append({
            "title": it.title,
            "source": it.source,
            "why_it_matters": f"规则评分 {it.score}，命中关键词：{', '.join(it.matched_keywords[:8])}",
            "market_impact": "需要结合盘面确认；该条信息与关注主题存在交集。",
            "already_priced_in_risk": "未知，需观察相关板块是否已提前上涨。",
            "related_assets": [],
        })
        translated.append({
            "id": idx,
            "source": it.source,
            "original_title": it.title,
            "chinese_title": it.title,
            "chinese_summary": "LLM 未启用或调用失败，暂时只能显示原始标题。配置 OpenRouter 后会自动生成中文翻译和中文摘要。",
            "trading_relevance": f"规则评分 {it.score}，命中关键词：{', '.join(it.matched_keywords[:8])}",
        })
    return {
        "one_sentence_conclusion": "LLM 未启用或调用失败，当前邮件基于规则评分生成。",
        "top_intel": top,
        "translated_items": translated,
        "theme_shift_alerts": [str(x) for x in theme_shift.get("alerts", [])],
        "trump_policy_watch": [],
        "musk_ai_tesla_watch": [],
        "institution_watch": [],
        "cn_stock_watchlist": [f"{k}: {', '.join(v)}" for k, v in stock_map.get("cn", {}).items()][:20],
        "us_stock_watchlist": [f"{k}: {', '.join(v)}" for k, v in stock_map.get("us", {}).items()][:20],
        "tomorrow_observation": ["重点观察高分主题是否在竞价、成交额和板块扩散上确认。"],
        "risks": ["规则筛选不能替代人工判断。", "来源可能滞后或已被市场提前交易。"],
    }


def render_html(date: str, analysis: dict, items: list[IntelItem]) -> str:
    return _TEMPLATE.render(date=date, analysis=analysis, items=items, generated_at=datetime.now().isoformat(timespec="seconds"))
