"""Unit test untuk Orchestrator — agents/orchestrator.py.

Hanya test method statis (tanpa panggil LLM asli).
"""

import json

from agents.orchestrator import Orchestrator


class TestExtractJson:
    def test_json_sederhana(self):
        text = '{"thought": "oke", "tool": "ls", "input": {}, "done": false}'
        result = Orchestrator._extract_json(text)
        assert result["thought"] == "oke"
        assert result["tool"] == "ls"
        assert result["done"] is False

    def test_json_dengan_teks_sebelum(self):
        text = 'Ini analisis saya:\n{"thought": "ok", "tool": null, "input": {}, "done": true, "answer": "selesai"}'
        result = Orchestrator._extract_json(text)
        assert result["done"] is True

    def test_json_dengan_teks_sesudah(self):
        text = '{"thought": "ok", "tool": null, "input": {}, "done": true}\nSelesai ya.'
        result = Orchestrator._extract_json(text)
        assert result["done"] is True

    def test_json_dengan_markdown_fence(self):
        text = '''```json
{"thought": "oke", "tool": "run_terminal", "input": {"command": "ls"}, "done": false}
```'''
        result = Orchestrator._extract_json(text)
        assert result["tool"] == "run_terminal"

    def test_json_dengan_fence_tanpa_label(self):
        text = '''```
{"thought": "oke", "tool": null, "input": {}, "done": true, "answer": "ok"}
```'''
        result = Orchestrator._extract_json(text)
        assert result["done"] is True

    def test_tidak_ada_json_mustahil(self):
        import pytest
        with pytest.raises(json.JSONDecodeError):
            Orchestrator._extract_json("tidak ada json di sini")

    def test_json_empty_object(self):
        # "{" saja tanpa "}" harus gagal
        import pytest
        with pytest.raises(json.JSONDecodeError):
            Orchestrator._extract_json("hanya kurung buka {")


class TestTrimHistory:
    def _make_msg(self, content: str) -> dict:
        return {"role": "user", "content": content}

    def test_tidak_perlu_trim(self):
        history = [self._make_msg("a"), self._make_msg("b")]
        result = Orchestrator._trim_history(history, max_chars=1000)
        assert len(result) == 2

    def test_trim_hapus_msg_kedua(self):
        history = [
            self._make_msg("task pertama"),       # index 0 - tidak dihapus
            self._make_msg("a" * 5000),            # index 1 - dihapus
            self._make_msg("respons"),             # index 2
        ]
        result = Orchestrator._trim_history(history, max_chars=100)
        # msg pertama (index 0) harus tetap ada
        assert result[0]["content"] == "task pertama"
        # msg "a" * 5000 harus sudah dihapus
        assert all(m["content"] != "a" * 5000 for m in result)

    def test_trim_pertahanan_msg_pertama(self):
        history = [
            self._make_msg("Tugas: buat fungsi X"),
            self._make_msg("b" * 3000),
            self._make_msg("c" * 3000),
        ]
        result = Orchestrator._trim_history(history, max_chars=50)
        assert result[0]["content"] == "Tugas: buat fungsi X"

    def test_trim_tidak_hapus_sampai_sisa_2(self):
        history = [
            self._make_msg("a" * 500),
            self._make_msg("b" * 500),
            self._make_msg("c" * 500),
        ]
        result = Orchestrator._trim_history(history, max_chars=10)
        assert len(result) >= 2  # minimal sisa 2 pesan
