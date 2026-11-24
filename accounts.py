"""Administrasi akun oleh Kepala BPBD dan perubahan password pemilik akun."""

import re
import secrets
import sqlite3
from datetime import datetime, timezone

from flask import abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from auth import ROLES, require_role
from database import insert_id


def validate_account(email, name, password, role):
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Isi alamat email yang valid.")
    if not name or len(name) > 120:
        raise ValueError("Nama harus diisi, maksimal 120 karakter.")
    if role not in ROLES:
        raise ValueError("Pilih salah satu dari tiga peran SiBantu.")
    validate_password(password)


def validate_password(password):
    if not 12 <= len(password) <= 1024:
        raise ValueError("Kata sandi harus terdiri dari 12 sampai 1024 karakter.")


def register_accounts(app, connect, check_form):
    def audit(db, action, target):
        db.execute("INSERT INTO account_audit(actor_id,target_user_id,action,created_at) VALUES (?,?,?,?)",
                   (g.user["id"], target, action, datetime.now(timezone.utc).isoformat(timespec="seconds")))

    @app.route("/pengguna", methods=["GET", "POST"])
    def users():
        require_role("bpbd")
        error, code = None, 200
        if request.method == "POST":
            check_form()
            data = request.form
            with connect() as db, db:
                db.execute("BEGIN IMMEDIATE")
                actor = db.execute("SELECT is_active,session_version FROM app_users WHERE id=?",
                                   (g.user["id"],)).fetchone()
                if not actor or not actor["is_active"] or session.get("auth_version") != actor["session_version"]:
                    session.clear()
                    return redirect(url_for("login"), code=303)
                try:
                    action = data.get("action")
                    if action == "create":
                        email, name, role = (data.get(key, "").strip() for key in ("email", "display_name", "role"))
                        email = email.lower()
                        password = data.get("password", "")
                        validate_account(email, name, password, role)
                        user_id = insert_id(db, "INSERT INTO app_users(email,display_name,password_hash,role) "
                                            "VALUES (?,?,?,?)", (email, name, generate_password_hash(password), role))
                        audit(db, "CREATE", user_id)
                        flash("Akun baru berhasil dibuat.")
                    elif action in {"active", "reset_password"}:
                        try:
                            user_id = int(data.get("user_id", ""))
                        except ValueError:
                            abort(400)
                        target = db.execute("SELECT id,role,is_active FROM app_users WHERE id=?", (user_id,)).fetchone()
                        if not target:
                            abort(404)
                        if user_id == g.user["id"]:
                            abort(409, "Gunakan halaman Akun saya untuk mengubah kata sandi sendiri. Akun sendiri tidak dapat dinonaktifkan.")
                        if action == "active":
                            raw = data.get("is_active")
                            if raw not in {"0", "1"}:
                                abort(400)
                            active = int(raw)
                            if not active and target["role"] == "bpbd" and target["is_active"]:
                                count = db.execute("SELECT COUNT(*) AS total FROM app_users "
                                                   "WHERE role='bpbd' AND is_active=1").fetchone()["total"]
                                if count <= 1:
                                    abort(409, "Minimal satu akun Kepala BPBD harus tetap aktif.")
                            if active != target["is_active"]:
                                db.execute("UPDATE app_users SET is_active=?,session_version=session_version+1 WHERE id=?",
                                           (active, user_id))
                                audit(db, "ACTIVATE" if active else "DEACTIVATE", user_id)
                            flash("Status akun berhasil diperbarui.")
                        else:
                            password = data.get("new_password", "")
                            validate_password(password)
                            db.execute("UPDATE app_users SET password_hash=?,session_version=session_version+1 WHERE id=?",
                                       (generate_password_hash(password), user_id))
                            audit(db, "RESET_PASSWORD", user_id)
                            flash("Kata sandi berhasil diganti. Pengguna perlu masuk kembali.")
                    else:
                        abort(400)
                except ValueError as exc:
                    error, code = str(exc), 422
                except sqlite3.IntegrityError:
                    error, code = "Email sudah digunakan. Pakai alamat email lain.", 409
                else:
                    return redirect(url_for("users"), code=303)
        with connect() as db:
            records = db.execute("SELECT id,email,display_name,role,is_active FROM app_users "
                                 "ORDER BY is_active DESC,display_name,id").fetchall()
            history = db.execute("""SELECT a.action,a.created_at,t.display_name AS target_name,
                                 u.display_name AS actor_name FROM account_audit a
                                 JOIN app_users t ON t.id=a.target_user_id
                                 LEFT JOIN app_users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 20""").fetchall()
        return render_template("accounts.html", section="users", users=records, history=history, error=error), code

    @app.route("/akun", methods=["GET", "POST"])
    def account():
        error = None
        if request.method == "POST":
            check_form()
            old = request.form.get("current_password", "")
            password = request.form.get("new_password", "")
            with connect() as db, db:
                db.execute("BEGIN IMMEDIATE")
                user = db.execute("SELECT * FROM app_users WHERE id=?", (g.user["id"],)).fetchone()
                if not user or not user["is_active"] or session.get("auth_version") != user["session_version"]:
                    session.clear()
                    return redirect(url_for("login"), code=303)
                try:
                    if len(old) > 1024 or not check_password_hash(user["password_hash"], old):
                        raise ValueError("Kata sandi saat ini tidak sesuai.")
                    validate_password(password)
                    if password != request.form.get("confirm_password"):
                        raise ValueError("Konfirmasi kata sandi belum sama.")
                except ValueError as exc:
                    error = str(exc)
                else:
                    db.execute("UPDATE app_users SET password_hash=?,session_version=session_version+1 WHERE id=?",
                               (generate_password_hash(password), user["id"]))
                    audit(db, "CHANGE_PASSWORD", user["id"])
                    session.clear()
                    session.update(user_id=user["id"], auth_version=user["session_version"] + 1,
                                   form_token=secrets.token_urlsafe(24))
                    session.permanent = True
                    flash("Kata sandi berhasil diubah. Sesi lain pada akun ini sudah diakhiri.")
                    return redirect(url_for("account"), code=303)
        return render_template("accounts.html", section="account", error=error), 422 if error else 200
