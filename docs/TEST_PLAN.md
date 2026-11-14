# Test Plan and Acceptance Scenarios

## Test tiers
1. **Unit:** pure AHP, TOPSIS, Borda, input derivations.
2. **Integration:** permissions, persistence, status transition, snapshot and computation.
3. **E2E:** admin → field officer → admin → 3 DM → group outcome → BPBD finalization.
4. **Review/UAT:** manual comparison with independently calculated spreadsheet/matrix, user comprehensibility.

## Math tests
| ID | Test | Expected |
|---|---|---|
| M01 | AHP all-ones 6x6 | w=1/6, lambda≈6, CR≈0 |
| M02 | Invalid AHP scales, missing pairs, nonreciprocal construction | reject or correct reciprocal server-side |
| M03 | Highly inconsistent AHP | CR>0.10; cannot submit |
| M04 | TOPSIS cost criterion C5 lower is better (other scores same) | lower C5 ranked higher |
| M05 | TOPSIS monotonic benefit scenario | larger relevant benefit can improve score |
| M06 | All-zero column, identical alternatives | deterministic, no NaN, warning |
| M07 | Known Borda ranks from 3 DM | exact N..1 totals |
| M08 | Borda tie | BPBD_HEAD ranking wins tie |
| M09 | TOPSIS same data with changed AHP weights | recalculated DM-dependent result |
| M10 | Recalculate same round twice | identical inputs/results/rounding display only |

## Functional & permissions tests
| ID | Scenario | Expected |
|---|---|---|
| F01 | Unauthenticated visit protected route | login/401 |
| F02 | Field officer adds case or sees unassigned report | 403/404 |
| F03 | DM changes field report | reject |
| F04 | Admin opens round without all verified districts | reject with checklist |
| F05 | Field officer submits incomplete/invalid vulnerable count | validation error |
| F06 | Admin reject with reason, officer resubmits | transitions, audit preserved |
| F07 | Change case data after round lock | round snapshot unchanged; new round needed |
| F08 | Borda before 3 valid AHP/TOPSIS rankings | blocked |
| F09 | User other than BPBD_HEAD finalizes | forbidden |
| F10 | Finalized result edit attempt | blocked |
| F11 | Re-enter same district code in case | unique constraint |
| F12 | Reports in demo | show SIMULASI label everywhere |

## Demo walkthrough
Use `examples/seed_case.json` (fictional), one collector assigned across five districts; verify all. Each DM completes all 15 pairs (all ones fixture initially valid; vary comparisons for meaningful demo while preserving CR). View three TOPSIS outputs and a Borda recommendation, finalize as Kepala BPBD, attempt to edit locked snapshot and confirm rejection.

## Quality gates
- No `NaN`/`Infinity`, no silent data manipulation, deterministic sorting, clear error messages.
- All units/ranges validated on server.
- Tests written **before** accepting decision engine results; document independent expected values.
