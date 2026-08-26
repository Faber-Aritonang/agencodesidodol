"""Tools inti DodolAgent: file ops, terminal aman, pencarian.
Sandbox: timeout + blokir command berbahaya."""

from core.sandbox import Sandbox

_sandbox = Sandbox()

from pathlib import Path

PROJECT_ROOT = Path.cwd()
BLOCKED = {"rm -rf /", "mkfs", "dd if=", ":(){:|:&};:"}
MAX_TIMEOUT = 60


def read_files(paths: list[str]) -> dict[str, str]:
    result = {}
    for p in paths:
        path = PROJECT_ROOT / p
        if path.is_file():
            result[p] = path.read_text(errors="replace")[:100_000]
    return result


def write_file(path: str, content: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        return "ERROR: di luar project root"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"OK: {path} ditulis ({len(content)} chars)"


def run_terminal(command: str, timeout: int = None) -> dict:
    """Jalankan perintah lewat sandbox (blacklist + whitelist + timeout + log)."""
    return _sandbox.run(command, timeout=timeout)


def code_search(pattern: str) -> list[str]:
    """Cari teks di project pakai grep -rn."""
    out = run_terminal(f"grep -rn --include='*.py' {shlex.quote(pattern)} .")
    return out["output"].splitlines()[:50]


TOOL_REGISTRY = {
    "read_files": read_files,
    "write_file": write_file,
    "run_terminal": run_terminal,
    "code_search": code_search,
}


def run_tests(test_path: str = "tests/") -> dict:
    """Jalankan pytest dan kembalikan ringkasan lulus/gagal."""
    out = run_terminal(f"python -m pytest {test_path} -x --tb=short -q", timeout=120)
    return {
        "status": out["status"],
        "output": out["output"][:3000],
        "passed": out["status"] == "OK",
    }


TOOL_REGISTRY["run_tests"] = run_tests
