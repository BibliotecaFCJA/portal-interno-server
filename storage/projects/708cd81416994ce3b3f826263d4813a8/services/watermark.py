"""
Serviço de marca d'água — Digitaliza FCJA.

Princípios:
- O arquivo ORIGINAL nunca é alterado: a imagem é aberta em modo leitura,
  processada em memória e salva em um NOVO arquivo (pasta "processadas").
- A proporção (aspect ratio) da logo é sempre preservada.
- O tamanho da logo é calculado proporcionalmente à página, com limites
  mínimo e máximo configuráveis.
- A resolução original da página é preservada (DPI e dimensões).
"""

from pathlib import Path

from PIL import Image

from services.storage import chave_natural

# Posições suportadas: (fator_x, fator_y) — 0 = início, 1 = fim.
POSICOES = {
    'superior_esquerdo': (0.0, 0.0),
    'superior_centro': (0.5, 0.0),
    'superior_direito': (1.0, 0.0),
    'centro_esquerdo': (0.0, 0.5),
    'centro': (0.5, 0.5),
    'centro_direito': (1.0, 0.5),
    'inferior_esquerdo': (0.0, 1.0),
    'inferior_centro': (0.5, 1.0),
    'inferior_direito': (1.0, 1.0),
}

# Limites absolutos de segurança (independem das configurações).
LIMITE_ABSOLUTO_MIN = 20
LIMITE_ABSOLUTO_MAX = 2000


class ErroMarcaDagua(Exception):
    """Erro de domínio para falhas na aplicação da marca d'água."""


def carregar_logo(caminho_logo):
    """Carrega a logo com canal alfa. Levanta ErroMarcaDagua se inválida."""
    caminho = Path(caminho_logo)
    if not caminho.is_file():
        raise ErroMarcaDagua(f'Logo não encontrada: {caminho}')
    try:
        logo = Image.open(caminho)
        logo.load()
    except Exception as exc:
        raise ErroMarcaDagua(f'Não foi possível abrir a logo: {exc}') from exc
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    return logo


def calcular_tamanho_logo(largura_imagem, altura_imagem, cfg):
    """Calcula (largura, altura) da logo para uma página.

    Regra: largura da logo = percentual da largura da imagem (padrão 8%),
    limitado por mínimos e máximos configuráveis e por limites absolutos
    de segurança. A altura acompanha a proporção original da logo.
    """
    largura_imagem = max(1, int(largura_imagem))
    altura_imagem = max(1, int(altura_imagem))

    try:
        percentual = float(cfg.get('wm_tamanho_percentual', 8))
    except (TypeError, ValueError):
        percentual = 8.0
    percentual = min(max(percentual, 1.0), 50.0)

    try:
        minimo = int(float(cfg.get('wm_tamanho_minimo_px', 80)))
        maximo = int(float(cfg.get('wm_tamanho_maximo_px', 600)))
    except (TypeError, ValueError):
        minimo, maximo = 80, 600
    minimo = max(minimo, LIMITE_ABSOLUTO_MIN)
    maximo = min(max(maximo, minimo), LIMITE_ABSOLUTO_MAX)

    if str(cfg.get('wm_tamanho_modo', 'automatico')) == 'fixo':
        try:
            largura_logo = int(float(cfg.get('wm_tamanho_fixo_px', 200)))
        except (TypeError, ValueError):
            largura_logo = 200
    else:
        largura_logo = int(round(largura_imagem * percentual / 100.0))

    largura_logo = min(max(largura_logo, minimo), maximo)
    # A logo nunca pode ser maior que a própria página.
    largura_logo = min(largura_logo, largura_imagem, altura_imagem)
    largura_logo = max(largura_logo, 1)
    return largura_logo


def calcular_margem(largura_imagem, altura_imagem, cfg):
    """Calcula a margem da marca d'água (proporcional ou fixa)."""
    if str(cfg.get('wm_margem_modo', 'automatico')) == 'fixo':
        try:
            return max(0, int(float(cfg.get('wm_margem_fixa_px', 40))))
        except (TypeError, ValueError):
            return 40
    try:
        percentual = float(cfg.get('wm_margem_percentual', 2.5))
    except (TypeError, ValueError):
        percentual = 2.5
    percentual = min(max(percentual, 0.0), 20.0)
    base = min(largura_imagem, altura_imagem)
    return int(round(base * percentual / 100.0))


def calcular_posicao(largura_imagem, altura_imagem, largura_logo, altura_logo,
                     margem, posicao):
    """Calcula o canto superior esquerdo (x, y) onde a logo será colada."""
    fx, fy = POSICOES.get(posicao, POSICOES['superior_esquerdo'])
    espaco_x = largura_imagem - largura_logo - 2 * margem
    espaco_y = altura_imagem - altura_logo - 2 * margem
    if espaco_x < 0:
        espaco_x = 0
    if espaco_y < 0:
        espaco_y = 0
    x = int(round(margem + espaco_x * fx))
    y = int(round(margem + espaco_y * fy))
    x = min(max(x, 0), max(0, largura_imagem - largura_logo))
    y = min(max(y, 0), max(0, altura_imagem - altura_logo))
    return x, y


def preparar_logo(logo, largura_logo, opacidade):
    """Redimensiona a logo preservando proporção e aplica a opacidade."""
    largura_original, altura_original = logo.size
    if largura_original <= 0 or altura_original <= 0:
        raise ErroMarcaDagua('Logo com dimensões inválidas.')
    largura_logo = max(1, int(largura_logo))
    altura_logo = max(1, int(round(largura_logo * altura_original / largura_original)))
    redimensionada = logo.resize((largura_logo, altura_logo), Image.LANCZOS)

    if opacidade is None:
        return redimensionada
    opacidade = min(max(int(opacidade), 0), 100)
    if opacidade >= 100:
        return redimensionada
    canais = list(redimensionada.split())
    alfa = canais[3].point(lambda a: (a * opacidade) // 100)
    canais[3] = alfa
    redimensionada.putalpha(alfa)
    return redimensionada


def aplicar_marca_dagua(imagem, logo, cfg):
    """Aplica a marca d'água sobre uma imagem PIL (sem alterar o original).

    Retorna uma NOVA imagem; a imagem de entrada não é modificada.
    """
    if imagem.mode not in ('RGB', 'RGBA'):
        imagem = imagem.convert('RGB')
    base = imagem.copy()

    largura_logo = calcular_tamanho_logo(base.width, base.height, cfg)
    logo_preparada = preparar_logo(logo, largura_logo, cfg.get('wm_opacidade', 85))
    margem = calcular_margem(base.width, base.height, cfg)
    posicao = str(cfg.get('wm_posicao', 'superior_esquerdo'))
    x, y = calcular_posicao(base.width, base.height, logo_preparada.width,
                            logo_preparada.height, margem, posicao)

    if base.mode == 'RGBA':
        # Composição correta: a logo (com alfa/opacidade) é sobreposta à
        # imagem tanto no RGB quanto no canal alfa.
        camada = Image.new('RGBA', base.size, (0, 0, 0, 0))
        camada.paste(logo_preparada, (x, y), logo_preparada)
        base = Image.alpha_composite(base, camada)
    else:
        base.paste(logo_preparada, (x, y), logo_preparada)
    return base


def processar_arquivo(caminho_entrada, caminho_saida, logo, cfg,
                      formato_saida='original', qualidade_jpeg=95,
                      preservar_resolucao=True):
    """Processa um arquivo de página: lê o ORIGINAL e grava um NOVO arquivo.

    - Nunca escreve em caminho_entrada.
    - Preserva dimensões, DPI e modo de cor sempre que possível.
    - Retorna dicionário com metadados do resultado.
    """
    entrada = Path(caminho_entrada)
    saida = Path(caminho_saida)
    if not entrada.is_file():
        raise ErroMarcaDagua(f'Arquivo original não encontrado: {entrada}')

    try:
        with Image.open(entrada) as imagem:
            imagem.load()
            largura_original, altura_original = imagem.size
            dpi_original = imagem.info.get('dpi')
            formato_original = (imagem.format or '').upper()
            icc_original = imagem.info.get('icc_profile')

            processada = aplicar_marca_dagua(imagem, logo, cfg)
    except ErroMarcaDagua:
        raise
    except Exception as exc:
        raise ErroMarcaDagua(f'Erro ao abrir a imagem original: {exc}') from exc

    # Formato de saída -------------------------------------------------
    formato = (formato_saida or 'original').lower()
    if formato == 'original':
        formato = formato_original.lower() if formato_original else 'tiff'
    if formato not in ('jpeg', 'jpg', 'png', 'tiff', 'tif'):
        formato = 'tiff'

    extensoes = {'jpeg': '.jpg', 'jpg': '.jpg', 'png': '.png',
                 'tiff': '.tif', 'tif': '.tif'}
    extensao = extensoes[formato]
    if saida.suffix.lower() != extensao:
        saida = saida.with_suffix(extensao)

    saida.parent.mkdir(parents=True, exist_ok=True)

    # Salvamento sem sobrescrever o original ---------------------------
    try:
        if formato in ('jpeg', 'jpg'):
            if processada.mode == 'RGBA':
                fundo = Image.new('RGB', processada.size, (255, 255, 255))
                fundo.paste(processada, mask=processada.split()[3])
                processada = fundo
            elif processada.mode != 'RGB':
                processada = processada.convert('RGB')
            parametros = {'quality': min(max(int(qualidade_jpeg), 1), 100),
                          'optimize': True}
            if preservar_resolucao and dpi_original:
                parametros['dpi'] = dpi_original
            if icc_original:
                parametros['icc_profile'] = icc_original
            processada.save(str(saida), 'JPEG', **parametros)
        elif formato == 'png':
            parametros = {'optimize': True}
            if preservar_resolucao and dpi_original:
                parametros['dpi'] = dpi_original
            if icc_original:
                parametros['icc_profile'] = icc_original
            processada.save(str(saida), 'PNG', **parametros)
        else:  # TIFF
            if processada.mode == 'RGBA':
                processada = processada.convert('RGB')
            parametros = {'compression': 'tiff_deflate'}
            if preservar_resolucao and dpi_original:
                parametros['dpi'] = dpi_original
            if icc_original:
                parametros['icc_profile'] = icc_original
            processada.save(str(saida), 'TIFF', **parametros)
    except Exception as exc:
        raise ErroMarcaDagua(f'Erro ao salvar a imagem processada: {exc}') from exc

    dpi_texto = ''
    if dpi_original:
        try:
            dpi_texto = f'{int(round(float(dpi_original[0])))}x{int(round(float(dpi_original[1])))} DPI'
        except (TypeError, ValueError, IndexError):
            dpi_texto = ''
    return {
        'caminho': str(saida),
        'largura': processada.width,
        'altura': processada.height,
        'formato': formato.upper(),
        'resolucao': dpi_texto,
        'dimensoes_preservadas': (processada.width, processada.height)
        == (largura_original, altura_original),
    }


def ordenar_nomes_natural(nomes):
    """Ordena nomes de arquivos numericamente (1, 2, ..., 10, 11)."""
    return sorted(nomes, key=chave_natural)