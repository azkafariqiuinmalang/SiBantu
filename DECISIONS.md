# Decision Log

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

Untuk tahap penilaian, bahasa Python mengikuti arahan pengguna. Implementasi demo lokal memakai Flask dan SQLite dengan satu ronde simulasi dan pemilih peran. Stack untuk fitur lain masih terbuka.

| ID | Item | Default sementara |
|---|---|---|
| OPEN-01 | Stack frontend/backend/DB | Jika repo kosong: TypeScript full-stack + relational DB; lihat arsitektur |
| OPEN-02 | Data kejadian demo yang digunakan | Semua seed fiktif (SIMULASI) |
| OPEN-03 | Format rubrik C2, C4 | Skala 1–5 rinci disetujui sebelum implementasi final |
| OPEN-04 | Rumus operasional kecukupan logistik C5 | Rasio paket-equivalent stok/kebutuhan periode seragam |
| OPEN-05 | Definisi C6 bila belum menerima bantuan | Jam sejak `assessment_baseline_at` |
| OPEN-06 | Status Kepala BPBD finalisasi | Hanya pengesahan laporan, tidak override matematis |
| OPEN-07 | Tie pada TOPSIS individual | Sort deterministic by alternative_code untuk presentation dan ranking unik; documented |
| OPEN-08 | Ketentuan dosen voting saat seri | Gunakan ranking DM1 sementara, konfirmasi jika ada aturan tertulis |
| OPEN-09 | Output ekspor | PDF/CSV opsional pasca MVP |

Jangan menyatakan open decision sebagai permintaan user yang sudah final. Jika agent perlu memilih demi kemajuan, dokumentasikan asumsi dan jadikan configurable.
