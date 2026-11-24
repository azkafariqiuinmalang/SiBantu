# Batas kecamatan Malang Raya

`malang_raya.geojson` memuat 41 fitur Polygon/MultiPolygon: 33 kecamatan Kabupaten Malang, 5 Kota Malang, dan 3 Kota Batu. Geometri dipakai untuk visualisasi prototipe dan bukan penetapan batas administrasi resmi. Kode adalah pengenal katalog dari ekspor sumber, belum diverifikasi terhadap register administrasi resmi terbaru.

Sumber ekspor: https://github.com/aaronsanger/idn-geojson, tiga berkas berikut.

| Berkas sumber | Git blob SHA |
|---|---|
| districts/35_07.geojson | a4a79435a06218824de1f301055d99e885bb898f |
| districts/35_73.geojson | ca891cd46557d50838ec4e549a9280135a00ff4d |
| districts/35_79.geojson | 735edc7d1a019ef06ea4d386391d35043971b875 |

Fitur yang dipakai mencantumkan `cahyadsn` sebagai sumber. Proyek sumber: https://github.com/cahyadsn/wilayah_boundaries. README ekspor mengingatkan bahwa pengekspor bukan pengumpul asli dan pengguna perlu mengecek sumber/lisensi tiap data.

Transformasi lokal hanya menggabungkan ketiga koleksi dan menormalkan properti menjadi `code`, `name`, `regency`, `regency_code`. Koordinat geometri dipertahankan. Warna peta berasal dari status laporan di database, tanpa interpolasi tingkat bahaya atau ranking. Tidak ada data gempa nyata yang ditambahkan pada geometri.

## Lisensi sumber Cahya DSN

MIT License

Copyright (c) 2024 Cahya DSN

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
