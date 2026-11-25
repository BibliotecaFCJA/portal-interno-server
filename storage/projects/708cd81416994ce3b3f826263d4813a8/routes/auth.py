"""Autenticação: login, logout e proteção de rotas."""

from functools import wraps

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for,
)

from models import usuario

bp = Blueprint('auth', __name__)


def usuario_atual():
    """Retorna o usuário da sessão (ou None)."""
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return None
    return usuario.buscar_por_id(usuario_id)


def login_obrigatorio(visualizador_ok=True):
    """Decorator que protege rotas exigindo login (e papel mínimo)."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = usuario_atual()
            if not user:
                return redirect(url_for('auth.login', proximo=request.path))
            if not visualizador_ok and user['papel'] == 'visualizador':
                flash('Seu perfil não tem permissão para esta ação.', 'erro')
                return redirect(url_for('dashboard.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def somente_administrador(view):
    """Decorator para rotas administrativas (ex.: usuários)."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = usuario_atual()
        if not user:
            return redirect(url_for('auth.login', proximo=request.path))
        if user['papel'] != 'administrador':
            flash('Ação permitida apenas a administradores.', 'erro')
            return redirect(url_for('dashboard.index'))
        return view(*args, **kwargs)
    return wrapped


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        senha = request.form.get('senha') or ''
        user = usuario.autenticar(email, senha)
        if not user:
            flash('E-mail ou senha incorretos.', 'erro')
        else:
            session.clear()
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['usuario_papel'] = user['papel']
            session.permanent = True
            destino = request.args.get('proximo') or url_for('dashboard.index')
            if not destino.startswith('/'):
                destino = url_for('dashboard.index')
            return redirect(destino)
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))