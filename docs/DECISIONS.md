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

## 5. Verifikasi state agent harus berbasis nilai, bukan string matching
Bug: mencocokkan '"passed": True' pada repr() dict Python gagal karena
Python memakai kutip tunggal ('passed': True). Agent masuk loop tanpa akhir.
Fix: rekam bukti secara TERSTRUKTUR saat tool dieksekusi (flag tests_passed),
bukan parse ulang representasi string.

## 6. run_terminal wajib shell=True untuk perintah compound
LLM sering menghasilkan "cd x && python y". Tanpa shell=True → FileNotFoundError.
Trade-off: sandbox lokal saja; produksi butuh whitelist perintah.

## 7. Pesan penolakan harus jelas & tidak ambigu
Pesan DITOLAK yang menyebut syarat ganda membuat model menebak-nebak
dan menjalankan tool yang sama berulang kali. Satu alasan spesifik per penolakan.

## 9. Model harus kompatibel dengan protokol agent
- llama-3.3-70b-versatile sudah tidak ada di Groq → 404.
  Selalu cek daftar model via API sebelum hardcode.
- gpt-oss memancarkan tool-call internal meski tanpa schema
  tools → Groq 400. Llama/Qwen aman untuk JSON parsing manual.

## 10. Selalu verifikasi .env dengan cat -A
Append tanpa \n membuat DODOL_MODEL ketempel di belakang
API key dalam satu baris. Debug butuh beberapa iterasi.

## 11. load_dotenv() gagal di mode python3 - << EOF
find_dotenv() butuh frame pemanggil. Pakai load_dotenv(".env")
saat testing via stdin.

## 12. Memory hanya disimpan di jalur sukses
note_task + save() hanya setelah done sah. Tapi note_file/note_tests
tercatat real-time saat tool dieksekusi — sehingga progres parsial
tetap berguna walau run gagal (terbukti: fungsi tertulis saat run
budget-habis tetap terdeteksi run berikutnya).

## 13. Hard-stop budget harus di awal loop
Cek budget SEBELUM panggil LLM. Sebaliknya: LLM diminta done,
ditolak gerbang bukti, loop 17x membakar token sia-sia.

## 14. LLM sering membungkus JSON dalam ```json fence
Parser harus strip fence dulu. Jangan andalkan find("{") saja.

## 15. Hard-stop budget butuh jalur keluar untuk done sah
Jika tests_passed dan done=true datang saat budget habis,
terima langsung. Jangan lewat gerbang tolak → loop bakar token.

## 19. Satu DODOL_MODEL untuk semua provider = tabrakan namespace
"qwen/qwen3.6-27b" (Groq) dikirim ke Ollama → 404 model not found.
Fix: env var model per-provider (GROQ_MODEL, OLLAMA_MODEL, dst).
Pelajaran: config global untuk resource lintas-sistem itu jebakan.

## 18-19. Dua bug provider Ollama
a) requests mengikuti HTTP_PROXY env → localhost ikut ter-proxy.
b) Satu DODOL_MODEL lintas-provider = tabrakan namespace
   ("qwen/qwen3.6-27b" dikirim ke Ollama → 404).
Fix: proxies=None internal + env var model per-provider.

## 20. Model lokal 7b: hemat tapi kurang presisi instruksi
Trade-off nyata lokal vs API. Parser anti-fence & gerbang bukti
Dodol tetap menahannya — arsitektur agent menyelamatkan LLM lemah.

## 21. pytest binary vs python -m pytest: beda sys.path
Agent harus diarahkan selalu pakai `python -m pytest`.
conftest.py dgn sys.path.insert adalah jaring pengaman.

## 23. Failover tidak boleh menumpuk retry internal
super()._create_with_retry() di chain = 3x60s per provider mati
sebelum pindah → hang total. Failover = coba sekali per provider.

## 24. Override __init__ wajib panggil super().__init__()
ResilientProvider menimpa constructor → total_tokens hilang.
Test unit menangkapnya — nilai dari mengetes kode sendiri.

## 25. CI minimal dulu: pytest + dotenv saja
Runner bersih = deteksi dependency tersembunyi. Kalau CI hijau,
berarti project bisa dipasang siapa pun dari clone fresh.

## 26. "Hijau di laptop" ≠ hijau di CI
CI menguji hasil git clone, bukan folder kerja. Bug hantu muncul
kalau fix lupa di-commit ATAU patch menargetkan pola string yang
tidak ada di file (fix OK: False tapi commit tetap jalan!).
Proses aman: lihat file dulu (grep) → patch → test bersih tanpa
__pycache__ → git diff --cached sebagai bukti isi commit → baru push.

## 28. Chat interaktif memanggil cli.py via subprocess
Alih-alih duplikasi loop agent, chat.py mendelegasikan task ke
cli.py (mesin teruji). Keuntungan: satu sumber kebenaran; budget,
sandbox, memory otomatis konsisten. Kontra: proses baru per task
(overhead ~0.5s) — dapat dioptimalkan nanti dengan integrasi langsung.
