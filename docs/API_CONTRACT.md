# API Contract (Proposed REST Semantics)

**Not committed to REST vs server actions**; these are contractual responsibilities implementable by either approach. All writes require authenticated server-side RBAC and validation. IDs are opaque. Errors consistently structured `{code,message,details?}`; no stack traces to client.

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/api/cases` | ADMIN | Daftarkan kejadian |
| GET | `/api/cases` | ALL | Daftar kasus berizin |
| PATCH | `/api/cases/:id` | ADMIN | Edit sebelum lock/ikuti rules |
| POST | `/api/cases/:id/districts` | ADMIN | Daftar kecamatan awal |
| POST | `/api/cases/:id/assignments` | ADMIN | Tugaskan petugas |
| GET | `/api/assignments/me` | FIELD_OFFICER | Tugas sendiri |
| POST | `/api/districts/:id/reports` | FIELD_OFFICER | Buat draft pendataan |
| PATCH | `/api/reports/:id` | OWNER OFFICER | Edit draft/rejected |
| POST | `/api/reports/:id/submit` | OWNER OFFICER | Kirim verifikasi |
| POST | `/api/reports/:id/review` | ADMIN | Verify/reject + alasan |
| POST | `/api/cases/:id/rounds` | ADMIN | Buat snapshot & lock |
| GET | `/api/rounds/:id/snapshot` | ADMIN/DM | Data dasar penilaian |
| PUT | `/api/rounds/:id/ahp/me` | ASSIGNED DM | Simpan 15 comparisons draft |
| GET | `/api/rounds/:id/ahp/me/preview` | ASSIGNED DM | Bobot, CI, CR preview |
| POST | `/api/rounds/:id/ahp/me/submit` | ASSIGNED DM | Submit AHP valid |
| GET | `/api/rounds/:id/topsis/me` | ASSIGNED DM | Ranking individual |
| POST | `/api/rounds/:id/aggregate` | ADMIN/SYSTEM | Agregasi Borda setelah 3 selesai |
| GET | `/api/rounds/:id/results` | AUTHORIZED | Rincian agregasi |
| POST | `/api/rounds/:id/finalize` | BPBD_HEAD | Pengesahan rekomendasi |

## Example payloads
```json
{
  "case_name": "Gempa Kabupaten X (SIMULASI)",
  "incident_at": "2026-11-14T00:00:00+07:00",
  "province": "Jawa Timur",
  "regency": "Kabupaten X",
  "information_source": "Data fiktif untuk UAS",
  "is_simulation": true
}
```

Example pairwise AHP submission structure:
```json
{
  "comparisons": [
    {"criterion_i":"C1","criterion_j":"C2","value":3},
    {"criterion_i":"C1","criterion_j":"C3","value":1}
  ]
}
```
Example abbreviated; **production requires all 15 distinct comparisons**. Server derives reciprocal values, not trusting client-provided mirror pairs.

## HTTP failure guide
400 invalid data/scale; 401 unauthenticated; 403 forbidden; 404 not found/not visible; 409 invalid state, stale version or changed snapshot; 422 CR > 0.10/missing criteria; 500 sanitized unexpected error.
