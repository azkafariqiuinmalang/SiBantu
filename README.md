# SiBantu

SiBantu (Sistem Informasi Bantuan) adalah prototipe GDSS untuk menentukan prioritas kecamatan penerima bantuan logistik pascagempa.

## Menjalankan SiBantu

Jalankan dari folder ini dengan Python 3.10+.

```powershell
python -m pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000. Pilih peran, isi 15 pasangan AHP, cek konsistensi, lalu kirim. Ulangi untuk tiga peran. Ranking TOPSIS muncul per peran, dan Borda muncul di **Hasil kelompok** setelah penilaian ketiga dikirim. Dari sana, gunakan **Sahkan sebagai Kepala BPBD**.

Demo penilaian memakai snapshot awal dari `examples/seed_case.json`. SQLite menyimpan data dan hasil di `instance/assessment.sqlite3`. Migrasi pendataan berjalan otomatis saat aplikasi dibuka. Untuk memakai database demo kosong sambil menyimpan data sebelumnya, gunakan `$env:GDSS_DB_PATH = 'instance/percobaan-2.sqlite3'` sebelum menjalankan aplikasi lagi.

### Demo pendataan dan verifikasi

1. Buka **Pendataan**. Pilih **Admin**, daftarkan kejadian gempa yang sudah terjadi, tambahkan kecamatan, lalu tugaskan petugas. Centang **Data simulasi** untuk kasus fiktif.
2. Kembali ke **Pendataan** dan pilih petugas yang ditugaskan. Buka kecamatan di **Tugas saya**, isi observasi, lalu pilih **Kirim untuk verifikasi**. Draf dapat disimpan sebelum semua nilai diisi.
3. Pilih lagi **Admin**, buka kejadian dan laporan, lalu setujui atau tolak dengan alasan. Petugas dapat mengoreksi lewat versi baru. Admin dapat meninjau versi sebelumnya.

Pemilih peran tersedia untuk demo lokal. Pembuatan ronde dari laporan terverifikasi dan autentikasi masih dalam rencana pengembangan.

Pengujian: `python -m unittest discover -s tests -v`.

**Status:** demo pendataan, verifikasi, dan penilaian untuk prototipe UAS. **Bahasa produk:** Indonesia.

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
