"""Multi-provider adapter untuk DodolAgent.

Semua provider mengembalikan LLMResponse yang sama, sehingga
orchestrator tidak perlu tahu backend mana yang dipakai.
Pilih via .env: DODOL_PROVIDER=groq|claude|openai|nararouter|ollama
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv(override=True)


@dataclass
class LLMResponse:
    content: str
    tokens_used: int


class BaseProvider(ABC):
    DEFAULT_MODEL = ""   # default aman; subclass override
    """Interface tunggal semua backend LLM."""

    ENV_KEY = "DODOL_MODEL"   # override per-provider jika mau spesifik

    def __init__(self, model: str | None = None):
        # prioritas: argumen > env khusus provider > default class
        self.model = (model
                      or os.environ.get(self.ENV_KEY, "").strip()
                      or self.DEFAULT_MODEL)
        self.total_tokens = 0

    @abstractmethod
    def _create(self, system: str, messages: list[dict], temperature: float):
        """Panggil API mentah. Return objek dengan .content dan token count."""

    def chat(self, system: str, messages: list[dict],
             temperature: float = 0.2, stream: bool = False) -> LLMResponse:
        if stream:
            return self._chat_stream(system, messages, temperature)
        content, tokens = self._create_with_retry(system, messages, temperature)
        self.total_tokens += tokens
        return LLMResponse(content=content, tokens_used=tokens)

    def _chat_stream(self, system: str, messages: list[dict],
                     temperature: float) -> LLMResponse:
        """Streaming chat — tampilkan token saat tiba."""
        # Default: fallback ke non-streaming
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
    ENV_KEY = "GROQ_MODEL"
    DEFAULT_MODEL = "qwen/qwen3.6-27b"

    def __init__(self, model: str | None = None):
        super().__init__(model)
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
    ENV_KEY = "ANTHROPIC_MODEL"
    DEFAULT_MODEL = "claude-haiku-4-5"   # termurah Anthropic

    def __init__(self, model: str | None = None):
        super().__init__(model)
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
    ENV_KEY = "OPENAI_MODEL"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None):
        super().__init__(model)
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


# ───────────────────────── NaraRouter ─────────────────────────

class NaraRouterProvider(BaseProvider):
    """NaraRouter — OpenAI-compatible gateway (router.bynara.id).

    Base URL  : https://router.bynara.id/v1
    Auth      : Bearer sk-nry-xxxxx
    Endpoint  : POST /v1/chat/completions
    Streaming : supported (stream=True)
    Reasoning : supported (reasoning_effort: low|medium|high)

    Popular free/cheap model aliases:
      deepseek-v4-flash-free  — Mocin tier, Rp157/1M input
      deepseek-v4-flash       — Mocin tier, Rp2.280/1M input
      qwen3.8-flash           — Mocin tier, Rp799/1M input
      gpt-5.6-luna            — Mocin tier, Rp357/1M input
      kimi-k3                 — Mocin tier, Rp43.100/1M input
      qwen3.7-flash           — Mocin tier, Rp372/1M input
      mistral-large           — Mocin tier, Rp887/1M input

    Combo model fallback: combo/<name> (auto-failover between models)
    Rate limits: Free=15 req/min, Freemium=50 req/min, FreeMiumMax=60 req/min
    Daily token bucket: 5M free, per-tier buckets for paid (Dasar 60M, Mocin 70M, etc)
    """
    ENV_KEY = "NARAROUTER_MODEL"
    DEFAULT_MODEL = "deepseek-v4-flash-free"
    BASE_URL = "https://router.bynara.id/v1"

    # Reasoning-capable model aliases (supports reasoning_effort param)
    REASONING_MODELS = {
        "deepseek-v4-pro", "deepseek-v4-pro-0813-bynara",
        "gpt-5.5-pro", "gpt-5.4-lite",
        "kimi-k3", "kimi-k3-bynara",
        "qwen3.8-max", "qwen3.7-max", "qwen-3.7-max",
        "glm-5.2", "glm-5.3",
        "grok-4.6", "muse-spark-1.1", "muse-spark-1.2",
    }

    def __init__(self, model: str | None = None):
        super().__init__(model)
        from openai import OpenAI
        self.client = OpenAI(
            api_key=_clean_key("NARAROUTER_API_KEY"),
            base_url=self.BASE_URL,
        )

    def _build_kwargs(self, system, messages, temperature, stream=False):
        kwargs: dict = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": stream,
        }
        if self.model in self.REASONING_MODELS:
            reasoning = os.environ.get("NARAROUTER_REASONING_EFFORT", "medium").strip()
            if reasoning:
                kwargs["reasoning_effort"] = reasoning
        return kwargs

    def _create(self, system, messages, temperature):
        kwargs = self._build_kwargs(system, messages, temperature, stream=False)
        resp = self.client.chat.completions.create(**kwargs)
        return (resp.choices[0].message.content or "",
                resp.usage.total_tokens)

    def _chat_stream(self, system, messages, temperature):
        """Streaming — tampilkan token saat tiba, kumpulkan full response."""
        import sys
        kwargs = self._build_kwargs(system, messages, temperature, stream=True)
        stream = self.client.chat.completions.create(**kwargs)
        content = ""
        tokens = 0
        print("   ", end="", flush=True)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                content += delta.content
                print(delta.content, end="", flush=True)
            if chunk.usage:
                tokens = chunk.usage.total_tokens
        print()  # newline setelah streaming selesai
        self.total_tokens += tokens
        return LLMResponse(content=content, tokens_used=tokens)


# ───────────────────────── Ollama (lokal) ─────────────────

class OllamaProvider(BaseProvider):
    ENV_KEY = "OLLAMA_MODEL"
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


class ResilientProvider(BaseProvider):
    """Wrapper failover: coba provider utama, gagal → pindah cadangan.

    Hanya menangkap error transient (rate limit/koneksi) — error logis
    (key salah, model tidak ada) tetap dilempar agar terlihat.
    """

    def __init__(self, chain: list[BaseProvider]):
        super().__init__()          # warisi total_tokens & infrastruktur base
        self.chain = chain
        self.active = chain[0]
        self.model = self.active.model

    def _create(self, system, messages, temperature):
        return self.active._create(system, messages, temperature)

    def _chat_stream(self, system, messages, temperature):
        return self.active._chat_stream(system, messages, temperature)

    def _create_with_retry(self, system, messages, temperature,
                           max_attempts: int = 3):
        for idx, prov in enumerate(self.chain):
            self.active = prov
            try:
                # satu percobaan langsung per provider — TANPA retry
                # internal (retry 60s hanya relevan utk provider aktif,
                # bukan saat failover berantai)
                content, tokens = prov._create(system, messages, temperature)
                if idx > 0:
                    print(f"🔀 Fallback ke {type(prov).__name__} — sukses")
                return content, tokens
            except Exception as e:
                err = str(e).lower()
                transient = any(k in err for k in
                                ("rate_limit", "429", "connection",
                                 "timeout", "overloaded"))
                last = idx == len(self.chain) - 1
                if transient and not last:
                    print(f"⚠️ {type(prov).__name__} gagal ({err[:80]}) "
                          f"→ mencoba fallback...")
                    continue
                raise


PROVIDERS: dict[str, type] = {
    "groq": GroqProvider,
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,
    "nararouter": NaraRouterProvider,
    "ollama": OllamaProvider,
}


def make_provider(model: str | None = None) -> BaseProvider:
    """Factory: pilih provider dari DODOL_PROVIDER (+ fallback opsional)."""
    name = os.environ.get("DODOL_PROVIDER", "groq").lower().strip()
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"DODOL_PROVIDER='{name}' tidak dikenal. "
                         f"Pilihan: {', '.join(PROVIDERS)}")
    primary = cls(model)
    print(f"🔌 Provider: {name} | Model: {primary.model}")

    fb_name = os.environ.get("DODOL_FALLBACK", "").lower().strip()
    if fb_name and fb_name != name:
        fb_cls = PROVIDERS.get(fb_name)
        if fb_cls is not None:
            print(f"🛟 Fallback siap: {fb_name}")
            return ResilientProvider([primary, fb_cls(model)])
    return primary
