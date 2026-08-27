# ![CI](https://github.com/Faber-Aritonang/agencodesidodol/actions/workflows/ci.yml/badge.svg) 🍬 Agent Code Si Dodol

> Sticky AI coding agent. Menempel pada tugas sampai selesai.
> Privasi-first: tanpa iklan, tanpa pelacakan, API key milik sendiri.

## ✨ Fitur

- 🧠 **Test-First Self-Healing Loop** — orchestrator JSON-aksi dengan eksekusi terverifikasi
- 🧠 **Project Memory** — mengingat file, hasil test & riwayat task antar sesi (`docs/memory.json`)
- 💰 **Token Budget Controller** — meteran live + hard-stop adaptif
- 🛡️ **Sandbox Berlapis** — blacklist regex, whitelist opsional, timeout, audit log (`docs/exec_log.jsonl`)
- 🔌 **Multi-Provider** — Groq / Claude / OpenAI / **Ollama lokal** (offline & gratis!), ganti via `DODOL_PROVIDER`
- 🔄 **Auto-Fallback** — provider cadangan aktif otomatis saat provider utama gagal
- 💬 **CLI Interaktif** — sesi multi-task dengan memori hidup (`chat.py`)

## 🚀 Cara Pakai

```bash
pip install -r requirements.txt
cp .env.example .env   # isi API key / set DODOL_PROVIDER=ollama

# Single task
python cli.py --budget 8000 "buat fungsi X beserta test-nya"

# Sesi interaktif
python chat.py
```

## 📜 Keputusan Teknis

25+ entri pelajaran debugging nyata (proxy env, namespace config,
parser markdown-fence, rate-limit strategy) — lihat [docs/DECISIONS.md](docs/DECISIONS.md).

## 📊 Status

| Fase | Fitur | Status |
|------|-------|--------|
| 1 | Fondasi orkestrasi | ✅ Selesai |
| 2 | Test-first self-healing loop | ✅ Selesai |
| 3 | Budget controller adaptif | ✅ Selesai |
| 4 | Project memory persisten | ✅ Selesai |
| 5 | Multi-provider adapter | ✅ Selesai |
| 6 | Sandbox keamanan berlapis + Ollama lokal | ✅ Selesai |
| 7 | Auto-fallback provider | ✅ Selesai |
| 8 | Unit test coverage & code hardening | 🔜 roadmap |
| 9 | CLI interaktif (chat.py) | ✅ Selesai |
