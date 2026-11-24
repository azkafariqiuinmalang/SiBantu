# SiBantu — Design System Master ("Pusat Kendali")

Revisi 24 November 2026, mengikuti referensi visual dashboard pusat komando bencana yang dikirim pengguna. Halaman pada `pages/` menimpa aturan di sini bila berbeda.

## Arah visual
- Tema gelap "pusat kendali" (navy-slate), kepadatan tinggi ala dashboard operasi. Identitas hijau SiBantu tetap menjadi warna aksi utama.
- Rekomendasi skill ui-ux-pro-max (`disaster emergency command center dashboard dark`, density 8): gaya **Accessible & Ethical** (pemerintahan/publik), merah sebagai sinyal kritis, pasangan tipografi sans + mono untuk data. Palet merah/latar terang dari hasil pencarian tidak dipakai mentah karena bertentangan dengan identitas hijau dan tema gelap referensi.
- Tidak ada "AI confidence" atau skor fiktif. Gauge menampilkan progres nyata 0–3 aktor; tabel prioritas hanya berisi peringkat Borda dari ronde aktual.

## Token (static/theme.css)
| Token | Nilai | Pakai |
|---|---|---|
| `--page` / `--panel` / `--panel-2` | #0a1017 / #101922 / #142030 | latar, kartu, input |
| `--line` / `--line-strong` | #22313f / #31465a | garis, border kontrol |
| `--text` / `--muted` | #e6edf3 / #9aabbb | teks utama / sekunder (≥ 4.5:1 pada panel) |
| `--accent` | #22c55e (teks gelap #04140a di atasnya) | tombol utama, tab aktif, progres |
| `--critical` | #f43f5e | wilayah terdampak, peringkat 1, error |
| `--warning` | #f59e0b | SIMULASI, menunggu verifikasi |
| `--info` | #38bdf8 | menunggu laporan/draf |
| `--font-sans` | Segoe UI Variable / system-ui | teks |
| `--font-mono` | Cascadia Mono / Consolas | angka, kode, label eyebrow, jam |

Tanpa font/CDN eksternal (ADR-025); angka memakai `tabular-nums`.

## Pola komponen
- **Header**: tanda perisai, eyebrow mono "BPBD · Malang Raya / Pusat Kendali Keputusan", jam WIB langsung (`static/shell.js`), avatar inisial, tombol keluar; baris tab berikon SVG dengan `aria-current`.
- **KPI**: 4 kartu, garis aksen kiri berwarna nada, ikon dalam kotak tint, angka mono besar, keterangan sumber angka.
- **Peta**: kanvas di atas grid halus, kontrol zoom vertikal 44px di kanan, label "Batas kecamatan / geometri lokal", strip "Indeks peta" di bawah. Wilayah terdampak merah transparan + glow; terpilih bergaris hijau.
- **Panel samping**: gauge progres keputusan + daftar aktor; umpan status wilayah terdampak (ikon + chip status).
- **Tabel prioritas**: Peringkat mono 01..N, baris peringkat 1 bergradasi merah, chip status, tombol "Lihat di peta".
- **Chip status** selalu berteks dengan titik warna — warna tidak pernah satu-satunya penanda.

## Aksesibilitas & interaksi
Skip link, focus ring 3px `--focus`, target ≥ 44px pada kontrol peta/aksi, input 16px di mobile, `prefers-reduced-motion` mematikan transisi/animasi, tanpa scroll horizontal pada 375px (diverifikasi di browser).
