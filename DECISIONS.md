# Decision Log

## Pembaruan 20 November 2026 (menggantikan rancangan aktor awal)

| ID | Keputusan | Status |
|---|---|---|
| ADR-011 | Tiga aktor: Kepala BPBD sekaligus admin; Koordinator Lapangan sekaligus pendataan; Perwakilan Dinas Sosial | Arahan pengguna, diterapkan |
| ADR-012 | Login sebelum dashboard, hak akses berasal dari akun server; pemilih peran demo dihapus | Arahan pengguna, diterapkan |
| ADR-013 | PostgreSQL Supabase sebagai database target; SQLite untuk uji lokal | Pengguna mengonfirmasi koneksi berhasil; migrasi versi 4 dan tiga akun awal sudah dibuat |
| ADR-014 | Sesi Flask dan password hash di database; psycopg melalui Session pooler/SSL, schema sibantu | Pilihan implementasi; bukan Supabase Auth |
| ADR-015 | Dashboard poligon 41 kecamatan Malang Raya dengan status pendataan per kejadian | Arahan pengguna, diterapkan |
| ADR-016 | Metode perhitungan akan dikonfirmasi kemudian; simulasi AHP/TOPSIS/Borda serta snapshot lama dipertahankan | Arahan pengguna |
| ADR-017 | Usulan kecamatan koordinator otomatis menjadi tugas pendataannya; Kepala BPBD menyetujui usulan sebelum verifikasi laporan | Pilihan implementasi dari pemetaan operasional |
| ADR-018 | Kepala BPBD mengelola akun dan status; semua aktor mengganti password sendiri. Versi sesi berubah saat password/status berubah | Implementasi tugas administrasi dan login; aktivitas akun diaudit |
| ADR-019 | Simulasi empat kecamatan Gedangan, Sumbermanjing Wetan, Dampit, Tirtoyudo; nilai lapangan fiktif, penilaian aktor kosong | Permintaan pengguna 21 November 2026, sudah diisi ke Supabase |
| ADR-020 | Ronde per kejadian membekukan nilai serta ID/versi laporan; migrasi menyalin ronde legacy tanpa mengubahnya | Diterapkan untuk memisahkan simulasi baru dan penilaian lama |
| ADR-021 | Peta mempunyai mode wilayah terdampak, status laporan dan prioritas Borda; prioritas baru muncul setelah tiga kiriman | Diterapkan; tidak mengarang skor/sebaran bahaya |
| ADR-022 | C6 menjadi jarak posko induk ke titik gempa (km), benefit; laporan/ronde baru versi 2.0 | Revisi eksplisit pengguna 21 November 2026, diterapkan dengan arsip versi 1.0 |
| ADR-023 | Koordinator hanya melihat tugas pendataannya pada halaman utama; waktu observasi berupa kalender/jam WIB | Revisi eksplisit pengguna, termasuk pembaruan formulir dan kartu tugas |
| ADR-024 | Form AHP ketiga DM bertahap seperti Google Form: pilih kriteria lalu tingkat kepentingan, progres dan tinjauan sebelum kirim | Disetujui pengguna 21 November 2026; tetap 15 pasangan dan seluruh skala Saaty, tanpa perubahan metode |
| ADR-025 | Tema UI gelap "Pusat Kendali" untuk semua halaman (theme.css, MASTER.md); tetap Flask/Jinja + CSS/JS biasa, tanpa font/CDN eksternal | Permintaan pengguna 24 November 2026 berdasar referensi dashboard komando bencana; tidak mengubah data, rute, atau metode |
| ADR-026 | Alat bantu konsistensi AHP: langkah urutkan kriteria (opsional, disimpan di browser) dengan peringatan arah yang berlawanan, perkiraan transitif per pasangan dari jawaban lain, serta saran 3 pasangan penyebab CR tinggi beserta nilai Saaty yang lebih konsisten | Disetujui pengguna 25 November 2026; tidak mengubah rumus AHP, batas CR 0,10, data tersimpan, maupun jawaban DM (tidak ada pengisian otomatis) |
| ADR-027 | Redesain visual "Lembar Survei": tema terang kertas-tinta (Hallmark Furrow) menggantikan tema gelap ADR-025; satu sinyal oranye sebagai isian, status berwarna redup, label tanpa mono/kapital, kartu KPI berikon diganti buku angka bergaris, gauge diganti angka n/3, peta bergrid dengan kartu catatan kecamatan, warna peta dibaca dari token CSS | Permintaan pengguna 25 November 2026 (memperbaiki tampilan yang terasa generik); alur tiap aktor, rute, form, id/hook JS, data, dan metode tidak berubah; tetap tanpa font/CDN eksternal |
| ADR-028 | Palet ADR-027 diganti: kertas abu dingin (#edf3f4), tinta biru-hitam (#0b151f), satu sinyal biru petrol (#006065) dengan teks putih; status, peta prioritas, dan tata letak tetap | Permintaan pengguna 25 November 2026: palet manila-oranye terlalu mirip warna Claude; hanya token warna di theme.css dan halo garis terpilih di peta yang berubah |

Rencana lima metode masih menunggu pembahasan lanjutan. C6 jarak bertipe benefit sudah diterapkan pada versi 2.0; tiga rumus yang tersedia tetap dipakai. Rancangan di bawah merupakan riwayat; bila bertentangan, pembaruan ini berlaku.

## Keputusan yang disepakati (accepted)
| ID | Keputusan | Alasan |
|---|---|---|
| ADR-001 | Fokus logistik kebutuhan dasar pascagempa | Satu domain keputusan untuk UAS |
| ADR-002 | Alternatif berupa kecamatan, 5 kecamatan untuk demo | Penilaian wilayah, extensible ke N |
| ADR-003 | Admin **mendaftarkan kejadian** yang benar-benar terjadi; data dummy boleh untuk simulasi demo | Istilah dan urutan proses jelas |
| ADR-004 | Petugas pendataan mengumpulkan kondisi, admin memverifikasi | Pisahkan data dan penilaian |
| ADR-005 | 3 DM: Kepala BPBD, Koordinator Lapangan, Dinas Sosial | GDSS kelompok dengan sudut pandang berbeda |
| ADR-006 | AHP per DM → TOPSIS per DM → Borda kelompok | Metode inti |
| ADR-007 | CR AHP ≤ 0.10; ketiga DM memakai snapshot sama | Konsistensi & fairness |
| ADR-008 | Borda: N sampai 1 poin; seri diputus lewat ranking Kepala BPBD (aturan prototipe, perlu validasi dosen) | Aturan seri eksplisit |
| ADR-009 | 6 kriteria C1–C6; C5 cost, lainnya benefit | Uji multi-kriteria, tanpa bias jarak = kebutuhan |
| ADR-010 | Rekomendasi saja, tidak melakukan distribusi otomatis | Batas produk dan safety |

## Open decisions / perlu validasi

Bahasa Python dan Flask dipertahankan. SQLite menjadi opsi lokal, PostgreSQL Supabase menjadi database target. Satu ronde penilaian simulasi lama masih tersedia melalui akun masing-masing aktor.

| ID | Item | Default sementara |
|---|---|---|
| OPEN-01 | Stack frontend/backend/DB | Jika repo kosong: TypeScript full-stack + relational DB; lihat arsitektur |
| OPEN-02 | Data kejadian demo yang digunakan | Semua seed fiktif (SIMULASI) |
| OPEN-03 | Format rubrik C2, C4 | Skala 1–5 rinci disetujui sebelum implementasi final |
| OPEN-04 | Rumus operasional kecukupan logistik C5 | Rasio paket-equivalent stok/kebutuhan periode seragam |
| CLOSED-05 | C6 versi sebelumnya berupa jam | Digantikan ADR-022; tidak berlaku untuk laporan baru |
| OPEN-06 | Status Kepala BPBD finalisasi | Hanya pengesahan laporan, tidak override matematis |
| OPEN-07 | Tie pada TOPSIS individual | Sort deterministic by alternative_code untuk presentation dan ranking unik; documented |
| OPEN-08 | Ketentuan dosen voting saat seri | Gunakan ranking DM1 sementara, konfirmasi jika ada aturan tertulis |
| OPEN-09 | Output ekspor | PDF/CSV opsional pasca MVP |

Jangan menyatakan open decision sebagai permintaan user yang sudah final. Jika agent perlu memilih demi kemajuan, dokumentasikan asumsi dan jadikan configurable.
