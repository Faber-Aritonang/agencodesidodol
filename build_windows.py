"""
Dodol Agent — Windows Builder
Membuat .exe self-contained pakai PyInstaller.

Cara pakai (di Windows):
    pip install pyinstaller
    python build_windows.py

Atau pakai PowerShell:
    python -m PyInstaller dodol-agent.spec --clean
"""

import subprocess
import sys
import shutil
from pathlib import Path

APP_NAME = "dodol-agent"
VERSION = "1.0.0"


def main():
    print("🍬 Dodol Agent — Windows Builder")
    print("═══════════════════════════════")

    # Pastikan PyInstaller terinstall
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("📥 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Bersihkan build sebelumnya
    for d in ["build", "dist"]:
        if Path(d).exists():
            print(f"🧹 Cleaning {d}/...")
            shutil.rmtree(d)

    print("🔨 Building .exe...")

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",              # Satu file .exe
        "--console",              # Console app (CLI)
        "--clean",
        # Hidden imports yang mungkin terlewat
        "--hidden-import", "dotenv",
        "--hidden-import", "groq",
        "--hidden-import", "anthropic",
        "--hidden-import", "openai",
        "--hidden-import", "requests",
        # Collect all submodules
        "--collect-all", "core",
        "--collect-all", "agents",
        # Entry point
        "chat.py",
    ]

    subprocess.check_call(cmd)

    exe_path = Path("dist") / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("")
        print("═══════════════════════════════════════════════════════════════")
        print(f"✅ Berhasil: {exe_path}")
        print(f"📊 Ukuran: {size_mb:.1f} MB")
        print("")
        print("🚀 Cara pakai:")
        print(f"   {exe_path}")
        print("")
        print("📋 Setup .env:")
        print("   copy .env.example .env")
        print("   # lalu isi API key di .env")
        print("═══════════════════════════════════════════════════════════════")
    else:
        print("❌ Build gagal — .exe tidak ditemukan di dist/")
        sys.exit(1)


if __name__ == "__main__":
    main()
