"""Sandbox berlapis untuk eksekusi terminal Dodol.

Lapisan:
1. Blacklist pola regex (anti-variasi spasi/urutan flag)
2. Whitelist opsional via DODOL_SANDBOX_WHITELIST
3. Timeout paksa
4. Batas ukuran output
+ Audit log semua eksekusi ke docs/exec_log.jsonl
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path.cwd()
LOG_PATH = PROJECT_ROOT / "docs" / "exec_log.jsonl"

# Pola destruktif — regex, tahan variasi whitespace & urutan flag
BLACKLIST_PATTERNS = [
    r"\brm\b.*\s-[a-z]*r[a-z]*f",          # rm -rf, -fr, -Rf ...
    r"\brm\b\s+-[a-z]*f[a-z]*r",           # rm -fr
    r"\bmkfs",                              # format filesystem
    r"\bdd\b[^|]*\bof=/dev/",              # dd tulis ke device
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",  # fork bomb
    r"\bshutdown\b|\breboot\b|\bhalt\b",
    r">\s*/dev/sd[a-z]",                   # tulis langsung ke disk
    r"\bchmod\b\s+-R\s+777\s+/",
    r"\bcurl\b[^|]*\|\s*(ba)?sh",          # curl | sh
    r"\bwget\b[^|]*&&\s*(ba)?sh",
    r"\bhistory\s+-c",
    r"\bcrontab\b.*-r",
    r"/etc/(passwd|shadow|sudoers)",
    r"\bkill(all)?\b\s+-9\s+1\b",
]

# Whitelist default kalau mode ketat aktif
DEFAULT_WHITELIST = [
    "python", "python3", "pytest", "pip",
    "ls", "cat", "head", "tail", "grep", "find", "wc",
    "echo", "mkdir", "touch", "cp", "mv",
    "git status", "git log", "git diff",
]

MAX_OUTPUT = 20_000


class Sandbox:
    def __init__(self):
        self.timeout = int(os.environ.get("DODOL_SANDBOX_TIMEOUT", "30"))
        wl = os.environ.get("DODOL_SANDBOX_WHITELIST", "").strip()
        self.strict = bool(wl) or os.environ.get("DODOL_SANDBOX_STRICT") == "1"
        if self.strict and not wl:
            self.whitelist = DEFAULT_WHITELIST
        elif wl:
            self.whitelist = [w.strip() for w in wl.split(",")]
        else:
            self.whitelist = []

    def check(self, command: str) -> tuple[bool, str]:
        """(boleh?, alasan). Alasan informatif → Dodol bisa menyesuaikan."""
        for pat in BLACKLIST_PATTERNS:
            if re.search(pat, command):
                return False, (f"DITOLAK sandbox: cocok pola berbahaya '{pat}'. "
                               f"Gunakan cara yang lebih aman.")
        if self.strict:
            allowed = any(command.startswith(w) for w in self.whitelist)
            if not allowed:
                return False, (f"DITOLAK sandbox (mode ketat): perintah harus "
                               f"diawali salah satu dari: {', '.join(self.whitelist)}")
        return True, ""

    def _log(self, command: str, verdict: str, detail: str):
        LOG_PATH.parent.mkdir(exist_ok=True)
        entry = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "command": command[:500],
            "verdict": verdict,
            "detail": detail[:300],
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run(self, command: str, timeout: int | None = None) -> dict:
        """Format return IDENTIK dgn run_terminal lama → drop-in replacement."""
        timeout = timeout or self.timeout
        ok, reason = self.check(command)
        if not ok:
            self._log(command, "BLOCKED", reason)
            return {"status": "BLOCKED", "output": reason,
                    "exit_code": -1}

        start = time.time()
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=PROJECT_ROOT,
            )
            out = (proc.stdout + proc.stderr).strip()[:MAX_OUTPUT]
            status = "OK" if proc.returncode == 0 else f"EXIT {proc.returncode}"
            self._log(command, status, f"{time.time()-start:.1f}s")
            return {"status": status, "output": out,
                    "exit_code": proc.returncode}
        except subprocess.TimeoutExpired:
            msg = f"Perintah melebihi {timeout}s — dihentikan paksa."
            self._log(command, "TIMEOUT", msg)
            return {"status": "TIMEOUT", "output": msg, "exit_code": -1}
