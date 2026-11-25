"""
Acesso ao banco de dados SQLite do Digitaliza FCJA.

Cada operação abre uma conexão própria e a fecha ao final — isso evita
problemas de concorrência entre a aplicação web e a thread de
processamento em lote.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config import BASE_DIR

CAMINHO_PADRAO = str(BASE_DIR / 'instance' / 'database.sqlite')

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT 'operador',
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    autor TEXT,
    ano TEXT,
    colecao TEXT,
    descricao TEXT,
    responsavel TEXT,
    data_cadastro TEXT NOT NULL,
    quantidade_paginas INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pendente',
    data_processamento TEXT
);

CREATE TABLE IF NOT EXISTS paginas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    nome_original TEXT NOT NULL,
    arquivo_original TEXT NOT NULL,
    arquivo_processado TEXT,
    largura INTEGER,
    altura INTEGER,
    formato TEXT,
    resolucao TEXT,
    tamanho_bytes INTEGER,
    status_processamento TEXT NOT NULL DEFAULT 'original',
    erro_mensagem TEXT,
    data_processamento TEXT,
    UNIQUE (obra_id, numero),
    UNIQUE (obra_id, arquivo_original)
);

CREATE TABLE IF NOT EXISTS processamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    tamanho_logo TEXT,
    opacidade INTEGER,
    margem TEXT,
    posicao TEXT,
    quantidade_processada INTEGER NOT NULL DEFAULT 0,
    quantidade_erros INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    mensagem_erro TEXT
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    usuario TEXT,
    acao TEXT NOT NULL,
    detalhes TEXT
);

CREATE INDEX IF NOT EXISTS idx_paginas_obra ON paginas(obra_id);
CREATE INDEX IF NOT EXISTS idx_obras_status ON obras(status);
"""


def _resolver_caminho(caminho=None):
    """Resolve o caminho do banco: explícito, da aplicação Flask ou padrão."""
    if caminho:
        return caminho
    try:
        from flask import current_app
        return current_app.config['DATABASE_PATH']
    except RuntimeError:
        return CAMINHO_PADRAO


def conectar(caminho=None):
    """Abre uma nova conexão SQLite (uma por uso, segura para threads)."""
    caminho = _resolver_caminho(caminho)
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def banco(caminho=None):
    """Contexto de conexão: faz commit ao final e sempre fecha."""
    conn = conectar(caminho)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_banco(caminho, admin_email, admin_nome, admin_senha):
    """Cria o banco, as tabelas e os dados iniciais."""
    conn = conectar(caminho)
    try:
        conn.executescript(SCHEMA)
        _garantir_admin(conn, admin_email, admin_nome, admin_senha)
        _garantir_configuracoes(conn)
        conn.commit()
    finally:
        conn.close()


def recuperar_interrupcoes(caminho):
    """Corrige estados deixados por processamentos interrompidos."""
    with banco(caminho) as conn:
        conn.execute(
            "UPDATE paginas SET status_processamento = 'erro', "
            "erro_mensagem = 'Processamento interrompido por reinicialização do sistema.' "
            "WHERE status_processamento = 'processando'"
        )
        obras = conn.execute(
            "SELECT id FROM obras WHERE status = 'processando'"
        ).fetchall()
        for obra in obras:
            total = conn.execute(
                'SELECT COUNT(*) AS c FROM paginas WHERE obra_id = ?',
                (obra['id'],),
            ).fetchone()['c']
            ok = conn.execute(
                "SELECT COUNT(*) AS c FROM paginas "
                "WHERE obra_id = ? AND status_processamento = 'processada'",
                (obra['id'],),
            ).fetchone()['c']
            if total and ok == total:
                status = 'processada'
            elif ok:
                status = 'parcial'
            else:
                status = 'pendente'
            conn.execute(
                'UPDATE obras SET status = ? WHERE id = ?', (status, obra['id'])
            )


def _garantir_admin(conn, email, nome, senha):
    from werkzeug.security import generate_password_hash
    total = conn.execute('SELECT COUNT(*) AS c FROM usuarios').fetchone()['c']
    if total:
        return
    conn.execute(
        'INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, criado_em) '
        'VALUES (?, ?, ?, ?, 1, ?)',
        (
            nome,
            email,
            generate_password_hash(senha),
            'administrador',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ),
    )


def _garantir_configuracoes(conn):
    from models.configuracoes import PADROES
    for chave, valor in PADROES.items():
        conn.execute(
            'INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)',
            (chave, str(valor)),
        )