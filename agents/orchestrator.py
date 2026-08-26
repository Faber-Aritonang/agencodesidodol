"""Dodol the Orchestrator — agent utama.
Fase 2: Test-First Self-Healing Loop.
done hanya sah jika run_tests lulus + klaim didukung bukti eksekusi."""

import json

from core.groq_client import DodolLLM
from core.tools import TOOL_REGISTRY
from core.budget import TokenBudget
from core.memory import ProjectMemory

SYSTEM_PROMPT = """Kamu adalah Dodol, AI coding agent yang lengket pada tugas
sampai selesai. Bekerja langkah demi langkah.

ATURAN PENTING:
- JANGAN PERNAH mengarang output program. Untuk mengetahui hasil sebuah
  program, WAJIB panggil tool run_terminal dan gunakan output ASLI-nya.
- TEST-FIRST: setelah menulis/mengubah kode, WAJIB panggil run_tests.
- Kode belum selesai sampai semua test LULUS. Jangan set done=true
  jika run_tests belum pernah lulus pada kode final.
- Self-healing: baca error di output run_tests, perbaiki kode,
  jalankan run_tests lagi sampai lulus.

Balas HANYA dengan JSON (satu objek, tanpa teks lain):
{"thought": "...", "tool": "nama_tool|null", "input": {...}, "done": bool, "answer": "..."}

Tools: read_files(paths), write_file(path, content),
run_terminal(command), code_search(pattern), run_tests(test_path).
Set done=true dan isi answer saat tugas selesai."""


class Orchestrator:
    def __init__(self, llm: DodolLLM, max_steps: int = 20, budget: int = 8000):
        self.llm = llm
        self.max_steps = max_steps
        self.history: list[dict] = []
        self.evidence: list[str] = []   # kumpulan bukti dari tool nyata
        self.tests_passed = False
        self.budget = TokenBudget(budget)
        self.memory = ProjectMemory()

    @staticmethod
    def _extract_json(text: str) -> dict:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise json.JSONDecodeError("tidak ada JSON", text, 0)
        return json.loads(text[start:end + 1])

    def _has_evidence(self, claim: str) -> bool:
        """done sah jika test lulus DAN ada bukti eksekusi nyata."""
        return self.tests_passed and bool(self.evidence)

    @staticmethod
    def _trim_history(history: list[dict], max_chars: int = 6000) -> list[dict]:
        total = sum(len(m["content"]) for m in history)
        while total > max_chars and len(history) > 2:
            removed = history.pop(1)
            total -= len(removed["content"])
        return history

    def _reject(self, resp_content: str, reason: str):
        self.history.append({"role": "assistant", "content": resp_content})
        self.history.append({"role": "user", "content": reason})

    def run(self, task: str) -> str:
        ctx = self.memory.context_block()
        full_task = f"{task}\n\n{ctx}" if ctx else task
        self.history.append({"role": "user", "content": f"Tugas: {full_task}"})
        for step in range(1, self.max_steps + 1):
            history = self._trim_history(self.history)
            # Info budget hidup: tempel sebagai konteks terakhir
            history = history + [{"role": "user", "content": self.budget.guidance()}]
            resp = self.llm.chat(SYSTEM_PROMPT, history)
            self.budget.spend(resp.tokens_used)
            print(f"\n🍬 Dodol [step {step}, {resp.tokens_used} tok] {self.budget.meter()}")
            print(resp.content or "(thinking...)")
            if not resp.content.strip():
                self._reject("", "Respons kosong. Balas HANYA satu objek JSON aksi.")
                continue

            try:
                action = self._extract_json(resp.content)
            except (json.JSONDecodeError, ValueError):
                self._reject(resp.content, "JSON invalid. Balas HANYA satu objek JSON.")
                continue

            # --- Penanganan done ---
            if self.budget.exhausted and not action.get("done"):
                return ("⏹️ Token budget habis. Progres terakhir:\n"
                        f"{resp.content[:500]}")

            if action.get("done"):
                answer = action.get("answer", "Selesai.")
                if not self._has_evidence(answer):
                    status = []
                    if not any("passed" in ev for ev in self.evidence):
                        status.append("run_tests belum LULUS pada kode final")
                    else:
                        status.append("klaim tidak cocok dengan bukti eksekusi")
                    self._reject(resp.content,
                        f"DITOLAK: {'; '.join(status)}. "
                        "Jalankan run_tests / run_terminal dulu, "
                        "lalu laporkan hasil ASLI di answer.")
                    continue
                self.memory.note_task(task, answer)
                self.memory.save()
                return f"{answer}\n\n✅ Diverifikasi via eksekusi nyata."

            # --- Eksekusi tool ---
            tool_name = action.get("tool")
            if tool_name in TOOL_REGISTRY:
                result = TOOL_REGISTRY[tool_name](**action.get("input", {}))
                result_str = str(result)

                # Rekam bukti secara TERSTRUKTUR, bukan string-matching rapuh
                if tool_name == "run_terminal":
                    out = result.get("output", "") if isinstance(result, dict) else str(result)
                    self.evidence.append(out[:2000])
                elif tool_name == "run_tests":
                    if isinstance(result, dict) and result.get("passed"):
                        self.tests_passed = True
                        self.evidence.append(
                            f"TESTS PASSED ({result.get('summary', 'semua lulus')})"
                        )
                    elif isinstance(result, dict):
                        self.evidence.append(result.get("output", "")[:2000])
                    else:
                        self.evidence.append(str(result)[:2000])

                # Catat ke memori jangka panjang
                if tool_name == "write_file":
                    p = action.get("input", {}).get("path", "?")
                    c = action.get("input", {}).get("content", "")
                    self.memory.note_file(p, c)
                elif tool_name == "run_tests" and isinstance(result, dict):
                    self.memory.note_tests(result)

                self.history.append({"role": "assistant", "content": resp.content})
                self.history.append({"role": "user", "content": f"Hasil {tool_name}:\n{result_str[:2000]}"})
            else:
                self._reject(resp.content, f"Tool '{tool_name}' tidak dikenal. Gunakan tools yang tersedia.")
        return "Batas langkah tercapai — tugas belum selesai."
