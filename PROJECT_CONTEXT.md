# Project Context

## 1. Identitas
- **Judul akademik:** Implementasi Group Decision Support System (GDSS) Berbasis Web untuk Penentuan Prioritas Wilayah Penerima Bantuan Pascagempa Bumi.
- **Konteks:** proyek UAS Praktikum Information System, prototipe berbasis web.
- **Masalah:** wilayah terdampak membutuhkan logistik dasar yang berbeda-beda dan sumber daya bantuan terbatas; prioritas perlu dinilai oleh lebih dari satu pengambil keputusan.
- **Output:** **ranking rekomendasi kecamatan** dengan bukti perhitungan, bukan alokasi jumlah barang, rute kendaraan, atau perintah distribusi otomatis.
- **Lokasi geografis:** Indonesia; unit alternatif adalah **kecamatan**, terasosiasi dengan satu kejadian gempa.

## 2. Ruang lingkup bantuan
Pangan/air minum, selimut/pakaian/perlengkapan kebersihan, perlengkapan pengungsian sementara, perlengkapan kebutuhan dasar kelompok rentan. Ini **satu kategori payung logistik kebutuhan dasar**, bukan alternatif berbeda yang diranking.

## 3. Aktor dan pemisahan tanggung jawab
| Aktor | Tugas | Memberi bobot AHP? |
|---|---|---|
| Administrator/Koordinator Data | Mendaftarkan kejadian gempa **yang telah terjadi**, mengelola kasus dan daftar kecamatan, menugaskan petugas, memverifikasi laporan, membekukan dataset | Tidak |
| Petugas Pendataan Lapangan | Mencatat/memperbaiki hasil pendataan kecamatan yang ditugaskan, mencatat sumber/waktu; dapat mengusulkan kecamatan baru | Tidak |
| DM1 Kepala BPBD | Menilai kepentingan kriteria melalui AHP, meninjau hasil, finalisasi rekomendasi | Ya |
| DM2 Koordinator Tim Lapangan | Menilai kepentingan kriteria melalui AHP, meninjau hasil | Ya |
| DM3 Perwakilan Dinas Sosial | Menilai kepentingan kriteria melalui AHP, meninjau hasil | Ya |

Petugas mendata **fakta/observasi**, tiga DM menetapkan **bobot kepentingan**, sistem menghitung **ranking**. Jangan membuat DM memasukkan skor kecamatan sembarangan. Minimal akun demo: 1 admin, 1 petugas, 3 DM. Di dunia nyata, seseorang dapat memiliki banyak peran tetapi untuk demo pisahkan akun agar pengujian RBAC mudah.

## 4. Alur yang disepakati
Gempa terjadi → admin **mendaftarkan kejadian** berdasarkan sumber informasi → wilayah yang diduga terdampak diidentifikasi → admin menugaskan petugas → petugas mendata dan mengirim laporan per kecamatan → admin memvalidasi → dataset per ronde dikunci → 3 DM mengisi matriks AHP independen + CR → TOPSIS masing-masing DM → Borda agregasi peringkat → Kepala BPBD mengesahkan **rekomendasi** (bukan eksekusi bantuan).

## 5. Enam kriteria versi awal
| ID | Kriteria | Arah | Unit | Catatan |
|---|---|---|---|---|
| C1 | Jumlah pengungsi membutuhkan bantuan | benefit | orang | >= 0 |
| C2 | Tingkat kerusakan hunian | benefit | skor 1–5 | rubrik harus terdokumentasi |
| C3 | Proporsi pengungsi kelompok rentan | benefit | % | hitung dari jumlah rentan / pengungsi; 0 jika pengungsi 0 hanya saat konsisten |
| C4 | Tingkat gangguan fasilitas kebutuhan dasar | benefit | skor 1–5 | definisikan rubrik |
| C5 | Kecukupan logistik lokal | cost | % | hitung stok vs kebutuhan untuk periode sama; 0–100% untuk MVP |
| C6 | Jam sejak penerimaan logistik terakhir | benefit | jam | bagi yang belum pernah menerima, tetapkan acuan mulai pendataan pada kasus |

**Perhatian:** C6 bukan jarak ke posko. C5 adalah *cost* dalam preferensi keputusan, bukan harga logistik. Sumber pendataan dapat memuat data kasar; mesin ranking memakai enam nilai terverifikasi/diturunkan.

## 6. Non-goals
- Memprediksi gempa/tsunami atau memonitor BMKG real-time.
- Menyatakan megathrust pasti terjadi dalam waktu dekat.
- Mengoptimasi rute, inventaris gudang, anggaran pembelian, kuantitas paket atau alokasi kendaraan.
- Memutuskan keselamatan jiwa secara otomatis; kondisi kritis harus diekskalasi manusia.
- Mengklaim digunakan resmi oleh BPBD/BNPB.

## 7. Aturan transparansi
UI harus menampilkan sumber dan waktu pendataan, enam nilai input, bobot per DM, CR AHP, nilai TOPSIS, rank individual, poin Borda, aturan tie-break, waktu snapshot, dan status finalisasi. Angka seed = **data simulasi**.
