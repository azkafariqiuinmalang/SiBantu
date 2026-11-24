"""Koneksi SQLite lokal dan PostgreSQL Supabase dengan transaksi yang sama."""

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 6


def load_environment(root):
    path = root / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


class PostgresConnection:
    """Menjaga query parameterized dan perilaku transaksi penulisan aplikasi."""

    def __init__(self, url):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            raise RuntimeError("Pasang requirements.txt untuk memakai PostgreSQL Supabase.") from None
        self.connection = psycopg.connect(
            url, row_factory=dict_row, connect_timeout=10, sslmode="require",
            options="-c search_path=sibantu,public",
        )

    def execute(self, query, args=()):
        if query.strip() == "BEGIN IMMEDIATE":
            self.connection.execute("BEGIN")
            return self.connection.execute("SELECT pg_advisory_xact_lock(725321)")
        query = query.replace("?", "%s")
        has_insert = query.lstrip().upper().startswith("INSERT ")
        if not has_insert:
            return self.connection.execute(query, args)
        # Existing callers recover from uniqueness errors inside a transaction.
        # A savepoint keeps PostgreSQL usable for their subsequent reads.
        self.connection.execute("SAVEPOINT write_operation")
        try:
            cursor = self.connection.execute(query, args)
        except Exception as error:
            self.connection.execute("ROLLBACK TO SAVEPOINT write_operation")
            self.connection.execute("RELEASE SAVEPOINT write_operation")
            if (getattr(error, "sqlstate", None) or "").startswith("23"):
                raise sqlite3.IntegrityError("Data melanggar batas integritas database.") from None
            raise
        self.connection.execute("RELEASE SAVEPOINT write_operation")
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind:
            self.connection.rollback()
        else:
            self.connection.commit()

    def close(self):
        self.connection.close()


def insert_id(db, query, args):
    """Ambil ID tanpa bergantung pada lastrowid yang khusus SQLite."""
    if isinstance(db, PostgresConnection):
        return db.execute(query + " RETURNING id", args).fetchone()["id"]
    return db.execute(query, args).lastrowid


def migrate(db, root, initial_schema):
    postgres = isinstance(db, PostgresConnection)
    if postgres:
        db.execute("SELECT pg_advisory_xact_lock(725321)")
        present = db.execute("SELECT EXISTS (SELECT 1 FROM information_schema.schemata "
                             "WHERE schema_name='sibantu') AS present").fetchone()["present"]
        if not present:
            db.execute("CREATE SCHEMA sibantu")
    else:
        db.execute("BEGIN IMMEDIATE")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
    record = db.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
    version = record["version"] or 0
    if not postgres and version == 0:
        version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise RuntimeError("Versi database lebih baru dari aplikasi.")
    scripts = []
    if version == 0:
        scripts.append(initial_schema)
    if version < 2:
        scripts.append((root / "migrations" / "002_fieldwork.sql").read_text(encoding="utf-8"))
    if version < 3:
        scripts.append((root / "migrations" / "003_auth.sql").read_text(encoding="utf-8"))
    if version < 4:
        scripts.append((root / "migrations" / "004_accounts.sql").read_text(encoding="utf-8"))
    if version < 5:
        scripts.append((root / "migrations" / "005_decision_rounds.sql").read_text(encoding="utf-8"))
    if version < 6:
        scripts.append((root / "migrations" / "006_distance_criterion.sql").read_text(encoding="utf-8"))
    for script in scripts:
        if postgres:
            script = script.replace("COLLATE NOCASE", "").replace(
                "id INTEGER PRIMARY KEY,", "id BIGSERIAL PRIMARY KEY,").replace("REAL", "DOUBLE PRECISION")
        for statement in script.split(";"):
            if statement.strip():
                db.execute(statement)
    if postgres and version < 5:
        for table in ("decision_rounds", "round_assessments"):
            db.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    if version < SCHEMA_VERSION:
        db.execute("INSERT INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))
    if not postgres:
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def sqlite_connection(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
