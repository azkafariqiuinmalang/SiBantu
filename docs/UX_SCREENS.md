# UX Pages and Role Views

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
- AHP UI: one pair at a time or matrix; do not expose reciprocal cell editing, show consistency warnings and suggested re-evaluation without modifying user choices automatically.
- Snapshot date/time prominent to prevent mistaken "live" interpretation.
- Display explanatory table: each district, C1..C6, sources; per DM weight, CR, TOPSIS coefficient/rank; Borda points and final rank.
- Use neutral professional styling; accessibility: keyboard, contrast, labels, error messages.
- Charts/maps optional, never replace numeric text results.
- Visible 'SIMULASI — bukan data kejadian nyata' if is_simulation true.
