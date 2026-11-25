import http.cookiejar
import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class BibliotecaTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "biblioteca.sqlite3"
        self.database_patch = patch.object(app, "DB_PATH", self.database)
        self.database_patch.start()
        with app.db_connect() as db:
            db.executescript(app.SCHEMA)

    def tearDown(self):
        self.database_patch.stop()
        self.temp_dir.cleanup()

    def test_imports_existing_xlsx_rows(self):
        spreadsheet = Path(__file__).resolve().parents[1] / "planilhas" / "biblioteca_folhetos.xlsx"
        rows = app.spreadsheet_rows(spreadsheet.read_bytes())
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["registration"], "00001")
        self.assertEqual(rows[0]["title"], "Quando a palavra toma assento")
        self.assertEqual(rows[0]["type"], "Folhetos")

    def test_corrected_submission_date_is_preserved_in_source_workbooks(self):
        root = Path(__file__).resolve().parents[1] / "planilhas"
        for filename in ("biblioteca_geral.xlsx", "biblioteca_livro.xlsx"):
            matches = [
                row
                for row in app.workbook_rows(root / filename)
                if row["title"] == "Por dentro do serviço público"
            ]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["record_date"], "02/07/2026")

    def test_initial_import_is_not_repeated_after_catalog_is_emptied(self):
        root = Path(self.temp_dir.name)
        data_root = root / "dados"
        seed_dir = root / "planilhas"
        seed_dir.mkdir()
        source = Path(__file__).resolve().parents[1] / "planilhas" / "biblioteca_folhetos.xlsx"
        (seed_dir / source.name).write_bytes(source.read_bytes())
        with patch.object(app, "DATA_ROOT", data_root):
            app.ensure_database()
            with app.db_connect() as db:
                self.assertGreater(db.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
                db.execute("DELETE FROM items")
            app.ensure_database()
            with app.db_connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)

    def test_server_startup_invalidates_existing_sessions(self):
        data_root = Path(self.temp_dir.name) / "dados"
        with patch.object(app, "DATA_ROOT", data_root):
            with app.db_connect() as db:
                cursor = db.execute(
                    "INSERT INTO users (username, display_name, password_hash, role, created_at) "
                    "VALUES ('teste.admin', 'Admin de teste', 'hash', 'admin', ?)",
                    (app.utc_now().isoformat(),),
                )
                db.execute(
                    "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) "
                    "VALUES ('token-antigo', ?, 'csrf-antigo', ?)",
                    (cursor.lastrowid, (app.utc_now() + app.timedelta(hours=1)).isoformat()),
                )

            app.invalidate_sessions()

            with app.db_connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_import_skips_duplicate_records_across_workbooks(self):
        root = Path(__file__).resolve().parents[1] / "planilhas"
        result = app.import_spreadsheets(
            [root / "biblioteca_geral.xlsx", root / "biblioteca_livro.xlsx"]
        )
        self.assertGreater(result["inserted"], 0)
        self.assertGreater(result["duplicates"], 0)
        self.assertEqual(result["errors"], [])

    def test_item_fingerprint_ignores_accents_and_case(self):
        first = {"type": "Livro", "title": "Ação", "author": "João", "year": "2024"}
        second = {"type": "livro", "title": "ACAO", "author": "JOAO", "year": "2024"}
        self.assertEqual(app.fingerprint(first), app.fingerprint(second))

    def test_duplicate_catalog_item_is_rejected(self):
        item = {"title": "Registro de teste", "author": "Autora", "type": "Livro"}
        with app.db_connect() as db:
            app.save_item(db, item)
        with self.assertRaises(app.APIError) as error:
            with app.db_connect() as db:
                app.save_item(db, item)
        self.assertEqual(error.exception.status, 409)

    def test_password_hash_verifies_only_matching_password(self):
        stored = app.password_hash("senha-segura-123")
        self.assertTrue(app.password_matches("senha-segura-123", stored))
        self.assertFalse(app.password_matches("senha-errada", stored))

    def test_http_catalog_and_loan_flow(self):
        server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.BibliotecaHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        base_url = f"http://127.0.0.1:{server.server_port}"

        def request(path, method="GET", body=None, csrf=""):
            headers = {}
            data = None
            if body is not None:
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            if csrf:
                headers["X-CSRF-Token"] = csrf
            request = urllib.request.Request(
                base_url + path, data=data, headers=headers, method=method
            )
            with opener.open(request) as response:
                content = response.read()
                if "application/json" in response.headers.get("Content-Type", ""):
                    return json.loads(content)
                return content

        try:
            logo = request("/fcja-logo.jpg")
            self.assertTrue(logo.startswith(b"\xff\xd8"))
            request(
                "/api/setup",
                "POST",
                {
                    "username": "admin.teste",
                    "displayName": "Administração",
                    "password": "senha-segura-123",
                },
            )
            session = request("/api/me")
            csrf = session["csrfToken"]
            created = request(
                "/api/items",
                "POST",
                {"title": "Livro para empréstimo", "type": "Livro", "copies": "1"},
                csrf,
            )
            item_id = created["id"]
            request(
                "/api/items",
                "POST",
                {
                    "title": "Registro mais recente",
                    "type": "Folhetos",
                    "record_date": "15/02/2026",
                },
                csrf,
            )
            request(
                "/api/items",
                "POST",
                {
                    "title": "Registro mais antigo",
                    "type": "Folhetos",
                    "record_date": "03/01/2026",
                },
                csrf,
            )
            request(
                "/api/items",
                "POST",
                {
                    "title": "Item de outra tipologia",
                    "type": "Folhetos de Cordel",
                    "record_date": "02/01/2026",
                },
                csrf,
            )
            catalog = request("/api/items?q=empr%C3%A9stimo")
            self.assertEqual(len(catalog["items"]), 1)
            self.assertEqual(catalog["items"][0]["available"], 1)
            dated_catalog = request("/api/items?type=Folhetos")["items"]
            self.assertEqual(
                [item["title"] for item in dated_catalog],
                ["Registro mais antigo", "Registro mais recente"],
            )
            other_type = request("/api/items?type=Folhetos%20de%20Cordel")["items"]
            self.assertEqual([item["title"] for item in other_type], ["Item de outra tipologia"])

            request(
                "/api/loans",
                "POST",
                {
                    "itemId": item_id,
                    "borrower": "Leitora de teste",
                    "dueDate": (date.today() + timedelta(days=7)).isoformat(),
                },
                csrf,
            )
            loans = request("/api/loans?status=open")["loans"]
            self.assertEqual(len(loans), 1)
            catalog_after_loan = request("/api/items")["items"]
            checked_out_item = next(item for item in catalog_after_loan if item["id"] == item_id)
            self.assertEqual(checked_out_item["available"], 0)
            request(f"/api/loans/{loans[0]['id']}/return", "POST", {}, csrf)
            self.assertEqual(request("/api/loans?status=open")["loans"], [])
            self.assertEqual(len(request("/api/loans?status=returned")["loans"]), 1)
            catalog_after_return = request("/api/items")["items"]
            returned_item = next(item for item in catalog_after_return if item["id"] == item_id)
            self.assertEqual(returned_item["available"], 1)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
