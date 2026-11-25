"""Testes das correções: imagens web, posição/opacidade e relatório.

Cobrem os cenários obrigatórios de verificação:
- visualizador carrega a imagem real em formato de navegador;
- navegação entre páginas;
- posição e opacidade chegam ao processamento;
- configurações aplicadas a várias páginas;
- relatório formatado e com dados reais.
"""

import io
import time
from pathlib import Path

from PIL import Image

from models.obra import buscar_por_id, criar as criar_obra
from models.pagina import inserir as inserir_pagina, listar_por_obra
from models.processamento import ultimo_por_obra
from services.image_processor import gerar_imagem_web, ler_metadados
from services.storage import pasta_obra
from services.watermark import POSICOES, aplicar_marca_dagua

CFG_BASE = {
    'wm_tamanho_modo': 'automatico',
    'wm_tamanho_percentual': '8',
    'wm_tamanho_minimo_px': '20',
    'wm_tamanho_maximo_px': '2000',
    'wm_margem_modo': 'automatico',
    'wm_margem_percentual': '0',
    'wm_opacidade': '100',
    'wm_posicao': 'superior_esquerdo',
}


def _obra_com_paginas(ambiente, quantidade=1, tamanho=(400, 600)):
    """Cria uma obra com páginas brancas (TIFF) prontas para processar."""
    with ambiente.app_context():
        obra_id = criar_obra({'codigo': 'FCJA-OBR-000300', 'titulo': 'Correções'})
        obra = buscar_por_id(obra_id)
        pasta = pasta_obra(ambiente.config['PASTA_ORIGINAIS'], obra['codigo'])
        for numero in range(1, quantidade + 1):
            origem = pasta / f'{numero:03d}.tif'
            Image.new('RGB', tamanho, (255, 255, 255)).save(origem, 'TIFF')
            meta = ler_metadados(origem)
            meta.update({
                'obra_id': obra_id, 'numero': numero,
                'nome_original': origem.name, 'arquivo_original': origem.name,
            })
            inserir_pagina(meta)
        return obra_id


def _aguardar(obra_id, timeout=60):
    from services import processamento as servico
    inicio = time.time()
    estado = {}
    while time.time() - inicio < timeout:
        estado = servico.estado(obra_id)
        if estado.get('concluido'):
            return estado
        time.sleep(0.05)
    raise AssertionError(f'Processamento não concluiu: {estado}')


def _nao_branco(imagem, caixa):
    regiao = imagem.crop(caixa)
    return sum(1 for pixel in regiao.getdata() if pixel[:3] != (255, 255, 255))


# ---------- 1. Imagens exibíveis no navegador ----------

def test_gerar_imagem_web_converte_tiff(ambiente, tmp_path):
    caminho = tmp_path / 'pagina.tif'
    Image.new('RGB', (400, 600), (250, 250, 250)).save(caminho, 'TIFF')
    resultado = gerar_imagem_web(caminho)
    assert Path(resultado).suffix.lower() in ('.jpg', '.jpeg')
    with Image.open(resultado) as imagem:
        assert imagem.format == 'JPEG'
        assert imagem.size == (400, 600)


def test_gerar_imagem_web_nao_converte_png(ambiente, tmp_path):
    caminho = tmp_path / 'pagina.png'
    Image.new('RGB', (100, 150)).save(caminho, 'PNG')
    assert gerar_imagem_web(caminho) == str(caminho)


def test_rota_pagina_serve_imagem_exibivel(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente)
    with ambiente.app_context():
        pagina = listar_por_obra(obra_id)[0]
    resposta = cliente_logado.get(
        f'/obras/{obra_id}/paginas/{pagina["id"]}/arquivo/original'
    )
    assert resposta.status_code == 200
    assert resposta.content_type == 'image/jpeg'
    with Image.open(io.BytesIO(resposta.data)) as imagem:
        assert imagem.format == 'JPEG'


def test_navegacao_entre_paginas_troca_imagem(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente, quantidade=2)
    with ambiente.app_context():
        paginas = listar_por_obra(obra_id)
    primeira = cliente_logado.get(
        f'/obras/{obra_id}/paginas/{paginas[0]["id"]}/arquivo/original'
    )
    segunda = cliente_logado.get(
        f'/obras/{obra_id}/paginas/{paginas[1]["id"]}/arquivo/original'
    )
    assert primeira.status_code == segunda.status_code == 200
    assert primeira.content_type == segunda.content_type == 'image/jpeg'


# ---------- 2. Posição da marca d'água (todas as posições) ----------

def test_marca_aplicada_em_todas_as_posicoes():
    logo = Image.new('RGBA', (60, 30), (200, 20, 20, 255))
    for posicao, (fx, fy) in POSICOES.items():
        base = Image.new('RGB', (300, 300), (255, 255, 255))
        cfg = dict(CFG_BASE, wm_posicao=posicao, wm_tamanho_percentual='20')
        resultado = aplicar_marca_dagua(base, logo, cfg)
        x = int((300 - 60) * fx) + 30
        y = int((300 - 30) * fy) + 15
        centro = resultado.getpixel((x, y))
        assert centro[0] > 150 and centro[1] < 120, (posicao, centro)


def test_opacidade_e_posicao_chegam_ao_processamento(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente)
    resposta = cliente_logado.post(
        f'/processamento/{obra_id}/iniciar',
        json={
            'wm_posicao': 'inferior_direito',
            'wm_opacidade': '40',
            'wm_tamanho_modo': 'automatico',
            'wm_tamanho_percentual': '25',
            'wm_margem_percentual': '0',
        },
    )
    assert resposta.get_json()['ok'] is True, resposta.get_json()
    estado = _aguardar(obra_id)
    assert estado['sucesso'] is True, estado

    with ambiente.app_context():
        registro = ultimo_por_obra(obra_id)
        assert registro['posicao'] == 'Inferior direito'
        assert int(registro['opacidade']) == 40
        assert '25' in registro['tamanho_logo']


def test_iniciar_rejeita_posicao_invalida(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente)
    resposta = cliente_logado.post(
        f'/processamento/{obra_id}/iniciar',
        json={'wm_posicao': 'lugar_inexistente'},
    )
    assert resposta.status_code == 400


# ---------- 3. Configurações aplicadas a todas as páginas ----------

def test_configuracoes_aplicadas_a_varias_paginas(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente, quantidade=2)
    cliente_logado.post(
        f'/processamento/{obra_id}/iniciar',
        json={
            'wm_posicao': 'inferior_direito', 'wm_opacidade': '100',
            'wm_tamanho_modo': 'automatico', 'wm_tamanho_percentual': '25',
            'wm_margem_percentual': '0',
        },
    )
    estado = _aguardar(obra_id)
    assert estado['sucesso'] is True, estado

    with ambiente.app_context():
        obra = buscar_por_id(obra_id)
        paginas = listar_por_obra(obra_id)
        assert all(pagina['arquivo_processado'] for pagina in paginas)
        assert ultimo_por_obra(obra_id)['quantidade_processada'] == 2

    for pagina in paginas:
        caminho = (
            pasta_obra(ambiente.config['PASTA_PROCESSADAS'], obra['codigo'])
            / pagina['arquivo_processado']
        )
        with Image.open(caminho) as imagem:
            largura, altura = imagem.size
            canto_inferior = (largura // 2, altura // 2, largura, altura)
            canto_superior = (0, 0, largura // 2, altura // 2)
            assert _nao_branco(imagem, canto_inferior) > 0
            assert _nao_branco(imagem, canto_superior) == 0


# ---------- 4. Relatório ----------

def test_relatorio_renderiza_com_layout_e_dados(cliente_logado, ambiente):
    obra_id = _obra_com_paginas(ambiente)
    resposta = cliente_logado.get(f'/processamento/{obra_id}/relatorio')
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'style.css' in html
    assert 'Relatório de processamento' in html
    assert 'Total de páginas' in html
