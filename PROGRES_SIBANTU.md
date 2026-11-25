# Progres Pengembangan SiBantu

**Pembaruan terakhir:** 25 November 2026.

## Redesain visual "Lembar Survei" (25 November 2026)

- Halaman login diberi satu foto Tugu Kota Malang (Ulumarifah, CC BY-SA 4.0, Wikimedia Commons) setinggi layar di kolom kiri, lengkap dengan kredit. Sumbernya dicatat di `static/img/SUMBER_FOTO.md`.
- Palet direvisi (ADR-028): kertas abu dingin, tinta biru-hitam, dan sinyal biru petrol menggantikan manila-oranye yang terlalu mirip warna Claude.
- Tema gelap "Pusat Kendali" diganti tema terang kertas-tinta (ADR-027, `design-system/sibantu/MASTER.md`). Alur setiap aktor, rute, form, dan perhitungan tidak berubah.
- Pola yang terasa generik dibuang: latar navy bercahaya, kartu KPI berikon, gauge, titik status, label mono kapital, cahaya berdenyut di login, dan heading dua warna. Penggantinya buku angka bergaris, angka `n/3` beserta daftar aktor, chip status berteks, dan satu warna sinyal oranye.
- Peta menjadi lembar survei bergrid. Kecamatan terpilih tampil sebagai kartu catatan lapangan. Warna kanvas kini dibaca dari token CSS, tidak lagi ditulis langsung di `malang-map.js`.
- Teks meta yang dipisah titik tengah diganti kalimat biasa. Eyebrow dihapus dan isinya dipindah ke paragraf.
- 35 pengujian Python dan 7 pengujian JavaScript lulus. Diperiksa di browser (SQLite sementara dan seed SIMULASI, bukan Supabase) pada 1440 dan 375 piksel: login, dashboard dengan mode peta terdampak dan prioritas, Pendataan (BPBD dan Koordinator), Penilaian AHP (form dan baca-saja), serta Hasil kelompok. Tidak ada scroll horizontal dan tidak ada error console.

## Logo SiBantu (25 November 2026)

- Logo "Tangan yang Menjadi Atap": dua tangan yang ujung jarinya bertemu membentuk atap di atas keluarga, dengan titik gempa kecil di bawah garis tanah. Berkas SVG/PNG, favicon, dan filosofi ada di `static/img/logo/`.
- Logo dipasang di bilah atas semua halaman internal dan halaman login; favicon dan apple-touch-icon dipasang di semua template. Diuji otomatis dan diperiksa di browser pada 1440 dan 375 piksel.

## Alat bantu konsistensi AHP (25 November 2026)

- Masalah: setiap DM harus mencapai CR ≤ 0,10 dari 15 perbandingan, dan penilai mudah bingung pasangan mana yang perlu diubah.
- **Urutkan kriteria dulu:** langkah awal opsional untuk mengurutkan C1–C6. Saat mengisi pasangan, sistem menampilkan urutan tersebut dan memberi peringatan bila arah pilihan berlawanan. Tidak memblokir dan tidak mengisi jawaban.
- **Saran pasangan penyebab CR tinggi:** bila CR > 0,10 (Cek konsistensi atau Kirim), panel Konsistensi menampilkan hingga tiga pasangan, nilai yang lebih konsisten, dan perkiraan CR setelah perubahan, dengan tautan Ubah pasangan.
- Rumus AHP/TOPSIS/Borda, batas CR, skema database, dan data tersimpan tidak berubah (ADR-026).
- **Revisi UX:** perkiraan nilai dari jawaban lain per pasangan (mencegah salah besar, bukan hanya salah arah), saran CR dalam kalimat verbal, tanda saran langsung di daftar tinjauan, tautan dari pesan error, tombol Kembali ke tinjauan, peringatan perubahan belum disimpan, dan target gulir yang tidak tertutup header.
- 35 pengujian Python dan 7 pengujian JavaScript lulus. Diperiksa di browser (SQLite sementara) pada 1440 dan 375 piksel: urutan, perkiraan dan peringatan, saran pasangan di panel dan tinjauan, Kembali ke tinjauan, serta tanpa scroll horizontal.


## Redesain UI "Pusat Kendali" (24 November 2026)

- Seluruh halaman memakai tema gelap baru (`static/theme.css`) mengikuti referensi dashboard komando bencana; panduan di `design-system/sibantu/MASTER.md`, keputusan ADR-025.
- Header baru: identitas BPBD · Malang Raya, jam WIB langsung, avatar akun, tab berikon (Ringkasan Operasi, Pendataan Wilayah, Penilaian AHP, Hasil Kelompok, Pengguna) dan skip link.
- Dashboard: pemilih operasi aktif, 4 KPI (kecamatan terdampak, total pengungsi C1, status pendataan, penilaian 0–3), peta gelap dengan kontrol vertikal dan strip legenda, gauge progres keputusan kelompok, umpan status wilayah terdampak, tabel prioritas Borda, dan daftar 41 kecamatan yang dapat dibuka.
- Tidak ada angka hardcoded: peringkat/poin hanya dari hasil ronde, gauge dari jumlah aktor yang mengirim.
- Label peta tidak lagi bertumpuk: posisi label memakai titik tengah luas poligon (dijamin di dalam wilayah), lalu penempatan menghindari tabrakan. Wilayah terpilih/terdampak didahulukan; label yang digeser diberi garis penunjuk, label kecamatan lain yang tidak muat disembunyikan sampai peta diperbesar.
- 33 pengujian Python dan 4 pengujian JavaScript lulus. Diperiksa di browser (SQLite sementara + seed SIMULASI, bukan Supabase) pada 1440px dan 375px: login, dashboard, pemilihan kecamatan, Pendataan, Penilaian; tanpa scroll horizontal.


## Form penilaian bertahap untuk ketiga decision maker

- Kepala BPBD, Koordinator Lapangan dan Perwakilan Dinas Sosial memakai template penilaian yang sama. Form aktif menampilkan satu pasangan kriteria, pilihan kriteria/nilai sama penting, lalu tingkat kepentingannya.
- Nama kriteria ditampilkan lengkap. Pilihan utama 3/5/7/9 memakai penjelasan verbal; nilai antara 2/4/6/8 tersedia melalui bagian yang dapat dibuka. Seluruh 17 pilihan Saaty dan nilai resiprokal tetap didukung tanpa perubahan rumus.
- Tersedia progres jawaban, Sebelumnya/Berikutnya, tinjauan semua jawaban dengan tombol Ubah, dan validasi jawaban belum lengkap. Navigasi mempertahankan isian di halaman; penyimpanan ke database tetap memerlukan Simpan draf atau Kirim penilaian. Cek konsistensi hanya menghitung pratinjau.
- Draf/hasil tetap terpisah per aktor dan ronde. Penilaian terkirim serta ronde arsip tetap baca-saja. Jika JavaScript tidak aktif, form pilihan biasa dengan nama lengkap dan penjelasan verbal tetap dapat digunakan.
- **33 pengujian Python dan 4 pengujian JavaScript lulus** setelah koneksi lingkungan pulih. Pengujian mencakup semua pilihan Saaty, penyimpanan draf parsial, arah resiprokal, dan alur tiga aktor. Verifikasi visual/interaksi di browser belum dijalankan.

## Revisi Koordinator Lapangan dan C6 jarak

- Waktu observasi memakai pilihan tanggal/jam WIB dengan batas waktu kejadian dan waktu saat ini. Validasi server menolak waktu sebelum kejadian, masa depan, jarak negatif/non-finite dan laporan yang tidak lengkap saat dikirim.
- C6 laporan baru menjadi jarak posko induk ke titik gempa (km), benefit. Tidak ada input waktu sejak bantuan terakhir pada formulir Koordinator.
- Halaman utama Koordinator menampilkan Tugas saya, ringkasan status, kartu kecamatan, pencarian dan filter. Daftar administrasi kejadian tidak tampil; POST pendaftaran kejadian tetap ditolak untuk Koordinator.
- Form dibagi menjadi empat kelompok, dengan bantuan pengisian, error dekat kolom, ringkasan error yang menerima fokus, pratinjau C3/C5, indikator proses kirim dan tata letak responsif. Panduan desain ada di design-system/sibantu/pages/coordinator.md. Tidak ditambahkan dependensi UI atau font eksternal.
- Migrasi schema versi 6 menambah field_reports.criteria_version. Ronde/laporan versi 1.0 tetap menjadi arsip. Angka jam lama tidak dikonversi menjadi kilometer. Nilai C6 yang belum diperbarui ditampilkan kosong pada data terbaru, bukan sebagai km palsu.
- Supabase mempunyai empat versi laporan baru untuk contoh aplikasi dan ronde 3 versi 2.0. Jarak fiktif: Gedangan 38 km, Sumbermanjing Wetan 52 km, Dampit 44 km, Tirtoyudo 61 km. Ronde 1/2 dan empat laporan lama tidak berubah; checksum isi sebelum/sesudah cocok. Ketiga penilaian ronde baru masih kosong.
- Perubahan skema C6 tidak menambah MOORA/ELECTRE atau mengganti rumus AHP/TOPSIS/Borda. Pemeriksaan visual browser otomatis masih belum tersedia pada lingkungan agent.

## Simulasi Malang Raya empat kecamatan

Kasus GB-SIM-MLG-001 ada di Supabase sebagai **SIMULASI**, kejadian ID 1 dan ronde aktif ID 3 dengan C6 jarak. Ronde ID 2 menjadi arsip kriteria sebelumnya. Empat laporan terbaru berstatus VERIFIED dengan catatan verifikasi otomatis khusus latihan. Penilaian Kepala BPBD, Koordinator Lapangan, dan Dinas Sosial masih kosong pada ronde baru (0/3).

| Kecamatan | Kode | C1 pengungsi | C2 kerusakan | C3 rentan (%) | C4 gangguan | C5 kecukupan (%) | C6 km |
|---|---|---:|---:|---:|---:|---:|---:|
| Gedangan | 35.07.29 | 1600 | 4 | 20 | 4 | 16,67 | 38 |
| Sumbermanjing Wetan | 35.07.04 | 1850 | 5 | 30 | 4 | 28,57 | 52 |
| Dampit | 35.07.05 | 2100 | 3 | 40 | 3 | 43,75 | 44 |
| Tirtoyudo | 35.07.30 | 1200 | 4 | 45 | 5 | 16 | 61 |

Total pengungsi contoh 6750 orang. File sumber examples/malang_raya_simulation.json kini menggunakan C6 jarak sesuai revisi pengguna. Perubahan metode selain tiga metode yang tersedia tetap menunggu keputusan lanjutan.

Dashboard menandai empat wilayah dengan warna jingga, menampilkan progres tiga aktor dan rincian kriteria ketika kecamatan dipilih. Pilihan peta: wilayah terdampak, status pendataan, prioritas kelompok. Mode prioritas baru tersedia setelah tiga aktor mengirim; warna/ranking dihitung dari Borda, tidak ditetapkan pada data seed. Tersedia filter fokus empat kecamatan.

Migrasi sibantu_case_decision_rounds ke versi 5 menambahkan decision_rounds dan round_assessments. Ronde/snapshot/penilaian lama disalin tanpa menimpa tabel asal. Laporan terbaru tidak mengubah ronde terkunci; setelah finalisasi dan verifikasi laporan baru, Kepala BPBD dapat membuka ronde baru. Perintah seed-malang-simulation idempoten dan tidak mereset penilaian yang sudah dikirim.

## Revisi formulir kejadian, 21 November 2026

- Kode kejadian mendapat placeholder GB-001 dan penjelasan kode internal/nomor urut. Kode tetap diisi pengguna dan unik per kejadian.
- Waktu kejadian menggunakan kontrol datetime-local untuk memilih tanggal dan jam, disertai keterangan WIB. Pengetikan mengikuti format kontrol browser; pengguna tidak perlu menulis ISO atau zona waktu.
- Backend mengartikan pilihan tanpa zona sebagai WIB dan menyimpannya sebagai UTC. Format lama dengan zona tetap diterima. Detail kejadian menampilkan DD/MM/YYYY, HH:MM WIB.
- Pilihan waktu dipertahankan setelah validasi/duplikasi gagal. Waktu tidak valid atau masa depan ditolak. Tidak ada perubahan schema atau data lama.

Koneksi aplikasi ke Supabase sudah dikonfirmasi berhasil oleh pengguna. Tahap ini melanjutkan login, pengelolaan tiga aktor, dan dashboard Malang Raya. Perubahan metode perhitungan tetap ditunda.

## Hasil terbaru

| Bagian | Implementasi |
|---|---|
| Tiga aktor | Kepala BPBD merangkap administrasi; Koordinator Lapangan merangkap pendataan; Perwakilan Dinas Sosial membaca kebutuhan dan ikut penilaian. |
| Akun awal | Tiga akun aktif sudah dibuat di Supabase: bpbd@sibantu.local, lapangan@sibantu.local, sosial@sibantu.local. Password acak disimpan di instance/AKUN_AWAL_SIBANTU.txt, di luar Git. |
| Login | Email/password, hash scrypt, CSRF, pembatasan percobaan, cookie HTTPOnly/SameSite, logout, pengecekan akun aktif dan versi sesi. |
| Pengguna | Kepala BPBD membuat akun, mengaktifkan/menonaktifkan akun lain, serta mengganti password pengguna melalui /pengguna. Akun sendiri tidak dapat dinonaktifkan. |
| Akun saya | Semua aktor dapat mengganti password sendiri melalui /akun dengan password lama dan konfirmasi password baru. |
| Pencabutan sesi | Password/status berubah menaikkan session_version; sesi lain dan cookie lama ditolak. Aktor diperiksa ulang di dalam transaksi administrasi. |
| Audit akun | Pembuatan akun, aktivasi/nonaktivasi, reset password dan perubahan password sendiri tercatat tanpa menyimpan password asli. |
| Operasional | BPBD mendaftarkan kejadian, menyetujui usulan kecamatan, menugaskan Koordinator dan memverifikasi laporan. Koordinator mengusulkan/mendata/memperbaiki laporan. Dinas Sosial dapat membaca laporan. |
| Dashboard | Peta 41 kecamatan dengan mode terdampak/status/prioritas, fokus wilayah terdampak, nilai kriteria dan progres tiga aktor. Geometri lokal; warna prioritas hanya dari hasil kelompok aktual. |
| Pesan aplikasi | Halaman kesalahan 400/403/404/409/413/500 dalam Bahasa Indonesia, dengan tautan kembali. |
| Supabase | Schema privat sibantu memiliki 14 tabel versi 6 dan tag versi kriteria per laporan. Role database backend sibantu_app berbeda dari tiga role pengguna aplikasi. |
| Perhitungan | Rumus AHP/TOPSIS/Borda dipertahankan, C6 versi 2.0 memakai jarak km benefit. Ronde baru dari laporan terverifikasi; MOORA/ELECTRE belum ditambahkan. |

## Pengujian dan batas verifikasi

- **31 pengujian otomatis lulus** dengan `python -m unittest discover -s tests -v`. Enam pengujian Koordinator mencakup halaman tugas sesuai peran, kalender observasi WIB, validasi jarak, draf parsial, C6 benefit, migrasi dan preservasi arsip lama. Alur tiga aktor, akun/sesi, pendataan dan perhitungan tetap lulus.
- `node --check static/malang-map.js` berhasil.
- Query server sebagai sibantu_app memastikan kasus simulasi ID 1, ronde 2 dengan empat kecamatan, empat laporan VERIFIED dan nol penilaian aktor. Query sebelumnya memastikan tiga akun aktif dengan hash scrypt. Akses schema untuk anon tidak diberikan.
- Uji baca/tulis sebelumnya sebagai role sibantu_app berhasil di server dan transaksi uji dibatalkan. Pengguna sudah mengonfirmasi perintah database-status berhasil dari terminalnya.
- HTTP langsung dari runtime agent dibatasi jaringan, termasuk localhost. Chrome otomatis juga gagal diluncurkan. Karena itu, pengujian request memakai Flask test client dengan SQLite sementara; hasil tersebut tidak diklaim sebagai uji browser atau koneksi langsung ke Supabase.
- Pemeriksaan visual desktop/mobile dan login melalui browser pengguna masih perlu dilakukan. Tidak ada screenshot yang diklaim sebagai hasil verifikasi.

## Cara menjalankan

1. Buka folder UAS dan jalankan JALANKAN_SIBANTU.bat, atau jalankan `python app.py` dengan GDSS_PORT=5050.
2. Buka http://127.0.0.1:5050/login.
3. Lihat email/password awal di instance/AKUN_AWAL_SIBANTU.txt. Klik nama akun setelah login untuk mengganti password.
4. Pilih simulasi empat kecamatan di Dashboard lalu klik Buka penilaian saya. Ketiga aktor mengirim penilaian masing-masing. Refresh dashboard untuk melihat progres; setelah 3/3, pilih mode Prioritas bantuan kelompok.
5. Jika server versi lama masih berjalan, hentikan dengan Ctrl+C pada terminalnya lalu jalankan kembali agar perubahan kode dimuat.

## Penyimpanan dan keamanan database

URI koneksi disimpan pada .env; file ini dan folder instance diabaikan Git. Schema sibantu tidak dibuka ke Data API dan role anon/authenticated tidak memiliki akses schema. Backend adalah pemilik tabel; otorisasi pengguna ditegakkan melalui Flask. Auth aplikasi belum menggunakan Supabase Auth.

Advisor memberi INFO RLS tanpa policy pada 14 tabel privat. RLS menolak akses non-owner; backend sebagai pemilik menjalankan operasi aplikasi. [Penjelasan advisor](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy). Tidak ada password asli pada tabel audit atau migrasi server; provisioning role koneksi menggunakan verifier SCRAM.

Perubahan kode tahap ini masih berada di workspace lokal; belum dipush pada tahap ini. Riwayat di bawah mendeskripsikan versi sebelumnya.

## Riwayat 14 November 2026

**Tanggal pembaruan** 14 November 2026  
**Branch** `main`  
**Commit implementasi terakhir** [`eb28e27` – Add SiBantu field reporting and verification](https://github.com/azkafariqiuinmalang/SiBantu/commit/eb28e27f50ef984ec2a675350f574721ea65ce80)

SiBantu adalah prototipe sistem pendukung keputusan kelompok untuk menentukan prioritas kecamatan penerima bantuan logistik pascagempa. Aplikasi berjalan lokal menggunakan Python, Flask, dan SQLite.

## Fitur yang sudah dikerjakan

| Bagian | Implementasi |
|---|---|
| Pencatatan kejadian | Admin mendaftarkan kejadian yang sudah berlangsung, mencatat waktu, lokasi, dan sumber informasi, serta menandai kasus simulasi. |
| Kecamatan dan penugasan | Admin menambahkan kecamatan dengan kode unik per kejadian dan menugaskan petugas. Dalam mode demo, server memeriksa peran yang dipilih dan kepemilikan tugas. |
| Laporan lapangan | Petugas menyimpan draf atau mengirim laporan dengan waktu dan sumber observasi. Server memvalidasi input, menghitung C3 (persentase pengungsi rentan) dan C5 (kecukupan logistik), serta menolak kiriman ketika kebutuhan logistik bernilai nol dan perlu verifikasi khusus. |
| Verifikasi dan revisi | Admin menyetujui laporan atau menolaknya dengan alasan. Perbaikan masuk sebagai versi baru. Riwayat laporan dan pemeriksaan tetap tercatat. Admin bisa melihat jumlah kecamatan yang laporan terbarunya sudah terverifikasi. |
| Penilaian simulasi | Ketiga pengambil keputusan mengisi masing-masing 15 perbandingan AHP. Pengiriman diterima jika CR ≤ 0,10. TOPSIS menghitung peringkat per pengambil keputusan, Borda muncul setelah ketiganya mengirim hasil, lalu Kepala BPBD dapat mengesahkan rekomendasi dalam demo. |
| Penyimpanan | Migrasi SQLite ke versi 2 menambahkan tabel pendataan, versi laporan, verifikasi, dan audit. Migrasi diuji dengan basis data lama yang sudah memiliki ronde dan penilaian. |

## Cara mencoba secara lokal

Jalankan dari folder proyek.

```powershell
python -m pip install -r requirements.txt
python app.py
```

1. Buka [Pendataan](http://127.0.0.1:5000/pendataan) dan pilih **Admin**. Daftarkan satu kasus simulasi, tambah dua kecamatan, lalu tugaskan petugas ke kedua kecamatan.
2. Pilih petugas yang ditugaskan. Buka **Tugas saya**, isi laporan tiap kecamatan, lalu kirim untuk verifikasi.
3. Kembali sebagai **Admin**. Setujui satu laporan dan tolak satu laporan dengan alasan. Pilih petugas lagi untuk mengirim versi perbaikan, lalu verifikasi versi terbaru sebagai admin.
4. Buka [Penilaian](http://127.0.0.1:5000/) untuk mencoba perhitungan AHP, TOPSIS, dan Borda dengan snapshot dari kasus simulasi bawaan.

## Hasil pengujian

**6 pengujian otomatis lulus** dengan perintah berikut.

```powershell
python -m unittest discover -s tests -v
```

Pengujian mencakup alur dua kecamatan sampai keduanya terverifikasi, pembatasan akses tugas berdasarkan peran demo dan penugasan, penyimpanan versi lama, migrasi basis data, validasi AHP, penanganan kriteria cost pada TOPSIS, serta aturan seri dan pengesahan Borda.

## Langkah berikutnya

Penilaian saat ini memakai satu snapshot simulasi bawaan. Data dari menu **Pendataan** belum menjadi masukan ronde. Pemilih peran masih digunakan untuk demo lokal. Autentikasi dijadwalkan pada tahap berikutnya.

1. Siapkan pembuatan ronde oleh admin ketika semua kecamatan yang akan dinilai memiliki laporan terbaru yang terverifikasi.
2. Saat ronde dibuka, simpan salinan nilai C1–C6, ID dan versi laporan, serta waktu penguncian. Gunakan salinan yang sama untuk ketiga pengambil keputusan.
3. Simpan draf dan hasil AHP, TOPSIS, Borda, serta pengesahan berdasarkan ID ronde. Uji bahwa pembaruan laporan untuk ronde berikutnya tidak mengubah hasil ronde sebelumnya.
