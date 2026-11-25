"""Dashboard (página inicial) e helpers compartilhados entre as rotas."""

from flask import Blueprint, render_template

from .auth import login_obrigatorio
from models.logs import listar as listar_logs
from models.obra import ROTULOS_STATUS, estatisticas, recentes

bp = Blueprint('dashboard', __name__)


def _formatar_data(valor):
    """Formata 'AAAA-MM-DD HH:MM:SS' como DD/MM/AAAA HH:MM."""
    if not valor:
        return '—'
    try:
        data, hora = str(valor).split(' ')
        ano, mes, dia = data.split('-')
        hora_curta = hora[:5]
        return f'{dia}/{mes}/{ano} {hora_curta}'
    except (ValueError, IndexError):
        return str(valor)


def _formatar_data_simples(valor):
    try:
        data = str(valor).split(' ')[0]
        ano, mes, dia = data.split('-')
        return f'{dia}/{mes}/{ano}'
    except (ValueError, IndexError):
        return str(valor)


@bp.route('/')
@login_obrigatorio()
def index():
    stats = estatisticas()
    ultimas = recentes(limite=8)
    logs, _ = listar_logs(pagina=1, por_pagina=6)
    return render_template(
        'dashboard.html',
        stats=stats,
        obras_recentes=ultimas,
        logs=logs,
        rotulos_status=ROTULOS_STATUS,
    )
