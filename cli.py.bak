"""CLI DodolAgent: python cli.py "buat script backup sederhana\"."""

import sys

from agents.orchestrator import Orchestrator
from core.groq_client import DodolLLM


def main():
    task = " ".join(sys.argv[1:]) or input("🍬 Tugas untuk Dodol: ")
    llm = DodolLLM()
    agent = Orchestrator(llm)
    print(f"\n=== 🍬 DodolAgent mengerjakan: {task} ===\n")
    answer = agent.run(task)
    print(f"\n✅ {answer}")
    print(f"\n💰 Total token: {llm.total_tokens}")


if __name__ == "__main__":
    main()
