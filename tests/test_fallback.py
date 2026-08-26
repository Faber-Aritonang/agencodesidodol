"""Test failover tanpa memanggil API asli."""

from core.providers import BaseProvider, LLMResponse, ResilientProvider


class OkProvider(BaseProvider):
    DEFAULT_MODEL = "fake-ok"

    def __init__(self): super().__init__(); self.calls = 0

    def _create(self, system, messages, temperature):
        self.calls += 1
        return ("OK", 1)


class RateLimitedProvider(BaseProvider):
    DEFAULT_MODEL = "fake-dead"

    def __init__(self): super().__init__()

    def _create(self, system, messages, temperature):
        raise Exception("rate_limit_exceeded 429")


class BrokenProvider(BaseProvider):
    """Error non-transient → TIDAK boleh fallback."""
    DEFAULT_MODEL = "fake-broken"

    def __init__(self): super().__init__()

    def _create(self, system, messages, temperature):
        raise Exception("invalid_api_key")


def test_failover_ke_cadangan():
    r = ResilientProvider([RateLimitedProvider(), OkProvider()])
    resp = r.chat("sys", [{"role": "user", "content": "hi"}])
    assert resp.content == "OK"


def test_error_logis_tidak_fallback():
    r = ResilientProvider([BrokenProvider(), OkProvider()])
    try:
        r.chat("sys", [{"role": "user", "content": "hi"}])
        assert False, "harusnya raise"
    except Exception as e:
        assert "invalid_api_key" in str(e)


def test_semua_gagal_tetap_raise():
    r = ResilientProvider([RateLimitedProvider(), RateLimitedProvider()])
    try:
        r.chat("sys", [{"role": "user", "content": "hi"}])
        assert False, "harusnya raise"
    except Exception:
        pass
