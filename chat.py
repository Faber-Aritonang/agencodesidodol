"""Dodol Agent — CLI interaktif sesi multi-task dengan memori hidup.

Semua task berjalan dalam satu proses, berbagi Orchestrator yang sama
sehingga budget, history, dan memory persisten antar task.
"""
import json
import sys
from pathlib import Path

from core.providers import make_provider
from core.budget import TokenBudget
from core.memory import ProjectMemory
from agents.orchestrator import Orchestrator

MEMORY_PATH = Path("docs/memory.json")

HELP = """
/stats   - statistik sesi (task, token, budget)
/memory  - lihat isi ingatan project
/reset   - hapus ingatan sesi & mulai dari nol
/help    - bantuan ini
/exit    - keluar
"""

BANNER = "Ketik task Anda. Perintah: /stats /memory /reset /help /exit"


class Session:
    """Melacak statistik satu sesi interaktif."""

    def __init__(self, budget_total: int):
        self.task_count = 0
        self.total_tokens = 0
        self.budget_total = budget_total

    def stats(self, agent: Orchestrator) -> str:
        lines = [
            f"📊 Sesi ini:",
            f"   Task dieksekusi : {self.task_count}",
            f"   Total token     : {self.total_tokens}",
            f"   Token terpakai : {agent.budget.used}",
        ]
        return "\n".join(lines)


def main():
    provider = make_provider()
    budget_total = 0  # 0 = unlimited
    agent = Orchestrator(provider, max_steps=30, budget=budget_total)
    session = Session(budget_total)

    print(f"🟢 Dodol siap | model: {provider.model} | provider: {type(provider).__name__}")
    print(f"💰 Token: unlimited | Max steps: 30")
    print(BANNER)

    while True:
        try:
            user_in = input("\nAnda> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_in:
            continue

        # --- Slash commands ---
        if user_in in ("/exit", "/quit"):
            break

        if user_in == "/help":
            print(HELP)
            continue

        if user_in == "/stats":
            print(session.stats(agent))
            continue

        if user_in == "/memory":
            if MEMORY_PATH.exists():
                data = MEMORY_PATH.read_text()
                print(data if data.strip() else "(memori kosong)")
            else:
                print("(memori kosong)")
            continue

        if user_in == "/reset":
            confirm = input("Hapus ingatan sesi? (y/N) ").strip().lower()
            if confirm == "y":
                # Reset orchestrator state
                agent.history.clear()
                agent.evidence.clear()
                agent.tests_passed = False
                agent.budget = TokenBudget(budget_total)
                # Reset persistent memory
                agent.memory = ProjectMemory()
                MEMORY_PATH.unlink(missing_ok=True)
                agent.memory = ProjectMemory()
                # Reset session counters
                session.task_count = 0
                session.total_tokens = 0
                session.budget_total = budget_total
                print("🧹 Ingatan sesi dihapus. Mulai dari nol.")
            continue

        # --- Task coding ---
        print(f"\n🤖 Dodol mengerjakan: '{user_in[:60]}...'\n")
        try:
            answer = agent.run(user_in)
            session.task_count += 1
            session.total_tokens += agent.budget.used
            print(f"\n{answer}")
        except KeyboardInterrupt:
            print("\n⏹️  Task dibatalkan (Ctrl+C). Lanjutkan task lain atau /exit.")
        except Exception as e:
            print(f"\n❌ Error: {e}")

        print(f"\n🤖 Task selesai. Lanjutkan dengan task lain atau /exit.")

    print("👋 Sampai jumpa!")


if __name__ == "__main__":
    main()
