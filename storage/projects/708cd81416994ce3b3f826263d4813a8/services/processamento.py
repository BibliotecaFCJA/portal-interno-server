"""
Orquestrador do processamento em lote de uma obra.

Executa em uma THREAD separada (para não travar a interface), grava o
progresso em memória compartilhada (lido pela rota de status) e atualiza
o banco página a página. Nunca altera os arquivos originais.
"""

import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from config import Config
from models.configuracoes import (
    descrever_margem, descrever_posicao, descrever_tamanho,
)
from models.logs import registrar as registrar_log
from models.pagina import (
    atualizar_processamento, definir_status, listar_por_obra,
)
from models.processamento import concluir as concluir_registro
from models.processamento import registrar as registrar_processamento
from models.obra import atualizar_status
from services.storage import pasta_obra
from services.watermark import (
    ErroMarcaDagua, carregar_logo, processar_arquivo,
)

# Progresso em memória: {obra_id: {...}} — acessado pela rota de status.
_estados = {}
_trava = threading.Lock()


def estado(obra_id):
    """Retorna uma cópia do estado de progresso de uma obra."""
    with _trava:
        copia = dict(_estados.get(int(obra_id), {}))
    return copia


def em_execucao(obra_id):
    with _trava:
        info = _estados.get(int(obra_id))
        return bool(info and info.get('executando'))


def _definir(obra_id, **campos):
    with _trava:
        atual = _estados.setdefault(int(obra_id), {})
        atual.update(campos)


def cancelar(obra_id):
    """Solicita o cancelamento do processamento em andamento."""
    with _trava:
        info = _estados.get(int(obra_id))
        if info and info.get('executando'):
            info['cancelar'] = True
            return True
    return False


def _deve_cancelar(obra_id):
    with _trava:
        info = _estados.get(int(obra_id))
        return bool(info and info.get('cancelar'))


def validar_pre_requisitos(obra, caminho_banco=None):
    """Checklist exibido antes de processar. Retorna (ok, itens, problemas)."""
    from models.pagina import contar_por_obra
    itens = []
    problemas = []

    itens.append({'texto': 'Obra cadastrada', 'ok': bool(obra)})
    if not obra:
        return False, itens, ['Obra não encontrada.']

    total = contar_por_obra(obra['id'], caminho_banco)
    itens.append({'texto': f'{total} páginas encontradas', 'ok': total > 0})
    if total == 0:
        problemas.append('A obra não possui páginas adicionadas.')

    logo_ok = Path(Config.LOGO_PATH).is_file()
    itens.append({'texto': 'Logo institucional disponível', 'ok': logo_ok})
    if not logo_ok:
        problemas.append('Logo da FCJA não encontrada no servidor.')

    cfg_ok = True
    try:
        from models.configuracoes import obter_todas
        obter_todas(caminho_banco)
    except Exception:
        cfg_ok = False
    itens.append({'texto': 'Configurações válidas', 'ok': cfg_ok})

    espaco = 0
    try:
        from services.storage import espaco_livre_bytes
        espaco = espaco_livre_bytes(Config.PASTA_PROCESSADAS)
    except Exception:
        pass
    espaco_ok = espaco == 0 or espaco > 100 * 1024 * 1024
    itens.append({
        'texto': 'Espaço de armazenamento disponível',
        'ok': espaco_ok,
    })
    if not espaco_ok:
        problemas.append('Pouco espaço em disco na pasta de processadas.')

    return (len(problemas) == 0), itens, problemas


def iniciar_processamento(obra_id, usuario, cfg_override=None, caminho_banco=None):
    """Inicia a thread de processamento, se já não houver uma em execução.

    "cfg_override" são os parâmetros escolhidos na interface (posição,
    tamanho, margem, opacidade). Eles prevalecem sobre as configurações
    salvas apenas nesta execução, sem alterá-las no banco.
    """
    obra_id = int(obra_id)
    if em_execucao(obra_id):
        raise RuntimeError('Já existe um processamento em andamento para esta obra.')

    from models.obra import buscar_por_id
    obra = buscar_por_id(obra_id, caminho_banco)
    ok, itens, problemas = validar_pre_requisitos(obra, caminho_banco)
    if not ok:
        raise RuntimeError('; '.join(problemas))

    _definir(
        obra_id,
        executando=True, cancelar=False, total=0, concluidas=0, erros=0,
        pagina_atual='', status='Preparando...', iniciado_em=time.time(),
        concluido=False, sucesso=False, mensagem='',
    )
    thread = threading.Thread(
        target=_executar, args=(obra_id, usuario, cfg_override, caminho_banco),
        daemon=True,
    )
    thread.start()
    return True


def _executar(obra_id, usuario, cfg_override=None, caminho_banco=None):
    obra = None
    try:
        from models.obra import buscar_por_id
        from models.configuracoes import obter_todas
        obra = buscar_por_id(obra_id, caminho_banco)
        if not obra:
            raise RuntimeError('Obra não encontrada.')

        cfg = obter_todas(caminho_banco)
        if cfg_override:
            cfg.update({k: v for k, v in cfg_override.items() if v is not None})
        logo = carregar_logo(Config.LOGO_PATH)
        paginas = listar_por_obra(obra_id, caminho_banco)
        if not paginas:
            raise RuntimeError('A obra não possui páginas.')

        total = len(paginas)
        _definir(obra_id, total=total, status='Processando...')

        atualizar_status(obra_id, 'processando', caminho=caminho_banco)
        pasta_saida = pasta_obra(Config.PASTA_PROCESSADAS, obra['codigo'])

        formato_saida = cfg.get('proc_formato_saida', 'original')
        qualidade = cfg.get('proc_qualidade_jpeg', '95')
        preservar = str(cfg.get('proc_preservar_resolucao', '1')) == '1'

        registro_id = registrar_processamento(
            {
                'obra_id': obra_id,
                'tamanho_logo': descrever_tamanho(cfg),
                'opacidade': cfg.get('wm_opacidade', '85'),
                'margem': descrever_margem(cfg),
                'posicao': descrever_posicao(cfg),
                'status': 'processando',
            },
            caminho_banco,
        )
        registrar_log(
            usuario, 'Processamento iniciado',
            f'{obra["codigo"]} — {total} páginas', caminho_banco,
        )

        processadas = 0
        erros = 0
        for pagina in paginas:
            if _deve_cancelar(obra_id):
                _definir(obra_id, status='Cancelado pelo usuário.')
                concluir_registro(
                    registro_id, 'cancelado', processadas, erros,
                    'Processamento cancelado pelo usuário.', caminho_banco,
                )
                registrar_log(
                    usuario, 'Processamento cancelado', obra['codigo'], caminho_banco,
                )
                _recalcular_status_obra(obra_id, caminho_banco)
                _definir(
                    obra_id, executando=False, concluido=True, sucesso=False,
                    mensagem='Processamento cancelado.',
                )
                return

            nome_arquivo = pagina['arquivo_original']
            _definir(
                obra_id,
                pagina_atual=nome_arquivo,
                status=f'Processando página {pagina["numero"]} de {total}...',
            )
            definir_status(pagina['id'], 'processando', caminho=caminho_banco)

            origem = pasta_obra(Config.PASTA_ORIGINAIS, obra['codigo']) / nome_arquivo
            try:
                resultado = processar_arquivo(
                    origem, pasta_saida / Path(nome_arquivo).stem, logo, cfg,
                    formato_saida=formato_saida,
                    qualidade_jpeg=int(qualidade),
                    preservar_resolucao=preservar,
                )
                atualizar_processamento(
                    pagina['id'], resultado['caminho'].split('/')[-1],
                    resultado['largura'], resultado['altura'],
                    resultado['resolucao'], caminho=caminho_banco,
                )
                processadas += 1
            except Exception as exc:
                erros += 1
                definir_status(
                    pagina['id'], 'erro', str(exc), caminho=caminho_banco,
                )
                _definir(
                    obra_id, erros=erros,
                    status=f'Erro ao processar {nome_arquivo}: continuando...',
                )
            _definir(
                obra_id, concluidas=processadas + erros,
            )

        status_final = 'processada' if erros == 0 else 'parcial'
        atualizar_status(
            obra_id, status_final,
            data_processamento=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            caminho=caminho_banco,
        )
        concluir_registro(
            registro_id, 'concluido', processadas, erros, None, caminho_banco,
        )
        registrar_log(
            usuario, 'Processamento concluído',
            f'{obra["codigo"]} — {processadas} processadas, {erros} erros',
            caminho_banco,
        )
        _definir(
            obra_id,
            executando=False, concluido=True, sucesso=erros == 0,
            status='Concluído.',
            mensagem=(
                f'{processadas} páginas processadas com sucesso, '
                f'{erros} com erro.'
            ),
        )
    except Exception as exc:
        traceback.print_exc()
        if obra:
            try:
                _recalcular_status_obra(obra_id, caminho_banco)
            except Exception:
                pass
        _definir(
            obra_id,
            executando=False, concluido=True, sucesso=False,
            status='Erro.', mensagem=str(exc),
        )
        try:
            registrar_log(
                usuario, 'Erro no processamento',
                f'Obra {obra_id}: {exc}', caminho_banco,
            )
        except Exception:
            pass


def _recalcular_status_obra(obra_id, caminho_banco):
    """Define o status da obra com base nas páginas processadas."""
    from models.pagina import contar_por_status
    from models.obra import atualizar_status
    contagens = contar_por_status(obra_id, caminho_banco)
    total = sum(contagens.values())
    ok = contagens.get('processada', 0)
    if total and ok == total:
        atualizar_status(
            obra_id, 'processada',
            data_processamento=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            caminho=caminho_banco,
        )
    elif ok:
        atualizar_status(obra_id, 'parcial', caminho=caminho_banco)
    else:
        atualizar_status(obra_id, 'pendente', caminho=caminho_banco)