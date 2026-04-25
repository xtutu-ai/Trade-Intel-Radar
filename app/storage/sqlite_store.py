from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.models import IntelItem, now_iso


class SQLiteStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.init()

    def init(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS intel_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stable_key TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                content TEXT,
                published_at TEXT,
                author TEXT,
                score REAL DEFAULT 0,
                matched_keywords TEXT DEFAULT '[]',
                raw_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                html_path TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS theme_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                theme_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def save_items(self, items: list[IntelItem]) -> int:
        saved = 0
        before = self.conn.total_changes
        for item in items:
            try:
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO intel_items
                    (stable_key, source, title, url, content, published_at, author, score, matched_keywords, raw_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.stable_key(), item.source, item.title, item.url, item.content,
                        item.published_at, item.author, item.score,
                        json.dumps(item.matched_keywords, ensure_ascii=False),
                        json.dumps(item.raw, ensure_ascii=False), now_iso(),
                    ),
                )
            except sqlite3.Error:
                continue
        self.conn.commit()
        saved = self.conn.total_changes - before
        return max(0, saved)

    def save_report(self, report_date: str, html_path: str, analysis: dict) -> None:
        self.conn.execute(
            "INSERT INTO daily_reports (report_date, html_path, analysis_json, created_at) VALUES (?, ?, ?, ?)",
            (report_date, html_path, json.dumps(analysis, ensure_ascii=False), now_iso()),
        )
        self.conn.commit()

    def save_theme_snapshot(self, snapshot_date: str, theme: dict) -> None:
        self.conn.execute(
            "INSERT INTO theme_snapshots (snapshot_date, theme_json, created_at) VALUES (?, ?, ?)",
            (snapshot_date, json.dumps(theme, ensure_ascii=False), now_iso()),
        )
        self.conn.commit()

    def load_recent_theme_snapshots(self, limit: int = 7) -> list[dict]:
        rows = self.conn.execute(
            "SELECT snapshot_date, theme_json FROM theme_snapshots ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for row in rows:
            try:
                out.append({"date": row["snapshot_date"], "theme": json.loads(row["theme_json"])})
            except json.JSONDecodeError:
                pass
        return out
