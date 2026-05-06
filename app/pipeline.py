from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.collectors.x_collector import XCollector
from app.config import Settings
from app.intelligence.scoring import dedup_items, score_items
from app.llm.openai_compatible import LLMClient
from app.logging_utils import setup_logging
from app.models import IntelItem
from app.report.html_renderer import fallback_analysis, render_html
from app.report.mail_sender import MailSender
from app.report.prompts import build_daily_messages
from app.storage.sqlite_store import SQLiteStore

log = logging.getLogger(__name__)


def _configured_accounts(watchlist: dict) -> list[str]:
    out: list[str] = []
    for person in (watchlist.get("people") or {}).values():
        out.extend(person.get("accounts", []) or [])
    return list(dict.fromkeys([str(x).strip().lstrip("@") for x in out if str(x).strip()]))


def _same_utc_day(item: IntelItem) -> bool:
    if not item.published_at:
        return False
    try:
        ts = datetime.fromisoformat(item.published_at.replace("Z", "+00:00"))
        return ts.date() == datetime.now(timezone.utc).date()
    except Exception:
        return False


def _keep_configured_author(item: IntelItem, accounts: list[str]) -> bool:
    allowed = {x.lower() for x in accounts}
    return (item.author or "").strip().lower() in allowed


def collect_all(settings: Settings) -> list[IntelItem]:
    cfg = settings.config
    runtime = cfg.get("runtime", {})
    timeout = settings.int_env("HTTP_TIMEOUT_SECONDS", int(runtime.get("http_timeout_seconds", 20)))
    xcfg = cfg.get("x_api", {})
    accounts = _configured_accounts(settings.watchlist)

    collector = XCollector(
        bearer_token=settings.env("X_BEARER_TOKEN"),
        account_names=accounts,
        keyword_queries=[],
        max_keyword_queries=0,
        max_results_per_query=10,
        max_posts_per_account=int(xcfg.get("max_posts_per_account", 80)),
        max_accounts=len(accounts),
        timeout=timeout,
        sleep_seconds=float(runtime.get("request_sleep_seconds", 0.2)),
    )

    try:
        items = collector.collect()
        log.info("collector=%s items=%s", collector.name, len(items))
    except Exception as exc:
        log.exception("X collector failed: %s", exc)
        items = []

    items = [x for x in items if _keep_configured_author(x, accounts) and _same_utc_day(x)]
    log.info("configured_accounts_today_items=%s", len(items))
    return items


def run_daily(send_mail: bool = True, dry_run: bool = False) -> Path:
    settings = Settings()
    setup_logging(settings.path(settings.config["app"].get("log_dir", "logs")))
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    store = SQLiteStore(settings.db_path)

    items = collect_all(settings)
    items = dedup_items(items)
    items = score_items(items, settings.config.get("scoring", {}))
    items = sorted(items, key=lambda x: x.published_at, reverse=True)
    log.info("selected_items=%s", len(items))

    today = datetime.now().strftime("%Y-%m-%d")
    raw_dir = settings.path(settings.config["app"].get("raw_dir", "data/raw"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"x-posts-{today}.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.__dict__, ensure_ascii=False) + "\n")

    store.save_items(items)

    llm = LLMClient(
        api_key=settings.env("LLM_API_KEY"),
        base_url=settings.env("LLM_BASE_URL"),
        model=settings.env("LLM_MODEL"),
        fallback_model=settings.env("LLM_FALLBACK_MODEL"),
        timeout=settings.int_env("LLM_TIMEOUT_SECONDS", 120),
        max_tokens=settings.int_env("LLM_MAX_TOKENS", 3500),
    )
    max_llm_items = settings.int_env("LLM_MAX_INPUT_ITEMS", 80)
    analysis = llm.chat_json(build_daily_messages(items[:max_llm_items], settings.watchlist, {}, {}))
    if analysis.get("fallback_report") or not analysis.get("translated_items"):
        analysis = fallback_analysis(items, {}, {})

    html = render_html(today, analysis, items)
    html_path = settings.output_dir / f"x-posts-{today}.html"
    html_path.write_text(html, encoding="utf-8")
    store.save_report(today, str(html_path), analysis)

    if send_mail and not dry_run:
        mail_cfg = settings.config.get("mail", {})
        sender = MailSender(
            host=settings.env("SMTP_HOST"),
            port=settings.int_env("SMTP_PORT", 587),
            user=settings.env("SMTP_USER"),
            password=settings.env("SMTP_PASSWORD"),
            mail_from=settings.env("MAIL_FROM"),
            mail_to=settings.env("MAIL_TO"),
        )
        subject = f"{mail_cfg.get('subject_prefix', 'X言论日报')}-{today}"
        sender.send_html(subject, html)

    log.info("report_html=%s", html_path)
    return html_path
