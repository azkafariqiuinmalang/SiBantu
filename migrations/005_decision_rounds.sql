CREATE TABLE decision_rounds (
    id INTEGER PRIMARY KEY,
    case_id INTEGER REFERENCES disaster_cases(id),
    snapshot TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    group_result TEXT,
    finalized_at TEXT
);
CREATE INDEX decision_round_case ON decision_rounds(case_id);
CREATE TABLE round_assessments (
    round_id INTEGER NOT NULL REFERENCES decision_rounds(id),
    role TEXT NOT NULL CHECK (role IN ('bpbd', 'lapangan', 'sosial')),
    choices TEXT NOT NULL,
    revision INTEGER NOT NULL,
    submitted_at TEXT,
    result TEXT,
    PRIMARY KEY (round_id, role)
);
INSERT INTO decision_rounds(case_id,snapshot,locked_at,algorithm_version,group_result,finalized_at)
    SELECT NULL,snapshot,locked_at,algorithm_version,group_result,finalized_at FROM assessment_round;
INSERT INTO round_assessments(round_id,role,choices,revision,submitted_at,result)
    SELECT (SELECT id FROM decision_rounds ORDER BY id LIMIT 1),role,choices,revision,submitted_at,result
    FROM assessment;
