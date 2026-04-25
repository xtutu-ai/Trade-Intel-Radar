from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

log = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, fallback_model: str = "", timeout: int = 120, max_tokens: int = 3500):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout) if api_key else None

    def available(self) -> bool:
        return bool(self.client and self.api_key and self.base_url and self.model)

    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not self.available():
            return {"ok": False, "reason": "missing_llm_config", "fallback_report": True}
        for model in [self.model, self.fallback_model]:
            if not model:
                continue
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception as exc:
                log.warning("LLM model %s failed: %s", model, exc)
        return {"ok": False, "reason": "all_llm_models_failed", "fallback_report": True}
