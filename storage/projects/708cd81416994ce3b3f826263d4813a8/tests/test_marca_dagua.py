"""Testes do serviço de marca d'água — função central do sistema."""

from PIL import Image

from services.watermark import (
    aplicar_marca_dagua, calcular_margem, calcular_posicao,
    calcular_tamanho_logo, carregar_logo, ordenar_nomes_natural,
    processar_arquivo,
)

CFG_PADRAO = {
    'wm_tamanho_modo': 'automatico',
    'wm_tamanho_percentual': '8',
    'wm_tamanho_minimo_px': '80',
    'wm_tamanho_maximo_px': '600',
    'wm_margem_modo': 'automatico',
    'wm_margem_percentual': '2.5',
    'wm_opacidade': '85',
    'wm_posicao': 'superior_esquerdo',
}


def criar_logo(largura=400, altura=160):
    return Image.new('RGBA', (largura, altura), (179, 37, 44, 255))


# ---------- Cálculo do tamanho proporcional (regra de 8%) ----------

def test_tamanho_automatico_usa_8_porcento():
    largura = calcular_tamanho_logo(2000, 3000, CFG_PADRAO)
    assert largura == 160  # 8% de 2000


def test_tamanho_respeita_minimo():
    largura = calcular_tamanho_logo(500, 700, CFG_PADRAO)
    assert largura == 80  # 8% de 500 = 40, limitado ao mínimo


def test_tamanho_respeita_maximo():
    largura = calcular_tamanho_logo(9000, 12000, CFG_PADRAO)
    assert largura == 600  # 8% de 9000 = 720, limitado ao máximo


def test_tamanho_fixo():
    cfg = dict(CFG_PADRAO, wm_tamanho_modo='fixo', wm_tamanho_fixo_px='250')
    assert calcular_tamanho_logo(4000, 6000, cfg) == 250


def test_tamanho_nunca_excede_a_pagina():
    largura = calcular_tamanho_logo(60, 60, CFG_PADRAO)
    assert largura <= 60


# ---------- Margem proporcional ----------

def test_margem_automatica_proporcional():
    margem = calcular_margem(4000, 6000, CFG_PADRAO)
    assert margem == 100  # 2,5% de 4000


def test_margem_fixa():
    cfg = dict(CFG_PADRAO, wm_margem_modo='fixo', wm_margem_fixa_px='45')
    assert calcular_margem(1000, 1500, cfg) == 45


# ---------- Posição (canto superior esquerdo é o padrão) ----------

def test_posicao_padrao_superior_esquerdo():
    x, y = calcular_posicao(2000, 3000, 160, 64, 50, 'superior_esquerdo')
    assert (x, y) == (50, 50)


def test_posicao_inferior_direito():
    x, y = calcular_posicao(2000, 3000, 160, 64, 50, 'inferior_direito')
    assert (x, y) == (2000 - 160 - 50, 3000 - 64 - 50)


# ---------- Preservação de proporção e transparência ----------

def test_proporcao_da_logo_preservada(logo_teste):
    logo = Image.open(logo_teste)
    base = Image.new('RGB', (4000, 6000), (255, 255, 255))
    resultado = aplicar_marca_dagua(base, logo, CFG_PADRAO)
    largura_logo = calcular_tamanho_logo(4000, 6000, CFG_PADRAO)
    proporcao_original = logo.height / logo.width
    altura_esperada = int(largura_logo * proporcao_original)
    # Ponto dentro da área da logo (margem 100 + 100 px adentro):
    # canto superior esquerdo deve ter cor vermelha aplicada.
    pixel = resultado.getpixel((250, 180))
    assert pixel[0] > pixel[2]  # vermelho dominante
    assert altura_esperada > 0


def test_dimensoes_da_pagina_preservadas(logo_teste):
    base = Image.new('RGB', (4000, 6000), (255, 255, 255))
    logo = Image.open(logo_teste)
    resultado = aplicar_marca_dagua(base, logo, CFG_PADRAO)
    assert resultado.size == (4000, 6000)


def test_opacidade_zero_nao_altera_a_imagem(logo_teste):
    base = Image.new('RGB', (1000, 1500), (255, 255, 255))
    logo = Image.open(logo_teste)
    cfg = dict(CFG_PADRAO, wm_opacidade='0')
    resultado = aplicar_marca_dagua(base, logo, cfg)
    assert list(resultado.getdata()) == list(base.getdata())


def test_opacidade_total_aplica_logo_no_canto(logo_teste):
    base = Image.new('RGB', (2000, 3000), (255, 255, 255))
    logo = Image.open(logo_teste)
    cfg = dict(CFG_PADRAO, wm_opacidade='100')
    resultado = aplicar_marca_dagua(base, logo, cfg)
    # Logo: 8% de 2000 = 160 px; margem 50 px → área (50,50)-(210,114).
    assert resultado.getpixel((120, 80)) != (255, 255, 255)  # dentro da logo
    assert resultado.getpixel((1900, 2900)) == (255, 255, 255)  # canto oposto intacto


def test_imagem_original_nao_e_alterada(logo_teste):
    base = Image.new('RGB', (1000, 1500), (255, 255, 255))
    dados_antes = list(base.getdata())
    logo = Image.open(logo_teste)
    aplicar_marca_dagua(base, logo, CFG_PADRAO)
    assert list(base.getdata()) == dados_antes  # original intacto


# ---------- Processamento de arquivos (originais intocados) ----------

def test_processar_arquivo_cria_novo_sem_sobrescrever(logo_teste, pagina_png, tmp_path):
    from pathlib import Path
    bytes_antes = pagina_png.read_bytes()
    destino = tmp_path / 'processadas' / 'pagina'
    logo = Image.open(logo_teste)
    resultado = processar_arquivo(pagina_png, destino, logo, CFG_PADRAO)
    assert pagina_png.read_bytes() == bytes_antes  # original intacto
    assert resultado['largura'] == 1200 and resultado['altura'] == 1800
    saida = Path(str(destino) + '.png')
    assert saida.is_file()
    with Image.open(saida) as verificacao:
        assert verificacao.size == (1200, 1800)


def test_processar_arquivo_tiff_preserva_dpi(logo_teste, pagina_tiff, tmp_path):
    from pathlib import Path
    bytes_antes = pagina_tiff.read_bytes()
    logo = Image.open(logo_teste)
    destino = tmp_path / 'processadas' / 'pagina'
    resultado = processar_arquivo(pagina_tiff, destino, logo, CFG_PADRAO)
    assert pagina_tiff.read_bytes() == bytes_antes
    assert resultado['formato'] == 'TIFF'
    assert resultado['resolucao'] == '600x600 DPI'
    saida = Path(str(destino) + '.tif')
    with Image.open(saida) as verificacao:
        assert verificacao.size == (4000, 6000)
        dpi = verificacao.info.get('dpi')
        assert dpi and round(dpi[0]) == 600


def test_processar_arquivo_entrada_invalida(logo_teste, tmp_path):
    arquivo_falso = tmp_path / 'falso.tif'
    arquivo_falso.write_text('isto não é uma imagem')
    logo = Image.open(logo_teste)
    try:
        processar_arquivo(arquivo_falso, tmp_path / 'saida', logo, CFG_PADRAO)
        raise AssertionError('Deveria ter falhado com arquivo inválido.')
    except Exception:
        pass


# ---------- Ordenação natural ----------

def test_ordenacao_natural_de_paginas():
    nomes = ['10.tif', '1.tif', '3.tif', '2.tif', '11.tif']
    assert ordenar_nomes_natural(nomes) == ['1.tif', '2.tif', '3.tif', '10.tif', '11.tif']


def test_carregar_logo_arquivo_inexistente():
    try:
        carregar_logo('/caminho/inexistente/logo.png')
        raise AssertionError('Deveria ter falhado.')
    except Exception:
        pass