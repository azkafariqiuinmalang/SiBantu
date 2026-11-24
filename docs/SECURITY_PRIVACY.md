# Security, Privacy, Audit

## Auth & role authorization
- Implementasi 20 November 2026 memakai hash scrypt Werkzeug, cookie HTTPOnly/SameSite=Lax, CSRF dan pembatasan percobaan login. COOKIE_SECURE diaktifkan saat hosting HTTPS.
- RBAC server mempunyai tiga role: `bpbd`, `lapangan`, `sosial`. Tugas admin dijalankan Kepala BPBD dan pendataan oleh Koordinator Lapangan. Pengguna tidak dapat mengganti role melalui payload/session.
- Hanya Kepala BPBD mengelola akun melalui /pengguna. Akun sendiri tidak dapat dinonaktifkan. Perubahan password/status menaikkan session_version; cookie versi lama ditolak pada request berikutnya. Halaman /akun memverifikasi password lama dan konfirmasi password baru.
- Koordinator mengubah laporan penugasan lapangan; setiap DM hanya mengubah penilaiannya sendiri; finalisasi hanya oleh Kepala BPBD.
- Database memakai schema privat sibantu, dengan akses schema ditolak bagi anon/authenticated. Backend memakai role sibantu_app. Tabel mengaktifkan RLS tanpa policy untuk klien non-owner; backend adalah pemilik tabel dan menegakkan RBAC Flask. Ini menghasilkan INFO advisor RLS tanpa policy, bukan akses publik. [Rincian advisor](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy).
- File .env, instance/session.key, dan kredensial akun awal pada instance/ tidak masuk Git. Kata sandi asli tidak disimpan di tabel audit atau cookie sesi. Respons halaman internal menggunakan Cache-Control private/no-store.
- Least privilege, server-side ownership checks, input schema checks, SQL parameterization or ORM.

## Data handling
- Aggregate kecamatan data only. No names, IDs, health data, addresses of individual evacuees.
- Mark synthetic scenarios as `is_simulation=true` throughout UI, exports, audit; never present demo as real emergency data.
- Track data provenance (`source_note`, `observed_at`, author, approval) and algorithm version.
- Verify field data before decision; immutable snapshots defend against retroactive manipulation.

## Integrity and audit
- Append-only audit actions: create/update/report submit/review/lock/submit AHP/aggregate/finalize/cancel.
- Atomic transactions for lock and aggregate; unique per DM per round, unique result per district.
- Reject stale writes and attempts to modify finalized round; access to audit only privileged user.

## Safety boundary
- Decision output = recommendation, not real-time operational command.
- Label urgent protection/medical rescue issues as requiring immediate human escalation outside routine ranking.
- Megathrust risk never treated as an impending prediction.
