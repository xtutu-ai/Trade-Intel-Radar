from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PdfReader

from app.collectors.base import Collector
from app.models import IntelItem

log = logging.getLogger(__name__)


class ReportFolderCollector(Collector):
    name = "reports_folder"

    def __init__(self, folder: Path, max_chars_per_file: int = 8000):
        self.folder = folder
        self.max_chars = max_chars_per_file

    def collect(self) -> list[IntelItem]:
        self.folder.mkdir(parents=True, exist_ok=True)
        items: list[IntelItem] = []
        for path in sorted(self.folder.glob("**/*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            try:
                text = self._read_file(path)
                if not text.strip():
                    continue
                items.append(IntelItem(source="local_report", title=path.name, url=str(path), content=text[: self.max_chars], raw={"path": str(path)}))
            except Exception as exc:
                log.warning("Failed reading report %s: %s", path, exc)
        return items

    def _read_file(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join([(page.extract_text() or "") for page in reader.pages[:20]])
        return ""
