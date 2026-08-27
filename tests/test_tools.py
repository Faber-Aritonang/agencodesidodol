"""Unit test untuk core/tools.py — read_files, write_file, code_search, run_tests."""

from pathlib import Path

import core.tools as tools_mod


class TestReadFiles:
    def test_baca_file_ada(self):
        result = tools_mod.read_files(["hitung.py"])
        assert "hitung.py" in result
        assert "is_prime" in result["hitung.py"]

    def test_baca_file_tidak_ada(self):
        result = tools_mod.read_files(["file_tidak_ada_xyz.py"])
        assert result == {}

    def test_baca_beberapa_file(self):
        result = tools_mod.read_files(["hitung.py", "konversi.py"])
        assert "hitung.py" in result
        assert "konversi.py" in result

    def test_baca_list_kosong(self):
        result = tools_mod.read_files([])
        assert result == {}

    def test_baca_direktori_bukan_file(self):
        result = tools_mod.read_files(["tests"])
        assert result == {}  # direktori bukan file


class TestWriteFile:
    def test_tulis_file_baru(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools_mod, "PROJECT_ROOT", tmp_path)
        target = "subdir/test_write.txt"
        msg = tools_mod.write_file(target, "hello world")
        assert "OK" in msg
        assert (tmp_path / target).read_text() == "hello world"

    def test_tulis_overwrite(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools_mod, "PROJECT_ROOT", tmp_path)
        tools_mod.write_file("overwrite.txt", "v1")
        tools_mod.write_file("overwrite.txt", "v2")
        assert (tmp_path / "overwrite.txt").read_text() == "v2"

    def test_tulis_di_luar_project_root(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools_mod, "PROJECT_ROOT", tmp_path)
        msg = tools_mod.write_file("../../etc/passwd", "evil")
        assert "ERROR" in msg


class TestCodeSearch:
    def test_cari_def_is_prime(self):
        results = tools_mod.code_search("def is_prime")
        assert len(results) > 0
        assert any("hitung.py" in r for r in results)

    def test_cari_tidak_ada(self):
        results = tools_mod.code_search("zzz_nonexistent_function_xyz")
        # grep bisa menemukan string ini di test file itu sendiri,
        # jadi kita cek tidak ada hasil di modul inti
        assert not any("core/" in r or "agents/" in r for r in results)

    def test_batas_50_baris(self):
        results = tools_mod.code_search("def")
        # mungkin banyak hasil, tapi max 50
        assert len(results) <= 50


class TestRunTests:
    def test_run_tests_semua_lulus(self):
        result = tools_mod.run_tests("tests/test_budget.py")
        assert result["passed"] is True
        assert result["status"] == "OK"

    def test_run_tests_output_ada(self):
        result = tools_mod.run_tests("tests/test_budget.py")
        assert "passed" in result["output"] or "PASSED" in result["output"]

    def test_run_tests_path_tidak_ada(self):
        result = tools_mod.run_tests("tests/test_tidak_ada_xyz.py")
        assert result["passed"] is False
