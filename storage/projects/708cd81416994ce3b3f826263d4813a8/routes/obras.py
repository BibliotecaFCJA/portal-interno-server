"""Rotas de obras: cadastro, listagem, detalhes, visualizador e exclusão."""

import math
from pathlib import Path

from flask import (
    Blueprint, abort, flash, redirect, render_template, request,
    send_file, session, url_for,
)

from .auth import login_obrigatorio
from config import Config
from models.logs import registrar as registrar_log
from models.pagina import ROTULOS_STATUS as ROTULOS_PAGINA
from models.pagina import (
    buscar_por_id as buscar_pagina, listar_por_obra, contar_por_status,
)
from models.obra import (
    ROTULOS_STATUS, buscar_por_id, buscar_por_codigo, criar, gerar_proximo_codigo,
    listar,
)
from models.processamento import listar_por_obra as listar_processamentos
from services.obras_service import (
    ErroNegocio, excluir_obra_completa, obter_obra_por_id, salvar_paginas,
)
from services.storage import (
    espaco_livre_bytes, nome_arquivo_seguro, pasta_obra, tamanho_formatado,
)

bp = Blueprint('obras', __name__, url_prefix='/obras')


def _dados_formulario(form):
    return {
        'codigo': (form.get('codigo') or '').strip().upper(),
        'titulo': (form.get('titulo') or '').strip(),
        'autor': (form.get('autor') or '').strip(),
        'ano': (form.get('ano') or '').strip()[:9],
        'colecao': (form.get('colecao') or '').strip(),
        'responsavel': (form.get('responsavel') or '').strip(),
        'descricao': (form.get('descricao') or '').strip(),
    }


@bp.route('/nova', methods=['GET', 'POST'])
@login_obrigatorio(visualizador_ok=False)
def nova():
    erros = []
    dados = {'codigo': '', 'titulo': '', 'autor': '', 'ano': '',
             'colecao': '', 'responsavel': '', 'descricao': ''}
    if request.method == 'POST':
        dados = _dados_formulario(request.form)
        if not dados['titulo']:
            erros.append('Informe o título da obra.')
        if not dados['codigo']:
            # Sugere automaticamente o próximo código sequencial.
            dados['codigo'] = gerar_proximo_codigo()
        else:
            existente = buscar_por_codigo(dados['codigo'])
            if existente:
                erros.append('Já existe uma obra com este código.')
        if dados['ano'] and not dados['ano'].isdigit():
            erros.append('O ano deve conter apenas números.')
        if not erros:
            try:
                obra_id = criar(dados)
                registrar_log(
                    session.get('usuario_nome'), 'Obra criada', dados['codigo'],
                )
                flash('Obra cadastrada com sucesso. Adicione as páginas.', 'sucesso')
                return redirect(url_for('obras.detalhes', obra_id=obra_id))
            except ValueError as exc:
                erros.append(str(exc))
    sugerido = gerar_proximo_codigo()
    return render_template('nova_obra.html', dados=dados, erros=erros,
                           codigo_sugerido=sugerido)


@bp.route('/')
@login_obrigatorio()
def lista():
    busca = (request.args.get('busca') or '').strip()
    status = (request.args.get('status') or '').strip()
    ordenar = (request.args.get('ordenar') or 'recentes').strip()
    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = 20

    linhas, total = listar(
        busca=busca or None, status=status or None, ordenar=ordenar,
        pagina=pagina, por_pagina=por_pagina,
    )
    total_paginas = max(1, math.ceil(total / por_pagina))
    return render_template(
        'obras.html', obras=linhas, total=total, busca=busca,
        status=status, ordenar=ordenar, pagina=pagina,
        total_paginas=total_paginas,
        rotulos_status=ROTULOS_STATUS,
    )


@bp.route('/<int:obra_id>')
@login_obrigatorio()
def detalhes(obra_id):
    obra = obter_obra_por_id(obra_id)
    paginas = listar_por_obra(obra_id)
    contagens = contar_por_status(obra_id)
    processamentos = listar_processamentos(obra_id)
    espaco = espaco_livre_bytes(Config.PASTA_PROCESSADAS)
    return render_template(
        'detalhes_obra.html', obra=obra, paginas=paginas,
        contagens=contagens, processamentos=processamentos,
        rotulos_status=ROTULOS_STATUS, rotulos_pagina=ROTULOS_PAGINA,
        espaco_livre=tamanho_formatado(espaco),
    )


@bp.route('/<int:obra_id>/paginas/upload', methods=['POST'])
@login_obrigatorio(visualizador_ok=False)
def upload_paginas(obra_id):
    arquivos = request.files.getlist('arquivos')
    substituir = request.form.get('substituir') == '1'
    try:
        resumo = salvar_paginas(obra_id, arquivos, session.get('usuario_nome'),
                                substituir=substituir)
    except ErroNegocio as exc:
        return {'erro': str(exc)}, 400

    mensagens = []
    if resumo['adicionadas']:
        mensagens.append(f"{resumo['adicionadas']} imagens adicionadas com sucesso.")
    if resumo['substituidas']:
        mensagens.append(f"{resumo['substituidas']} páginas substituídas.")
    if resumo['duplicadas']:
        mensagens.append(
            f"{resumo['duplicadas']} página(s) já existiam e não foram alteradas."
        )
    if resumo['ignoradas']:
        mensagens.append(f"{resumo['ignoradas']} arquivo(s) ignorado(s).")
    for erro in resumo['erros'][:8]:
        mensagens.append(f"Atenção: {erro}")
    corpo = {'ok': resumo['adicionadas'] + resumo['substituidas'] > 0
             or resumo['duplicadas'] > 0,
             'mensagens': mensagens, 'resumo': {
                 k: v for k, v in resumo.items() if k != 'novas_paginas'}}
    return corpo


@bp.route('/<int:obra_id>/paginas/<int:pagina_id>/remover', methods=['POST'])
@login_obrigatorio(visualizador_ok=False)
def remover_pagina(obra_id, pagina_id):
    try:
        from services.obras_service import remover_pagina as remover
        remover(obra_id, pagina_id, session.get('usuario_nome'))
        flash('Página removida da obra (o arquivo original foi preservado).', 'sucesso')
    except ErroNegocio as exc:
        flash(str(exc), 'erro')
    return redirect(url_for('obras.detalhes', obra_id=obra_id))


@bp.route('/<int:obra_id>/paginas/<int:pagina_id>/arquivo/<tipo>')
@login_obrigatorio()
def arquivo_pagina(obra_id, pagina_id, tipo):
    """Serve a imagem original ou processada de uma página (com zoom no JS)."""
    obra = obter_obra_por_id(obra_id)
    pagina = buscar_pagina(pagina_id)
    if not pagina or pagina['obra_id'] != obra['id']:
        abort(404)
    if tipo not in ('original', 'processada'):
        abort(404)
    if tipo == 'processada' and not pagina['arquivo_processado']:
        abort(404)

    nome = (pagina['arquivo_processado'] if tipo == 'processada'
            else pagina['arquivo_original'])
    if not nome_arquivo_seguro(nome):
        abort(404)
    pasta_base = (Config.PASTA_PROCESSADAS if tipo == 'processada'
                  else Config.PASTA_ORIGINAIS)
    caminho = pasta_obra(pasta_base, obra['codigo']) / nome
    if not caminho.is_file():
        abort(404)
    # TIFF (e outros formatos sem suporte nativo) são convertidos para um
    # formato exibível no navegador; o arquivo original permanece intacto.
    from services.image_processor import gerar_imagem_web
    try:
        exibivel = gerar_imagem_web(caminho)
    except Exception:
        abort(404)
    return send_file(exibivel)


@bp.route('/<int:obra_id>/excluir', methods=['POST'])
@login_obrigatorio(visualizador_ok=False)
def excluir(obra_id):
    """Exclusão com confirmação explícita — originais só se confirmado."""
    confirmar = (request.form.get('confirmar') or '').strip().upper()
    codigo = obter_obra_por_id(obra_id)['codigo']
    if confirmar != codigo:
        flash(
            'Confirmação inválida: digite o código da obra exatamente como '
            'solicitado para excluir.',
            'erro',
        )
        return redirect(url_for('obras.detalhes', obra_id=obra_id))
    excluir_obra_completa(obra_id, session.get('usuario_nome'),
                          excluir_originais=True)
    flash(f'Obra {codigo} excluída permanentemente.', 'sucesso')
    return redirect(url_for('obras.lista'))


@bp.route('/<int:obra_id>/visualizador')
@login_obrigatorio()
def visualizador(obra_id):
    obra = obter_obra_por_id(obra_id)
    paginas = listar_por_obra(obra_id)
    return render_template('visualizador.html', obra=obra, paginas=paginas)


@bp.route('/<int:obra_id>/baixar')
@login_obrigatorio()
def baixar(obra_id):
    """Gera e entrega o ZIP da obra (apenas processadas, por padrão)."""
    from services.zip_service import gerar_zip_obra
    try:
        incluir_originais = request.args.get('originais') == '1'
        caminho, quantidade = gerar_zip_obra(
            obra_id, incluir_originais=incluir_originais,
        )
    except ValueError as exc:
        flash(str(exc), 'erro')
        return redirect(url_for('obras.detalhes', obra_id=obra_id))
    return send_file(
        caminho, as_attachment=True,
        download_name=Path(caminho).name,
    )