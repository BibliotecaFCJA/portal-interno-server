"""Rotas de configurações do sistema e comparação antes/depois."""

from flask import (
    Blueprint, abort, flash, redirect, render_template, request,
    send_file, session, url_for,
)

from .auth import login_obrigatorio
from config import Config
from models.configuracoes import (
    ROTULOS_FORMATO, ROTULOS_POSICAO, obter_todas, salvar, validar,
)
from models.logs import registrar as registrar_log
from models.pagina import buscar_por_id as buscar_pagina
from services.image_processor import chave_configuracao, gerar_preview_processado
from services.obras_service import obter_obra_por_id
from services.watermark import carregar_logo

bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')


@bp.route('/', methods=['GET', 'POST'])
@login_obrigatorio(visualizador_ok=False)
def index():
    if request.method == 'POST':
        limpos, erros = validar(request.form)
        if erros:
            for erro in erros:
                flash(erro, 'erro')
        else:
            salvar(limpos)
            registrar_log(
                session.get('usuario_nome'),
                'Configurações atualizadas',
                ', '.join(sorted(limpos.keys())),
            )
            flash('Configurações salvas com sucesso.', 'sucesso')
            return redirect(url_for('configuracoes.index'))
    cfg = obter_todas()
    return render_template(
        'configuracoes.html', cfg=cfg,
        posicoes=ROTULOS_POSICAO, formatos=ROTULOS_FORMATO,
    )


@bp.route('/comparacao/<int:pagina_id>')
@login_obrigatorio()
def comparacao(pagina_id):
    """Imagens original e processada (preview) para comparação lado a lado."""
    pagina = buscar_pagina(pagina_id)
    if not pagina:
        abort(404)
    obra = obter_obra_por_id(pagina['obra_id'])
    cfg = obter_todas()
    for chave in ('wm_posicao', 'wm_tamanho_modo', 'wm_margem_modo'):
        if request.args.get(chave):
            cfg[chave] = request.args[chave]
    for chave in ('wm_tamanho_percentual', 'wm_margem_percentual',
                  'wm_opacidade'):
        bruto = request.args.get(chave)
        if bruto not in (None, ''):
            try:
                cfg[chave] = str(bruto).replace(',', '.')
            except ValueError:
                pass

    origem = (
        f'{Config.PASTA_ORIGINAIS}/{obra["codigo"]}/{pagina["arquivo_original"]}'
    )
    try:
        logo = carregar_logo(Config.LOGO_PATH)
        chave_cache = chave_configuracao('cmp', obra['id'], pagina['id'], cfg)
        caminho = gerar_preview_processado(origem, logo, cfg, chave_cache)
    except Exception:
        abort(404)
    return send_file(caminho, mimetype='image/jpeg')