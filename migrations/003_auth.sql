CREATE TABLE app_users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('bpbd', 'lapangan', 'sosial')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY,
    identity TEXT NOT NULL,
    attempted_at REAL NOT NULL
);
CREATE INDEX login_attempt_identity ON login_attempts(identity, attempted_at);
ALTER TABLE districts ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'APPROVED'
    CHECK (verification_status IN ('PENDING', 'APPROVED'));
ALTER TABLE districts ADD COLUMN proposed_by TEXT;
