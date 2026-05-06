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
.original { white-space: pre-wrap; color:#111827; background:#f9fafb; padding:10px; border-radius:8px; margin-top:8px; }
.muted { color:#6b7280; font-size: 13px; }
.badge { display:inline-block; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; margin-right:6px; }
.badge-green { background:#dcfce7; color:#166534; }
.footer { margin-top: 30px; color:#6b7280; font-size:12px; }
a { color:#2563eb; text-decoration:none; }
</style>
</head>
<body>
<div class="container">
<h1>X 言论日报 - {{ date }}</h1>
<div class="muted">仅抓取 watchlist.yaml 中配置账号的当天 X 发言。原文 + 中文翻译，仅作信息整理，不构成投资建议。</div>
<h2>今日原文与中文翻译</h2>
{% for x in analysis.get('translated_items', []) %}
<div class="card translation">
  <div>
    <span class="badge badge-green">中文翻译</span>
    <span class="badge">{{ x.get('source','x.com') }}</span>
    <strong>{{ x.get('chinese_title','') }}</strong>
  </div>
  <div class="muted">编号：{{ x.get('id','') }}</div>
  <div class="original">原文：{{ x.get('original_title','') }}</div>
  <p><strong>中文：</strong>{{ x.get('chinese_summary','') }}</p>
  <p><strong>交易相关性：</strong>{{ x.get('trading_relevance','') }}</p>
</div>
{% else %}
<div class="card muted">今天没有抓到配置账号的 X 发言，或者 LLM 未返回翻译结果。</div>
{% endfor %}
<h2>原始抓取列表</h2>
{% for item in items %}
<div class="card">
  <div><span class="badge">{{ item.author }}</span><span class="badge">{{ item.published_at }}</span></div>
  <div class="original">{{ item.content }}</div>
  {% if item.url %}<div class="muted"><a href="{{ item.url }}">打开 X 原文</a></div>{% endif %}
</div>
{% else %}
<div class="card muted">无原始抓取数据。</div>
{% endfor %}
<div class="footer">Generated at {{ generated_at }}.</div>
</div>
</body>
</html>
""")


def fallback_analysis(items: list[IntelItem], theme_shift: dict, stock_map: dict) -> dict:
    translated = []
    for idx, it in enumerate(items, start=1):
        translated.append({
            "id": idx,
            "source": it.source,
            "original_title": it.content or it.title,
            "chinese_title": it.title,
            "chinese_summary": "LLM 未启用或调用失败，暂时只显示原文。配置 OpenRouter 后会自动生成中文翻译。",
            "trading_relevance": "仅信息整理，不构成投资建议。",
        })
    return {"translated_items": translated}


def render_html(date: str, analysis: dict, items: list[IntelItem]) -> str:
    return _TEMPLATE.render(date=date, analysis=analysis, items=items, generated_at=datetime.now().isoformat(timespec="seconds"))
