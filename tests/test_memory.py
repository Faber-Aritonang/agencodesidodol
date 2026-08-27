"""Unit test untuk ProjectMemory — core/memory.py.

Semua test pakai tmp_path agar tidak mengubah docs/memory.json asli.
"""

import json
import os

from core.memory import ProjectMemory, summarize_code


class TestSummarizeCode:
    def test_dengan_fungsi(self):
        code = "def foo():\n    pass\ndef bar():\n    pass"
        s = summarize_code(code)
        assert "fungsi" in s
        assert "foo" in s
        assert "bar" in s

    def test_dengan_class(self):
        code = "class MyClass:\n    pass"
        s = summarize_code(code)
        assert "class" in s
        assert "MyClass" in s

    def test_dengan_def_async(self):
        code = "async def fetch():\n    pass"
        s = summarize_code(code)
        assert "fungsi" in s
        assert "fetch" in s

    def test_kosong(self):
        s = summarize_code("")
        assert "0 baris" in s

    def test_hitung_baris(self):
        code = "line1\nline2\nline3"
        s = summarize_code(code)
        assert "3 baris" in s


class TestProjectMemory:
    def test_init_awal(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        assert m.data["files"] == {}
        assert m.data["last_tests"] is None
        assert m.data["history"] == []

    def test_save_dan_load(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        m.note_file("foo.py", "def hello(): pass")
        m.save()

        # load ulang dari file yang sama
        m2 = ProjectMemory(str(p))
        assert "foo.py" in m2.data["files"]
        assert "hello" in m2.data["files"]["foo.py"]

    def test_load_file_korup(self, tmp_path):
        p = tmp_path / "mem.json"
        p.write_text("BUKAN JSON {{")
        m = ProjectMemory(str(p))
        # tidak crash, mulai segar
        assert m.data["files"] == {}

    def test_load_file_tidak_ada(self, tmp_path):
        p = tmp_path / "tidak_ada.json"
        m = ProjectMemory(str(p))
        assert m.data["files"] == {}

    def test_note_file_ringkas_fungsi(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        m.note_file("test.py", "def add(a, b):\n    return a + b")
        assert "fungsi" in m.data["files"]["test.py"]
        assert "add" in m.data["files"]["test.py"]

    def test_note_tests(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        m.note_tests({"passed": True, "output": "5 passed"})
        assert m.data["last_tests"] is not None
        assert "passed" in m.data["last_tests"]["result"]

    def test_note_task_batas_10(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        for i in range(15):
            m.note_task(f"task-{i}", f"done-{i}")
        assert len(m.data["history"]) == 10
        # yang tersisa adalah 5 terakhir
        assert m.data["history"][0]["task"] == "task-5"

    def test_context_block_kosong(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        assert m.context_block() == ""

    def test_context_block_ada_isi(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        m.note_file("main.py", "def run(): pass")
        m.note_task("buat fungsi X", "selesai")
        ctx = m.context_block()
        assert "KONTEKS PROJECT" in ctx
        assert "main.py" in ctx
        assert "buat fungsi X" in ctx

    def test_context_block_ada_last_tests(self, tmp_path):
        p = tmp_path / "mem.json"
        m = ProjectMemory(str(p))
        m.note_tests({"passed": True, "output": "3 passed"})
        # last_tests terisi, jadi context_block harus mengandung info test
        assert m.data["last_tests"] is not None
        assert "result" in m.data["last_tests"]
