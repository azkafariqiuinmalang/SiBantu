# Product Requirements Document (PRD)

## Product vision
Prototipe GDSS web yang merekam kejadian gempa, menghimpun dan memverifikasi kondisi kecamatan, memfasilitasi pembobotan independen oleh tiga pemangku keputusan, dan menjelaskan rekomendasi urutan prioritas logistik kebutuhan dasar dengan metode AHP–TOPSIS–Borda.

## Masalah pengguna
- **Admin:** butuh satu dataset konsisten dan tertelusur untuk kasus dan ronde keputusan.
- **Petugas lapangan:** butuh formulir sederhana untuk laporan per kecamatan dengan sumber/waktu.
- **DM:** butuh matriks perbandingan kriteria yang mudah digunakan dengan pengecekan konsistensi.
- **Pemimpin:** butuh hasil grup yang dapat dipertanggungjawabkan beserta perbedaan pandangan DM.

## Persona / peran
Lihat `PROJECT_CONTEXT.md`, `docs/WORKFLOWS.md`.

**Pembaruan 20 November 2026:** tiga peran login menggantikan lima aktor awal. Kepala BPBD merangkap admin, Koordinator Lapangan merangkap pendataan, Perwakilan Dinas Sosial membaca kebutuhan dan ikut penilaian. Lingkup tahap ini adalah login, pembatasan akses, koneksi database Supabase, dan peta kecamatan Malang Raya. Perubahan metode perhitungan ditunda. Istilah admin/petugas pada rancangan workflow lama merujuk pada tugas BPBD/Koordinator, bukan peran login tambahan.

## Fitur MVP (wajib)
| ID | Fitur | Acceptance criteria |
|---|---|---|
| F01 | Login & RBAC tiga aktor | Login sebelum halaman internal; sesi Flask, password hash, CSRF, pembatasan percobaan login; server menolak akses di luar peran |
| F02 | Daftarkan kejadian gempa | Admin mencatat judul, lokasi, waktu, sumber informasi, label simulasi/riil; tidak memicu otomatisasi bencana |
| F03 | Alternatif kecamatan Malang Raya | Kepala BPBD menambahkan kecamatan dari katalog; koordinator dapat mengusulkan dan menunggu persetujuan; unik per kasus |
| F04 | Penugasan pendataan | Admin menetapkan petugas ke kecamatan; petugas hanya mengubah data yang ditugaskan |
| F05 | Form per kecamatan | Observasi kalender/jam WIB; input C1,C2,C4, jarak C6 kilometer, jumlah rentan dan stok/kebutuhan; C3/C5 diturunkan; draf boleh parsial, pengiriman lengkap; error dekat kolom |
| F06 | Verifikasi | Admin approve/reject dengan alasan; data yang belum diverifikasi tidak masuk ronde |
| F07 | Snapshot/assessment round | Lock himpunan kecamatan, kriteria, nilai; jika revisi penting, buat ronde baru, jangan diam-diam mengubah ranking lama |
| F08 | AHP per DM | 15 pasangan untuk 6 kriteria; input skala Saaty 1–9 + resiprokal; matrix diagonal 1, resiprokal otomatis; CR ≤ 0.10 untuk submit |
| F09 | TOPSIS per DM | Ranking individual dari snapshot yang sama dengan bobot AHP masing-masing; tampilkan nilai preferensi dan rincian hitung |
| F10 | Borda grup | Saat ketiga DM valid, terbit ranking dengan poin 5,4,3,2,1 untuk 5 alternatif, generalisasikan N..1 untuk N alternatif; seri diselesaikan berdasar posisi pada ranking DM Kepala BPBD |
| F11 | Finalisasi | Kepala BPBD mengesahkan rekomendasi; hasil menjadi read-only dan ada timestamp |
| F12 | Dashboard audit | Status per role/per kecamatan/per DM; hasil lengkap dan data sumber dapat dilihat pengguna berwenang |
| F13 | Peta dashboard Malang Raya | Poligon 41 kecamatan, filter kejadian/wilayah, pemilihan kecamatan dan legenda status; data bersumber dari pendataan, tanpa skor/hazard buatan |
| F14 | PostgreSQL Supabase | Konfigurasi server melalui .env; SSL; migrasi schema sibantu; kredensial tidak berada di frontend; koneksi aktual perlu diuji setelah proyek tersedia |
| F15 | Pengelolaan akun | Kepala BPBD membuat/mengaktifkan/menonaktifkan akun lain serta mengganti password pengguna; akun sendiri tidak dapat dinonaktifkan; audit tercatat |
| F16 | Akun saya | Semua aktor dapat mengganti password dengan password lama dan konfirmasi; minimal 12 karakter; sesi lain dicabut setelah perubahan |
| F17 | Simulasi empat kecamatan | Gedangan, Sumbermanjing Wetan, Dampit, Tirtoyudo dengan data fiktif dan ronde terpisah; tiap aktor menilai sendiri; seed idempoten |
| F18 | Progres dan prioritas pada peta | Tampilkan progres 0/3 sampai 3/3; warna prioritas kelompok hanya dari hasil Borda aktual; perbedaan laporan terbaru/snapshot ronde dijelaskan |
| F19 | Ruang kerja Koordinator | Tugas saya berupa kartu kecamatan/status, pencarian dan filter; daftar administrasi kejadian tidak tampil; pendaftaran kejadian tetap ditolak server untuk Koordinator |

## Fitur opsional (jangan blok MVP)
- PDF/CSV export, grafik ranking, peta berbasis koordinat valid, unggah lampiran, multi-petugas, notifikasi in-app, refresh data BMKG secara manual (bukan otomatis).

## User stories ringkas
- Sebagai admin, saya ingin mencatat kejadian yang sudah terjadi untuk memulai pendataan dengan sumber jelas.
- Sebagai admin, saya ingin menugaskan petugas dan memverifikasi laporan agar ranking tidak menggunakan data belum sah.
- Sebagai petugas, saya ingin mendata satu kecamatan dan memperbaiki data yang ditolak dengan alasan.
- Sebagai DM, saya ingin membandingkan kepentingan kriteria dan memperoleh masukan jika CR tidak konsisten.
- Sebagai Kepala BPBD, saya ingin melihat pandangan 3 DM dan memfinalisasi rekomendasi kelompok.

## Aturan penting
1. Belum lengkap/terverifikasi → tombol mulai ronde nonaktif.
2. Ronde terkunci → update pada kasus membuat **revisi/ronde baru**, tidak mengubah snapshot yang sedang dinilai.
3. AHP CR > 0.10 → tidak valid; perhitungan sementara boleh dipreview, tidak boleh disubmit final.
4. 3 DM belum selesai → tidak ada hasil Borda final.
5. Hasil Borda adalah rekomendasi ranking, tidak mengeluarkan perintah distribusi bantuan.
6. Masalah kritis penyelamatan jiwa di luar scoring rutin: tampilkan eskalasi manual, jangan tunggu ranking.

## Validasi data
- Waktu kejadian, sumber rujukan, wilayah kasus valid; dukung placeholder sementara hanya pada *draft*.
- C1 integer ≥0; kelompok rentan integer ≥0 dan ≤ C1; C2,C4 integer 1..5; C5 0..100; C6 jarak kilometer >=0, finite, bertipe benefit. Nilai jam versi sebelumnya tidak boleh menjadi nilai kilometer.
- C3 diturunkan 100×kelompok_rentan/C1; jika C1 = 0 dan rentan = 0, C3 = 0 dengan flag no-evacuees; jika C1 = 0 dan rentan > 0, reject.
- Untuk C5: stok/kebutuhan yang dinyatakan setara paket-or-equivalent dan periode yang sama; C5 = min(100,100×stok/kebutuhan). Bila kebutuhan = 0 → minta verifikasi khusus; jangan membagi nol diam-diam.
- Setiap form punya `observed_at`, `source_note`, `entered_by`; audit perubahan.

## Success criteria UAS
- Demo 1 kasus/5 kecamatan, 1 petugas, 3 DM dengan data dummy diberi label.
- End-to-end workflow berjalan tanpa bypass role atau penilaian.
- Semua komputasi dibandingkan fixture independen pada unit test.
- Laporan menunjukkan sumber data, bobot, CR, skor TOPSIS, Borda, dan status final.

## Non-functional requirements
Security (RBAC dan validasi server); integrity (snapshot immutable), accessibility (form dengan label), performance (dataset MVP <2 s secara lokal sebagai target, bukan klaim), maintainability (pure math functions, tests), reliability (pesan error spesifik), bahasa Indonesia, mobile responsive.
