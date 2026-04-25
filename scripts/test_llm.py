from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.llm.openai_compatible import LLMClient


settings = Settings()
client = LLMClient(
    api_key=settings.env("LLM_API_KEY"),
    base_url=settings.env("LLM_BASE_URL"),
    model=settings.env("LLM_MODEL"),
    fallback_model=settings.env("LLM_FALLBACK_MODEL"),
    timeout=settings.int_env("LLM_TIMEOUT_SECONDS", 120),
    max_tokens=500,
)

if not client.available():
    print("LLM not configured. Fill LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in .env")
    raise SystemExit(1)

resp = client.chat_json([
    {"role": "system", "content": "Return JSON only."},
    {"role": "user", "content": "Return {\"ok\": true, \"message\": \"hello\"}."},
])
print(resp)
