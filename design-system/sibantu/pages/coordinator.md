# Pendataan Koordinator Lapangan

Revisi 21 November 2026. Stack dipertahankan: Flask/Jinja, CSS dan JavaScript biasa. Arahan visual mengikuti hasil pencarian yang relevan: Minimalism & Swiss Style untuk dashboard, serta Forms / Inline Validation, Focusable Error Summary dan Submit Feedback untuk formulir web.

- Pertahankan identitas hijau SiBantu. Gunakan permukaan putih, latar hijau keabu-abuan, garis batas tenang dan hierarki teks yang jelas. Tidak menambah font/CDN atau paket UI.
- Konten utama Koordinator adalah Tugas saya. Daftar dan pendaftaran kejadian berada pada peran yang sesuai; Koordinator tidak memperoleh formulir pendaftaran kejadian.
- Kartu tugas menyebut nama kecamatan, kejadian, kode, status teks, versi, dan satu tindakan utama. Pencarian/status memfilter kartu tanpa mengubah data.
- Formulir dibagi menjadi identitas observasi, dampak penduduk, kondisi wilayah, serta logistik dan jarak. Semua kontrol mempunyai label; bantuan dan error tersambung melalui aria-describedby.
- Observasi memakai datetime-local dengan WIB dan batas sebelum kejadian/masa depan. C6 berupa jarak kilometer bertipe benefit. Tidak ada input jam sejak bantuan terakhir.
- Draf boleh belum lengkap, pengiriman memerlukan data lengkap. Error server ditampilkan dekat kolom dan dalam ringkasan yang mendapat fokus. Tombol pengiriman mempunyai umpan balik dan pencegahan kirim ganda.
- Sasaran tombol/kontrol setidaknya 44 piksel, focus ring terlihat, nilai turunan memakai angka tabular. Warna status selalu dilengkapi teks.
- Grid turun menjadi satu kolom pada layar sempit. Input mobile 16px. Hindari overlay yang menutupi fokus dan hormati prefers-reduced-motion.

Validasi request diuji dengan Flask test client. Pemeriksaan visual browser dan ukuran viewport sesungguhnya belum dapat dijalankan pada lingkungan agent yang membatasi proses browser.
