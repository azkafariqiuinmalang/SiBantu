# UX Pages and Role Views

## Rute yang sudah diimplementasikan (20 November 2026)

| Rute | Aktor | Fungsi |
|---|---|---|
| /login | Belum masuk | Form email dan password |
| /dashboard | Ketiga aktor | Peta 41 kecamatan, status pendataan, filter kejadian dan wilayah |
| /pendataan | Ketiga aktor | BPBD mengelola kejadian; Koordinator melihat kartu Tugas saya dengan pencarian/filter tanpa daftar administrasi kejadian |
| /pendataan/kejadian/:id | Ketiga aktor | Daftar kecamatan dan laporan; penambahan/penugasan/persetujuan sesuai role |
| /pendataan/tugas/:id | Koordinator Lapangan | Form berkelompok, kalender/jam WIB, C6 jarak km, pratinjau C3/C5, draf parsial dan pengiriman; error dekat kolom |
| /pendataan/laporan/:id | Ketiga aktor | Membaca laporan; verifikasi/penolakan oleh BPBD |
| /pengguna | Kepala BPBD | Pembuatan/status/reset password akun dan aktivitas akun |
| /akun | Ketiga aktor | Mengganti password sendiri |
| /penilaian/:role | Aktor sesuai role | Simulasi penilaian lama, perubahan metode ditunda |
| /hasil | Ketiga aktor | Hasil kelompok simulasi lama |

Bagian sitemap di bawah merupakan rancangan awal untuk pengembangan ronde dan bukan daftar endpoint yang sudah tersedia.

## Sitemap
| Route (suggested) | Users | Main UI |
|---|---|---|
| `/login` | anonymous | Sign-in, validation |
| `/dashboard` | all authorized | Role-specific overview, task/status |
| `/cases` | admin, DM | Cases with simulation label |
| `/cases/:id` | authorized | Incident summary, district counts, source and status |
| `/cases/:id/districts` | admin | Manage list and assignments |
| `/my-assignments` | officer | Assigned districts and due status |
| `/reports/:id/edit` | assigned officer | Condition & provenance form, submit |
| `/reports/review` | admin | Verify/reject checklist with reason |
| `/rounds/:id` | admin, DM | Snapshot data, DM progress |
| `/rounds/:id/ahp` | assigned DM | 15 comparisons, weights, CR preview, submit |
| `/rounds/:id/my-ranking` | assigned DM | TOPSIS score + rank |
| `/rounds/:id/group-results` | admin, DM | Borda breakdown, tie information, result history |

## Usability requirements
- Stepper with domain stages: registered → collection → verified → assessment → recommendation.
- Label fields with unit and help text for 1–5 rubrics.
- AHP UI: implemented one pair at a time for all three decision makers. First choose the criterion by full name or equal importance, then select verbal intensity 3/5/7/9; expand intermediate values 2/4/6/8 when needed. Show answered progress, previous/next, and an editable review before consistency check/submission. Draft saving is explicit; navigation alone does not save to the database. Reciprocal values are automatic, and user choices are never changed automatically to improve CR. Submitted and legacy assessments stay read-only. Native selects remain as the no-JavaScript fallback.
- Snapshot date/time prominent to prevent mistaken "live" interpretation.
- Display explanatory table: each district, C1..C6, sources; per DM weight, CR, TOPSIS coefficient/rank; Borda points and final rank.
- Use neutral professional styling; accessibility: keyboard, contrast, labels, error messages.
- Charts/maps optional, never replace numeric text results.
- Visible 'SIMULASI — bukan data kejadian nyata' if is_simulation true.
