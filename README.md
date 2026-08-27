# ![CI](https://github.com/Faber-Aritonang/agencodesidodol/actions/workflows/ci.yml/badge.svg) 🍬 Dodol Agent — AI Coding Agent Gratis

> **Sticky AI coding agent** yang menempel pada tugas sampai selesai.
> Privasi-first: tanpa iklan, tanpa pelacakan, API key milik sendiri.

---

## Apa Itu Dodol Agent?

Dodol Agent adalah **asisten AI yang bisa menulis kode, memperbaiki bug, dan menjalankan test secara otomatis**. Anda cukup kasih tugas, dia akan:

1. 🧠 Menganalisis tugas
2. ✍️ Menulis kode
3. 🧪 Menjalankan test otomatis
4. 🔧 Memperbaiki error sendiri (self-healing)
5. ✅ Menyelesaikan tugas

**Contoh penggunaan:**
```
Anda> buat fungsi menghitung luas persegi beserta test-nya

🤖 Dodol mengerjakan: 'buat fungsi menghitung luas persegi beserta test-nya...'

🍬 Dodol [step 1, 150 tok] 🟢 [████████████████████] 7850/8000 tok sisa (98%)
{"thought": "Saya akan buat fungsi luas_persegi di kotak.py", "tool": "write_file", ...}

✅ Diverifikasi via eksekusi nyata.
```

---

## 🚀 Mulai Dari Sini — Pilih Sistem Operasi Anda

| Sistem Operasi | Langkah Instalasi |
|---|---|
| 🐧 **Linux** (Ubuntu, Fedora, dll) | [Klik di sini](#-linux) |
| 🪟 **Windows** (10/11) | [Klik di sini](#-windows) |
| 🍎 **macOS** | [Klik di sini](#-macos) |

---

# 🐧 Linux

## Langkah 1: Download AppImage

AppImage adalah file yang **sudah siap pakai** — tidak perlu install Python atau apapun.

1. Buka browser, kunjungi:
   👉 **https://github.com/Faber-Aritonang/agencodesidodol/releases**

2. Cari file bernama **`dodol-agent.AppImage`**

3. Klik file tersebut untuk download

4. Pindahkan file ke folder yang Anda inginkan, misal:
   ```
   /home/nama-anda/dodol-agent/
   ```

## Langkah 2: Install FUSE (Hanya Sekali)

Buka **Terminal** (tekan `Ctrl+Alt+T`), lalu ketik:

```bash
sudo apt install -y libfuse2
```

Tekan **Enter**, masukkan password jika diminta.

> 💡 **FUSE** adalah program yang dibutuhkan AppImage untuk berjalan. Tanpa ini, AppImage tidak bisa dibuka.

## Langkah 3: Jalankan Dodol Agent

Masuk ke folder tempat Anda menyimpan AppImage:

```bash
cd ~/dodol-agent/
```

Berikan permission execute (hanya sekali):

```bash
chmod +x dodol-agent.AppImage
```

Jalankan:

```bash
./dodol-agent.AppImage
```

## Langkah 4: Setup API Key (Penting!)

Dodol Agent butuh **API Key** dari provider AI. Pilih salah satu:

### Opsi A: Pakai Ollama (Gratis, Offline) ⭐ Direkomendasikan

1. Install Ollama: https://ollama.com
2. Jalankan: `ollama serve`
3. Buka file `.env` (atau buat baru):
   ```bash
   cp .env.example .env
   nano .env
   ```
4. Isi:
   ```
   DODOL_PROVIDER=ollama
   ```

### Opsi B: Pakai Groq (Gratis, Online)

1. Buka: https://console.groq.com
2. Daftar gratis
3. Buat API Key
4. Buka file `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
5. Isi:
   ```
   DODOL_PROVIDER=groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxx
   ```

### Opsi C: Pakai OpenAI (Berbayar)

1. Buka: https://platform.openai.com
2. Buat API Key
3. Isi di `.env`:
   ```
   DODOL_PROVIDER=openai
   OPENAI_API_KEY=sk-xxxxxxxxxxxxx
   ```

---

# 🪟 Windows

## Langkah 1: Download .exe

1. Buka browser, kunjungi:
   👉 **https://github.com/Faber-Aritonang/agencodesidodol/releases**

2. Cari file bernama **`dodol-agent.exe`**

3. Klik untuk download

4. Buat folder baru, misal: `C:\dodol-agent\`

5. Pindahkan file `dodol-agent.exe` ke folder tersebut

## Langkah 2: Setup API Key (Penting!)

1. Buka **File Explorer**, masuk ke folder `C:\dodol-agent\`

2. Klik kanan di dalam folder → **New** → **Text Document**

3. Buka file tersebut, paste isi berikut:
   ```
   DODOL_PROVIDER=groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxx
   ```

4. **Save As** → ubah nama file menjadi `.env` (hapus `.txt`)

5. Jika Windows bertanya "Anda yakin?", klik **Yes**

> 💡 **Tip:** Jika tidak bisa rename ke `.env`, jalankan di PowerShell:
> ```powershell
> Rename-Item "New Text Document.txt" ".env"
> ```

## Langkah 3: Jalankan Dodol Agent

### Cara 1: Double-click
- Buka folder `C:\dodol-agent\`
- **Double-click** file `dodol-agent.exe`

### Cara 2: Via Command Prompt
1. Tekan `Win+R`, ketik `cmd`, tekan Enter
2. Ketik:
   ```
   cd C:\dodol-agent
   dodol-agent.exe
   ```

---

# 🍎 macOS

## Langkah 1: Download .app

1. Buka browser, kunjungi:
   👉 **https://github.com/Faber-Aritonang/agencodesidodol/releases**

2. Cari file **`Dodol Agent.app`** atau **`dodol-agent`**

3. Download file tersebut

4. Pindahkan ke folder Applications:
   ```
   /Applications/
   ```

## Langkah 2: Buka Permission (Hanya Sekali)

Karena aplikasi dari internet, macOS mungkin memblokirnya. Buka:

**System Preferences → Security & Privacy → General**

Klik **"Open Anyway"** jika ada peringatan.

Atau jalankan di Terminal:
```bash
xattr -cr /Applications/Dodol\ Agent.app
```

## Langkah 3: Setup API Key (Penting!)

1. Buka **Terminal** (cari di Spotlight: `Cmd+Space` → ketik `Terminal`)

2. Jalankan:
   ```bash
   mkdir -p ~/.dodol-agent
   cp .env.example ~/.dodol-agent/.env
   nano ~/.dodol-agent/.env
   ```

3. Isi API Key Anda, lalu tekan `Ctrl+X` → `Y` → `Enter` untuk save

## Langkah 4: Jalankan

### Cara 1: Double-click
- Buka folder **Applications**
- Klik ganda **Dodol Agent**

### Cara 2: Via Terminal
```bash
cd /Applications/Dodol\ Agent.app/Contents/MacOS
./dodol-agent
```

---

# 📋 Cara Menggunakan (Semua OS)

Setelah berhasil menjalankan, Anda akan melihat:

```
🟢 Dodol siap | model: qwen/qwen3.6-27b | provider: GroqProvider
Ketik task Anda. Perintah: /stats /memory /reset /help /exit
```

### Perintah yang Tersedia

| Perintah | Fungsi |
|----------|--------|
| Ketik tugas langsung | Dodol akan mengerjakan tugas coding Anda |
| `/stats` | Lihat statistik sesi ini |
| `/memory` | Lihat ingatan project |
| `/reset` | Hapus ingatan sesi |
| `/help` | Lihat bantuan |
| `/exit` | Keluar |

### Contoh Tugas yang Bisa Dikerjakan

```
Anda> buat fungsi faktorial beserta test-nya
Anda> perbaiki bug di hitung.py
Anda> buat program kalkulator sederhana
Anda> tambahkan fitur validasi input di konversi.py
Anda> refactor kode di matematika.py agar lebih rapi
```

---

# ⚙️ Build Sendiri (Opsional)

Jika Anda ingin build sendiri dari source code:

## Linux (AppImage)

```bash
# 1. Clone repository
git clone https://github.com/Faber-Aritonang/agencodesidodol.git
cd agencodesidodol

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build AppImage
bash build_appimage.sh

# 4. Jalankan
./dodol-agent.AppImage
```

## Windows (.exe)

```powershell
# 1. Clone repository
git clone https://github.com/Faber-Aritonang/agencodesidodol.git
cd agencodesidodol

# 2. Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# 3. Build .exe
python build_windows.py

# 4. Jalankan
dist\dodol-agent.exe
```

## macOS (.app)

```bash
# 1. Clone repository
git clone https://github.com/Faber-Aritonang/agencodesidodol.git
cd agencodesidodol

# 2. Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# 3. Build .app
chmod +x build_macos.sh
./build_macos.sh

# 4. Jalankan
open "dist/Dodol Agent.app"
```

---

# ❓ Troubleshooting (Masalah Umum)

### "FUSE not found" (Linux)
```bash
sudo apt install -y libfuse2
```

### "Command not found" (Linux)
Pastikan pakai `./` di depan nama file:
```bash
./dodol-agent.AppImage
```

### "Blocked by macOS"
Buka Terminal, jalankan:
```bash
xattr -cr /Applications/Dodol\ Agent.app
```

### "Python not found"
Install Python 3.12+: https://www.python.org/downloads/

### "API Key tidak valid"
Pastikan API key sudah benar di file `.env`

### AppImage tidak bisa dibuka (Linux)
Coba tanpa FUSE:
```bash
./dodol-agent.AppImage --appimage-extract-and-run
```

---

# 📊 Fitur

| Fitur | Deskripsi |
|-------|-----------|
| 🧠 **Test-First Self-Healing** | Menulis kode + test, memperbaiki error otomatis |
| 🧠 **Project Memory** | Mengingat file & riwayat task antar sesi |
| 💰 **Token Budget** | Meteran live + hard-stop adaptif |
| 🛡️ **Sandbox** | Keamanan berlapis — blokir command berbahaya |
| 🔌 **Multi-Provider** | Groq / Claude / OpenAI / Ollama lokal |
| 🔄 **Auto-Fallback** | Provider cadangan aktif otomatis |
| 💬 **CLI Interaktif** | Sesi multi-task dengan memori hidup |

---

# 📜 Lisensi

Project ini open-source. Lihat file lisensi di repository.

---

# 🔗 Link Penting

- **Repository:** https://github.com/Faber-Aritonang/agencodesidodol
- **Releases:** https://github.com/Faber-Aritonang/agencodesidodol/releases
- **Issues:** https://github.com/Faber-Aritonang/agencodesidodol/issues
