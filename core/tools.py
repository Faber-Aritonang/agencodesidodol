"""Tools inti DodolAgent: file ops, terminal aman, pencarian.
Sandbox: timeout + blokir command berbahaya."""

import shlex
import subprocess
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


def run_terminal(command: str, timeout: int = MAX_TIMEOUT) -> dict:
    if any(b in command for b in BLOCKED):
        return {"status": "BLOCKED", "output": "Command diblokir sandbox"}
    try:
        proc = subprocess.run(
            shlex.split(command), cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "status": "OK" if proc.returncode == 0 else f"EXIT {proc.returncode}",
            "output": (proc.stdout + proc.stderr)[:10_000],
        }
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "output": f">{timeout}s"}


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
