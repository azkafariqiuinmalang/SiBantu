# Penilaian AHP bertahap

Revisi 21 November 2026, disetujui pengguna. Pertahankan Flask/Jinja dan CSS/JavaScript biasa serta identitas hijau SiBantu. Pencarian panduan UX "multi step form progress" menghasilkan kecocokan Feedback / Progress Indicators, Forms / Submit Feedback dan Accessibility / Form Labels untuk formulir web ini.

- Satu pasangan tampil per langkah, memakai nama kriteria lengkap. Gunakan radio native dalam fieldset dengan legend untuk pemilihan kriteria dan intensitas.
- Sama penting bernilai 1. Nilai utama 3/5/7/9 memakai bahasa verbal; nilai antara 2/4/6/8 berada dalam details/summary. Nilai resiprokal dihitung dari arah pilihan.
- Progres menyebut jumlah jawaban, posisi menyebut nomor pasangan. Ringkasan jawaban mengulang nama kriteria dan arah prioritas untuk mencegah salah interpretasi.
- Sebelumnya/Berikutnya mempertahankan isian tanpa menyimpan otomatis. Simpan draf selalu tersedia. Tinjauan menyediakan tombol Ubah per pasangan serta aksi cek konsistensi/kirim.
- Pindahkan fokus ke judul saat berpindah langkah dan ke kontrol yang perlu diisi saat validasi gagal. Gunakan indikator fokus, label terlihat, error dekat kontrol, serta target tombol minimal 44 piksel.
- Form biasa tetap tersedia tanpa JavaScript; penilaian terkirim/arsip tidak diubah menjadi formulir editable. Tidak ada dependensi/font/CDN baru.

Pengujian konversi JavaScript dan request Flask lulus. Pemeriksaan visual/interaksi browser masih belum terverifikasi.
