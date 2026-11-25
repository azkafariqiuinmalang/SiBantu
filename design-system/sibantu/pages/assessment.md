# Penilaian AHP bertahap

Revisi 21 November 2026, disetujui pengguna. Pertahankan Flask/Jinja dan CSS/JavaScript biasa serta identitas hijau SiBantu. Pencarian panduan UX "multi step form progress" menghasilkan kecocokan Feedback / Progress Indicators, Forms / Submit Feedback dan Accessibility / Form Labels untuk formulir web ini.

- Satu pasangan tampil per langkah, memakai nama kriteria lengkap. Gunakan radio native dalam fieldset dengan legend untuk pemilihan kriteria dan intensitas.
- Sama penting bernilai 1. Nilai utama 3/5/7/9 memakai bahasa verbal; nilai antara 2/4/6/8 berada dalam details/summary. Nilai resiprokal dihitung dari arah pilihan.
- Progres menyebut jumlah jawaban, posisi menyebut nomor pasangan. Ringkasan jawaban mengulang nama kriteria dan arah prioritas untuk mencegah salah interpretasi.
- Sebelumnya/Berikutnya mempertahankan isian tanpa menyimpan otomatis. Simpan draf selalu tersedia. Tinjauan menyediakan tombol Ubah per pasangan serta aksi cek konsistensi/kirim.
- Pindahkan fokus ke judul saat berpindah langkah dan ke kontrol yang perlu diisi saat validasi gagal. Gunakan indikator fokus, label terlihat, error dekat kontrol, serta target tombol minimal 44 piksel.
- Form biasa tetap tersedia tanpa JavaScript; penilaian terkirim/arsip tidak diubah menjadi formulir editable. Tidak ada dependensi/font/CDN baru.

Pengujian konversi JavaScript dan request Flask lulus. Pemeriksaan visual/interaksi browser masih belum terverifikasi.

## Alat bantu konsistensi (25 November 2026, ADR-026)

- Sebelum 15 pasangan, DM dapat mengurutkan C1–C6 dari yang paling penting dengan tombol Naik/Turun (bukan drag, agar dapat dipakai dengan keyboard). Tombol Lewati selalu tersedia; urutan disimpan di localStorage browser per ronde dan aktor, bukan di database.
- Setiap pasangan menampilkan catatan urutan. Bila arah pilihan berlawanan dengan urutan, muncul peringatan kuning tepat di bawah pilihan kriteria; peringatan tidak memblokir. Tinjauan jawaban menandai pasangan yang berlawanan.
- Bila CR > 0,10, panel Konsistensi AHP menampilkan maksimal tiga pasangan penyebab, pilihan saat ini, nilai yang lebih konsisten, perkiraan CR bila hanya pasangan itu diubah, dan tautan Ubah pasangan yang membuka langkah pasangan tersebut. Tanpa JavaScript, tautan menuju select pasangan.
- Tidak ada jawaban yang diisi atau diubah otomatis.

## Revisi UX (25 November 2026)

Audit sebagai penilai menemukan celah berikut; semuanya diperbaiki tanpa mengubah rumus atau data.

- **Panduan besar, bukan hanya arah:** setiap pasangan menampilkan perkiraan dari jawaban lain (a_ij ≈ a_ik × a_kj, rata-rata geometrik bila lebih dari satu dasar) dalam kalimat verbal. Bila pilihan berbeda sekitar empat kali lipat atau lebih dari perkiraan, muncul peringatan lunak. Tidak memblokir, tidak mengisi jawaban.
- **Satu panduan per pasangan:** bila cek konsistensi memberi saran untuk pasangan tersebut dan jawabannya belum diubah, saran server menggantikan perkiraan lokal agar tidak bertentangan.
- **Bahasa verbal:** saran CR memakai istilah yang sama dengan form (sedikit/kuat/sangat/mutlak lebih penting; nilai antara disebut rentangnya), dengan skala dalam kurung.
- **Saran di tempat bertindak:** pasangan yang disarankan ditandai langsung di daftar Tinjau jawaban (penting di ponsel, karena panel samping berada di bawah). Pesan error CR memiliki tautan Lihat saran pasangan.
- **Kembali ke tinjauan:** Ubah dari tinjauan atau tautan saran membuka pasangan dengan tombol Kembali ke tinjauan, bukan Berikutnya.
- **Cegah kehilangan jawaban:** catatan Ada perubahan yang belum disimpan dan konfirmasi browser saat meninggalkan halaman sebelum Simpan draf/Kirim.
- **Header menempel:** target gulir/tautan memakai scroll-margin agar tidak tertutup header.

