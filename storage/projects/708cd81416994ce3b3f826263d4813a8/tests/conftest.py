"""Fixtures compartilhadas dos testes do Digitaliza FCJA."""

import os
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault('DATABASE_URL', 'instance/database.sqlite')

from app import app as app_digitaliza  # noqa: E402
from config import Config as classe_config  # noqa: E402
from models.database import inicializar_banco  # noqa: E402
from models.usuario import criar as criar_usuario  # noqa: E402


@pytest.fixture()
def ambiente(tmp_path):
    """Aplicação isolada com pastas e banco em diretório temporário."""
    configuracoes = {
        'TESTING': True,
        'UPLOAD_FOLDER': str(tmp_path / 'uploads'),
        'PASTA_ORIGINAIS': str(tmp_path / 'uploads' / 'originais'),
        'PASTA_PROCESSADAS': str(tmp_path / 'uploads' / 'processadas'),
        'PASTA_CACHE': str(tmp_path / 'uploads' / 'cache'),
        'PASTA_TMP': str(tmp_path / 'uploads' / 'tmp'),
        'DATABASE_PATH': str(tmp_path / 'instance' / 'banco.sqlite'),
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.test',
        'LOGO_PATH': str(RAIZ / 'static' / 'img' / 'logo-fcja.png'),
    }
    app_digitaliza.config.update(configuracoes)
    # Os serviços leem a classe Config diretamente; aplica os overrides
    # também nela para que os testes usem as pastas temporárias.
    for chave, valor in configuracoes.items():
        if chave.isupper() and hasattr(classe_config, chave):
            setattr(classe_config, chave, valor)
    for chave in ('UPLOAD_FOLDER', 'PASTA_ORIGINAIS', 'PASTA_PROCESSADAS',
                  'PASTA_CACHE', 'PASTA_TMP'):
        Path(configuracoes[chave]).mkdir(parents=True, exist_ok=True)
    Path(configuracoes['DATABASE_PATH']).parent.mkdir(parents=True, exist_ok=True)
    inicializar_banco(
        configuracoes['DATABASE_PATH'],
        'admin@teste.local', 'Administrador', 'teste-admin',
    )
    yield app_digitaliza
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture()
def cliente(ambiente):
    return ambiente.test_client()


@pytest.fixture()
def usuario_administrador(ambiente):
    with ambiente.app_context():
        identificador = criar_usuario(
            'Operadora Teste', 'operadora@teste.local', 'senha-forte',
            papel='administrador',
        )
    return identificador


@pytest.fixture()
def cliente_logado(cliente, usuario_administrador):
    cliente.post('/login', data={
        'email': 'operadora@teste.local',
        'senha': 'senha-forte',
    })
    return cliente


@pytest.fixture()
def logo_teste(ambiente, tmp_path):
    """Logo PNG vermelha opaca (simula a logo institucional)."""
    caminho = tmp_path / 'logo-teste.png'
    logo = Image.new('RGBA', (400, 160), (179, 37, 44, 255))
    logo.save(caminho, 'PNG')
    ambiente.config['LOGO_PATH'] = str(caminho)
    return caminho


@pytest.fixture()
def pagina_tiff(tmp_path):
    """Cria uma página TIFF 4000x6000 simulando digitalização em alta."""
    caminho = tmp_path / 'pagina.tif'
    imagem = Image.new('RGB', (4000, 6000), (250, 250, 250))
    for y in range(400, 5600, 120):  # linhas simulando texto
        for x in range(300, 3700, 7):
            imagem.putpixel((x, y), (20, 20, 20))
    imagem.save(caminho, 'TIFF', dpi=(600, 600))
    return caminho


@pytest.fixture()
def pagina_png(tmp_path):
    caminho = tmp_path / 'pagina.png'
    imagem = Image.new('RGB', (1200, 1800), (255, 255, 255))
    imagem.save(caminho, 'PNG', dpi=(300, 300))
    return caminho