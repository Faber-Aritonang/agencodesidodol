"""Adapter Groq LLM untuk DodolAgent. Privasi-first: hanya mengirim
prompt ke Groq API dengan key milik user, tanpa logging perantara."""

import os
from dataclasses import dataclass

from groq import Groq


@dataclass
class LLMResponse:
    content: str
    tokens_used: int


class DodolLLM:
    """Wrapper Groq dengan pelacakan token sederhana (fondasi budget controller)."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = model
        self.total_tokens = 0

    def chat(self, system: str, messages: list[dict], temperature: float = 0.2) -> LLMResponse:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            temperature=temperature,
        )
        self.total_tokens += resp.usage.total_tokens
        return LLMResponse(
            content=resp.choices[0].message.content,
            tokens_used=resp.usage.total_tokens,
        )
