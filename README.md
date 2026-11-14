# SiBantu

SiBantu (Sistem Informasi Bantuan) adalah prototipe GDSS untuk menentukan prioritas kecamatan penerima bantuan logistik pascagempa.

## Menjalankan demo penilaian Python

Jalankan dari folder ini dengan Python 3.10+.

```powershell
python -m pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000. Pilih peran, isi 15 pasangan AHP, cek konsistensi, lalu kirim. Ulangi untuk tiga peran. Ranking TOPSIS muncul per peran, dan Borda muncul di **Hasil kelompok** setelah penilaian ketiga dikirim. Dari sana, gunakan **Sahkan sebagai Kepala BPBD**.

Demo lokal ini memakai satu snapshot awal dari `examples/seed_case.json` dan pemilih peran tanpa login. Autentikasi, pendataan, verifikasi, serta pembuatan ronde baru berada di luar tahap ini. SQLite menyimpan snapshot, draf, hasil, dan waktu pengesahan di `instance/assessment.sqlite3`. Untuk mencoba ronde demo kosong dengan tetap menyimpan ronde sebelumnya, gunakan file database baru, misalnya `$env:GDSS_DB_PATH = 'instance/percobaan-2.sqlite3'` sebelum menjalankan aplikasi lagi.

Pengujian: `python -m unittest discover -s tests -v`.

**Status:** demo penilaian untuk prototipe UAS. **Bahasa produk:** Indonesia.

## Dokumen yang menjadi sumber kebenaran
1. [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md): tujuan, konteks, cakupan dan istilah.
2. [`PRD.md`](PRD.md): kebutuhan produk, acceptance criteria, batasan MVP.
3. [`AGENTS.md`](AGENTS.md): instruksi tetap untuk AI coding agent.
4. [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md): use case dan status/transisi.
5. [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md): ERD konseptual, integritas data.
6. [`docs/DECISION_ENGINE.md`](docs/DECISION_ENGINE.md): AHP → TOPSIS → Borda + edge cases.
7. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): modular architecture dan opsi stack.
8. [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md): endpoint konseptual dan kesalahan.
9. [`docs/SECURITY_PRIVACY.md`](docs/SECURITY_PRIVACY.md): auth, RBAC, audit, privasi.
10. [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md): pengujian fungsi dan matematika.
11. [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md): fase build dan definition of done.
12. [`docs/UX_SCREENS.md`](docs/UX_SCREENS.md): rute dan elemen UI.
13. [`DECISIONS.md`](DECISIONS.md): keputusan final vs belum final.
14. [`examples/seed_case.json`](examples/seed_case.json): contoh data **fiktif** yang konsisten.
15. [`examples/ahp_consistent_matrix.json`](examples/ahp_consistent_matrix.json): fixture AHP konsisten untuk automated tests.

## Mulai untuk agent
- Baca `AGENTS.md`, `PROJECT_CONTEXT.md`, `PRD.md`, `DECISIONS.md` terlebih dahulu.
- Periksa repo yang ada. **Jangan mengganti stack/proyek yang sudah ada secara sepihak.** Jika repo kosong, ikuti opsi default dalam `docs/ARCHITECTURE.md` dan catat pilihan di `DECISIONS.md`.
- Implementasikan *vertical slice*: daftar kasus → input data kecamatan → verifikasi → AHP → TOPSIS → Borda → laporan.
- Data gempa contoh bukan kejadian sebenarnya. Labeli jelas **SIMULASI** di UI dan seed.

## Definisi selesai MVP
Semua role dapat login sesuai hak akses, satu kasus dengan 5 kecamatan dapat menjalani workflow lengkap, 3 DM menghasilkan AHP valid lalu TOPSIS dan Borda yang diuji dengan fixture, hasil final dapat diaudit, serta data satu ronde tidak berubah setelah dikunci.
