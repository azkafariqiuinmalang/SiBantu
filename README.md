# SiBantu

SiBantu (Sistem Informasi Bantuan) adalah prototipe GDSS untuk menentukan prioritas kecamatan penerima bantuan logistik pascagempa.

## Menjalankan SiBantu

Jalankan dari folder ini dengan Python 3.10+.

```powershell
python -m pip install -r requirements.txt
$env:GDSS_PORT = '5050'
python app.py
```

Buka http://127.0.0.1:5050/login atau jalankan `JALANKAN_SIBANTU.bat`. Tiga akun awal di proyek Supabase saat ini adalah `bpbd@sibantu.local`, `lapangan@sibantu.local`, dan `sosial@sibantu.local`. Password acak tersimpan secara lokal di `instance/AKUN_AWAL_SIBANTU.txt` dan tidak masuk GitHub. Klik nama akun setelah masuk untuk mengganti password.

Untuk instalasi baru, buat akun Kepala BPBD dengan `python -m flask --app app create-user --role bpbd`, lalu tambahkan pengguna lainnya melalui menu **Pengguna**. Khusus SQLite lokal, perintah `init-demo-users` dapat membuat tiga akun demo acak. Keluar lalu masuk dengan akun lain untuk berganti aktor; peran selalu diperiksa di server.

Demo penilaian memakai snapshot awal dari `examples/seed_case.json`. Saat Supabase dikonfigurasi, semua data aplikasi disimpan di PostgreSQL. Tanpa URI Supabase, aplikasi memakai SQLite `instance/assessment.sqlite3`. Migrasi berjalan otomatis saat aplikasi dibuka. Parameter `database` pada factory aplikasi dipakai oleh pengujian untuk memilih SQLite sementara tanpa mengakses Supabase.

Form penilaian Kepala BPBD, Koordinator Lapangan dan Perwakilan Dinas Sosial menggunakan alur bertahap: pilih kriteria yang lebih penting atau sama penting, lalu tingkat kepentingannya. Tersedia 15 perbandingan, progres, Sebelumnya/Berikutnya, tinjauan jawaban dan cek konsistensi. Nilai antara 2/4/6/8 dapat dibuka bila diperlukan. Klik **Simpan draf** sebelum meninggalkan halaman untuk menyimpan ke database; navigasi antarpasangan mempertahankan isian di halaman. Jawaban tiap aktor tetap independen, dengan metode AHP/TOPSIS/Borda yang sama.

### Login, dashboard, dan pendataan

1. Masuk sebagai **Kepala BPBD**. Daftarkan kejadian pada Malang Raya, Kabupaten Malang, Kota Malang, atau Kota Batu. Untuk kasus fiktif, centang **Data simulasi**. Tambahkan kecamatan dari katalog, lalu tugaskan Koordinator Lapangan.
2. Masuk sebagai **Koordinator Lapangan**. Buka **Tugas saya**, isi observasi lalu simpan draf atau kirim untuk verifikasi. Koordinator juga bisa mengusulkan kecamatan; usulan otomatis masuk tugasnya dan perlu disetujui Kepala BPBD.
3. Kepala BPBD menyetujui usulan kecamatan, lalu menyetujui atau menolak laporan dengan alasan. Perbaikan laporan masuk sebagai versi baru.
4. **Perwakilan Dinas Sosial** dapat membaca pendataan dan laporan untuk meninjau kebutuhan. Ketiga aktor dapat mengisi penilaiannya masing-masing. Finalisasi hasil hanya oleh Kepala BPBD.
5. Dashboard menampilkan poligon 41 kecamatan: Kabupaten Malang 33, Kota Malang 5, Kota Batu 3. Pilih tampilan wilayah terdampak, status pendataan, atau prioritas kelompok. Warna prioritas tersedia setelah tiga aktor mengirim; warna wilayah terdampak bukan tingkat bahaya. Klik kecamatan untuk melihat data kriterianya.
6. Kepala BPBD dapat membuka **Pengguna** untuk membuat akun, mengaktifkan/menonaktifkan akun lain, dan mengganti password pengguna. Akun sendiri tidak dapat dinonaktifkan. Setiap aktor dapat mengganti password sendiri lewat nama akun di navigasi. Perubahan password atau status akun mencabut sesi lama dan aktivitasnya tercatat.

Geometri peta disimpan lokal sehingga tidak memerlukan layanan peta eksternal. Sumber, keterbatasan, dan atribusi ada di [`data/README.md`](data/README.md). Kode kecamatan lama di luar katalog tetap tersimpan dan dapat dilihat di Pendataan.

Pada formulir kejadian, kode internal diberi contoh `GB-001` (gempa bumi, urutan 001); kode tetap diisi pengguna dan harus unik. Waktu kejadian dapat dipilih melalui kalender tanggal/jam bawaan browser. Pengetikan mengikuti format yang tampil pada kontrol browser. Jam dianggap WIB, disimpan dalam UTC, dan ditampilkan kembali sebagai `DD/MM/YYYY, HH:MM WIB`. Tanggal tidak valid atau waktu masa depan ditolak, dan pilihan waktu tetap terisi ketika formulir lain perlu diperbaiki.

### Database Supabase

**Pembaruan 21 November 2026:** koneksi aplikasi telah dikonfirmasi pengguna. Schema privat `sibantu` kini memiliki 14 tabel versi 6, tiga akun aplikasi dan simulasi empat kecamatan dengan C6 jarak pada ronde 3. Backend memakai role database `sibantu_app`; ini berbeda dari peran pengguna. Migrasi `sibantu_c6_distance_version` menandai arti kriteria pada setiap laporan. Uji SQL server memastikan laporan/ronde sebelumnya tetap utuh. Lingkungan agent tetap dibatasi jaringan; pengujian HTTP otomatis memakai SQLite sementara. Langkah konfigurasi manual di bawah ditujukan untuk proyek baru.

Tanpa `SUPABASE_DB_URL`, aplikasi memakai SQLite lokal. Status backend aktif dapat diperiksa dengan:

```powershell
python -m flask --app app database-status
```

Untuk menghubungkan proyek:

1. Salin `.env.example` menjadi `.env` di folder UAS.
2. Dari panel Supabase **Connect**, ambil URI **Session pooler** port 5432. Isi `SUPABASE_DB_URL`, dengan password database yang sudah di-URL-encode. Isi juga `SECRET_KEY` dengan nilai acak panjang. Simpan kredensial hanya pada mesin/server, jangan kirim melalui chat atau commit GitHub.
3. Jalankan `python -m pip install -r requirements.txt`, lalu `python -m flask --app app database-status`. Inisialisasi membuat schema `sibantu` dan migrasi secara otomatis memakai SSL. Sukses harus menampilkan `Database aktif: supabase; koneksi baca berhasil.` Jika konfigurasi Supabase gagal, aplikasi berhenti dengan error dan tidak beralih diam-diam ke SQLite.
4. Buat akun melalui terminal untuk masing-masing peran. Contoh: `python -m flask --app app create-user --role bpbd`. Isi email, nama, dan password minimal 12 karakter saat diminta. Ulangi dengan `--role lapangan` dan `--role sosial`.
5. Jalankan kembali `python app.py` dan buka halaman login. `COOKIE_SECURE=1` digunakan saat hosting memakai HTTPS.

Autentikasi memakai sesi Flask dan password hash yang disimpan pada database, **belum menggunakan Supabase Auth**. Schema `sibantu` tidak perlu diekspos ke Data API. URI database hanya digunakan oleh backend. Data SQLite yang lama tidak otomatis disalin ke proyek Supabase; simpan database lama untuk arsip dan rencanakan pemindahan data terpisah bila diperlukan.

### Penilaian yang dipertahankan

Rumus yang tersedia tetap memakai AHP, TOPSIS dan Borda. C6 sudah berubah menjadi **jarak posko induk ke titik gempa (km), benefit** untuk laporan dan ronde versi 2.0. MOORA/ELECTRE masih ditunda. Ronde baru mengambil snapshot laporan terverifikasi dengan C6 terbaru. Ronde 1.0 tetap menjadi arsip baca-saja dan tidak mengubah hasil lama.

### Ruang kerja Koordinator Lapangan

Halaman Pendataan untuk Koordinator langsung menampilkan **Tugas saya**, ringkasan status, pencarian dan filter. Daftar kejadian tidak ditampilkan. Kepala BPBD tetap mendaftarkan dan mengelola kejadian.

Formulir laporan dikelompokkan menjadi identitas observasi, dampak penduduk, kondisi wilayah, serta logistik dan jarak. Waktu observasi dipilih melalui kalender/jam WIB, dengan batas waktu kejadian dan waktu saat ini. C6 diisi sebagai kilometer. Pratinjau C3/C5 membantu pengisian; backend tetap menghitung dan memvalidasinya kembali. Draf dapat disimpan sebagian; pengiriman memerlukan data lengkap. Error dikaitkan dengan kolomnya dan formulir mempertahankan input.

Migrasi versi 6 menandai laporan lama sebagai criteria_version 1.0, tanpa mengubah JSON atau nilai kriterianya. Untuk laporan nyata, Koordinator mengisi jarak baru dan mengirim versi laporan baru. Empat laporan simulasi bawaan sudah mempunyai versi baru dengan jarak fiktif dan ronde 3; seluruh data/ronde lama tetap disimpan.

### Simulasi Malang Raya siap dicoba

Kasus `GB-SIM-MLG-001` sudah ada di Supabase: **Gedangan, Sumbermanjing Wetan, Dampit, Tirtoyudo**. Data fiktif disimpan pada [`examples/malang_raya_simulation.json`](examples/malang_raya_simulation.json). Empat laporan disiapkan sebagai terverifikasi dengan catatan verifikasi otomatis khusus simulasi. Nilai AHP ketiga aktor tidak diisi otomatis.

| Kecamatan | C1 pengungsi | C2 kerusakan (1-5) | C3 rentan (%) | C4 gangguan (1-5) | C5 kecukupan (%) | C6 jarak (km) |
|---|---:|---:|---:|---:|---:|---:|
| Gedangan | 1600 | 4 | 20 | 4 | 16,67 | 38 |
| Sumbermanjing Wetan | 1850 | 5 | 30 | 4 | 28,57 | 52 |
| Dampit | 2100 | 3 | 40 | 3 | 43,75 | 44 |
| Tirtoyudo | 1200 | 4 | 45 | 5 | 16 | 61 |

1. Mulai ulang server lalu buka Dashboard. Pilih kejadian simulasi empat kecamatan. Keempat wilayah ditandai jingga; gunakan **Fokus wilayah terdampak** untuk memperbesar ke wilayah ini.
2. Masuk sebagai masing-masing aktor dan pilih **Buka penilaian saya**. Isi/cek konsistensi/kirim sendiri. Progres dashboard berubah dari 0/3 hingga 3/3.
3. Sesudah ketiganya mengirim, hasil Borda dan tampilan peta **Prioritas bantuan kelompok** tersedia. Refresh dashboard untuk memuat status terbaru. Kepala BPBD dapat mengesahkan hasil.
4. Ronde sebelumnya tetap dapat dibuka melalui pemilih ronde. Setelah sebuah ronde disahkan, Kepala BPBD dapat membuka ronde baru bila semua laporan terbaru kembali terverifikasi.

Untuk membuat contoh ini pada database lain, jalankan `python -m flask --app app seed-malang-simulation`. Perintah idempoten dan tidak mereset penilaian yang sudah diisi. Proyek Supabase saat ini sudah diisi, sehingga cukup mulai ulang aplikasi.

Pengujian: `python -m unittest discover -s tests -v`.

Pengujian mencakup autentikasi, pencabutan sesi, pengelolaan akun, migrasi, pendataan, peta, dan regresi perhitungan. Browser otomatis belum dapat dijalankan pada lingkungan agent; tampilan desktop/mobile belum diverifikasi secara visual.

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
