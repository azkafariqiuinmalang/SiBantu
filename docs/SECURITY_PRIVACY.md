# Security, Privacy, Audit

## Auth & role authorization
- Store hashed passwords (Argon2id/bcrypt), secure session cookies, CSRF protection for cookie-based mutation, sensible rate limit for login.
- Enforce RBAC **server-side**: ADMIN, FIELD_OFFICER, BPBD_HEAD, FIELD_COORDINATOR_DM, SOCIAL_SERVICES_DM.
- `FIELD_OFFICER` update only own assigned district reports; `DM` compare own pairwise matrix only; BPBD_HEAD finalization only; users can't switch role in payload.
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
