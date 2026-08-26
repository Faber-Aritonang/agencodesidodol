"""DodolAgent CLI."""
import argparse

from core.groq_client import DodolLLM
from agents.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="🍬 DodolAgent — sticky coding agent dengan token budget",
    )
    parser.add_argument("task", help="Tugas coding untuk Dodol")
    parser.add_argument("--budget", type=int, default=8000)
    parser.add_argument("--max-steps", type=int, default=20)
    args = parser.parse_args()

    print(f"=== 🍬 DodolAgent mengerjakan: {args.task} ===")
    print(f"💰 Token budget: {args.budget} | Max steps: {args.max_steps}\n")

    llm = DodolLLM()
    agent = Orchestrator(llm, max_steps=args.max_steps, budget=args.budget)
    answer = agent.run(args.task)
    print(f"\n{answer}")


if __name__ == "__main__":
    main()
