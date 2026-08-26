"""Multi-provider adapter untuk DodolAgent.

Semua provider mengembalikan LLMResponse yang sama, sehingga
orchestrator tidak perlu tahu backend mana yang dipakai.
Pilih via .env: DODOL_PROVIDER=groq|claude|openai|ollama
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()


@dataclass
class LLMResponse:
    content: str
    tokens_used: int


class BaseProvider(ABC):
    """Interface tunggal semua backend LLM."""

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("DODOL_MODEL", "")
        self.total_tokens = 0

    @abstractmethod
    def _create(self, system: str, messages: list[dict], temperature: float):
        """Panggil API mentah. Return objek dengan .content dan token count."""

    def chat(self, system: str, messages: list[dict],
             temperature: float = 0.2) -> LLMResponse:
        content, tokens = self._create_with_retry(system, messages, temperature)
        self.total_tokens += tokens
        return LLMResponse(content=content, tokens_used=tokens)

    def _create_with_retry(self, system, messages, temperature,
                           max_attempts: int = 3):
        for attempt in range(max_attempts):
            try:
                return self._create(system, messages, temperature)
            except Exception as e:
                err = str(e).lower()
                transient = any(k in err for k in
                                ("rate_limit", "overloaded", "timeout", "connection"))
                if transient and attempt < max_attempts - 1:
                    wait = 60 if "rate_limit" in err else 10
                    print(f"⏳ {type(e).__name__} — tunggu {wait}s "
                          f"(percobaan {attempt + 1}/{max_attempts})...")
                    time.sleep(wait)
                else:
                    raise


def _clean_key(env_name: str) -> str:
    """Sanitasi key: ambil baris pertama saja (anti .env korup)."""
    val = os.environ.get(env_name, "").strip().splitlines()[0].strip()
    if not val:
        raise ValueError(f"{env_name} tidak ada di .env — "
                         f"set DODOL_PROVIDER sesuai key yang tersedia.")
    return val


# ────────────────────────── Groq ──────────────────────────

class GroqProvider(BaseProvider):
    DEFAULT_MODEL = "qwen/qwen3.6-27b"

    def __init__(self, model: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        from groq import Groq
        self.client = Groq(api_key=_clean_key("GROQ_API_KEY"))

    def _create(self, system, messages, temperature):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            temperature=temperature,
            max_completion_tokens=2048,
        )
        return (resp.choices[0].message.content or "",
                resp.usage.total_tokens)


# ───────────────────────── Claude ─────────────────────────

class ClaudeProvider(BaseProvider):
    DEFAULT_MODEL = "claude-haiku-4-5"   # termurah Anthropic

    def __init__(self, model: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        import anthropic
        self.client = anthropic.Anthropic(api_key=_clean_key("ANTHROPIC_API_KEY"))

    def _create(self, system, messages, temperature):
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return (text, resp.usage.input_tokens + resp.usage.output_tokens)


# ───────────────────────── OpenAI ─────────────────────────

class OpenAIProvider(BaseProvider):
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None):
        super().__init__(model or self.DEFAULT_MODEL)
        from openai import OpenAI
        self.client = OpenAI(api_key=_clean_key("OPENAI_API_KEY"))

    def _create(self, system, messages, temperature):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            temperature=temperature,
            max_tokens=2048,
        )
        return (resp.choices[0].message.content or "",
                resp.usage.total_tokens)


# ───────────────────────── Ollama (lokal) ─────────────────

class OllamaProvider(BaseProvider):
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    URL = "http://localhost:11434/api/chat"

    def _create(self, system, messages, temperature):
        import requests
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 2048},
        }
        r = requests.post(self.URL, json=payload, timeout=120)
        r.raise_for_status()
        d = r.json()
        # estimasi token: ~4 char/token (Ollama tidak selalu mengirim count)
        tok = len(d.get("message", {}).get("content", "")) // 4 or 1
        return (d.get("message", {}).get("content", ""), tok)


PROVIDERS: dict[str, type] = {
    "groq": GroqProvider,
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def make_provider(model: str | None = None) -> BaseProvider:
    """Factory: pilih provider dari DODOL_PROVIDER di .env."""
    name = os.environ.get("DODOL_PROVIDER", "groq").lower().strip()
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"DODOL_PROVIDER='{name}' tidak dikenal. "
                         f"Pilihan: {', '.join(PROVIDERS)}")
    print(f"🔌 Provider: {name} | Model: {model or cls.DEFAULT_MODEL}")
    return cls(model)
