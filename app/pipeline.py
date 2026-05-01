from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from app.collectors.official_collector import OfficialPageCollector
from app.collectors.report_folder_collector import ReportFolderCollector
from app.collectors.rss_collector import RSSCollector
from app.collectors.x_collector import XCollector
from app.config import Settings
from app.intelligence.scoring import dedup_items, score_items
from app.intelligence.stock_mapper import map_stocks
from app.intelligence.theme_shift import build_theme_snapshot, compare_theme_shift
from app.llm.openai_compatible import LLMClient
from app.logging_utils import setup_logging
from app.models import IntelItem
from app.report.html_renderer import fallback_analysis, render_html
from app.report.mail_sender import MailSender
from app.report.prompts import build_daily_messages
from app.storage.sqlite_store import SQLiteStore

log = logging.getLogger(__name__)


def _flatten_watchlist_accounts(watchlist: dict) -> list[str]:
    out: list[str] = []
    for person in (watchlist.get("people") or {}).values():
        out.extend(person.get("accounts", []) or [])
    out.extend((watchlist.get("institutions") or {}).get("accounts", []) or [])
    return list(dict.fromkeys(out))


def _flatten_watchlist_queries(watchlist: dict) -> list[str]:
    out: list[str] = []
    for person in (watchlist.get("people") or {}).values():
        out.extend(person.get("keywords", []) or [])
    out.extend((watchlist.get("institutions") or {}).get("keywords", []) or [])
    return list(dict.fromkeys(out))


def collect_all(settings: Settings) -> list[IntelItem]:
    cfg = settings.config
    runtime = cfg.get("runtime", {})
    timeout = settings.int_env("HTTP_TIMEOUT_SECONDS", int(runtime.get("http_timeout_seconds", 20)))
    collectors = []
    if cfg.get("x_api", {}).get("enabled", True):
        xcfg = cfg.get("x_api", {})
        collectors.append(
            XCollector(
                bearer_token=settings.env("X_BEARER_TOKEN"),
                account_names=_flatten_watchlist_accounts(settings.watchlist),
                keyword_queries=_flatten_watchlist_queries(settings.watchlist),
                max_keyword_queries=int(xcfg.get("max_keyword_queries_per_run", 10)),
                max_results_per_query=int(xcfg.get("max_results_per_query", 10)),
                max_posts_per_account=int(xcfg.get("max_posts_per_account", 8)),
                max_accounts=int(xcfg.get("max_accounts", 20)),
                timeout=timeout,
                sleep_seconds=float(runtime.get("request_sleep_seconds", 0.2)),
            )
        )
    if cfg.get("rss", {}).get("enabled", True):
        rcfg = cfg.get("rss", {})
        collectors.append(RSSCollector(rcfg.get("feeds", []), int(rcfg.get("max_entries_per_feed", 12))))
    if cfg.get("official_pages", {}).get("enabled", True):
        ocfg = cfg.get("official_pages", {})
        collectors.append(OfficialPageCollector(ocfg.get("urls", []), timeout=timeout))
    if cfg.get("reports_folder", {}).get("enabled", True):
        fcfg = cfg.get("reports_folder", {})
        collectors.append(ReportFolderCollector(settings.path(fcfg.get("path", "data/reports")), int(fcfg.get("max_chars_per_file", 8000))))

    all_items: list[IntelItem] = []
    for collector in collectors:
        try:
            got = collector.collect()
            log.info("collector=%s items=%s", collector.name, len(got))
            all_items.extend(got)
        except Exception as exc:
            log.exception("collector=%s failed: %s", getattr(collector, "name", "unknown"), exc)
    return all_items


def run_daily(send_mail: bool = True, dry_run: bool = False) -> Path:
    settings = Settings()
    setup_logging(settings.path(settings.config["app"].get("log_dir", "logs")))
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    store = SQLiteStore(settings.db_path)

    max_total = settings.int_env("MAX_TOTAL_ITEMS", int(settings.config.get("runtime", {}).get("max_total_items", 250)))
    items = collect_all(settings)
    items = dedup_items(items)
    items = score_items(items, settings.config.get("scoring", {}))
    min_score = float(settings.config.get("scoring", {}).get("min_score_to_include", 10))
    items = [x for x in items if x.score >= min_score][:max_total]
    log.info("selected_items=%s", len(items))

    today = datetime.now().strftime("%Y-%m-%d")
    raw_dir = settings.path(settings.config["app"].get("raw_dir", "data/raw"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"items-{today}.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.__dict__, ensure_ascii=False) + "\n")

    store.save_items(items)
    theme_snapshot = build_theme_snapshot(items, settings.watchlist)
    recent = store.load_recent_theme_snapshots(limit=7)
    theme_shift = compare_theme_shift(theme_snapshot, recent)
    stock_map = map_stocks(items, settings.watchlist)

    llm = LLMClient(
        api_key=settings.env("LLM_API_KEY"),
        base_url=settings.env("LLM_BASE_URL"),
        model=settings.env("LLM_MODEL"),
        fallback_model=settings.env("LLM_FALLBACK_MODEL"),
        timeout=settings.int_env("LLM_TIMEOUT_SECONDS", 120),
        max_tokens=settings.int_env("LLM_MAX_TOKENS", 3500),
    )
    max_llm_items = settings.int_env("LLM_MAX_INPUT_ITEMS", 80)
    analysis = llm.chat_json(build_daily_messages(items[:max_llm_items], settings.watchlist, stock_map, theme_shift))
    if analysis.get("fallback_report"):
        analysis = fallback_analysis(items, theme_shift, stock_map)

    html = render_html(today, analysis, items)
    html_path = settings.output_dir / f"market-intel-{today}.html"
    html_path.write_text(html, encoding="utf-8")
    store.save_report(today, str(html_path), analysis)
    store.save_theme_snapshot(today, theme_snapshot)

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
        subject = f"{mail_cfg.get('subject_prefix', '每日交易情报')}-{today}"
        sender.send_html(subject, html)
    log.info("report_html=%s", html_path)
    return html_path
