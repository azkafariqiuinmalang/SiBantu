import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import ROOT, SCHEMA, create_app
from database import SCHEMA_VERSION
from support import PASSWORD, login, seed_users


class AccountsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "accounts.sqlite3"
        self.app = create_app(self.database)
        seed_users(self.database)
        self.client = self.app.test_client()

    def user_id(self, role):
        with closing(sqlite3.connect(self.database)) as db:
            return db.execute("SELECT id FROM app_users WHERE role=?", (role,)).fetchone()[0]

    def sign_in(self, client, email, password):
        client.post("/logout", data={})
        with client.session_transaction() as state:
            state.clear()
        token = re.search(rb'name="token" value="([^"]+)"', client.get("/login").data)[1].decode()
        return client.post("/login", data=dict(token=token,email=email,password=password))

    def test_account_creation_and_role_permissions(self):
        token = login(self.client, "lapangan")
        self.assertEqual(self.client.get("/pengguna").status_code, 403)
        self.assertEqual(self.client.post("/pengguna", data=dict(token=token,action="create")).status_code, 403)
        token = login(self.client, "bpbd")
        self.assertEqual(self.client.get("/pengguna").status_code, 200)
        data = dict(token=token,action="create",display_name="Koordinator Baru",email="BARU@sibantu.local",
                    role="lapangan",password="Kata sandi baru 2026")
        self.assertEqual(self.client.post("/pengguna",data={**data,"role":"admin"}).status_code, 422)
        self.assertEqual(self.client.post("/pengguna",data={**data,"password":"short"}).status_code, 422)
        self.assertEqual(self.client.post("/pengguna",data={**data,"email":"bad"}).status_code, 422)
        self.assertEqual(self.client.post("/pengguna",data=data).status_code, 303)
        response = self.client.post("/pengguna",data=data)
        self.assertEqual(response.status_code, 409)
        self.assertNotIn(data["password"].encode(),response.data)
        self.assertEqual(self.sign_in(self.app.test_client(),"baru@sibantu.local",data["password"]).status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM account_audit").fetchone()[0],1)

    def test_account_status_revokes_sessions_and_preserves_self(self):
        other = self.app.test_client()
        login(other,"sosial")
        old_cookie = other.get_cookie("session").value
        token = login(self.client,"bpbd")
        self.assertEqual(self.client.post("/pengguna",data=dict(token=token,action="active",
            user_id=self.user_id("bpbd"),is_active="0")).status_code,409)
        data = dict(token=token,action="active",user_id=self.user_id("sosial"),is_active="0")
        self.assertEqual(self.client.post("/pengguna",data=data).status_code,303)
        self.assertEqual(other.get("/dashboard").status_code,302)
        self.assertEqual(self.client.post("/pengguna",data={**data,"is_active":"1"}).status_code,303)
        other.set_cookie("session",old_cookie)
        self.assertEqual(other.get("/dashboard").status_code,302)
        self.assertEqual(self.sign_in(other,"sosial@example.test",PASSWORD).status_code,303)

    def test_password_change_revokes_other_sessions_and_updates_login(self):
        token = login(self.client,"lapangan")
        other = self.app.test_client()
        login(other,"lapangan")
        data = dict(token=token,current_password=PASSWORD,new_password="Password pengganti 2026",
                    confirm_password="Password pengganti 2026")
        self.assertEqual(self.client.post("/akun",data={**data,"current_password":"wrong"}).status_code,422)
        self.assertEqual(self.client.post("/akun",data={**data,"confirm_password":"different"}).status_code,422)
        self.assertEqual(self.client.post("/akun",data=data).status_code,303)
        self.assertEqual(self.client.get("/akun").status_code,200)
        self.assertEqual(other.get("/dashboard").status_code,302)
        self.assertEqual(self.sign_in(other,"lapangan@example.test",PASSWORD).status_code,401)
        self.assertEqual(self.sign_in(other,"lapangan@example.test",data["new_password"]).status_code,303)

    def test_admin_reset_invalidates_existing_password_and_sessions(self):
        other = self.app.test_client()
        login(other,"sosial")
        token = login(self.client,"bpbd")
        response = self.client.post("/pengguna",data=dict(token=token,action="reset_password",
            user_id=self.user_id("sosial"),new_password="Password sosial baru 2026"))
        self.assertEqual(response.status_code,303)
        self.assertEqual(other.get("/dashboard").status_code,302)
        self.assertEqual(self.sign_in(other,"sosial@example.test",PASSWORD).status_code,401)
        self.assertEqual(self.sign_in(other,"sosial@example.test","Password sosial baru 2026").status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT action FROM account_audit").fetchone()[0],"RESET_PASSWORD")

    def test_version_three_upgrade_preserves_accounts(self):
        legacy = self.database.with_name("legacy-v3.sqlite3")
        with closing(sqlite3.connect(legacy)) as db, db:
            db.executescript(SCHEMA)
            for name in ("002_fieldwork.sql","003_auth.sql"):
                db.executescript((ROOT/"migrations"/name).read_text(encoding="utf-8"))
            db.execute("PRAGMA user_version=3")
            db.execute("INSERT INTO app_users(email,display_name,password_hash,role,is_active) "
                       "VALUES ('lama@sibantu.local','Lama','original-hash','sosial',0)")
        create_app(legacy)
        create_app(legacy)
        with closing(sqlite3.connect(legacy)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],SCHEMA_VERSION)
            self.assertEqual(db.execute("SELECT password_hash,is_active,session_version FROM app_users").fetchone(),
                             ("original-hash",0,1))

    def test_cli_creates_validated_account_with_audit(self):
        args=["create-user","--role","sosial","--email","cli@sibantu.local","--name","Akun CLI"]
        runner=self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=args,input="short\nshort\n").exit_code,1)
        result=runner.invoke(args=args,input="Password dari CLI 2026\nPassword dari CLI 2026\n")
        self.assertEqual(result.exit_code,0,result.output)
        self.assertEqual(self.sign_in(self.app.test_client(),"cli@sibantu.local","Password dari CLI 2026").status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT action,actor_id FROM account_audit").fetchone(),("CREATE",None))
