"""Fase 9 - CLI interaktif Dodol: sesi multi-task dengan memori hidup."""
import subprocess
import sys
from pathlib import Path

from core.providers import make_provider

HELP = """
/stats   - statistik sesi
/memory  - lihat isi ingatan project
/reset   - hapus ingatan sesi
/help    - bantuan ini
/exit    - keluar"""

BANNER = "Ketik task Anda. Perintah: /stats /memory /reset /help /exit"


class Sesi:
    """Melacak statistik satu sesi interaktif."""

    def __init__(self):
        self.task_count = 0

    def stats(self) -> str:
        return f"📊 Sesi ini: {self.task_count} task dieksekusi"


def jalankan_task(task: str) -> int:
    """Eksekusi task via cli.py (mesin yang sama, sudah teruji)."""
    cmd = [sys.executable, "cli.py", "--budget", "5000", task]
    return subprocess.call(cmd)


def main():
    provider = make_provider()
    sesi = Sesi()
    print(f"🟢 Dodol siap | model: {provider.model} | provider: {type(provider).__name__}")
    print(BANNER)

    while True:
        try:
            user_in = input("\nAnda> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_in:
            continue
        if user_in in ("/exit", "/quit"):
            break
        if user_in == "/help":
            print(HELP)
            continue
        if user_in == "/stats":
            print(sesi.stats())
            continue
        if user_in == "/memory":
            p = Path("docs/memory.json")
            print(p.read_text() if p.exists() else "(memori kosong)")
            continue
        if user_in == "/reset":
            if input("Hapus ingatan sesi? (y/N) ").lower() == "y":
                Path("docs/memory.json").unlink(missing_ok=True)
                print("🧹 Ingatan sesi dihapus.")
            continue

        print(f"\n🤖 Dodol mengerjakan: '{user_in[:60]}...'\n")
        kode = jalankan_task(user_in)
        sesi.task_count += 1
        status = "✅ selesai" if kode == 0 else f"⚠️ exit code {kode}"
        print(f"\n🤖 Task {status}. Lanjutkan dengan task lain atau /exit.")

    print("👋 Sampai jumpa!")


if __name__ == "__main__":
    main()
