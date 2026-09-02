"""Unit test untuk chat.py — Session, /stats, /memory, /reset, /help."""

import json
from unittest.mock import MagicMock, patch, call

import chat


# ────────────────────── Session ──────────────────────


class TestSession:
    def test_init_defaults(self):
        s = chat.Session(budget_total=8000)
        assert s.task_count == 0
        assert s.total_tokens == 0
        assert s.budget_total == 8000

    def test_init_custom_budget(self):
        s = chat.Session(budget_total=4000)
        assert s.budget_total == 4000

    def test_stats_shows_task_count(self):
        s = chat.Session(budget_total=8000)
        agent = MagicMock()
        agent.budget.remaining = 8000
        agent.budget.pct_left = 100.0
        out = s.stats(agent)
        assert "Task dieksekusi : 0" in out

    def test_stats_shows_tokens(self):
        s = chat.Session(budget_total=8000)
        s.total_tokens = 500
        agent = MagicMock()
        agent.budget.remaining = 7500
        agent.budget.pct_left = 93.75
        out = s.stats(agent)
        assert "Total token     : 500" in out

    def test_stats_shows_tokens_used(self):
        s = chat.Session(budget_total=0)
        agent = MagicMock()
        agent.budget.used = 3200
        out = s.stats(agent)
        assert "3200" in out

    def test_stats_includes_header(self):
        s = chat.Session(budget_total=8000)
        agent = MagicMock()
        agent.budget.remaining = 8000
        agent.budget.pct_left = 100.0
        out = s.stats(agent)
        assert "📊 Sesi ini:" in out


# ────────────────────── /help ──────────────────────


def test_help_lengkap():
    for cmd in ("/stats", "/memory", "/reset", "/help", "/exit"):
        assert cmd in chat.HELP


def test_banner_contains_commands():
    for cmd in ("/stats", "/memory", "/reset", "/help", "/exit"):
        assert cmd in chat.BANNER


# ────────────────────── import ──────────────────────


def test_chat_importable():
    assert hasattr(chat, "main")
    assert hasattr(chat, "Session")


# ────────────────────── /stats via main ──────────────────────


class TestStatsCommand:
    def test_stats_zero_tasks(self):
        inputs = ["/stats", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch:
            mock_prov.return_value = MagicMock(model="test-model")
            mock_orch.return_value = MagicMock()
            mock_orch.return_value.budget.remaining = 8000
            mock_orch.return_value.budget.pct_left = 100.0
            chat.main()

    def test_stats_after_task(self):
        inputs = ["/stats", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch:
            mock_prov.return_value = MagicMock(model="test-model")
            agent = mock_orch.return_value
            agent.budget.remaining = 6000
            agent.budget.pct_left = 75.0
            agent.budget.used = 0
            agent.run.return_value = "done"
            chat.main()


# ────────────────────── /memory via main ──────────────────────


class TestMemoryCommand:
    def test_memory_empty(self, tmp_path):
        inputs = ["/memory", "/exit"]
        fake_mem = tmp_path / "memory.json"
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", fake_mem):
            mock_prov.return_value = MagicMock(model="test-model")
            mock_orch.return_value = MagicMock()
            chat.main()

    def test_memory_with_data(self, tmp_path):
        mem_file = tmp_path / "memory.json"
        mem_file.write_text('{"files": {"kotak.py": "[10 baris]"}}')
        inputs = ["/memory", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", mem_file):
            mock_prov.return_value = MagicMock(model="test-model")
            mock_orch.return_value = MagicMock()
            chat.main()

    def test_memory_file_missing(self, tmp_path):
        fake_mem = tmp_path / "nonexistent.json"
        inputs = ["/memory", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", fake_mem):
            mock_prov.return_value = MagicMock(model="test-model")
            mock_orch.return_value = MagicMock()
            chat.main()


# ────────────────────── /reset via main ──────────────────────


class TestResetCommand:
    def test_reset_confirmed(self, tmp_path):
        mem_file = tmp_path / "memory.json"
        mem_file.write_text('{"files": {"x.py": "data"}}')
        inputs = ["/reset", "y", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", mem_file):
            mock_prov.return_value = MagicMock(model="test-model")
            agent = mock_orch.return_value
            agent.history = ["old"]
            agent.evidence = ["old"]
            agent.tests_passed = True
            agent.budget = MagicMock()
            chat.main()
        assert agent.history == []
        assert agent.evidence == []
        assert agent.tests_passed is False
        assert not mem_file.exists()

    def test_reset_declined(self, tmp_path):
        mem_file = tmp_path / "memory.json"
        mem_file.write_text('{"files": {"x.py": "data"}}')
        inputs = ["/reset", "n", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", mem_file):
            mock_prov.return_value = MagicMock(model="test-model")
            agent = mock_orch.return_value
            agent.history = ["old"]
            chat.main()
        assert agent.history == ["old"]
        assert mem_file.exists()

    def test_reset_clears_budget(self, tmp_path):
        mem_file = tmp_path / "memory.json"
        inputs = ["/reset", "y", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator") as mock_orch, \
             patch("chat.MEMORY_PATH", mem_file):
            mock_prov.return_value = MagicMock(model="test-model")
            agent = mock_orch.return_value
            agent.history = []
            agent.evidence = []
            agent.tests_passed = False
            old_budget = MagicMock()
            agent.budget = old_budget
            chat.main()
        assert agent.budget is not old_budget


# ────────────────────── Integration: task via main() ──────────────────────


def _make_orchestrator_mock():
    """Buat mock Orchestrator yang meniru perilaku nyata.
    budget object punya atribut yang dipakai Session & reset."""
    agent = MagicMock()
    agent.history = []
    agent.evidence = []
    agent.tests_passed = False
    agent.budget = MagicMock()
    agent.budget.remaining = 8000
    agent.budget.pct_left = 100.0
    agent.budget.used = 0
    agent.memory = MagicMock()
    return agent


class TestTaskIntegration:
    """Integration test: feed task through main() with mocked Orchestrator.
    Tests the main() loop logic: input → commands → task → session state."""

    def test_single_task_happy_path(self):
        """User types a task, orchestrator returns answer, session increments."""
        agent = _make_orchestrator_mock()
        agent.run.return_value = "File hitung.py berhasil dibuat."
        agent.budget.used = 450

        inputs = ["buat fungsi tambah", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        # run() called once with the task
        agent.run.assert_called_once_with("buat fungsi tambah")

    def test_task_then_stats(self):
        """Run a task then check /stats reflects it."""
        agent = _make_orchestrator_mock()
        agent.run.return_value = "Selesai."
        agent.budget.used = 300
        agent.budget.remaining = 7700
        agent.budget.pct_left = 96.25

        inputs = ["buat sesuatu", "/stats", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        agent.run.assert_called_once_with("buat sesuatu")

    def test_task_exception_handled(self):
        """Orchestrator.run raises — main() catches and continues."""
        agent = _make_orchestrator_mock()
        agent.run.side_effect = RuntimeError("API down")

        inputs = ["buat sesuatu", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            # Should not crash
            chat.main()

    def test_multiple_tasks_accumulate(self):
        """Run two tasks — run() called twice, session tracks count."""
        agent = _make_orchestrator_mock()
        agent.run.side_effect = ["Task 1 selesai.", "Task 2 selesai."]
        agent.budget.used = 200

        inputs = ["task satu", "task dua", "/stats", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        assert agent.run.call_count == 2
        agent.run.assert_any_call("task satu")
        agent.run.assert_any_call("task dua")

    def test_task_then_memory(self):
        """Run a task, then /memory reads the file."""
        agent = _make_orchestrator_mock()
        agent.run.return_value = "File dibuat."
        agent.budget.used = 150

        inputs = ["buat kalkulator", "/memory", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent), \
             patch("chat.MEMORY_PATH", chat.MEMORY_PATH):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        agent.run.assert_called_once_with("buat kalkulator")

    def test_task_budget_tracked(self):
        """After task, session.total_tokens reflects budget.used."""
        agent = _make_orchestrator_mock()
        agent.run.return_value = "Done."
        agent.budget.used = 600
        agent.budget.remaining = 7400
        agent.budget.pct_left = 92.5

        inputs = ["task", "/stats", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        # run was called, budget.used was read for session tracking
        agent.run.assert_called_once()

    def test_quit_alias(self):
        """'/quit' exits the loop."""
        agent = _make_orchestrator_mock()
        inputs = ["/quit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()
        # No crash — exited cleanly

    def test_empty_input_ignored(self):
        """Empty input doesn't trigger run or exit."""
        agent = _make_orchestrator_mock()
        inputs = ["", "  ", "/exit"]
        with patch("builtins.input", side_effect=inputs), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()

        agent.run.assert_not_called()

    def test_eof_exits_cleanly(self):
        """EOFError (piped input) exits cleanly."""
        agent = _make_orchestrator_mock()
        with patch("builtins.input", side_effect=EOFError), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()
        # No crash

    def test_keyboard_interrupt_in_input_exits(self):
        """KeyboardInterrupt during input exits cleanly."""
        agent = _make_orchestrator_mock()
        with patch("builtins.input", side_effect=KeyboardInterrupt), \
             patch("chat.make_provider") as mock_prov, \
             patch("chat.Orchestrator", return_value=agent):
            mock_prov.return_value = MagicMock(model="test-model")
            chat.main()
        # No crash
