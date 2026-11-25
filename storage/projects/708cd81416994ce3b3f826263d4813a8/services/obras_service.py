"""
Regras de negócio de obras e páginas: upload, substituição, exclusão.

Segurança do original: os arquivos enviados são gravados SOMENTE em
uploads/originais/CODIGO/, com nomes normalizados e seguros, e nunca
mais são sobrescritos pelo processamento.
"""

from pathlib import Path

from config import Config
from models.logs import registrar as registrar_log
from models.pagina import (
    buscar_por_id, buscar_por_nome, excluir as excluir_pagina,
    excluir_por_obra, inserir as inserir_pagina, listar_por_obra,
    proximo_numero,
)
from models.obra import (
    atualizar_quantidade, buscar_por_id, buscar_por_codigo, excluir as excluir_obra_db,
)
from services.image_processor import ler_metadados, validar_arquivo_imagem
from services.storage import (
    extensao_segura, pasta_obra, sanitizar_codigo,
)


class ErroNegocio(Exception):
    """Erro de domínio com mensagem amigável para a interface."""


def _nome_normalizado(numero, extensao):
    """Nome padrão de página: 001.tif, 002.jpg..."""
    return f'{numero:03d}{extensao}'


def obter_obra_por_id(obra_id):
    obra = buscar_por_id(obra_id)
    if not obra:
        raise ErroNegocio('Obra não encontrada.')
    return obra


def salvar_paginas(obra_id, arquivos, usuario, substituir=False):
    """Salva múltiplos arquivos como páginas da obra.

    Retorna dicionário com resumo: adicionadas, substituidas, ignoradas,
    duplicadas (quando substituir=False) e erros por arquivo.
    """
    obra = obter_obra_por_id(obra_id)
    if not arquivos:
        raise ErroNegocio('Nenhum arquivo enviado.')

    # A pasta da obra só é criada quando o primeiro arquivo válido for
    # gravado (evita pastas vazias de uploads rejeitados).
    pasta = None
    resumo = {
        'adicionadas': 0, 'substituidas': 0, 'duplicadas': 0,
        'ignoradas': 0, 'erros': [], 'novas_paginas': [],
    }

    # Ordenação natural: 1, 2, ..., 10, 11 (não 1, 10, 11, 2).
    arquivos_ordenados = sorted(
        arquivos, key=lambda f: _chave_arquivo(f.filename or '')
    )

    for arquivo in arquivos_ordenados:
        nome_enviado = arquivo.filename or ''
        ext = extensao_segura(nome_enviado)
        if not ext:
            resumo['erros'].append(f'{nome_enviado}: formato não suportado.')
            resumo['ignoradas'] += 1
            continue
        if arquivo.mimetype not in Config.MIMES_PERMITIDOS:
            resumo['erros'].append(f'{nome_enviado}: tipo de arquivo não permitido.')
            resumo['ignoradas'] += 1
            continue

        # O nome original é usado apenas para referência/duplicidade;
        # o arquivo é gravado com nome normalizado seguro.
        try:
            if pasta is None:
                pasta = pasta_obra(Config.PASTA_ORIGINAIS, obra['codigo'])
            existente = buscar_por_nome(obra_id, nome_enviado)
            numero = (existente['numero'] if existente
                      else proximo_numero(obra_id))
            destino = pasta / _nome_normalizado(numero, f'.{ext}')

            arquivo.save(str(destino))

            if not validar_arquivo_imagem(destino):
                destino.unlink(missing_ok=True)
                resumo['erros'].append(f'{nome_enviado}: arquivo de imagem inválido.')
                resumo['ignoradas'] += 1
                continue

            metadados = ler_metadados(destino)
            if existente:
                if not substituir:
                    destino.unlink(missing_ok=True)
                    resumo['duplicadas'] += 1
                    continue
                excluir_pagina(existente['id'])
                from services.image_processor import limpar_chave_cache
                limpar_chave_cache(f'obra{obra_id}_p{existente["numero"]}')
            metadados['obra_id'] = obra_id
            metadados['numero'] = numero
            metadados['nome_original'] = Path(nome_enviado).name
            metadados['arquivo_original'] = destino.name
            metadados['tamanho_bytes'] = destino.stat().st_size
            inserir_pagina(metadados)
            if existente:
                resumo['substituidas'] += 1
            else:
                resumo['adicionadas'] += 1
                resumo['novas_paginas'].append(destino.name)
        except ValueError as exc:
            resumo['erros'].append(f'{nome_enviado}: {exc}')
            resumo['ignoradas'] += 1
        except Exception as exc:  # noqa: BLE001
            resumo['erros'].append(f'{nome_enviado}: erro inesperado ({exc}).')
            resumo['ignoradas'] += 1

    if resumo['adicionadas'] or resumo['substituidas']:
        atualizar_quantidade(obra_id)
        registrar_log(
            usuario, 'Upload realizado',
            f'{obra["codigo"]} — {resumo["adicionadas"]} adicionadas, '
            f'{resumo["substituidas"]} substituídas',
        )
    return resumo


def _chave_arquivo(nome):
    """Chave de ordenação natural por nome de arquivo."""
    import re
    return [
        int(parte) if parte.isdigit() else parte.lower()
        for parte in re.split(r'(\d+)', str(nome))
    ]


def remover_pagina(obra_id, pagina_id, usuario):
    """Remove uma página (registro do banco; arquivo original é mantido).

    O arquivo original NUNCA é apagado automaticamente — apenas o registro
    sai da lista. Para apagar arquivos, use a exclusão completa da obra.
    """
    obra = obter_obra_por_id(obra_id)
    pagina = buscar_por_id(pagina_id)
    if not pagina or pagina['obra_id'] != obra['id']:
        raise ErroNegocio('Página não encontrada.')
    excluir_pagina(pagina_id)
    atualizar_quantidade(obra_id)
    registrar_log(usuario, 'Página removida',
                  f'{obra["codigo"]} — página {pagina["numero"]}')


def listar_paginas(obra_id):
    return listar_por_obra(obra_id)


def excluir_obra_completa(obra_id, usuario, excluir_originais=True):
    """Exclui a obra do banco e, opcionalmente, suas pastas de arquivos.

    A exclusão de ORIGINAIS é explícita e exige confirmação na interface.
    """
    obra = obter_obra_por_id(obra_id)
    codigo = obra['codigo']
    pastas_removidas = []

    if excluir_originais:
        pasta = Path(Config.PASTA_ORIGINAIS) / sanitizar_codigo(codigo)
        if pasta.is_dir():
            import shutil
            shutil.rmtree(pasta)
            pastas_removidas.append('originais')
    pasta = Path(Config.PASTA_PROCESSADAS) / sanitizar_codigo(codigo)
    if pasta.is_dir():
        import shutil
        shutil.rmtree(pasta)
        pastas_removidas.append('processadas')

    excluir_por_obra(obra_id)
    from models.processamento import excluir_por_obra as excluir_processamentos
    excluir_processamentos(obra_id)
    excluir_obra_db(obra_id)
    registrar_log(
        usuario, 'Obra excluída',
        f'{codigo} — pastas removidas: {", ".join(pastas_removidas) or "nenhuma"}',
    )
    return pastas_removidas