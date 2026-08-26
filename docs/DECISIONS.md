# Keputusan Teknis agencodesidodol

## 1. Anti-halusinasi via verifikasi deterministik
Masalah: LLM mengklaim output program tanpa mengeksekusinya (terbukti 2x saat testing).
Keputusan: klaim `done` ditolak oleh kode jika tidak ada bukti dari run_terminal.
Pelajaran: prompt bisa dilanggar model; validasi di kode tidak.

## 2. Model dikonfigurasi via env var DODOL_MODEL
Alasan: katalog Groq berubah cepat (llama-3.3-70b sudah retire).
Default: openai/gpt-oss-120b (json-capable, reasoning).

## 3. Hemat token untuk free tier (8K TPM)
- Riwayat dipangkas (_trim_history, jaga pesan tugas pertama)
- Output tool dipotong 2000 char
- max_completion_tokens=2048
- Retry otomatis 60s saat rate limit
Ini fondasi fitur Token Budget Controller.

## 4. JSON diekstrak robust (_extract_json)
Model reasoning membungkus output dengan .
Kami ambil objek {...} pertama/terakhir daripada json.loads mentah.
