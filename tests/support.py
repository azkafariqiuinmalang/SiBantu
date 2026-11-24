import re
import sqlite3
from contextlib import closing

from werkzeug.security import generate_password_hash

PASSWORD = "SiBantu test password 2026"


def seed_users(database):
    with closing(sqlite3.connect(database)) as db, db:
        for role in ("bpbd", "lapangan", "sosial"):
            db.execute("INSERT INTO app_users(email, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                       (role + "@example.test", role, generate_password_hash(PASSWORD, method="pbkdf2:sha256:1000"), role))


def login(client, role):
    with client.session_transaction() as session:
        session.clear()
    page = client.get("/login")
    token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()
    response = client.post("/login", data=dict(token=token, email=role + "@example.test", password=PASSWORD))
    if response.status_code != 303:
        raise AssertionError(response.data)
    with client.session_transaction() as session:
        return session["form_token"]
