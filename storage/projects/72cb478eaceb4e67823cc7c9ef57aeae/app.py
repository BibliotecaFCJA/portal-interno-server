from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import unicodedata
import zipfile
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from typing import Iterator
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DATA_ROOT = ROOT / "dados"
DB_PATH = Path(os.environ.get("BIBLIOTECA_DB", DATA_ROOT / "biblioteca.sqlite3"))
HOST = os.environ.get("BIBLIOTECA_HOST", "0.0.0.0")
PORT = int(os.environ.get("BIBLIOTECA_PORT", "8002"))
SESSION_HOURS = 12
MAX_REQUEST_SIZE = 15 * 1024 * 1024
PASSWORD_ITERATIONS = 310_000
COOKIE_SECURE = os.environ.get("BIBLIOTECA_COOKIE_SECURE", "0") == "1"
LOG = logging.getLogger("biblioteca")

FIELDS = (
    "registration",
    "record_date",
    "author",
    "title",
    "place",
    "publisher",
    "edition",
    "volume",
    "number",
    "year",
    "copy",
    "copies",
    "origin",
    "cutter",
    "cdu",
    "subjects",
    "location",
    "type",
    "notes",
)

FIELD_ALIASES = {
    "data": "record_date",
    "registro": "registration",
    "autor": "author",
    "titulo": "title",
    "local": "place",
    "editora": "publisher",
    "edicao": "edition",
    "volume": "volume",
    "numero": "number",
    "ano": "year",
    "exemplar": "copy",
    "quantidade": "copies",
    "origem": "origin",
    "cutter": "cutter",
    "classificacao cdu": "cdu",
    "classificacao - cdu": "cdu",
    "assuntos": "subjects",
    "localizacao": "location",
    "tipologia": "type",
    "observacao": "notes",
    "observacoes": "notes",
}
FIELD_LABELS = {
    "registration": "Registro",
    "record_date": "Data",
    "author": "Autor",
    "title": "Título",
    "place": "Local",
    "publisher": "Editora",
    "edition": "Edição",
    "volume": "Volume",
    "number": "Número",
    "year": "Ano",
    "copy": "Exemplar",
    "copies": "Quantidade",
    "origin": "Origem",
    "cutter": "Cutter",
    "cdu": "Classificação - CDU",
    "subjects": "Assuntos",
    "location": "Localização",
    "type": "Tipologia",
    "notes": "Observação",
}

XML_NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    registration TEXT NOT NULL DEFAULT '',
    record_date TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    place TEXT NOT NULL DEFAULT '',
    publisher TEXT NOT NULL DEFAULT '',
    edition TEXT NOT NULL DEFAULT '',
    volume TEXT NOT NULL DEFAULT '',
    number TEXT NOT NULL DEFAULT '',
    year TEXT NOT NULL DEFAULT '',
    copy TEXT NOT NULL DEFAULT '',
    copies INTEGER NOT NULL DEFAULT 1 CHECK (copies >= 1),
    origin TEXT NOT NULL DEFAULT '',
    cutter TEXT NOT NULL DEFAULT '',
    cdu TEXT NOT NULL DEFAULT '',
    subjects TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_title ON items(title);
CREATE INDEX IF NOT EXISTS idx_items_registration ON items(registration);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    borrower TEXT NOT NULL,
    borrower_ref TEXT NOT NULL DEFAULT '',
    loaned_by INTEGER NOT NULL REFERENCES users(id),
    loaned_at TEXT NOT NULL,
    due_date TEXT NOT NULL,
    returned_at TEXT,
    returned_by INTEGER REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_loans_open ON loans(returned_at, due_date);
"""


class APIError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


@contextmanager
def db_connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().casefold()


def fingerprint(item: dict[str, object]) -> str:
    identity = "\x1f".join(
        normalize(item.get(field))
        for field in ("type", "title", "author", "year", "edition", "volume", "publisher")
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def csv_safe(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def password_matches(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def validate_password(password: object) -> str:
    if not isinstance(password, str) or len(password) < 10 or len(password) > 256:
        raise APIError(400, "A senha deve ter entre 10 e 256 caracteres.")
    return password


def validate_username(value: object) -> str:
    if not isinstance(value, str):
        raise APIError(400, "Informe um usuário válido.")
    username = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,40}", username):
        raise APIError(
            400, "O usuário deve ter de 3 a 40 caracteres: letras, números, ponto, _ ou -."
        )
    return username


def ensure_database() -> None:
    with db_connect() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(SCHEMA)
        count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        seeded = db.execute(
            "SELECT 1 FROM app_metadata WHERE key = 'initial_import_done'"
        ).fetchone()
        if seeded is None and count:
            db.execute(
                "INSERT INTO app_metadata (key, value) VALUES ('initial_import_done', '1')"
            )
            seeded = True
    if seeded is None:
        spreadsheets = sorted(DATA_ROOT.parent.joinpath("planilhas").glob("*.xlsx"))
        if spreadsheets:
            result = import_spreadsheets(spreadsheets)
            LOG.info(
                "Importação inicial: %s registros novos, %s duplicados.",
                result["inserted"],
                result["duplicates"],
            )
            for error in result["errors"]:
                LOG.error("Falha na importação inicial: %s", error)
            with db_connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO app_metadata (key, value) "
                    "VALUES ('initial_import_done', '1')"
                )


def invalidate_sessions() -> int:
    with db_connect() as db:
        invalidated_sessions = db.execute("DELETE FROM sessions").rowcount
    if invalidated_sessions:
        LOG.info("Sessões anteriores encerradas na inicialização: %s.", invalidated_sessions)
    return invalidated_sessions


def spreadsheet_rows(content: bytes) -> list[dict[str, str]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise APIError(400, "O arquivo enviado não é uma planilha XLSX válida.") from exc

    with archive:
        names = set(archive.namelist())
        if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
            raise APIError(400, "O arquivo não contém uma estrutura XLSX reconhecida.")
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        sheet = workbook.find("m:sheets/m:sheet", XML_NS)
        if sheet is None:
            raise APIError(400, "A planilha não contém abas para importar.")
        relationship_id = sheet.attrib.get(f"{{{XML_NS['r']}}}id")
        relation = next(
            (
                node
                for node in relationships.findall("p:Relationship", XML_NS)
                if node.attrib.get("Id") == relationship_id
            ),
            None,
        )
        if relation is None:
            raise APIError(400, "Não foi possível localizar a primeira aba da planilha.")
        target = relation.attrib.get("Target", "")
        sheet_path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        sheet_path = str(Path(sheet_path).as_posix())
        if sheet_path not in names:
            raise APIError(400, "A aba da planilha não foi encontrada.")

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in names:
            shared_xml = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for shared_item in shared_xml.findall("m:si", XML_NS):
                shared_strings.append(
                    "".join(node.text or "" for node in shared_item.findall(".//m:t", XML_NS))
                )

        root = ElementTree.fromstring(archive.read(sheet_path))
        rows = root.findall(".//m:sheetData/m:row", XML_NS)
        if not rows:
            return []

        def column_index(reference: str) -> int:
            letters = re.match(r"[A-Za-z]+", reference)
            if not letters:
                raise APIError(400, "A planilha contém uma coluna sem referência válida.")
            index = 0
            for char in letters.group(0).upper():
                index = index * 26 + ord(char) - ord("A") + 1
            return index - 1

        def row_values(row: ElementTree.Element) -> list[str]:
            cells: list[str] = []
            for cell in row.findall("m:c", XML_NS):
                position = column_index(cell.attrib.get("r", ""))
                while len(cells) <= position:
                    cells.append("")
                value = cell.find("m:v", XML_NS)
                inline = cell.find("m:is", XML_NS)
                cell_value = ""
                if inline is not None:
                    cell_value = "".join(
                        node.text or "" for node in inline.findall(".//m:t", XML_NS)
                    )
                elif value is not None:
                    cell_value = value.text or ""
                    if cell.attrib.get("t") == "s":
                        try:
                            cell_value = shared_strings[int(cell_value)]
                        except (ValueError, IndexError) as exc:
                            raise APIError(400, "A planilha contém texto compartilhado inválido.") from exc
                cells[position] = cell_value.strip()
            return cells

        headers = row_values(rows[0])
        mapped = [FIELD_ALIASES.get(normalize(header), "") for header in headers]
        if "title" not in mapped:
            raise APIError(400, "A primeira aba precisa conter a coluna Título.")

        result: list[dict[str, str]] = []
        for row in rows[1:]:
            values = row_values(row)
            item = {
                field: values[index] if index < len(values) and field else ""
                for index, field in enumerate(mapped)
                if field
            }
            if any(item.values()):
                result.append(item)
        return result


def workbook_rows(path: Path) -> list[dict[str, str]]:
    try:
        return spreadsheet_rows(path.read_bytes())
    except OSError as exc:
        raise RuntimeError(f"Não foi possível ler a planilha {path.name}: {exc}") from exc


def clean_item(source: dict[str, object]) -> dict[str, object]:
    item = {field: str(source.get(field, "") or "").strip() for field in FIELDS}
    if not item["title"]:
        raise APIError(400, "Cada registro precisa de um título.")
    item["copies"] = source.get("copies", 1)
    try:
        item["copies"] = int(item["copies"] or 1)
    except (ValueError, TypeError) as exc:
        raise APIError(400, "A quantidade de exemplares deve ser um número inteiro.") from exc
    if item["copies"] < 1 or item["copies"] > 10000:
        raise APIError(400, "A quantidade de exemplares deve estar entre 1 e 10.000.")
    if not item["type"]:
        item["type"] = "Não informado"
    return item


def save_item(db: sqlite3.Connection, source: dict[str, object], item_id: int | None = None) -> int:
    item = clean_item(source)
    now = utc_now().isoformat()
    item_fingerprint = fingerprint(item)
    values = [item[field] for field in FIELDS]
    if item_id is None:
        try:
            cursor = db.execute(
                f"INSERT INTO items ({', '.join(FIELDS)}, fingerprint, created_at, updated_at) "
                f"VALUES ({', '.join('?' for _ in FIELDS)}, ?, ?, ?)",
                (*values, item_fingerprint, now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise APIError(409, "Já existe um registro com esses dados bibliográficos.") from exc
        return int(cursor.lastrowid)

    existing = db.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if existing is None:
        raise APIError(404, "Registro não encontrado.")
    try:
        db.execute(
            f"UPDATE items SET {', '.join(f'{field} = ?' for field in FIELDS)}, "
            "fingerprint = ?, updated_at = ? WHERE id = ?",
            (*values, item_fingerprint, now, item_id),
        )
    except sqlite3.IntegrityError as exc:
        raise APIError(409, "Já existe outro registro com esses dados bibliográficos.") from exc
    return item_id


def import_spreadsheets(paths: list[Path]) -> dict[str, object]:
    inserted = 0
    duplicates = 0
    errors: list[str] = []
    with db_connect() as db:
        for path in paths:
            if path.suffix.lower() != ".xlsx":
                errors.append(f"{path.name}: formato não suportado.")
                continue
            try:
                rows = workbook_rows(path)
            except (APIError, RuntimeError) as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            for row_number, row in enumerate(rows, start=2):
                try:
                    item = clean_item(row)
                    item_fingerprint = fingerprint(item)
                    if db.execute(
                        "SELECT 1 FROM items WHERE fingerprint = ?", (item_fingerprint,)
                    ).fetchone():
                        duplicates += 1
                        continue
                    now = utc_now().isoformat()
                    values = [item[field] for field in FIELDS]
                    db.execute(
                        f"INSERT INTO items ({', '.join(FIELDS)}, fingerprint, created_at, updated_at) "
                        f"VALUES ({', '.join('?' for _ in FIELDS)}, ?, ?, ?)",
                        (*values, item_fingerprint, now, now),
                    )
                    inserted += 1
                except (APIError, sqlite3.IntegrityError) as exc:
                    errors.append(f"{path.name}, linha {row_number}: {exc}")
    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "errors": errors,
        "files": [path.name for path in paths],
    }


def row_dict(row: sqlite3.Row) -> dict[str, object]:
    return dict(row)


class BibliotecaHandler(BaseHTTPRequestHandler):
    server_version = "BibliotecaWeb/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        LOG.info("%s - %s", self.address_string(), fmt % args)

    def do_GET(self) -> None:
        self.dispatch("GET")

    def do_POST(self) -> None:
        self.dispatch("POST")

    def do_PUT(self) -> None:
        self.dispatch("PUT")

    def do_PATCH(self) -> None:
        self.dispatch("PATCH")

    def do_DELETE(self) -> None:
        self.dispatch("DELETE")

    def dispatch(self, method: str) -> None:
        try:
            path = urlsplit(self.path).path
            if path == "/" and method == "GET":
                self.serve_static("index.html")
                return
            if path in ("/app.js", "/style.css", "/fcja-logo.jpg") and method == "GET":
                self.serve_static(path[1:])
                return
            if not path.startswith("/api/"):
                raise APIError(404, "Página não encontrada.")
            if method != "GET":
                self.check_origin()
            self.route_api(method, path)
        except APIError as exc:
            self.send_json(exc.status, {"error": str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            LOG.debug("Cliente encerrou a conexão durante a resposta.")
        except Exception:
            LOG.exception("Erro inesperado ao processar %s %s", method, self.path)
            if not self.wfile.closed:
                self.send_json(500, {"error": "Erro interno. Consulte o log do servidor."})

    def serve_static(self, filename: str) -> None:
        path = WEB_ROOT / filename
        if not path.is_file():
            raise APIError(404, "Arquivo da interface não encontrado.")
        content_type = {
            "index.html": "text/html; charset=utf-8",
            "app.js": "text/javascript; charset=utf-8",
            "style.css": "text/css; charset=utf-8",
            "fcja-logo.jpg": "image/jpeg",
        }[filename]
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, filename: str, headers: list[str], rows: list[list[object]]) -> None:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows([[csv_safe(value) for value in row] for row in rows])
        body = ("\ufeff" + output.getvalue()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def check_origin(self) -> None:
        origin = self.headers.get("Origin")
        if origin:
            request_host = self.headers.get("Host", "")
            if urlsplit(origin).netloc.casefold() != request_host.casefold():
                raise APIError(403, "Origem da requisição não autorizada.")

    def read_body(self, max_size: int = MAX_REQUEST_SIZE) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise APIError(400, "Tamanho da requisição inválido.") from exc
        if length < 0 or length > max_size:
            raise APIError(413, "A requisição excede o tamanho permitido.")
        return self.rfile.read(length)

    def read_json(self) -> dict[str, object]:
        if "application/json" not in self.headers.get("Content-Type", ""):
            raise APIError(415, "Envie os dados no formato JSON.")
        try:
            payload = json.loads(self.read_body().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise APIError(400, "O corpo JSON é inválido.") from exc
        if not isinstance(payload, dict):
            raise APIError(400, "O corpo da requisição deve ser um objeto JSON.")
        return payload

    def get_session(self, required: bool = True) -> tuple[sqlite3.Row, str] | None:
        cookie = self.headers.get("Cookie", "")
        token = ""
        for part in cookie.split(";"):
            key, separator, value = part.strip().partition("=")
            if separator and key == "biblioteca_session":
                token = value
                break
        if not token:
            if required:
                raise APIError(401, "Faça login para continuar.")
            return None
        token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
        now = utc_now().isoformat()
        with db_connect() as db:
            session = db.execute(
                "SELECT s.csrf_token, u.id, u.username, u.display_name, u.role, u.active "
                "FROM sessions s JOIN users u ON u.id = s.user_id "
                "WHERE s.token_hash = ? AND s.expires_at > ?",
                (token_hash, now),
            ).fetchone()
            if session is None or not session["active"]:
                db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
                session = None
        if session is None:
            if required:
                raise APIError(401, "Sua sessão expirou. Entre novamente.")
            return None
        return session, session["csrf_token"]

    def require_user(self, write: bool = False) -> sqlite3.Row:
        session_info = self.get_session()
        assert session_info is not None
        user, csrf = session_info
        if write and not hmac.compare_digest(
            self.headers.get("X-CSRF-Token", ""), csrf
        ):
            raise APIError(403, "Token de segurança inválido. Atualize a página.")
        return user

    def require_admin(self, write: bool = False) -> sqlite3.Row:
        user = self.require_user(write=write)
        if user["role"] != "admin":
            raise APIError(403, "Esta operação exige perfil administrador.")
        return user

    def route_api(self, method: str, path: str) -> None:
        query = parse_qs(urlsplit(self.path).query)
        if path == "/api/me" and method == "GET":
            session = self.get_session(required=False)
            if session is None:
                with db_connect() as db:
                    setup_required = db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
                self.send_json(200, {"user": None, "setupRequired": setup_required})
            else:
                user, csrf = session
                self.send_json(
                    200,
                    {
                        "user": {
                            "id": user["id"],
                            "username": user["username"],
                            "displayName": user["display_name"],
                            "role": user["role"],
                        },
                        "csrfToken": csrf,
                        "setupRequired": False,
                    },
                )
            return
        if path == "/api/setup" and method == "POST":
            self.setup_admin()
            return
        if path == "/api/login" and method == "POST":
            self.login()
            return
        if path == "/api/logout" and method == "POST":
            self.logout()
            return

        if path == "/api/dashboard" and method == "GET":
            self.dashboard()
            return
        if path == "/api/items" and method == "GET":
            self.list_items(query)
            return
        if path == "/api/items" and method == "POST":
            user = self.require_user(write=True)
            payload = self.read_json()
            with db_connect() as db:
                item_id = save_item(db, payload)
            self.send_json(201, {"id": item_id})
            return
        item_match = re.fullmatch(r"/api/items/(\d+)", path)
        if item_match and method == "PUT":
            self.require_user(write=True)
            payload = self.read_json()
            with db_connect() as db:
                save_item(db, payload, int(item_match.group(1)))
            self.send_json(200, {"ok": True})
            return
        if item_match and method == "DELETE":
            self.require_admin(write=True)
            item_id = int(item_match.group(1))
            with db_connect() as db:
                try:
                    result = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
                except sqlite3.IntegrityError as exc:
                    raise APIError(409, "Não é possível excluir um item com histórico de empréstimos.") from exc
                if result.rowcount == 0:
                    raise APIError(404, "Registro não encontrado.")
            self.send_json(200, {"ok": True})
            return
        if path == "/api/import" and method == "POST":
            self.require_admin(write=True)
            self.import_uploads()
            return
        if path == "/api/loans" and method == "GET":
            self.list_loans(query)
            return
        if path == "/api/loans" and method == "POST":
            user = self.require_user(write=True)
            self.create_loan(user)
            return
        loan_match = re.fullmatch(r"/api/loans/(\d+)/return", path)
        if loan_match and method == "POST":
            user = self.require_user(write=True)
            self.return_loan(user, int(loan_match.group(1)))
            return
        if path == "/api/users" and method == "GET":
            self.list_users()
            return
        if path == "/api/users" and method == "POST":
            self.create_user()
            return
        user_match = re.fullmatch(r"/api/users/(\d+)", path)
        if user_match and method == "PATCH":
            self.update_user(int(user_match.group(1)))
            return
        if user_match and method == "POST":
            self.reset_user_password(int(user_match.group(1)))
            return
        if path == "/api/account/password" and method == "POST":
            self.change_password()
            return
        if path == "/api/reports" and method == "GET":
            self.reports()
            return
        if path == "/api/reports/export" and method == "GET":
            self.export_report(query)
            return
        raise APIError(404, "Operação da API não encontrada.")

    def setup_admin(self) -> None:
        payload = self.read_json()
        username = validate_username(payload.get("username"))
        display_name = str(payload.get("displayName", "")).strip()
        if not display_name:
            raise APIError(400, "Informe o nome do administrador.")
        password = validate_password(payload.get("password"))
        with db_connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
                raise APIError(409, "A configuração inicial já foi concluída.")
            cursor = db.execute(
                "INSERT INTO users (username, display_name, password_hash, role, created_at) "
                "VALUES (?, ?, ?, 'admin', ?)",
                (username, display_name, password_hash(password), utc_now().isoformat()),
            )
            token = self.create_session(db, int(cursor.lastrowid))
        self.send_auth_response(201, token)

    def create_session(self, db: sqlite3.Connection, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        expires = (utc_now() + timedelta(hours=SESSION_HOURS)).isoformat()
        db.execute(
            "DELETE FROM sessions WHERE expires_at <= ?", (utc_now().isoformat(),)
        )
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
            (token_hash, user_id, csrf, expires),
        )
        return token

    def send_auth_response(self, status: int, token: str) -> None:
        body = b'{"ok":true}'
        self.send_response(status)
        self.send_header(
            "Set-Cookie",
            f"biblioteca_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_HOURS * 3600}"
            + ("; Secure" if COOKIE_SECURE else ""),
        )
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def login(self) -> None:
        payload = self.read_json()
        username = str(payload.get("username", "")).strip()
        password = payload.get("password", "")
        if not isinstance(password, str):
            password = ""
        with db_connect() as db:
            user = db.execute(
                "SELECT id, password_hash, active FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
            if user is None or not user["active"] or not password_matches(password, user["password_hash"]):
                raise APIError(401, "Usuário ou senha inválidos.")
            db.execute("BEGIN IMMEDIATE")
            token = self.create_session(db, int(user["id"]))
        self.send_auth_response(200, token)

    def logout(self) -> None:
        session = self.get_session()
        assert session is not None
        user, _ = session
        cookie = self.headers.get("Cookie", "")
        token = next(
            (part.strip().partition("=")[2] for part in cookie.split(";") if part.strip().startswith("biblioteca_session=")),
            "",
        )
        token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
        with db_connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        self.send_response(200)
        self.send_header(
            "Set-Cookie",
            "biblioteca_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
            + ("; Secure" if COOKIE_SECURE else ""),
        )
        body = b'{"ok":true}'
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def dashboard(self) -> None:
        self.require_user()
        today = date.today().isoformat()
        with db_connect() as db:
            total_items = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            total_copies = db.execute("SELECT COALESCE(SUM(copies), 0) FROM items").fetchone()[0]
            open_loans = db.execute("SELECT COUNT(*) FROM loans WHERE returned_at IS NULL").fetchone()[0]
            overdue = db.execute(
                "SELECT COUNT(*) FROM loans WHERE returned_at IS NULL AND due_date < ?", (today,)
            ).fetchone()[0]
            categories = [
                {"type": row["type"], "count": row["count"]}
                for row in db.execute(
                    "SELECT type, COUNT(*) AS count FROM items GROUP BY type ORDER BY count DESC, type"
                )
            ]
            recent = [
                row_dict(row)
                for row in db.execute(
                    "SELECT l.id, l.borrower, l.loaned_at, l.due_date, i.title "
                    "FROM loans l JOIN items i ON i.id = l.item_id "
                    "WHERE l.returned_at IS NULL ORDER BY l.loaned_at DESC LIMIT 8"
                )
            ]
        self.send_json(
            200,
            {
                "items": total_items,
                "copies": total_copies,
                "openLoans": open_loans,
                "overdue": overdue,
                "categories": categories,
                "recentLoans": recent,
            },
        )

    def list_items(self, query: dict[str, list[str]]) -> None:
        self.require_user()
        search = query.get("q", [""])[0].strip()
        item_type = query.get("type", [""])[0].strip()
        conditions: list[str] = []
        parameters: list[object] = []
        if search:
            needle = f"%{search}%"
            conditions.append(
                "(title LIKE ? OR author LIKE ? OR registration LIKE ? OR subjects LIKE ? "
                "OR publisher LIKE ? OR location LIKE ?)"
            )
            parameters.extend([needle] * 6)
        if item_type:
            conditions.append("type = ?")
            parameters.append(item_type)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with db_connect() as db:
            rows = db.execute(
                "SELECT i.*, i.copies - (SELECT COUNT(*) FROM loans l "
                "WHERE l.item_id = i.id AND l.returned_at IS NULL) AS available "
                f"FROM items i {where} "
                "ORDER BY i.type COLLATE NOCASE, "
                "CASE "
                "WHEN record_date GLOB '[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]' "
                "THEN substr(record_date, 7, 4) || '-' || substr(record_date, 4, 2) || '-' || substr(record_date, 1, 2) "
                "WHEN record_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' "
                "THEN record_date "
                "ELSE '9999-12-31' END, "
                "i.registration COLLATE NOCASE, i.title COLLATE NOCASE LIMIT 1000",
                parameters,
            ).fetchall()
            types = [
                row["type"]
                for row in db.execute("SELECT DISTINCT type FROM items ORDER BY type COLLATE NOCASE")
            ]
        self.send_json(200, {"items": [row_dict(row) for row in rows], "types": types})

    def import_uploads(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data;"):
            raise APIError(415, "Envie as planilhas como formulário multipart.")
        body = self.read_body()
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii")
            + body
        )
        uploads: list[tuple[str, bytes]] = []
        for part in message.iter_parts():
            filename = part.get_filename()
            if filename:
                uploads.append((Path(filename).name, part.get_payload(decode=True) or b""))
        if not uploads:
            raise APIError(400, "Selecione ao menos uma planilha XLSX.")
        inserted = 0
        duplicates = 0
        errors: list[str] = []
        for filename, content in uploads:
            if Path(filename).suffix.lower() != ".xlsx":
                errors.append(f"{filename}: somente arquivos .xlsx são aceitos.")
                continue
            try:
                rows = spreadsheet_rows(content)
            except APIError as exc:
                errors.append(f"{filename}: {exc}")
                continue
            with db_connect() as db:
                for line_number, row in enumerate(rows, start=2):
                    try:
                        item = clean_item(row)
                        item_fingerprint = fingerprint(item)
                        if db.execute(
                            "SELECT 1 FROM items WHERE fingerprint = ?", (item_fingerprint,)
                        ).fetchone():
                            duplicates += 1
                            continue
                        now = utc_now().isoformat()
                        values = [item[field] for field in FIELDS]
                        db.execute(
                            f"INSERT INTO items ({', '.join(FIELDS)}, fingerprint, created_at, updated_at) "
                            f"VALUES ({', '.join('?' for _ in FIELDS)}, ?, ?, ?)",
                            (*values, item_fingerprint, now, now),
                        )
                        inserted += 1
                    except (APIError, sqlite3.IntegrityError) as exc:
                        errors.append(f"{filename}, linha {line_number}: {exc}")
        self.send_json(
            200,
            {"inserted": inserted, "duplicates": duplicates, "errors": errors},
        )

    def list_loans(self, query: dict[str, list[str]]) -> None:
        self.require_user()
        status = query.get("status", ["open"])[0]
        conditions: list[str] = []
        parameters: list[object] = []
        if status == "open":
            conditions.append("l.returned_at IS NULL")
        elif status == "returned":
            conditions.append("l.returned_at IS NOT NULL")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with db_connect() as db:
            rows = db.execute(
                "SELECT l.id, l.item_id, l.borrower, l.borrower_ref, l.loaned_at, l.due_date, "
                "l.returned_at, i.title, i.registration, u.display_name AS loaned_by_name, "
                "CASE WHEN l.returned_at IS NULL AND l.due_date < ? THEN 1 ELSE 0 END AS overdue "
                f"FROM loans l JOIN items i ON i.id = l.item_id "
                f"JOIN users u ON u.id = l.loaned_by {where} "
                "ORDER BY l.returned_at IS NULL DESC, l.due_date ASC, l.loaned_at DESC LIMIT 2000",
                [date.today().isoformat(), *parameters],
            ).fetchall()
        self.send_json(200, {"loans": [row_dict(row) for row in rows]})

    def create_loan(self, user: sqlite3.Row) -> None:
        payload = self.read_json()
        try:
            item_id = int(payload.get("itemId", 0))
        except (ValueError, TypeError) as exc:
            raise APIError(400, "Selecione um item válido.") from exc
        borrower = str(payload.get("borrower", "")).strip()
        borrower_ref = str(payload.get("borrowerRef", "")).strip()
        due_date = str(payload.get("dueDate", "")).strip()
        if not borrower:
            raise APIError(400, "Informe o nome da pessoa que retirou o item.")
        if len(borrower) > 150 or len(borrower_ref) > 80:
            raise APIError(400, "Nome ou identificação ultrapassa o limite permitido.")
        try:
            parsed_due_date = date.fromisoformat(due_date)
        except ValueError as exc:
            raise APIError(400, "Informe uma data de devolução válida.") from exc
        if parsed_due_date < date.today():
            raise APIError(400, "A data de devolução não pode estar no passado.")
        with db_connect() as db:
            db.execute("BEGIN IMMEDIATE")
            item = db.execute(
                "SELECT copies FROM items WHERE id = ?", (item_id,)
            ).fetchone()
            if item is None:
                raise APIError(404, "Item não encontrado.")
            borrowed = db.execute(
                "SELECT COUNT(*) FROM loans WHERE item_id = ? AND returned_at IS NULL",
                (item_id,),
            ).fetchone()[0]
            if borrowed >= item["copies"]:
                raise APIError(409, "Não há exemplar disponível para empréstimo.")
            cursor = db.execute(
                "INSERT INTO loans (item_id, borrower, borrower_ref, loaned_by, loaned_at, due_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, borrower, borrower_ref, user["id"], utc_now().isoformat(), due_date),
            )
        self.send_json(201, {"id": int(cursor.lastrowid)})

    def return_loan(self, user: sqlite3.Row, loan_id: int) -> None:
        with db_connect() as db:
            result = db.execute(
                "UPDATE loans SET returned_at = ?, returned_by = ? "
                "WHERE id = ? AND returned_at IS NULL",
                (utc_now().isoformat(), user["id"], loan_id),
            )
            if result.rowcount == 0:
                exists = db.execute("SELECT 1 FROM loans WHERE id = ?", (loan_id,)).fetchone()
                if exists is None:
                    raise APIError(404, "Empréstimo não encontrado.")
                raise APIError(409, "Este empréstimo já foi devolvido.")
        self.send_json(200, {"ok": True})

    def list_users(self) -> None:
        self.require_admin()
        with db_connect() as db:
            rows = db.execute(
                "SELECT id, username, display_name, role, active, created_at FROM users ORDER BY display_name"
            ).fetchall()
        self.send_json(200, {"users": [row_dict(row) for row in rows]})

    def create_user(self) -> None:
        self.require_admin(write=True)
        payload = self.read_json()
        username = validate_username(payload.get("username"))
        display_name = str(payload.get("displayName", "")).strip()
        if not display_name or len(display_name) > 120:
            raise APIError(400, "Informe um nome com até 120 caracteres.")
        role = str(payload.get("role", "staff"))
        if role not in ("admin", "staff"):
            raise APIError(400, "Perfil inválido.")
        password = validate_password(payload.get("password"))
        try:
            with db_connect() as db:
                cursor = db.execute(
                    "INSERT INTO users (username, display_name, password_hash, role, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (username, display_name, password_hash(password), role, utc_now().isoformat()),
                )
        except sqlite3.IntegrityError as exc:
            raise APIError(409, "Este nome de usuário já está cadastrado.") from exc
        self.send_json(201, {"id": int(cursor.lastrowid)})

    def update_user(self, user_id: int) -> None:
        actor = self.require_admin(write=True)
        payload = self.read_json()
        role = str(payload.get("role", "staff"))
        active = payload.get("active")
        display_name = str(payload.get("displayName", "")).strip()
        if role not in ("admin", "staff") or not isinstance(active, bool):
            raise APIError(400, "Perfil ou situação do usuário inválidos.")
        if not display_name or len(display_name) > 120:
            raise APIError(400, "Informe um nome com até 120 caracteres.")
        if actor["id"] == user_id and (role != "admin" or not active):
            raise APIError(400, "Não é permitido remover ou desativar seu próprio perfil administrador.")
        with db_connect() as db:
            current = db.execute(
                "SELECT role, active FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if current is None:
                raise APIError(404, "Usuário não encontrado.")
            if current["role"] == "admin" and current["active"] and (role != "admin" or not active):
                other_admins = db.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1 AND id != ?",
                    (user_id,),
                ).fetchone()[0]
                if other_admins == 0:
                    raise APIError(409, "O sistema precisa manter ao menos um administrador ativo.")
            result = db.execute(
                "UPDATE users SET display_name = ?, role = ?, active = ? WHERE id = ?",
                (display_name, role, int(active), user_id),
            )
            if result.rowcount == 0:
                raise APIError(404, "Usuário não encontrado.")
            if not active:
                db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        self.send_json(200, {"ok": True})

    def reset_user_password(self, user_id: int) -> None:
        self.require_admin(write=True)
        payload = self.read_json()
        password = validate_password(payload.get("password"))
        with db_connect() as db:
            result = db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash(password), user_id),
            )
            if result.rowcount == 0:
                raise APIError(404, "Usuário não encontrado.")
            db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        self.send_json(200, {"ok": True})

    def change_password(self) -> None:
        user = self.require_user(write=True)
        payload = self.read_json()
        old_password = payload.get("oldPassword", "")
        if not isinstance(old_password, str):
            old_password = ""
        new_password = validate_password(payload.get("newPassword"))
        with db_connect() as db:
            row = db.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
            ).fetchone()
            if row is None or not password_matches(old_password, row["password_hash"]):
                raise APIError(400, "A senha atual não confere.")
            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash(new_password), user["id"]),
            )
        self.send_json(200, {"ok": True})

    def reports(self) -> None:
        self.require_user()
        today = date.today().isoformat()
        with db_connect() as db:
            rows = db.execute(
                "SELECT type, COUNT(*) AS titles, SUM(copies) AS copies FROM items "
                "GROUP BY type ORDER BY type COLLATE NOCASE"
            ).fetchall()
            active = db.execute(
                "SELECT COUNT(*) FROM loans WHERE returned_at IS NULL"
            ).fetchone()[0]
            overdue = db.execute(
                "SELECT COUNT(*) FROM loans WHERE returned_at IS NULL AND due_date < ?", (today,)
            ).fetchone()[0]
            returned = db.execute(
                "SELECT COUNT(*) FROM loans WHERE returned_at IS NOT NULL"
            ).fetchone()[0]
            total_items = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        self.send_json(
            200,
            {
                "categories": [row_dict(row) for row in rows],
                "activeLoans": active,
                "overdue": overdue,
                "returnedLoans": returned,
                "titles": total_items,
            },
        )

    def export_report(self, query: dict[str, list[str]]) -> None:
        self.require_user()
        dataset = query.get("dataset", ["items"])[0]
        with db_connect() as db:
            if dataset == "items":
                rows = db.execute(
                    f"SELECT {', '.join(FIELDS)} FROM items ORDER BY title COLLATE NOCASE"
                ).fetchall()
                headers = [FIELD_LABELS[field] for field in FIELDS]
                self.send_csv("catalogo-biblioteca.csv", headers, [list(row) for row in rows])
                return
            if dataset == "loans":
                rows = db.execute(
                    "SELECT i.registration, i.title, l.borrower, l.borrower_ref, l.loaned_at, "
                    "l.due_date, l.returned_at FROM loans l JOIN items i ON i.id = l.item_id "
                    "ORDER BY l.loaned_at DESC"
                ).fetchall()
                self.send_csv(
                    "emprestimos-biblioteca.csv",
                    ["registro", "titulo", "pessoa", "identificacao", "emprestimo", "devolucao_prevista", "devolvido_em"],
                    [list(row) for row in rows],
                )
                return
        raise APIError(400, "Relatório solicitado não reconhecido.")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    ensure_database()
    server = ThreadingHTTPServer((HOST, PORT), BibliotecaHandler)
    invalidate_sessions()
    LOG.info("Sistema Biblioteca disponível em http://%s:%s", HOST, PORT)
    LOG.info("No primeiro acesso, crie o usuário administrador no navegador.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Encerrando o servidor.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
