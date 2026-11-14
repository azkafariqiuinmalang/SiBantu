# Progres Pengembangan SiBantu

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
