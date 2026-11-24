ALTER TABLE app_users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1;
CREATE TABLE account_audit (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER REFERENCES app_users(id),
    target_user_id INTEGER NOT NULL REFERENCES app_users(id),
    action TEXT NOT NULL CHECK (action IN ('CREATE', 'ACTIVATE', 'DEACTIVATE', 'RESET_PASSWORD', 'CHANGE_PASSWORD')),
    created_at TEXT NOT NULL
);
CREATE INDEX account_audit_target ON account_audit(target_user_id);
CREATE INDEX account_audit_actor ON account_audit(actor_id);
