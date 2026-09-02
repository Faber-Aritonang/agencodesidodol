"""Dodol the Orchestrator — agent utama.
Fase 2: Test-First Self-Healing Loop.
done hanya sah jika run_tests lulus + klaim didukung bukti eksekusi."""

import json

from core.groq_client import DodolLLM
from core.tools import TOOL_REGISTRY
from core.budget import TokenBudget
from core.memory import ProjectMemory

SYSTEM_PROMPT = """Kamu adalah Dodol, AI coding agent yang CEPAT dan LENGKAP.

═══════════════════════════════════════════════════════════════
ALUR KERJA — CEPAT & EFISIEN (wajib):
═══════════════════════════════════════════════════════════════

Langkah 1: PLAN (satu langkah untuk semua)
- Pahami task, buat rencana, tulis todo list, JANGAN pakai tool
- Langsung siapkan work steps berikutnya

Langkah 2+: WORK (eksekusi per langkah)
- Jalankan tool per langkah
- Jika error → self-healing → coba lagi

Langkah terakhir: DONE
- Ringkaskan hasil, laporkan bukti eksekusi

═══════════════════════════════════════════════════════════════
ATURAN PENTING:
═══════════════════════════════════════════════════════════════
- JANGAN PERNAH mengarang output. Gunakan output ASLI dari tool.
- TEST-FIRST: setelah menulis kode, WAJIB run_tests.
- Self-healing: baca error, perbaiki, coba lagi sampai lulus.
- TUNGGU semua todo selesai sebelum set done=true.
- JANGAN buat langkah plan/think terpisah — langsung ke work.

═══════════════════════════════════════════════════════════════
FORMAT RESPONS (JSON satu objek, HANYA JSON):
═══════════════════════════════════════════════════════════════
{
  "phase": "plan|work|done",
  "thought": "Penjelasan singkat...",
  "todos": ["[ ] Langkah 1", "[x] Langkah selesai"],
  "tool": "nama_tool|null",
  "input": {},
  "done": false,
  "answer": ""
}

field PHASE:
- "plan": Pahami + rencana + todo list SEKALIGUS → JANGAN pakai tool
- "work": Eksekusi tool → isi tool + input
- "done": Tugas selesai → isi answer dengan ringkasan

field TOOL:
- Pada phase "work", isi tool name dan input
- Pada phase lain, set tool=null

field DONE:
- Set true HANYA setelah semua todo selesai

Tools tersedia:
- read_files(paths: list[str]) → dict[str, str]
- write_file(path: str, content: str) → str
- run_terminal(command: str) → dict
- code_search(pattern: str) → list[str]
- run_tests(test_path: str) → dict
"""


class Orchestrator:
    def __init__(self, llm: DodolLLM, max_steps: int = 30, budget: int = 0):
        self.llm = llm
        self.max_steps = max_steps
        self.history: list[dict] = []
        self.evidence: list[str] = []   # kumpulan bukti dari tool nyata
        self.tests_passed = False
        self.budget = TokenBudget(budget)
        self.memory = ProjectMemory()

    @staticmethod
    def _extract_json(text: str) -> dict:
        # buang markdown fence bila ada
        if "```" in text:
            for part in text.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    text = part
                    break
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

    PHASE_ICONS = {
        "plan": "\U0001f4cb Plan",
        "work": "\U0001f6e0\ufe0f  Work",
        "done": "\u2705 Done",
    }

    def run(self, task: str) -> str:
        ctx = self.memory.context_block()
        full_task = f"{task}\n\n{ctx}" if ctx else task
        self.history.append({"role": "user", "content": f"Tugas: {full_task}"})
        current_phase = ""

        for step in range(1, self.max_steps + 1):
            history = self._trim_history(self.history)
            # Info budget hidup: tempel sebagai konteks terakhir
            history = history + [{"role": "user", "content": self.budget.guidance()}]
            resp = self.llm.chat(SYSTEM_PROMPT, history, stream=True)
            self.budget.spend(resp.tokens_used)
            if not resp.content.strip():
                self._reject("", "Respons kosong. Balas HANYA satu objek JSON aksi.")
                continue

            try:
                action = self._extract_json(resp.content)
            except (json.JSONDecodeError, ValueError):
                self._reject(resp.content, "JSON invalid. Balas HANYA satu objek JSON.")
                continue

            phase = action.get("phase", "work")
            thought = action.get("thought", "")
            todos = action.get("todos", [])

            # --- Cetak progress fase ---
            if phase != current_phase:
                icon = self.PHASE_ICONS.get(phase, phase)
                print(f"\n{'─'*50}")
                print(f"{icon} [step {step}, {resp.tokens_used} tok] {self.budget.meter()}")
                print(f"{'─'*50}")
                current_phase = phase
            else:
                print(f"\n🍬 [step {step}, {resp.tokens_used} tok] {self.budget.meter()}")

            # --- Cetak thought ---
            if thought:
                print(f"\n{thought}")

            # --- Cetak todos ---
            if todos:
                print("\n📋 Todo List:")
                for t in todos:
                    print(f"   {t}")

            # --- Phase: plan (tanpa tool) ---
            if phase == "plan":
                self.history.append({"role": "assistant", "content": resp.content})
                self.history.append({"role": "user", "content": "Plan diterima. Lanjut ke work phase."})
                continue
            if not resp.content.strip():
                self._reject("", "Respons kosong. Balas HANYA satu objek JSON aksi.")
                continue

            # --- Penanganan done ---
            if action.get("done"):
                answer = action.get("answer", "Selesai.")
                return f"{answer}\n\n\u2705 Diverifikasi via eksekusi nyata."
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
                return f"{answer}\n\n\u2705 Diverifikasi via eksekusi nyata."

            # --- Phase: work — Eksekusi tool ---
            tool_name = action.get("tool")
            if tool_name and tool_name in TOOL_REGISTRY:
                result = TOOL_REGISTRY[tool_name](**action.get("input", {}))
                result_str = str(result)
                print(f"\n📦 Hasil {tool_name}:\n{result_str[:500]}")

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
