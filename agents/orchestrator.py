"""Dodol the Orchestrator — agent utama.
Loop: rencana → aksi (tools) → observasi → ulang sampai selesai.
Anti-halusinasi: done hanya valid jika klaim diverifikasi via run_terminal."""

import json

from core.groq_client import DodolLLM
from core.tools import TOOL_REGISTRY

SYSTEM_PROMPT = """Kamu adalah Dodol, AI coding agent yang lengket pada tugas
sampai selesai. Bekerja langkah demi langkah.

ATURAN PENTING:
- JANGAN PERNAH mengarang output program. Untuk mengetahui hasil sebuah
  program, WAJIB panggil tool run_terminal dan gunakan output ASLI-nya.
- Jangan set done=true sebelum semua bagian tugas terverifikasi.

Balas HANYA dengan JSON (satu objek, tanpa teks lain):
{"thought": "...", "tool": "nama_tool|null", "input": {...}, "done": bool, "answer": "..."}

Tools: read_files(paths), write_file(path, content),
run_terminal(command), code_search(pattern).
Set done=true dan isi answer saat tugas selesai."""


class Orchestrator:
    def __init__(self, llm: DodolLLM, max_steps: int = 15):
        self.llm = llm
        self.max_steps = max_steps
        self.history: list[dict] = []
        self.last_terminal_output: str | None = None

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Ambil objek JSON pertama dari respons (tahan noise/reasoning)."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise json.JSONDecodeError("tidak ada JSON", text, 0)
        return json.loads(text[start:end + 1])

    def _verify_claim(self, answer: str) -> bool:
        """done hanya sah jika jawaban didukung output terminal asli."""
        if self.last_terminal_output is None:
            return False
        # Ambil baris angka/teks kunci dari jawaban, cek ada di output asli
        for line in answer.strip().splitlines():
            token = line.strip()
            if token and token in self.last_terminal_output:
                return True
        return False


    @staticmethod
    def _trim_history(history: list[dict], max_chars: int = 6000) -> list[dict]:
        """Jaga riwayat tetap ramping agar tidak melewati limit TPM."""
        total = sum(len(m["content"]) for m in history)
        while total > max_chars and len(history) > 2:
            removed = history.pop(1)   # jaga pesan tugas pertama
            total -= len(removed["content"])
        return history

    def run(self, task: str) -> str:
        self.history.append({"role": "user", "content": f"Tugas: {task}"})
        for step in range(1, self.max_steps + 1):
            history = self._trim_history(self.history)
            resp = self.llm.chat(SYSTEM_PROMPT, history)
            print(f"\n🍬 Dodol [step {step}, {resp.tokens_used} tok]:")
            print(resp.content or "(thinking...)")
            if not resp.content.strip():
                self.history.append({"role": "user", "content": "Respons kosong. Balas dengan JSON aksi."})
                continue

            try:
                action = self._extract_json(resp.content)
            except (json.JSONDecodeError, ValueError):
                self.history.append({"role": "user", "content": "JSON invalid. Balas HANYA satu objek JSON."})
                continue

            if action.get("done"):
                answer = action.get("answer", "Selesai.")
                if self._verify_claim(answer):
                    return f"{answer}\n\n✅ Terverifikasi via eksekusi nyata."
                self.history.append({
                    "role": "assistant", "content": resp.content,
                })
                self.history.append({
                    "role": "user",
                    "content": (
                        "DITOLAK: Anda mengklaim hasil tanpa verifikasi. "
                        "Jalankan dulu programnya dengan tool run_terminal "
                        "(contoh: python namafile.py), lalu laporkan output ASLI."
                    ),
                })
                continue

            tool_name = action.get("tool")
            if tool_name in TOOL_REGISTRY:
                result = TOOL_REGISTRY[tool_name](**action.get("input", {}))
                result_str = str(result)
                if tool_name == "run_terminal":
                    self.last_terminal_output = result_str
                self.history.append({"role": "assistant", "content": resp.content})
                self.history.append({"role": "user", "content": f"Hasil {tool_name}:\n{result_str[:2000]}"})
            else:
                self.history.append({"role": "user", "content": f"Tool '{tool_name}' tidak dikenal."})
        return "Batas langkah tercapai — tugas belum selesai."
