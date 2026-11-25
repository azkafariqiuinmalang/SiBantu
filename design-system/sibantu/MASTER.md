# SiBantu — Design System Master ("Lembar Survei")

Revisi 25 November 2026 (ADR-027, palet direvisi ADR-028), menggantikan tema gelap "Pusat Kendali" (ADR-025). Halaman pada `pages/` menimpa aturan di sini bila berbeda.

## Arah visual
- Tema terang seperti lembar survei lapangan: kertas abu dingin, tinta biru-hitam, garis tipis sebagai struktur. Permukaan dan kontrol mengikuti tema **Furrow** dari skill Hallmark (deal 2/3). Palet manila-oranye bawaan Furrow diganti atas permintaan pengguna karena terlalu mirip warna Claude (ADR-028).
- **Satu sinyal**, yaitu biru petrol `--accent`. Warna ini selalu berupa isian dengan teks putih, dan versi lembutnya (`--accent-soft`) dipakai dengan teks tinta. Sinyal hanya untuk aksi utama, tab aktif, pilihan yang sedang dipilih, dan garis kecamatan terpilih di peta.
- Status memakai warna semantik dengan nada redup (hijau, merah bata, oker, biru batu, ungu abu). Setiap status selalu berteks.
- Bagian yang paling dikenali (*signature*) adalah peta kecamatan berupa lembar survei bergrid. Kecamatan yang dipilih terbuka sebagai **kartu catatan lapangan**: kepala tinta, baris nilai di atas grid 8px, dan bayangan angkat.
- Pola gaya "dashboard AI" yang dihapus: latar navy dengan radial glow, kartu KPI berikon dan bergaris warna, gauge setengah lingkaran, titik status dekoratif, label mono kapital berspasi (eyebrow), cahaya merah berdenyut di halaman login, heading dua warna, dan panah yang menempel di teks tautan.

## Token (static/theme.css)
| Token | Nilai | Pakai |
|---|---|---|
| `--page` / `--panel` | #edf3f4 / #fbfefe | kertas, lembar |
| `--panel-2` / `--panel-3` | #e0e8ea / #d2dde0 | hover, nilai terkunci |
| `--line` / `--line-strong` | #d0d9dc / #a4b0b5 | garis antarbaris, border tombol sekunder |
| `--text` / `--muted` | #0b151f / #4c5760 | tinta, teks sekunder (6,6:1 pada kertas) |
| `--accent` / `--accent-soft` | #006065 / #cbecee | isian aksi utama dengan teks putih (7,3:1), pilihan lembut dengan teks tinta |
| `--focus` | #3a61c4 | cincin fokus 2px (5,1:1 pada kertas) |
| `--ok`, `--critical`, `--warning`, `--info`, `--pending` | lihat theme.css | teks status di atas latar lembut masing-masing (≥ 5,4:1) |
| `--map-*` | lihat theme.css | warna kanvas peta; dibaca `malang-map.js` lewat `getComputedStyle` |
| `--font-sans` / `--font-display` | Segoe UI Variable / system-ui | teks, judul |
| `--font-mono` | Cascadia Mono / Consolas | hanya angka, kode, dan waktu; tidak pernah untuk label |

Tanpa font/CDN eksternal (ADR-025 tetap berlaku). Red Hat milik Furrow tidak dimuat. Semua warna di CSS lain memakai `var()`, tidak ada hex di luar blok token.

## Pola komponen
- **Logo**: "Tangan yang Menjadi Atap" (`static/img/logo/`, filosofi di `FILOSOFI_LOGO.md`). Ikon 40px di bilah atas dan 56px di login, `alt=""` karena nama SiBantu sudah ada pada teks tautan; favicon SVG dan apple-touch-icon dipasang di semua halaman.
- **Bilah atas**: logo, wordmark SiBantu ("Si" petrol) dengan keterangan biasa, jam WIB (`data-clock`), nama akun dan peran, tombol Keluar. Tab tanpa ikon; tab aktif berupa isian petrol. Garis tinta 1px di bawah header.
- **Buku angka** (`.ledger`): empat sel dalam satu baris bergaris tinta di atas. Isinya label biasa, angka mono tabular, dan keterangan sumber. Tanpa ikon dan tanpa warna nada.
- **Peta**: lembar bergrid 32px, wilayah berwarna abu kertas dengan tepi abu-biru. Wilayah terdampak berwarna merah bata, prioritas Borda bergradasi dari merah tua ke merah muda, dan kecamatan terpilih bergaris petrol dengan halo putih. Label peta bertinta dengan halo kertas.
- **Progres keputusan**: angka `n/3` dan daftar aktor bergaris. Status "Sudah mengirim" ditandai chip hijau.
- **Tabel**: kepala tabel sentence case dengan garis tinta, garis horizontal saja. Baris peringkat 1 berlatar `--accent-soft`.
- **Login**: kolom kiri berisi satu foto Tugu Kota Malang setinggi layar (full-bleed) dengan label tinta. Kolom kanan berisi judul, form, dan kredit foto (`static/img/SUMBER_FOTO.md`). Di ponsel, foto menjadi banner 14rem di atas form.
- **Kartu tugas koordinator**: kepala tinta berisi kode kejadian (mono) dan badge Simulasi, dengan tombol aksi di kaki kartu.
- **Tombol**: tombol utama berupa isian petrol dengan sorotan tipis dan turun 1px saat ditekan. Tombol sekunder putih bergaris. Tombol disabled memakai tiga penanda (isian, tinta, kursor) ditambah atribut `disabled`. Jawaban AHP yang terkunci tetap terbaca (latar `--panel-2`, border putus-putus).

## Aksesibilitas & interaksi
Skip link, fokus `:focus-visible` 2px `--focus`, target ≥ 44px pada kontrol peta dan aksi, input 16px di mobile, `prefers-reduced-motion` mematikan transisi, `overflow-x: clip` pada html/body, tanpa scroll horizontal pada 375px (diverifikasi di browser 25 November 2026).

## Catatan Hallmark
Stamp, kritik pra-rilis, dan waiver ada di baris pertama `static/theme.css`. Sloplint menandai `focus-visible`/`overflow-x` per template karena tidak membaca stylesheet yang dimuat lewat `url_for`. Temuan ini dicatat sebagai *dismissed* di stamp.
