"""
Serviços de armazenamento: pastas, nomes seguros, ordenação natural.

Regra de ouro: os arquivos ORIGINAIS ficam em uploads/originais/ e nunca
são alterados; os processados ficam em uploads/processadas/.
"""

import re
import shutil
from pathlib import Path

EXTENSOES_IMAGEM = {'jpg', 'jpeg', 'png', 'tif', 'tiff'}
EXTENSAO_NORMALIZADA = {
    'jpg': '.jpg', 'jpeg': '.jpg', 'png': '.png',
    'tif': '.tif', 'tiff': '.tif',
}
FORMATO_POR_EXTENSAO = {
    '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG',
    '.tif': 'TIFF', '.tiff': 'TIFF',
}


def sanitizar_codigo(codigo):
    """Sanitiza o código da obra para uso seguro como nome de pasta."""
    limpo = re.sub(r'[^A-Za-z0-9_-]+', '-', (codigo or '').strip())
    limpo = limpo.strip('-_')
    return limpo[:60]


def extensao_segura(nome_arquivo):
    """Retorna a extensão (sem ponto) se suportada; caso contrário None."""
    sufixo = Path(nome_arquivo or '').suffix.lower().lstrip('.')
    return sufixo if sufixo in EXTENSOES_IMAGEM else None


def extensao_normalizada(nome_arquivo):
    """Extensão normalizada com ponto (ex.: 'foto.TIFF' → '.tif')."""
    ext = extensao_segura(nome_arquivo)
    if not ext:
        return None
    return EXTENSAO_NORMALIZADA[ext]


def chave_natural(texto):
    """Chave de ordenação natural: 1, 2, 10, 11 (não 1, 10, 11, 2)."""
    return [
        int(parte) if parte.isdigit() else parte.lower()
        for parte in re.split(r'(\d+)', str(texto))
    ]


def garantir_pastas(config):
    """Cria automaticamente todas as pastas necessárias do sistema."""
    for chave in ('UPLOAD_FOLDER', 'PASTA_ORIGINAIS', 'PASTA_PROCESSADAS',
                  'PASTA_CACHE', 'PASTA_TMP'):
        Path(config[chave]).mkdir(parents=True, exist_ok=True)


def pasta_obra(pasta_base, codigo):
    """Retorna (e cria) a pasta de uma obra dentro de originais/processadas."""
    caminho = Path(pasta_base) / sanitizar_codigo(codigo)
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def caminho_interno(base, *partes):
    """Resolve um caminho garantindo que permaneça dentro de "base"."""
    base_resolvida = Path(base).resolve()
    alvo = base_resolvida.joinpath(*partes).resolve()
    if alvo != base_resolvida and base_resolvida not in alvo.parents:
        raise ValueError('Caminho fora da pasta permitida.')
    return alvo


def nome_arquivo_seguro(nome):
    """Verifica se um nome de arquivo do banco é seguro (sem travessia)."""
    if not nome or '/' in nome or '\\' in nome or '..' in nome:
        return False
    return True


def espaco_livre_bytes(caminho):
    try:
        return shutil.disk_usage(caminho).free
    except OSError:
        return 0


def tamanho_formatado(quantidade):
    """Formata bytes em texto legível (KB, MB...)."""
    try:
        quantidade = float(quantidade or 0)
    except (TypeError, ValueError):
        quantidade = 0.0
    if quantidade < 1024:
        return f'{quantidade:.0f} B'
    for unidade in ('KB', 'MB', 'GB', 'TB'):
        quantidade /= 1024.0
        if quantidade < 1024 or unidade == 'TB':
            return f'{quantidade:.1f} {unidade}'
    return f'{quantidade:.1f} TB'