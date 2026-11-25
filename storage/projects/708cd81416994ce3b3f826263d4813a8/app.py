"""
Digitaliza FCJA — Sistema de Digitalização e Preservação Digital
Fundação Casa de José Américo (FCJA)

Ponto de entrada da aplicação Flask.

REGRAS DE OURO IMPLEMENTADAS NESTE SISTEMA:
1. O arquivo ORIGINAL de uma digitalização NUNCA é alterado, movido o
   sobrescrito pelo processamento. O fluxo é sempre:
   ORIGINAL → LEITURA → PROCESSAMENTO → NOVO ARQUIVO (processadas/).
2. A qualidade das imagens é preservada (resolução, DPI e formato).
3. A segurança do acervo vem antes da conveniência.
"""

from datetime import date, datetime
from pathlib import Path

from flask import (
    Flask, flash, jsonify, redirect, render_template, request, session,
    url_for,
)

from config import Config
from models.database import inicializar_banco, recuperar_interrupcoes
from models.logs import registrar as registrar_log
from routes.auth import bp as auth_bp, login_obrigatorio, usuario_atual
from routes.configuracoes import bp as configuracoes_bp
from routes.dashboard import bp as dashboard_bp
from routes.obras import bp as obras_bp
from routes.processamento import bp as processamento_bp
from services.storage import garantir_pastas


def formatar_data(valor):
    """Formata 'AAAA-MM-DD HH:MM:SS' como DD/MM/AAAA HH:MM."""
    if not valor:
        return '—'
    try:
        data, hora = str(valor).split(' ')
        ano, mes, dia = data.split('-')
        return f'{dia}/{mes}/{ano} {hora[:5]}'
    except (ValueError, IndexError):
        return str(valor)


def formatar_data_simples(valor):
    """Formata 'AAAA-MM-DD' como DD/MM/AAAA."""
    if not valor:
        return '—'
    try:
        return formatar_data_simples_str(valor)
    except Exception:
        return str(valor)


def formatar_data_simples_str(valor):
    data = str(valor).split(' ')[0]
    ano, mes, dia = data.split('-')
    return f'{dia}/{mes}/{ano}'


def criar_app():
    """Fábrica da aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 8  # 8 horas
    app.jinja_env.filters['data_br'] = formatar_data
    app.jinja_env.filters['data_br_simples'] = formatar_data_simples

    # Criação automática das pastas e do banco --------------------------
    garantir_pastas(app.config)
    Path(app.config['DATABASE_PATH']).parent.mkdir(parents=True, exist_ok=True)
    inicializar_banco(
        app.config['DATABASE_PATH'],
        Config.ADMIN_EMAIL, Config.ADMIN_NOME, Config.ADMIN_SENHA,
    )
    recuperar_interrupcoes(app.config['DATABASE_PATH'])

    # Blueprints ----------------------------------------------------------
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(obras_bp)
    app.register_blueprint(processamento_bp)
    app.register_blueprint(configuracoes_bp)

    # Contexto dos templates ----------------------------------------------
    @app.context_processor
    def injetar_contexto():
        return {
            'usuario': usuario_atual(),
            'ano_atual': date.today().year,
            'app_nome': 'Digitaliza FCJA',
            'app_subtitulo': 'Sistema de Digitalização e Preservação Digital',
            'instituicao': 'Fundação Casa de José Américo',
        }

    # Página de log de atividades (auditoria) -----------------------------
    @app.route('/logs')
    @login_obrigatorio()
    def logs():
        """Log agrupado por mês, com filtros de usuário, data e ação.

        O mês aberto vem de ?mes=AAAA-MM. Só são aceitos meses que de fato
        têm registros (e que passam pelos filtros), então o parâmetro não
        consegue apontar para nada fora do log. Sem ?mes, abre o mais
        recente.
        """
        from models.logs import (
            acoes_distintas, contar, listar_meses, listar_por_mes,
            normalizar_filtros, usuarios_distintos,
        )
        from urllib.parse import urlencode

        filtros = normalizar_filtros(request.args)
        meses = listar_meses(filtros)
        # Query string dos filtros, para os links de mês preservarem a busca
        # quando o JavaScript estiver desligado.
        base_qs = urlencode({k: v for k, v in filtros.items() if v})

        disponiveis = [item['mes'] for item in meses]
        mes_aberto = request.args.get('mes', '')
        if mes_aberto not in disponiveis:
            mes_aberto = disponiveis[0] if disponiveis else ''

        linhas, total_mes = ([], 0)
        if mes_aberto:
            linhas, total_mes = listar_por_mes(mes_aberto, filtros)

        return render_template(
            'logs.html',
            meses=meses, mes_aberto=mes_aberto, linhas=linhas,
            total_mes=total_mes, filtros=filtros, base_qs=base_qs,
            tem_filtro=any(filtros.values()),
            total=contar(filtros),
            usuarios=usuarios_distintos(), acoes=acoes_distintas(),
        )

    @app.route('/logs/mes/<mes>')
    @login_obrigatorio()
    def logs_mes(mes):
        """Entrega um mês já renderizado, para abrir sem recarregar a página.

        Devolve o mesmo HTML que a página inicial usa, gerado pelo mesmo
        parcial — não existe uma segunda versão da tabela para manter.
        """
        from models.logs import listar_por_mes, normalizar_filtros
        filtros = normalizar_filtros(request.args)
        linhas, total = listar_por_mes(mes, filtros)
        html = render_template(
            '_logs_mes.html', mes=mes, linhas=linhas, total=total,
            filtros=filtros,
        )
        return jsonify({'mes': mes, 'total': total, 'html': html})

    # Erros ----------------------------------------------------------------
    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template('erro.html', codigo=404,
                               mensagem='Página não encontrada.'), 404

    @app.errorhandler(500)
    def erro_interno(_erro):
        return render_template('erro.html', codigo=500,
                               mensagem='Erro interno do servidor.'), 500

    @app.errorhandler(413)
    def arquivo_grande(_erro):
        flash('Upload muito grande. Limite por requisição excedido.', 'erro')
        return redirect(url_for('dashboard.index')), 302

    return app


app = criar_app()


if __name__ == '__main__':
    registrar_log('sistema', 'Sistema iniciado', f'v1.0 — {datetime.now()}')
    try:
        app.run(
            host=Config.HOST, port=8001, debug=Config.DEBUG,
            threaded=True,
        )
    except OSError as erro:
        if 'Address already in use' in str(erro) or 'Endereço já em uso' in str(erro):
            print(
                '\n' + '=' * 62 +
                '\nERRO: A porta ' + str(Config.PORTA) + ' já está em uso.'
                '\n'
                '\nCausas prováveis:'
                '\n  1. O sistema já está em execução em outro terminal'
                '\n     (nesse caso, basta acessar http://127.0.0.1:' +
                str(Config.PORTA) + ' no navegador);'
                '\n  2. Um processo antigo ficou preso. Para encerrá-lo:'
                '\n       pkill -f "python app.py"'
                '\n'
                '\nAlternativa: use outra porta no arquivo .env:'
                '\n       FLASK_PORT=5001'
                '\n' + '=' * 62 + '\n'
            )
        else:
            raise
