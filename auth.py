"""Login dan otorisasi tiga aktor melalui sesi yang ditandatangani server."""

import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import click
from flask import abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database import insert_id

ROLES = {
    "bpbd": "Kepala BPBD",
    "lapangan": "Koordinator Lapangan",
    "sosial": "Perwakilan Dinas Sosial",
}


def require_role(*allowed):
    if not g.get("user") or g.user["role"] not in allowed:
        abort(403)
    return g.user["role"]


def register_auth(app, connect, check_form):
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    # A real hash keeps invalid-email and invalid-password paths comparable.
    dummy_hash = generate_password_hash(secrets.token_urlsafe(20))

    @app.before_request
    def authenticate():
        g.user = None
        if session.get("user_id"):
            with connect() as db:
                record = db.execute("SELECT id, email, display_name, role, session_version FROM app_users "
                                    "WHERE id=? AND is_active=1", (session["user_id"],)).fetchone()
            if record and session.get("auth_version") == record["session_version"]:
                g.user = dict(record)
            else:
                session.clear()
        if request.endpoint in {"login", "static"}:
            return None
        if g.user is None:
            return redirect(url_for("login"))

    @app.context_processor
    def identity_context():
        return dict(current_user=g.get("user"), role_labels=ROLES,
                    csrf_token=session.setdefault("form_token", secrets.token_urlsafe(24)))

    @app.after_request
    def private_pages(response):
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "private, no-store"
        return response

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        error = None
        code = 200
        if request.method == "POST":
            check_form()
            email = request.form.get("email", "").strip().lower()[:254]
            password = request.form.get("password", "")
            # Track both account and remote address independently.
            identities = ("email:" + email, "ip:" + (request.remote_addr or "unknown"))
            current_time = time.time()
            with connect() as db, db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (current_time - 900,))
                counts = [
                    db.execute("SELECT COUNT(*) AS total FROM login_attempts WHERE identity=?",
                               (identity,)).fetchone()["total"] for identity in identities
                ]
                if counts[0] >= 8 or counts[1] >= 40:
                    error, code = "Terlalu banyak percobaan. Coba lagi dalam 15 menit.", 429
                else:
                    user = db.execute("SELECT * FROM app_users WHERE email=? AND is_active=1", (email,)).fetchone()
                    valid = check_password_hash(user["password_hash"] if user else dummy_hash, password[:1024])
                    if user and valid and len(password) <= 1024:
                        db.execute("DELETE FROM login_attempts WHERE identity=?", (identities[0],))
                        session.clear()
                        session["user_id"] = user["id"]
                        session["auth_version"] = user["session_version"]
                        session["form_token"] = secrets.token_urlsafe(24)
                        session.permanent = True
                        return redirect(url_for("dashboard"), code=303)
                    for identity in identities:
                        db.execute("INSERT INTO login_attempts(identity, attempted_at) VALUES (?, ?)",
                                   (identity, current_time))
                    error, code = "Email atau kata sandi tidak sesuai.", 401
        return render_template("login.html", error=error), code

    @app.post("/logout")
    def logout():
        check_form()
        session.clear()
        return redirect(url_for("login"), code=303)

    @app.cli.command("create-user")
    @click.option("--role", type=click.Choice(list(ROLES)), required=True)
    @click.option("--email", prompt=True)
    @click.option("--name", prompt="Nama")
    @click.password_option()
    def create_user(role, email, name, password):
        """Buat akun melalui terminal dengan password yang dipilih pengguna."""
        from accounts import validate_account
        email = email.strip().lower()
        name = name.strip()
        try:
            validate_account(email, name, password, role)
        except ValueError as error:
            raise click.ClickException(str(error)) from None
        with connect() as db, db:
            try:
                user_id = insert_id(db, "INSERT INTO app_users(email, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                                    (email, name, generate_password_hash(password), role))
                db.execute("INSERT INTO account_audit(actor_id,target_user_id,action,created_at) VALUES (NULL,?,'CREATE',?)",
                           (user_id, datetime.now(timezone.utc).isoformat(timespec="seconds")))
            except sqlite3.IntegrityError:
                raise click.ClickException("Email sudah dipakai.") from None
        click.echo(f"Akun {ROLES[role]} dibuat.")

    @app.cli.command("database-status")
    def database_status():
        """Uji akses baca database aktif tanpa menampilkan kredensial."""
        with connect() as db:
            users = db.execute("SELECT COUNT(*) AS total FROM app_users").fetchone()["total"]
            cases = db.execute("SELECT COUNT(*) AS total FROM disaster_cases").fetchone()["total"]
        click.echo(f"Database aktif: {app.config['DATABASE_BACKEND']}; koneksi baca berhasil.")
        click.echo(f"Akun: {users}; kejadian: {cases}.")

    @app.cli.command("init-demo-users")
    def demo_users():
        """Buat tiga akun lokal dengan password acak yang dicetak satu kali."""
        if app.config["DATABASE_BACKEND"] != "sqlite":
            raise click.ClickException("Untuk Supabase, gunakan create-user dengan email pengguna.")
        generated = []
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            for role, name in ROLES.items():
                email = f"{role}@sibantu.local"
                if db.execute("SELECT id FROM app_users WHERE email=?", (email,)).fetchone():
                    click.echo(f"Akun {email} sudah ada.")
                    continue
                password = secrets.token_urlsafe(14)
                db.execute("INSERT INTO app_users(email, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                           (email, name, generate_password_hash(password), role))
                generated.append((email, password))
        for email, password in generated:
            click.echo(f"{email}  {password}")
