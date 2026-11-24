# AGENTS.md — Instruksi untuk AI Coding Agent

## Prioritas sumber
1. User instruction terbaru di chat.
2. `PROJECT_CONTEXT.md`, `PRD.md`, `DECISIONS.md`.
3. `docs/DECISION_ENGINE.md` untuk detail metode; `docs/WORKFLOWS.md` untuk siklus status.
4. Pola implementasi di repo yang ada.

## Cara bekerja
- Mulai dengan inspeksi repo, dependency, skema database, dan test. Ringkas temuan lalu usulkan urutan perubahan kecil.
- Jangan langsung membuat UI dummy tanpa wiring ke domain/backend. Jangan memakai skor ranking hardcoded di production code.
- Lakukan *vertical slices* dan tulis/memperbarui test pada tiap modul.
- Pisahkan pure decision engine dari UI dan DB; hasil kalkulasi deterministic, reproducible, tidak menyembunyikan formula.
- Gunakan migration/schema versioning, validation server-side, transaksi atomic, audit perubahan data.
- Gunakan Bahasa Indonesia untuk UI, English atau Bahasa Indonesia yang konsisten pada simbol kode.
- Jika memilih stack baru, dokumentasikan sebagai keputusan di `DECISIONS.md`, jangan mengklaim pilihan user.
- Tidak boleh menghapus data, merombak stack, atau mengubah spesifikasi metode tanpa konfirmasi/penjelasan.

## Business invariants (tidak boleh dilanggar)
- Pembaruan 20 November 2026: tiga role login `bpbd`, `lapangan`, `sosial`; admin adalah tugas Kepala BPBD dan pendataan adalah tugas Koordinator Lapangan. Seluruh halaman internal memerlukan login.
- Revisi 21 November 2026: C6 sudah disetujui menjadi jarak posko induk ke titik gempa (km), benefit. Gunakan criteria_version/algorithm_version 2.0 untuk laporan/ronde baru. Jam versi 1.0 tidak boleh dikonversi atau dilabeli sebagai kilometer. Perubahan metode lainnya masih ditunda.
- Koordinator melihat Tugas saya, bukan daftar administrasi kejadian. Form observasi menggunakan kalender/jam WIB. Ronde versi 1.0 menjadi arsip baca-saja; data dan hasilnya tetap disimpan.
- Permintaan 21 November 2026: simulasi empat kecamatan Gedangan, Sumbermanjing Wetan, Dampit, Tirtoyudo sudah diisi. Data lapangan fiktif boleh disiapkan; penilaian DM harus tetap diisi sendiri. Gunakan decision_rounds/round_assessments untuk ronde per kejadian; tabel legacy dipertahankan. Jangan mereset data/hasil ronde lama ketika membuat simulasi atau ronde baru.
- **Kejadian gempa harus sudah terjadi / diketahui** untuk didaftarkan; bukan fitur prediksi.
- Admin mendaftarkan kejadian → pendataan per kecamatan → admin verifikasi → snapshot locked → 3 DM AHP → 3 TOPSIS → Borda → finalisasi.
- Data lapangan dinilai petugas/koordinator; DM **menilai kepentingan kriteria**, bukan mengarang nilai kondisi wilayah.
- Kriteria standar C1..C6 sesuai `PROJECT_CONTEXT.md`; C5 cost, lainnya benefit.
- AHP matrix resiprokal, CR valid ≤ 0.10; tetap tangani kasus eigenvalue, zero division, dan precision.
- Ranking TOPSIS setiap DM menggunakan **snapshot sama + bobot DM sendiri**.
- Borda N..1 dari peringkat 1..N; 3 DM setara, peringkat Kepala BPBD hanya tie-break bila seri.
- Jangan finalisasi bila data/DM tidak lengkap; ronde lama tak boleh dimutasi.
- Data seed fiktif diberi watermark/label SIMULASI.
- Hasil rekomendasi bukan instruksi penyaluran otomatis.

## Engineering conventions
- Nama domain eksplisit: `disasterCase`, `district`, `assessmentRound`, `fieldReport`, `pairwiseComparison`, `decisionMaker`, `topsisResult`, `bordaResult`.
- Jangan hanya menyimpan ranking; simpan input & versi algoritma, trace agar dapat dihitung ulang.
- Gunakan types/schema bersama frontend dan backend bila mungkin.
- Backend menegakkan otorisasi walau tombol UI tersembunyi.
- Endpoint dan aksi mutasi perlu validasi peran, kepemilikan, status, serta constraint.
- Operasi update menghindari lost update (optimistic lock/version) jika diperlukan.
- Jangan menyimpan detail pribadi pengungsi; agregat per kecamatan saja.

## Definition of done tiap fitur
Kebutuhan diterapkan, input salah ditolak, unauthorized ditolak, valid state transition, test pass, UI error/success states bekerja, dokumentasi diubah, dan tidak mengubah hasil round terkunci.

## Larangan overengineering
Tidak perlu AI/LLM, model prediksi gempa, integrasi BMKG real time, routing, inventaris gudang kompleks, distribusi otomatis, multi-tenant enterprise atau microservice. Peta status pendataan per kecamatan Malang Raya sudah masuk lingkup atas permintaan pengguna.

## Format laporan kerja agent
Setelah satu perubahan: `Diubah`, `Alasan`, `Pengujian`, `Risiko/keputusan tertunda`, `Cara menjalankan`. Jangan mengklaim test pass bila tidak dieksekusi.
