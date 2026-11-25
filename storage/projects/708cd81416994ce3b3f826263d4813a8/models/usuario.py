"""Modelo de usuários e autenticação (estrutura simples e expansível)."""

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from models.database import banco

PAPEIS = ('administrador', 'operador', 'visualizador')


def criar(nome, email, senha, papel='operador', caminho=None):
    """Cria um usuário. Levanta ValueError se o e-mail já existir."""
    if papel not in PAPEIS:
        raise ValueError('Papel inválido.')
    if not nome or not email or not senha:
        raise ValueError('Nome, e-mail e senha são obrigatórios.')
    with banco(caminho) as conn:
        existente = conn.execute(
            'SELECT id FROM usuarios WHERE email = ?', (email,)
        ).fetchone()
        if existente:
            raise ValueError('Já existe um usuário com este e-mail.')
        cursor = conn.execute(
            'INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, criado_em) '
            'VALUES (?, ?, ?, ?, 1, ?)',
            (
                nome.strip(),
                email.strip().lower(),
                generate_password_hash(senha),
                papel,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ),
        )
        return cursor.lastrowid


def buscar_por_email(email, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM usuarios WHERE email = ?', (email.strip().lower(),)
        ).fetchone()


def buscar_por_id(usuario_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM usuarios WHERE id = ?', (usuario_id,)
        ).fetchone()


def autenticar(email, senha, caminho=None):
    """Verifica credenciais. Retorna o usuário se válido e ativo."""
    usuario = buscar_por_email(email, caminho)
    if not usuario or not usuario['ativo']:
        return None
    if check_password_hash(usuario['senha_hash'], senha):
        return usuario
    return None


def contar(caminho=None):
    with banco(caminho) as conn:
        return conn.execute('SELECT COUNT(*) AS c FROM usuarios').fetchone()['c']