"""Testes web: autenticação, cadastro de obras, upload, ZIP e segurança."""

import io
import zipfile
from pathlib import Path

from PIL import Image

from models.obra import buscar_por_id, criar as criar_obra


def imagem_em_memoria(formato='PNG', tamanho=(800, 1200)):
    buffer = io.BytesIO()
    Image.new('RGB', tamanho, (240, 240, 240)).save(buffer, formato)
    buffer.seek(0)
    return buffer


# ---------- Autenticação ----------

def test_login_obrigatorio_redireciona(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 302
    assert '/login' in resposta.headers['Location']


def test_login_com_credenciais_validas(cliente, usuario_administrador):
    resposta = cliente.post('/login', data={
        'email': 'operadora@teste.local', 'senha': 'senha-forte',
    }, follow_redirects=True)
    assert resposta.status_code == 200
    assert 'Dashboard'.encode() in resposta.data or 'Olá'.encode() in resposta.data


def test_login_com_senha_incorreta(cliente, usuario_administrador):
    resposta = cliente.post('/login', data={
        'email': 'operadora@teste.local', 'senha': 'errada',
    }, follow_redirects=True)
    assert 'incorretos'.encode() in resposta.data


def test_logout(cliente, cliente_logado):
    resposta = cliente_logado.get('/logout')
    assert resposta.status_code == 302
    resposta = cliente_logado.get('/', follow_redirects=False)
    assert resposta.status_code == 302  # volta a exigir login


# ---------- Cadastro de obra ----------

def test_cadastrar_obra_com_codigo_sugerido(cliente_logado):
    resposta = cliente_logado.post('/obras/nova', data={
        'titulo': 'A Bagaceira', 'autor': 'José Américo de Almeida',
        'ano': '1928', 'colecao': 'Obras raras', 'codigo': '',
    }, follow_redirects=True)
    assert resposta.status_code == 200
    assert 'sucesso'.encode() in resposta.data or 'A Bagaceira'.encode() in resposta.data


def test_cadastrar_obra_codigo_duplicado_rejeitado(cliente_logado, ambiente):
    with ambiente.app_context():
        criar_obra({'codigo': 'FCJA-OBR-000001', 'titulo': 'Primeira'})
    resposta = cliente_logado.post('/obras/nova', data={
        'titulo': 'Segunda', 'codigo': 'FCJA-OBR-000001',
    }, follow_redirects=True)
    assert 'Já existe'.encode() in resposta.data


def test_cadastrar_obra_sem_titulo(cliente_logado):
    resposta = cliente_logado.post('/obras/nova', data={'titulo': ''},
                                   follow_redirects=True)
    assert 'título'.encode() in resposta.data


# ---------- Upload de páginas ----------

def _obra(ambiente):
    with ambiente.app_context():
        return criar_obra({
            'codigo': 'FCJA-OBR-000099', 'titulo': 'Obra de Teste',
        })


def test_upload_de_paginas(cliente_logado, ambiente):
    obra_id = _obra(ambiente)
    dados = {'arquivos': [
        (io.BytesIO(imagem_em_memoria().getvalue()), '1.png'),
        (io.BytesIO(imagem_em_memoria().getvalue()), '2.png'),
    ]}
    resposta = cliente_logado.post(
        f'/obras/{obra_id}/paginas/upload', data=dados,
        content_type='multipart/form-data',
    )
    corpo = resposta.get_json()
    assert corpo['ok'] is True, corpo
    assert corpo['resumo']['adicionadas'] == 2
    # Arquivos gravados na pasta de originais com nomes normalizados.
    pasta = Path(ambiente.config['PASTA_ORIGINAIS']) / 'FCJA-OBR-000099'
    assert (pasta / '001.png').is_file()
    assert (pasta / '002.png').is_file()


def test_upload_formato_nao_suportado(cliente_logado, ambiente):
    obra_id = _obra(ambiente)
    dados = {'arquivos': [
        (io.BytesIO(b'<html>nao e imagem</html>'), 'site.html'),
    ]}
    resposta = cliente_logado.post(
        f'/obras/{obra_id}/paginas/upload', data=dados,
        content_type='multipart/form-data',
    )
    corpo = resposta.get_json()
    assert corpo['resumo']['ignoradas'] == 1, corpo
    assert not (Path(ambiente.config['PASTA_ORIGINAIS']) / 'FCJA-OBR-000099').exists()


def test_upload_arquivo_corrompido_e_rejeitado(cliente_logado, ambiente):
    obra_id = _obra(ambiente)
    dados = {'arquivos': [
        (io.BytesIO(b'isso parece png mas nao e'), 'falso.png'),
    ]}
    resposta = cliente_logado.post(
        f'/obras/{obra_id}/paginas/upload', data=dados,
        content_type='multipart/form-data',
    )
    corpo = resposta.get_json()
    assert corpo['resumo']['ignoradas'] == 1, corpo


def test_upload_exige_login(cliente):
    resposta = cliente.post('/obras/1/paginas/upload')
    assert resposta.status_code == 302


# ---------- Exclusão protegida ----------

def test_exclusao_exige_confirmacao_por_codigo(cliente_logado, ambiente):
    obra_id = _obra(ambiente)
    resposta = cliente_logado.post(
        f'/obras/{obra_id}/excluir', data={'confirmar': 'CODIGO-ERRADO'},
        follow_redirects=True,
    )
    assert 'inválida'.encode() in resposta.data
    with ambiente.app_context():
        assert buscar_por_id(obra_id) is not None


def test_exclusao_com_confirmacao_remove_obra(cliente_logado, ambiente):
    obra_id = _obra(ambiente)
    cliente_logado.post(
        f'/obras/{obra_id}/excluir', data={'confirmar': 'FCJA-OBR-000099'},
        follow_redirects=True,
    )
    with ambiente.app_context():
        assert buscar_por_id(obra_id) is None


# ---------- Proteção contra path traversal ----------

def test_caminho_interno_rejeita_travessia():
    from services.storage import caminho_interno
    try:
        caminho_interno('/tmp/base-segura', '..', '..', 'etc', 'passwd')
        raise AssertionError('Deveria rejeitar caminho fora da base.')
    except ValueError:
        pass


def test_sanitizacao_de_codigo():
    from services.storage import sanitizar_codigo
    assert sanitizar_codigo('../../etc') == 'etc'
    assert sanitizar_codigo('FCJA-OBR-000001!@#') == 'FCJA-OBR-000001'


def test_nome_arquivo_seguro():
    from services.storage import nome_arquivo_seguro
    assert nome_arquivo_seguro('001.tif') is True
    assert nome_arquivo_seguro('../001.tif') is False
    assert nome_arquivo_seguro('pasta/001.tif') is False
    assert nome_arquivo_seguro('') is False


# ---------- Serviço de ZIP ----------

def test_gerar_zip_apenas_com_processadas(ambiente, logo_teste):
    """O ZIP padrão NÃO deve incluir os originais."""
    from services.image_processor import ler_metadados
    from services.watermark import processar_arquivo
    from services.storage import pasta_obra
    from models.pagina import inserir as inserir_pagina
    from models.pagina import atualizar_processamento

    obra_id = _obra(ambiente)
    with ambiente.app_context():
        obra = buscar_por_id(obra_id)
        pasta = pasta_obra(ambiente.config['PASTA_ORIGINAIS'], obra['codigo'])
        origem = pasta / '001.png'
        Image.new('RGB', (800, 1200), (255, 255, 255)).save(origem, 'PNG')
        metadados = ler_metadados(origem)
        metadados.update({'obra_id': obra_id, 'numero': 1,
                          'nome_original': 'capa.png',
                          'arquivo_original': origem.name})
        pagina_id = inserir_pagina(metadados)

    logo = Image.open(logo_teste)
    saida = pasta_obra(ambiente.config['PASTA_PROCESSADAS'],
                       obra['codigo']) / '001'
    resultado = processar_arquivo(
        origem, saida, logo,
        {'wm_opacidade': '85', 'wm_posicao': 'superior_esquerdo'},
    )
    with ambiente.app_context():
        atualizar_processamento(
            pagina_id, Path(resultado['caminho']).name,
            resultado['largura'], resultado['altura'], resultado['resolucao'],
            caminho=ambiente.config['DATABASE_PATH'],
        )

    from services.zip_service import gerar_zip_obra
    caminho_zip, quantidade = gerar_zip_obra(
        obra_id, caminho_banco=ambiente.config['DATABASE_PATH'],
    )
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        nomes = arquivo_zip.namelist()
    assert '001.png' in nomes
    assert quantidade == 1


# ---------- Modelos ----------

def test_geracao_de_codigo_sequencial(ambiente):
    with ambiente.app_context():
        primeiro = criar_obra({'codigo': '', 'titulo': 'A'})
        # gerar_proximo_codigo respeita os existentes
        from models.obra import gerar_proximo_codigo
        proximo = gerar_proximo_codigo(ambiente.config['DATABASE_PATH'])
        assert proximo.endswith('000002')
        assert primeiro > 0


def test_logs_registrados(cliente_logado, ambiente):
    with ambiente.app_context():
        from models.logs import listar as listar_logs
        cliente_logado.post('/obras/nova', data={
            'titulo': 'Obra com log', 'codigo': '',
        })
        linhas, total = listar_logs(
            caminho=ambiente.config['DATABASE_PATH'],
        )
        acoes = [linha['acao'] for linha in linhas]
        assert 'Obra criada' in acoes
        assert total >= 1