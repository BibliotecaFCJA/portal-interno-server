"""
Configurações centrais do Digitaliza FCJA.

As configurações sensíveis vêm de variáveis de ambiente (arquivo ".env",
opcional). Nenhuma senha ou segredo é gravado no código-fonte.
"""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _carregar_arquivo_env(caminho=BASE_DIR / '.env'):
    """Carrega variáveis do arquivo .env sem dependências externas.

    Justificativa: o parser é simples e evita adicionar a biblioteca
    python-dotenv, mantendo o projeto com o mínimo de dependências.
    """
    if not caminho.is_file():
        return
    try:
        linhas = caminho.read_text(encoding='utf-8').splitlines()
    except OSError:
        return
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('#') or '=' not in linha:
            continue
        chave, _, valor = linha.partition('=')
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave:
            os.environ.setdefault(chave, valor)


_carregar_arquivo_env()


def _obter_secret_key():
    """Obtém a SECRET_KEY do ambiente; se ausente, gera e persiste localmente."""
    valor = os.environ.get('SECRET_KEY', '').strip()
    if valor:
        return valor
    arquivo = BASE_DIR / 'instance' / '.secret_key'
    try:
        if arquivo.exists():
            chave = arquivo.read_text(encoding='utf-8').strip()
            if chave:
                return chave
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        chave = secrets.token_hex(32)
        arquivo.write_text(chave, encoding='utf-8')
        return chave
    except OSError:
        return secrets.token_hex(32)


def _obter_caminho_banco():
    url = os.environ.get('DATABASE_URL', '').strip()
    if url.startswith('sqlite:///'):
        url = url.replace('sqlite:///', '', 1)
    if not url:
        url = 'instance/database.sqlite'
    if os.path.isabs(url):
        return url
    return str((BASE_DIR / url).resolve())


def _inteiro(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except (TypeError, ValueError):
        return padrao


class Config:
    """Configurações centrais do sistema."""

    # Segurança -------------------------------------------------
    SECRET_KEY = _obter_secret_key()
    MAX_CONTENT_LENGTH = _inteiro('MAX_CONTENT_LENGTH', 1024 * 1024 * 1024)
    MAX_TAMANHO_ARQUIVO = _inteiro('MAX_TAMANHO_ARQUIVO', 500 * 1024 * 1024)

    # Armazenamento ---------------------------------------------
    DATABASE_PATH = _obter_caminho_banco()
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(UPLOAD_FOLDER):
        UPLOAD_FOLDER = str(BASE_DIR / UPLOAD_FOLDER)
    UPLOAD_FOLDER = str(Path(UPLOAD_FOLDER).resolve())
    PASTA_ORIGINAIS = str(Path(UPLOAD_FOLDER) / 'originais')
    PASTA_PROCESSADAS = str(Path(UPLOAD_FOLDER) / 'processadas')
    PASTA_CACHE = str(Path(UPLOAD_FOLDER) / 'cache')
    PASTA_TMP = str(Path(UPLOAD_FOLDER) / 'tmp')

    # Marca d'água institucional ----------------------------------
    LOGO_PATH = str(BASE_DIR / 'static' / 'img' / 'marca-dagua.png')

    # Upload ------------------------------------------------------
    EXTENSOES_IMAGEM = {'jpg', 'jpeg', 'png', 'tif', 'tiff'}
    MIMES_PERMITIDOS = {'image/jpeg', 'image/png', 'image/tiff'}
    MAX_TAMANHO_ARQUIVO = _inteiro('MAX_TAMANHO_ARQUIVO', 500 * 1024 * 1024)

    # Usuário administrador inicial -------------------------------
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@fcja.pb.gov.br').strip()
    ADMIN_NOME = os.environ.get('ADMIN_NOME', 'Administrador')
    ADMIN_SENHA = os.environ.get('ADMIN_SENHA', '') or 'fcja@2026'

    # Servidor ----------------------------------------------------
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORTA = _inteiro('FLASK_PORT', 5000)
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'