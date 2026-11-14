# Implementation Plan (Sprints/Fases)

## Fase 0 — Discovery & setup
- Inspect current repo. Decide stack in `DECISIONS.md`; set tooling, lint, tests, local DB, migrations, sample env.
- Translate PRD into issues with acceptance criteria. Do **not** delete user files.

## Fase 1 — Domain & data workflow
- Auth, RBAC, users, cases, kecamatan, assignment.
- Field reports with source/time, C3/C5 derivation, submit/review/reject.
- Integration tests for ownership, validation, transitions.

## Fase 2 — Rounds & decision engine
- Snapshot locking; round state and immutability.
- Implement AHP as pure function with fixtures and CR rejection.
- Implement TOPSIS as pure function with benefit/cost, edge cases and verification.
- Implement Borda and tie-break + automated checks.

## Fase 3 — Decision UX and group result
- AHP matrix UX with 15 pairs and live CR feedback.
- DM rankings, admin completeness dashboard, Borda results, audit trail, finalization.
- Show method trace without overwhelming normal users (expandable details).

## Fase 4 — QA & delivery
- Seed 1 fictional case / 5 districts / 5 users; E2E/UAT.
- Confirm responsiveness, accessibility, no unexpected role escalation.
- README update with install/env/migrate/seed/run/test and demo account setup (do not publish real credentials).
- Capture screenshots, prepare report with limitations.

## Excluded until after MVP
Maps, BMKG integrations, export PDF/CSV, notification delivery, real-time data, warehouse/inventory control, relief allocation optimization, predictions.

## Agent work-request template
```markdown
Task:
Scope / acceptance criteria:
Files/modules expected:
Tests required:
Out-of-scope:
Known assumptions:
```
