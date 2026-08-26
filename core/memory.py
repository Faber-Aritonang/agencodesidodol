"""Memori project DodolAgent — persisten antar sesi."""

import json
import os
import re
from datetime import datetime

MEMORY_PATH = os.path.join("docs", "memory.json")


def summarize_code(content: str) -> str:
    """Ringkasan otomatis isi file: fungsi & class yang terdeteksi."""
    defs = re.findall(r"^(?:async )?def (\w+)", content, re.M)
    classes = re.findall(r"^class (\w+)", content, re.M)
    parts = []
    if classes:
        parts.append("class " + ", ".join(classes))
    if defs:
        parts.append("fungsi " + ", ".join(defs))
    lines = len(content.strip().splitlines()) if content.strip() else 0
    return f"[{lines} baris] " + "; ".join(parts) if parts else f"[{lines} baris]"


class ProjectMemory:
    """Simpan konteks project sederhana sebagai JSON."""

    def __init__(self, path: str = MEMORY_PATH):
        self.path = path
        self.data = {"files": {}, "last_tests": None, "history": []}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass  # memori korup → mulai segar, jangan crash

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def note_file(self, path: str, content: str) -> None:
        self.data["files"][path] = summarize_code(content)

    def note_tests(self, result: dict) -> None:
        self.data["last_tests"] = {
            "result": str(result.get("summary", result))[:200],
            "at": datetime.now().isoformat(timespec="seconds"),
        }

    def note_task(self, task: str, answer: str) -> None:
        self.data["history"].append({
            "task": task,
            "answer": answer[:200],
            "at": datetime.now().isoformat(timespec="seconds"),
        })
        self.data["history"] = self.data["history"][-10:]

    def context_block(self) -> str:
        """Blok teks untuk disuntikkan ke system prompt."""
        if not self.data["files"] and not self.data["history"]:
            return ""
        lines = ["KONTEKS PROJECT (dari sesi sebelumnya):"]
        if self.data["files"]:
            lines.append("File yang diketahui:")
            for p, s in self.data["files"].items():
                lines.append(f"  - {p}: {s}")
        if self.data["last_tests"]:
            lt = self.data["last_tests"]
            lines.append(f"Hasil test terakhir ({lt['at']}): {lt['result']}")
        if self.data["history"]:
            lines.append("Task yang pernah dikerjakan:")
            for h in self.data["history"][-5:]:
                lines.append(f"  - {h['task'][:100]}")
        return "\n".join(lines)
