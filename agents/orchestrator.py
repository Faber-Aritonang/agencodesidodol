"""Dodol the Orchestrator — agent utama.
Loop: rencana → aksi (tools) → observasi → ulang sampai selesai."""

import json

from core.groq_client import DodolLLM
from core.tools import TOOL_REGISTRY

SYSTEM_PROMPT = """Kamu adalah Dodol, AI coding agent yang lengket pada tugas
sampai selesai. Bekerja langkah demi langkah.

Balas HANYA dengan JSON:
{"thought": "...", "tool": "nama_tool|null", "input": {...}, "done": bool, "answer": "..."}

Tools: read_files(paths), write_file(path, content),
run_terminal(command), code_search(pattern).
Set done=true dan isi answer saat tugas selesai."""


class Orchestrator:
    def __init__(self, llm: DodolLLM, max_steps: int = 15):
        self.llm = llm
        self.max_steps = max_steps
        self.history: list[dict] = []

    def run(self, task: str) -> str:
        self.history.append({"role": "user", "content": f"Tugas: {task}"})
        for step in range(1, self.max_steps + 1):
            resp = self.llm.chat(SYSTEM_PROMPT, self.history)
            print(f"\n🍬 Dodol [step {step}, {resp.tokens_used} tok]: {resp.content[:200]}")
            try:
                action = json.loads(resp.content)
            except json.JSONDecodeError:
                self.history.append({"role": "user", "content": "JSON invalid. Ulangi format."})
                continue

            if action.get("done"):
                return action.get("answer", "Selesai.")

            tool_name = action.get("tool")
            if tool_name in TOOL_REGISTRY:
                result = TOOL_REGISTRY[tool_name](**action.get("input", {}))
                self.history.append({"role": "assistant", "content": resp.content})
                self.history.append({"role": "user", "content": f"Hasil {tool_name}:\n{result}"})
            else:
                self.history.append({"role": "user", "content": f"Tool '{tool_name}' tidak dikenal."})
        return "Batas langkah tercapai — tugas belum selesai."
