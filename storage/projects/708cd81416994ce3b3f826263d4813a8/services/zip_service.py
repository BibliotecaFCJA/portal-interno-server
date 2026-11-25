"""Serviço de exportação: geração de ZIP das obras processadas."""

import zipfile
from pathlib import Path

from config import Config
from models.pagina import listar_por_obra
from models.obra import buscar_por_id
from services.storage import caminho_interno, pasta_obra, sanitizar_codigo


def gerar_zip_obra(obra_id, incluir_originais=False, caminho_banco=None):
    """Gera o arquivo ZIP da obra para download.

    Por padrão, inclui APENAS as páginas processadas. Os originais só
    entram se "incluir_originais" for explicitamente True.
    Retorna (caminho_do_zip, quantidade_de_arquivos).
    """
    obra = buscar_por_id(obra_id, caminho_banco)
    if not obra:
        raise ValueError('Obra não encontrada.')
    paginas = listar_por_obra(obra_id, caminho_banco)
    if not paginas:
        raise ValueError('A obra não possui páginas.')

    nome_zip = f'{sanitizar_codigo(obra["codigo"])}_PROCESSADA.zip'
    pasta_saida = Path(Config.PASTA_TMP)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = caminho_interno(str(pasta_saida), nome_zip)

    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_STORED) as arquivo_zip:
        incluidos = 0
        for pagina in paginas:
            if pagina['arquivo_processado']:
                pasta = pasta_obra(Config.PASTA_PROCESSADAS, obra['codigo'])
                arquivo = pasta / pagina['arquivo_processado']
                if arquivo.is_file():
                    arquivo_zip.write(arquivo, arquivo.name)
                    incluidos += 1
            elif incluir_originais and pagina['arquivo_original']:
                pasta = pasta_obra(Config.PASTA_ORIGINAIS, obra['codigo'])
                arquivo = pasta / pagina['arquivo_original']
                if arquivo.is_file():
                    arquivo_zip.write(arquivo, arquivo.name)
                    incluidos += 1
        if incluidos == 0:
            raise ValueError('Nenhum arquivo disponível para exportação.')
    return str(destino), incluidos