"""Adapter LLM untuk DodolAgent — sekarang multi-provider.

DodolLLM tetap diekspor agar orchestrator/cli lama tidak berubah.
Pilih backend via .env: DODOL_PROVIDER=groq|claude|openai|ollama
"""

from core.providers import (LLMResponse, BaseProvider,
                            make_provider)  # noqa: F401


def DodolLLM(model=None):
    """Factory — kembalikan provider sesuai konfigurasi."""
    return make_provider(model)
