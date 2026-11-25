"""Rotas de processamento em lote, pré-visualização e comparação."""

from flask import (
    Blueprint, abort, current_app, flash, jsonify, redirect, render_template,
    request, send_file, session, url_for,
)

from .auth import login_obrigatorio
from config import Config
from models.configuracoes import obter_todas
from models.pagina import listar_por_obra
from services import processamento as servico
from services.image_processor import (
    chave_configuracao, gerar_miniatura, gerar_preview_processado,
)
from services.obras_service import ErroNegocio, obter_obra_por_id
from services.watermark import carregar_logo

bp = Blueprint('processamento', __name__)


@bp.route('/processamento/<int:obra_id>')
@login_obrigatorio()
def tela(obra_id):
    obra = obter_obra_por_id(obra_id)
    paginas = listar_por_obra(obra_id)
    cfg = obter_todas()
    ok, itens, problemas = servico.validar_pre_requisitos(obra)
    return render_template(
        'processamento.html', obra=obra, paginas=paginas, cfg=cfg,
        checklist=itens, problemas=problemas, pode_processar=ok,
    )


@bp.route('/processamento/<int:obra_id>/iniciar', methods=['POST'])
@login_obrigatorio(visualizador_ok=False)
def iniciar(obra_id):
    """Inicia o processamento com as configurações escolhidas na interface.

    Os parâmetros da marca d'água (posição, tamanho, margem e opacidade)
    são enviados pelo navegador e aplicados a TODAS as páginas desta
    execução, sem alterar as configurações globais salvas.
    """
    from models.configuracoes import validar

    dados = request.get_json(silent=True) or request.form.to_dict()
    parametros, erros = validar(dados)
    if erros:
        return {'ok': False, 'erro': '; '.join(erros)}, 400
    try:
        servico.iniciar_processamento(
            obra_id, session.get('usuario_nome'), parametros,
            caminho_banco=current_app.config['DATABASE_PATH'],
        )
        return {'ok': True}
    except RuntimeError as exc:
        return {'ok': False, 'erro': str(exc)}, 400


@bp.route('/processamento/<int:obra_id>/cancelar', methods=['POST'])
@login_obrigatorio(visualizador_ok=False)
def cancelar(obra_id):
    return {'ok': servico.cancelar(obra_id)}


@bp.route('/processamento/<int:obra_id>/status')
@login_obrigatorio()
def status(obra_id):
    return jsonify(servico.estado(obra_id))


@bp.route('/processamento/<int:obra_id>/relatorio')
@login_obrigatorio()
def relatorio(obra_id):
    obra = obter_obra_por_id(obra_id)
    from models.processamento import ultimo_por_obra
    registro = ultimo_por_obra(obra_id)
    cfg = obter_todas()
    rotulos_status = {
        'processando': 'Em andamento',
        'concluido': 'Concluído',
        'cancelado': 'Cancelado',
        'erro': 'Erro',
    }
    return render_template(
        'relatorio.html', obra=obra, registro=registro, cfg=cfg,
        rotulos_status=rotulos_status,
    )


@bp.route('/processamento/<int:obra_id>/preview')
@login_obrigatorio()
def preview(obra_id):
    """Pré-visualização: página de exemplo com a marca d'água aplicada."""
    obra = obter_obra_por_id(obra_id)
    paginas = listar_por_obra(obra_id)
    if not paginas:
        abort(404)
    indice = request.args.get('pagina', 0, type=int)
    indice = max(0, min(indice, len(paginas) - 1))
    pagina = paginas[indice]

    # Parâmetros temporários da interface (não alteram as configurações).
    cfg = obter_todas()
    for chave in ('wm_posicao', 'wm_tamanho_modo', 'wm_margem_modo',
                  'wm_modo_aplicacao'):
        if request.args.get(chave):
            cfg[chave] = request.args[chave]
    for chave in ('wm_tamanho_percentual', 'wm_tamanho_fixo_px',
                  'wm_margem_percentual', 'wm_margem_fixa_px',
                  'wm_opacidade'):
        bruto = request.args.get(chave)
        if bruto not in (None, ''):
            try:
                float(str(bruto).replace(',', '.'))
                cfg[chave] = str(bruto).replace(',', '.')
            except ValueError:
                pass

    try:
        logo = carregar_logo(Config.LOGO_PATH)
        chave = chave_configuracao('prev', obra_id, pagina['id'], cfg)
        caminho = gerar_preview_processado(
            f'{Config.PASTA_ORIGINAIS}/{obra["codigo"]}/{pagina["arquivo_original"]}',
            logo, cfg, chave,
        )
    except Exception:
        abort(404)
    return send_file(caminho, mimetype='image/jpeg')


@bp.route('/paginas/<int:pagina_id>/miniatura')
@login_obrigatorio()
def miniatura(pagina_id):
    """Miniatura da página original para as grades de páginas."""
    pagina = buscar_pagina_segura(pagina_id)
    if not pagina:
        abort(404)
    obra = obter_obra_por_id(pagina['obra_id'])
    caminho = (
        f'{Config.PASTA_ORIGINAIS}/{obra["codigo"]}/{pagina["arquivo_original"]}'
    )
    try:
        mini = gerar_miniatura(caminho, f'obra{obra["id"]}_p{pagina["numero"]}')
    except Exception:
        abort(404)
    return send_file(mini, mimetype='image/jpeg')


def buscar_pagina_segura(pagina_id):
    from models.pagina import buscar_por_id
    pagina = buscar_por_id(pagina_id)
    if not pagina:
        return None
    return pagina