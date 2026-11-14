CREATE TABLE disaster_cases (
    id INTEGER PRIMARY KEY,
    case_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL,
    incident_at TEXT NOT NULL,
    province TEXT NOT NULL,
    regency TEXT NOT NULL,
    magnitude REAL,
    information_source TEXT NOT NULL,
    is_simulation INTEGER NOT NULL CHECK (is_simulation IN (0, 1)),
    created_at TEXT NOT NULL
);
CREATE TABLE districts (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES disaster_cases(id),
    district_code TEXT NOT NULL COLLATE NOCASE,
    district_name TEXT NOT NULL,
    UNIQUE (case_id, district_code)
);
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY,
    district_id INTEGER NOT NULL REFERENCES districts(id),
    officer_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    UNIQUE (district_id, officer_id)
);
CREATE TABLE field_reports (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id),
    district_id INTEGER NOT NULL REFERENCES districts(id),
    version INTEGER NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'SUBMITTED', 'REJECTED', 'VERIFIED')),
    observations TEXT NOT NULL,
    criterion_values TEXT,
    created_at TEXT NOT NULL,
    submitted_at TEXT,
    UNIQUE (district_id, version)
);
CREATE UNIQUE INDEX one_open_field_report
    ON field_reports(district_id) WHERE status IN ('DRAFT', 'SUBMITTED');
CREATE TABLE field_report_reviews (
    report_id INTEGER PRIMARY KEY REFERENCES field_reports(id),
    reviewer_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('REJECTED', 'VERIFIED')),
    note TEXT,
    reviewed_at TEXT NOT NULL
);
CREATE TABLE fieldwork_audit (
    id INTEGER PRIMARY KEY,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
