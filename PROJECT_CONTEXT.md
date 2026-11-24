# Project Context

## 1. Identitas
- **Judul akademik:** Implementasi Group Decision Support System (GDSS) Berbasis Web untuk Penentuan Prioritas Wilayah Penerima Bantuan Pascagempa Bumi.
- **Konteks:** proyek UAS Praktikum Information System, prototipe berbasis web.
- **Masalah:** wilayah terdampak membutuhkan logistik dasar yang berbeda-beda dan sumber daya bantuan terbatas; prioritas perlu dinilai oleh lebih dari satu pengambil keputusan.
- **Output:** **ranking rekomendasi kecamatan** dengan bukti perhitungan, bukan alokasi jumlah barang, rute kendaraan, atau perintah distribusi otomatis.
- **Lokasi geografis:** Malang Raya (Kabupaten Malang, Kota Malang, Kota Batu); unit alternatif adalah **kecamatan**, terasosiasi dengan satu kejadian gempa.

## 2. Ruang lingkup bantuan
Pangan/air minum, selimut/pakaian/perlengkapan kebersihan, perlengkapan pengungsian sementara, perlengkapan kebutuhan dasar kelompok rentan. Ini **satu kategori payung logistik kebutuhan dasar**, bukan alternatif berbeda yang diranking.

## 3. Aktor dan pemisahan tanggung jawab
| Aktor | Tugas | Memberi bobot AHP? |
|---|---|---|
| Kepala BPBD (`bpbd`) | Merangkap administrasi: mendaftarkan kejadian, menambahkan/menyetujui usulan kecamatan, penugasan koordinator, verifikasi laporan; sekaligus DM1 dan pengesahan rekomendasi | Ya, simulasi lama |
| Koordinator Lapangan (`lapangan`) | Merangkap pendataan: mengusulkan kecamatan, mencatat/memperbaiki observasi dan sumber laporan; sekaligus DM2 | Ya, simulasi lama |
| Perwakilan Dinas Sosial (`sosial`) | Membaca kondisi dan kebutuhan kecamatan serta laporan; sekaligus DM3 | Ya, simulasi lama |

Keputusan 20 November 2026 menetapkan tepat tiga peran login. Fungsi admin dilaksanakan Kepala BPBD dan fungsi petugas oleh Koordinator Lapangan. Fakta/observasi tetap dibedakan dari penilaian kepentingan. Usulan kecamatan dari koordinator perlu disetujui Kepala BPBD sebelum laporan dapat diverifikasi. Penugasan petugas versi lama tetap terbaca oleh peran Koordinator Lapangan tanpa menghapus riwayat.

Login menjadi halaman awal. Backend menyediakan PostgreSQL Supabase dan SQLite untuk uji lokal. Koneksi telah dikonfirmasi pengguna. Schema privat sibantu memiliki 14 tabel versi 6; role koneksi backend sibantu_app berbeda dari tiga peran pengguna. Kepala BPBD mengelola akun melalui /pengguna; setiap aktor mengganti password melalui /akun. Dashboard memetakan 41 kecamatan dan memiliki mode wilayah terdampak, status laporan, serta prioritas kelompok setelah ketiga aktor mengirim. Pengujian HTTP agent memakai SQLite sementara karena jaringan runtime masih dibatasi.

Permintaan 21 November 2026 menambahkan kasus fiktif GB-SIM-MLG-001 untuk Gedangan, Sumbermanjing Wetan, Dampit, dan Tirtoyudo. Empat laporan contoh disiapkan sebagai terverifikasi, dengan sumber/catatan SIMULASI, lalu snapshot awal dibekukan menjadi ronde 2. Setelah revisi C6, ronde 2 menjadi arsip dan ronde 3 memakai jarak kilometer. Penilaian aktor pada ronde baru dibiarkan kosong. Ronde per kejadian menyimpan ID/versi laporan; perubahan laporan dan ronde baru tidak memutasi hasil sebelumnya. Ronde simulasi lama tetap disimpan dan dapat dipilih.

**Revisi C6, 21 November 2026:** pengguna mengonfirmasi jarak posko induk ke titik gempa dalam kilometer, bertipe benefit. Form observasi dan ronde baru menggunakan versi 2.0. Laporan/ronde versi 1.0 tetap disimpan sebagai arsip; angka jam tidak dipindahkan menjadi kilometer. Rumus AHP/TOPSIS/Borda dipertahankan; penambahan MOORA/ELECTRE masih menunggu keputusan lanjutan.

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
| C6 | Jarak posko induk ke titik gempa | benefit | km | >= 0 dan finite; diisi dari sumber observasi, bukan konversi jam lama |

**Perhatian:** C6 baru adalah jarak posko induk ke titik gempa, sesuai keputusan pengguna. C5 adalah cost dalam preferensi keputusan, bukan harga logistik. Data C6 lama berbentuk jam hanya boleh tampil dalam arsip versi sebelumnya.

## 6. Non-goals
- Memprediksi gempa/tsunami atau memonitor BMKG real-time.
- Menyatakan megathrust pasti terjadi dalam waktu dekat.
- Mengoptimasi rute, inventaris gudang, anggaran pembelian, kuantitas paket atau alokasi kendaraan.
- Memutuskan keselamatan jiwa secara otomatis; kondisi kritis harus diekskalasi manusia.
- Mengklaim digunakan resmi oleh BPBD/BNPB.

## 7. Aturan transparansi
UI harus menampilkan sumber dan waktu pendataan, enam nilai input, bobot per DM, CR AHP, nilai TOPSIS, rank individual, poin Borda, aturan tie-break, waktu snapshot, dan status finalisasi. Angka seed = **data simulasi**.
