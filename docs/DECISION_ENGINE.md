# Decision Engine — Spesifikasi Matematis dan Validasi

## 0. Input
Untuk satu `assessment_round`: `alternatives[]` (>=2), `criteria[]` terurut C1..C6, matriks nilai `X[m][6]` finite (snapshot immutable), 3 DM dengan matriks AHP masing-masing. Arah `C1,C2,C3,C4,C6 = benefit`; `C5 = cost`.

## 1. AHP per decision maker
Input 15 nilai segitiga atas dari skala Saaty `{1,2,3,4,5,6,7,8,9}` dan kebalikannya `{1/2,...,1/9}`. Bangun `A[i][i]=1`, `A[j][i] = 1/A[i][j]`. Tolak 0, null, nilai di luar skala, dan matriks tak resiprokal.

Metode pembobotan MVP: **principal right eigenvector** dari matriks positif `A`, dihitung lewat power iteration dengan toleransi dan batas iterasi. Normalisasi bobot hingga `sum(w)=1`, `w_i>0`. Hitung `lambda_max` (mis. rata-rata `(Aw)_i/w_i`), `CI=(lambda_max-n)/(n-1)`, `CR=CI/RI`. Untuk `n=6`, `RI=1.24`. Terima bila `CR<=0.10` dengan toleransi floating-point kecil yang terdokumentasi; selain itu wajib revisi. Hindari menggabungkan pendekatan geometric mean dengan lambda dari metode eigen tanpa disadari. Simpan `algorithm_version`, bobot, lambda, CI, CR.

### Saran perbaikan konsistensi (tampilan saja)
`inconsistency_hints(comparisons)` dipanggil hanya bila CR > 0,10. Untuk setiap pasangan (i, j), nilai saran adalah skala Saaty terdekat (dalam skala log) dengan rasio bobot saat ini `w_i/w_j`. Pasangan diurutkan menurut CR bila hanya pasangan itu yang diganti (lalu indeks pasangan agar deterministik), dan maksimal tiga ditampilkan beserta perkiraan CR-nya. Fungsi ini tidak mengubah jawaban, bobot, maupun data tersimpan; DM tetap memutuskan sendiri.

### Fixture konsistensi
`examples/ahp_consistent_matrix.json`: semua perbandingan 1, `w=1/6` setiap kriteria, `lambda_max=6`, `CI=0`, `CR=0`.

## 2. TOPSIS per DM
Data `X` sama untuk 3 DM; hanya `w_DM` yang berbeda. Untuk setiap kriteria j:
- Normalisasi vektor `r_ij = x_ij / sqrt(sum_i x_ij^2)`; jika penyebut 0, **jangan divide by zero** — tandai kriteria tanpa variasi dan terapkan aturan yang konsisten (mis. set seluruh `r_ij=0` serta beri warning).
- `v_ij = w_j * r_ij`.
- Solusi ideal positif/negatif: benefit: `A+ = max(v_ij)`, `A- = min(v_ij)`; cost: **balik** (`A+ = min`, `A- = max`).
- `D_i+ = sqrt(sum_j(v_ij - A_j+)^2)`; `D_i- = sqrt(sum_j(v_ij - A_j-)^2)`.
- `CC_i = D_i- / (D_i+ + D_i-)`, dalam [0,1]. Semakin tinggi semakin prioritas.
- Jika dua jarak 0 karena seluruh alternatif identik, `CC=0.5` netral; beri warning degenerate data.
- Urut descending `CC`. Untuk nilai skor yang sama dalam tolerance, urut stabil berdasarkan alternative_code; simpan tanda tie numeric agar jelas ranking tie dinormalisasi untuk Borda.

**Penting:** Tipe cost pada C5 hanya memengaruhi solusi ideal TOPSIS, jangan membuat data negatif atau mengubah arah pada normalisasi.

## 3. Borda kelompok
Input tiga ranking individual yang mencakup **semua** alternatif tepat sekali. Untuk `m` alternatif, poin alternatif pada DM k = `m - rank_ik + 1`, rank dimulai 1. Total `B_i = sum_{k=1..3}(m-rank_ik+1)`. Urut descending total.

**Tie-break:** jika poin total sama, dahulukan alternatif dengan ranking **lebih tinggi pada DM Kepala BPBD** (DM1). Jika masih setara secara numerik (harusnya tak mungkin dengan ranking unik), gunakan kode alternatif sebagai pengurutan deterministic dan tandai seri. Semua DM memiliki **bobot voting setara**, bukan weighted Borda.

## 4. Input validity / audit
- Semua alternatif harus memiliki semua kriteria, sumber, dan verifikasi pada satu timestamp snapshot.
- Semua matriks AHP valid dan ber-CR ≤0.10; jangan agregasi sebagian 1–2 DM.
- Simpan rounding hanya untuk tampilan; **hitung dengan presisi penuh**.
- Simpan metode/versi, input hash/snapshot identifier, bobot per DM, trace TOPSIS (normalization, ideals, distances, CC), detail poin per DM, total Borda, waktu.
- AHP eigen power iteration: test no convergence; error eksplisit, bukan fallback diam-diam.

## 5. Test minimum
- AHP all ones menghasilkan uniform weights/CR=0.
- AHP resiprokal invalid ditolak; matriks inkonsisten CR>0.1 tidak bisa submit.
- TOPSIS nilai C5 rendah diprioritaskan bila kriteria lain sama.
- TOPSIS min/max benefit benar dan tidak NaN saat kolom nol.
- Borda contoh urutan dan total yang diketahui; ties menurut DM1.
- 3 DM menggunakan snapshot identik, hasil deterministic antar-run.
