"""
Serviços auxiliares de processamento de imagens: metadados, validação,
miniaturas para pré-visualização e cache.
"""

import hashlib
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from config import Config
from services.storage import caminho_interno

Image.MAX_IMAGE_PIXELS = 300_000_000  # proteção contra imagens maliciosas

# Versão do desenho da marca d'água: invalida caches de pré-visualização
# gerados com versões anteriores.
VERSAO_PREVIEW = '2'

# Formatos que os navegadores exibem nativamente.
EXTENSOES_WEB = {'.jpg', '.jpeg', '.png'}


def ler_metadados(caminho_imagem):
    """Lê dimensões, formato e DPI de uma imagem, sem alterá-la."""
    caminho = Path(caminho_imagem)
    try:
        with Image.open(caminho) as imagem:
            largura, altura = imagem.size
            formato = (imagem.format or '').upper()
            dpi = imagem.info.get('dpi')
            modo = imagem.mode
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f'Arquivo de imagem inválido: {exc}') from exc
    resolucao = ''
    if dpi:
        try:
            resolucao = f'{int(round(float(dpi[0])))}x{int(round(float(dpi[1])))} DPI'
        except (TypeError, ValueError, IndexError):
            resolucao = ''
    return {
        'largura': largura,
        'altura': altura,
        'formato': formato,
        'resolucao': resolucao,
        'modo': modo,
    }


def validar_arquivo_imagem(caminho_imagem):
    """Abre a imagem para verificar integridade (sem alterá-la)."""
    try:
        with Image.open(caminho_imagem) as imagem:
            imagem.verify()
        return True
    except Exception:
        return False


def gerar_miniatura(caminho_imagem, chave_cache, largura_max=420):
    """Gera (uma vez) uma miniatura JPEG em cache para pré-visualização.

    A imagem original é apenas lida; a miniatura é gravada na pasta de
    cache com um nome determinístico. Retorna o caminho da miniatura.
    """
    fonte = Path(caminho_imagem)
    if not fonte.is_file():
        raise ValueError('Arquivo não encontrado.')
    pasta = Path(Config.PASTA_CACHE)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = caminho_interno(str(pasta), f'{chave_cache}.jpg')

    if destino.is_file():
        return str(destino)

    with Image.open(fonte) as imagem:
        imagem.load()
        mini = imagem.convert('RGB')
        mini.thumbnail((largura_max, largura_max * 4), Image.LANCZOS)
        mini.save(str(destino), 'JPEG', quality=82)
    return str(destino)


def gerar_preview_processado(caminho_imagem, logo, cfg, chave_cache):
    """Gera uma pré-visualização com a marca d'água aplicada.

    Processa a imagem em memória (sem tocar no original) e salva uma
    versão reduzida em cache para exibição rápida na interface.
    """
    from services.watermark import aplicar_marca_dagua
    fonte = Path(caminho_imagem)
    if not fonte.is_file():
        raise ValueError('Arquivo não encontrado.')
    pasta = Path(Config.PASTA_CACHE)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = caminho_interno(str(pasta), f'{chave_cache}.jpg')

    if destino.is_file():
        return str(destino)

    with Image.open(fonte) as imagem:
        imagem.load()
        processada = aplicar_marca_dagua(imagem, logo, cfg)
        mini = processada.convert('RGB')
        escala = 1400 / max(1, mini.width)
        if escala < 1:
            mini = mini.resize(
                (max(1, int(mini.width * escala)), max(1, int(mini.height * escala))),
                Image.LANCZOS,
            )
        mini.save(str(destino), 'JPEG', quality=85)
    return str(destino)


def chave_configuracao(prefixo, obra_id, pagina_id, cfg):
    """Gera uma chave de cache determinística a partir de uma configuração.

    Inclui todas as opções que alteram o resultado (posição, tamanho, margem,
    opacidade e modo de aplicação), garantindo que a pré-visualização seja
    regenerada quando qualquer parâmetro mudar.
    """
    campos = (
        'wm_posicao', 'wm_tamanho_modo', 'wm_tamanho_percentual',
        'wm_tamanho_fixo_px', 'wm_tamanho_minimo_px', 'wm_tamanho_maximo_px',
        'wm_margem_modo', 'wm_margem_percentual', 'wm_margem_fixa_px',
        'wm_opacidade', 'wm_modo_aplicacao',
    )
    partes = [prefixo, f'o{obra_id}', f'p{pagina_id}', f'r{VERSAO_PREVIEW}']
    partes.extend(str(cfg.get(campo, '')) for campo in campos)
    bruto = '_'.join(partes)
    return re.sub(r'[^A-Za-z0-9_.-]+', '-', bruto)


def gerar_imagem_web(caminho_imagem, largura_max=None, qualidade=88):
    """Devolve um arquivo exibível em navegador para uma página.

    - JPEG e PNG são servidos diretamente (o navegador já os exibe).
    - TIFF (e outros formatos sem suporte nativo no navegador) são
      convertidos para JPEG uma única vez, com cache invalidado pela data
      de modificação do arquivo de origem.

    O arquivo ORIGINAL nunca é alterado; a conversão é apenas uma cópia
    para exibição. Retorna o caminho do arquivo a ser enviado.
    """
    fonte = Path(caminho_imagem)
    if not fonte.is_file():
        raise ValueError('Arquivo não encontrado.')

    if fonte.suffix.lower() in EXTENSOES_WEB:
        return str(fonte)

    dados = fonte.stat()
    assinatura = (
        f'{fonte.resolve()}|{dados.st_mtime_ns}|{dados.st_size}|'
        f'{largura_max}|{qualidade}'
    )
    chave = 'web_' + hashlib.sha1(assinatura.encode('utf-8')).hexdigest()[:20]
    pasta = Path(Config.PASTA_CACHE)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = caminho_interno(str(pasta), f'{chave}.jpg')
    if destino.is_file():
        return str(destino)

    with Image.open(fonte) as imagem:
        imagem.load()
        if imagem.mode in ('RGBA', 'LA', 'PA') or (
            imagem.mode == 'P' and 'transparency' in imagem.info
        ):
            rgba = imagem.convert('RGBA')
            convertida = Image.new('RGB', rgba.size, (255, 255, 255))
            convertida.paste(rgba, mask=rgba.split()[-1])
        else:
            convertida = imagem.convert('RGB')
        if largura_max and convertida.width > largura_max:
            escala = largura_max / convertida.width
            convertida = convertida.resize(
                (largura_max, max(1, int(convertida.height * escala))),
                Image.LANCZOS,
            )
        convertida.save(str(destino), 'JPEG', quality=qualidade, optimize=True)
    return str(destino)


def limpar_chave_cache(chave_cache):
    """Remove miniaturas de uma chave (usada ao substituir/reprocessar)."""
    pasta = Path(Config.PASTA_CACHE)
    for sufixo in ('.jpg',):
        alvo = pasta / f'{chave_cache}{sufixo}'
        try:
            alvo.unlink()
        except OSError:
            pass