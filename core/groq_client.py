"""Adapter Groq LLM untuk DodolAgent. Privasi-first."""

import os
import time
from dataclasses import dataclass

from groq import Groq


@dataclass
class LLMResponse:
    content: str
    tokens_used: int


class DodolLLM:
    """Wrapper Groq dengan pelacakan token sederhana."""

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("DODOL_MODEL", "openai/gpt-oss-120b")
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.total_tokens = 0

    def chat(self, system: str, messages: list[dict], temperature: float = 0.2) -> LLMResponse:
        resp = self._create_with_retry(system, messages, temperature)
        self.total_tokens += resp.usage.total_tokens
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            tokens_used=resp.usage.total_tokens,
        )

    def _create_with_retry(self, system: str, messages: list[dict], temperature: float):
        """Retry otomatis saat kena rate limit TPM (tunggu 60 detik)."""
        for attempt in range(3):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system}, *messages],
                    temperature=temperature,
                    max_completion_tokens=2048,   # hemat kuota TPM
                )
            except Exception as e:
                if "rate_limit" in str(e) and attempt < 2:
                    print(f"⏳ Rate limit — tunggu 60 detik (percobaan {attempt + 1}/3)...")
                    time.sleep(60)
                else:
                    raise
