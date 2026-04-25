from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings:
    def __init__(self, config_path: str = "configs/config.yaml", watchlist_path: str = "configs/watchlist.yaml"):
        load_dotenv(ROOT_DIR / ".env")
        self.root = ROOT_DIR
        self.config = load_yaml(ROOT_DIR / config_path)
        self.watchlist = load_yaml(ROOT_DIR / watchlist_path)

    def env(self, key: str, default: str = "") -> str:
        return os.getenv(key, default)

    def int_env(self, key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def path(self, value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else self.root / p

    @property
    def db_path(self) -> Path:
        return self.path(self.config["app"].get("db_path", "data/market_intel.sqlite3"))

    @property
    def output_dir(self) -> Path:
        return self.path(self.config["app"].get("output_dir", "data/output"))
