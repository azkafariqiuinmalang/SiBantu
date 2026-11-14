# Data Model (Relational, konseptual)

Tidak mengunci vendor database. Gunakan migrations, foreign keys, unique constraints, timestamps UTC pada storage. Lokalisasi tanggal di UI (WIB/WITA/WIT jika relevan). Hindari menyimpan PII pengungsi; gunakan agregat kecamatan.

## Entitas
| Tabel | Kolom inti | Constraint |
|---|---|---|
| users | id, name, email, password_hash, role, is_active | unique(email); enum role |
| disaster_cases | id, case_code, name, incident_at, province, regency, magnitude?, information_source, is_simulation, status, created_by | unique(case_code) |
| districts | id, case_id, district_code, district_name, status | unique(case_id,district_code) |
| assignments | id, case_id, district_id, field_officer_id, assigned_by, assigned_at | valid FK, unique active assignment combination |
| field_reports | id, case_id, district_id, version, officer_id, observed_at, source_note, evacuees, vulnerable_people, housing_damage_score, essential_services_disruption_score, available_package_equivalents, required_package_equivalents, hours_since_last_delivery, status, rejection_reason? | check ranges, unique(district_id,version) |
| field_report_reviews | id, report_id, reviewer_id, outcome, note, reviewed_at | immutable history |
| criteria | id, criterion_code, name, direction, unit, rubric_version | unique(code) per version |
| assessment_rounds | id, case_id, round_no, baseline_at, snapshot_at, status, created_by, finalized_by?, finalized_at?, algorithm_version | unique(case_id,round_no) |
| round_alternatives | id, round_id, district_id, snapshot_report_id | unique(round_id,district_id) |
| round_values | id, round_id, district_id, criterion_code, numeric_value, source_report_id | unique(round_id,district_id,criterion_code) |
| dm_assessments | id, round_id, dm_user_id, dm_role, status, lambda_max?, ci?, cr?, submitted_at? | unique(round_id,dm_role); three approved DM roles required |
| ahp_comparisons | id, dm_assessment_id, criterion_i, criterion_j, comparison_value | unique(assessment_id,i,j), store i<j |
| ahp_weights | id, dm_assessment_id, criterion_code, weight | unique(assessment_id,criterion_code) |
| topsis_results | id, dm_assessment_id, district_id, distance_positive, distance_negative, closeness, rank, is_tied | unique(assessment_id,district_id) |
| borda_results | id, round_id, district_id, dm1_points, dm2_points, dm3_points, total_points, final_rank, tie_break_applied | unique(round_id,district_id) |
| audit_logs | id, actor_id, action, entity_type, entity_id, change_summary, created_at | append-only |

## Relationship sketch
`disaster_cases 1--N districts`; `districts 1--N field_reports`; `users(field_officer) 1--N assignments`; `disaster_cases 1--N assessment_rounds`; `assessment_rounds 1--N round_alternatives/round_values`; `assessment_rounds 1--3 dm_assessments`; `dm_assessments 1--15 ahp_comparisons`, `1--6 ahp_weights`, `1--N topsis_results`; `assessment_rounds 1--N borda_results`.

## Snapshot strategy
On creation of round: transactionally copy a consistent verified version per district into `round_values`, assign all 6 criterion values, validate no missing. `round_values`/`round_alternatives` become immutable after LOCKED. Never point computation at mutable latest field_report directly. Store `snapshot_report_id` for lineage.

## Data derivation
C1=`evacuees`; C2=`housing_damage_score`; C3 = `vulnerable_people/evacuees*100` with zero rule; C4=`essential_services_disruption_score`; C5 = `min(100, available_package_equivalents/required_package_equivalents*100)` (same period); C6=`hours_since_last_delivery` (if never served, derive using `baseline_at` and document).

## Rubric placeholder (must be agreed before real use)
C2 1=minimal affected, 2=light, 3=moderate, 4=heavy, 5=severe/widespread loss of shelter; C4 1=almost normal, 2=minor disruption, 3=partial major disruption, 4=widespread severe disruption, 5=critical/basic services nonfunctional. These are **demo conventions**, not BNPB-defined official rubrics.
