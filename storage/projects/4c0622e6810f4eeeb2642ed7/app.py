
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.serving import make_server
from dotenv import load_dotenv
import os
import sys

load_dotenv()

from database import (
    listar_instituicoes,
    adicionar_instituicao,
    buscar_instituicao,
    buscar_instituicoes_por_termo,
    atualizar_instituicao,
    excluir_instituicao,
    excluir_instituicoes
)
from database import (
    listar_pessoas,
    adicionar_pessoa,
    buscar_pessoa,
    atualizar_pessoa,
    excluir_pessoa,
    excluir_pessoas
)
app = Flask(__name__, template_folder='templates', static_folder='static')

if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY deve ser configurada em ambiente de produção.')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY deve ser configurada.')

app.config["SECRET_KEY"] = secret_key

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

csrf = CSRFProtect(app)

from database import db
from models import Pessoa, Instituicao

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar o painel administrativo.'


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    return render_template('login.html', error='Sessão expirada ou formulário inválido. Tente novamente.'), 400


@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return render_template('404.html'), 404


class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    expected_username = os.environ.get('ADMIN_USERNAME')
    if user_id == expected_username:
        return AdminUser(user_id)
    return None


def caminho_base():
    return os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

caminho_db = os.path.join(caminho_base(), "fundacao.db")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{caminho_db}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


def valor_formulario(nome):
    return (request.form.get(nome) or "").strip()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        expected_username = os.environ.get('ADMIN_USERNAME') or 'admin'
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        if stored_hash is None:
            admin_password_hash = os.environ.get('ADMIN_PASSWORD')

            if not admin_password_hash:
                raise RuntimeError('ADMIN_PASSWORD deve ser configurada.')

            stored_hash = generate_password_hash(admin_password_hash)

        if username == expected_username and check_password_hash(stored_hash, password):
            login_user(AdminUser(username))
            return redirect(url_for("index"))

        return render_template('login.html', error='Credenciais inválidas.'), 401, {
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0'
        }

    response = render_template('login.html')
    return response, 200, {
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -----------------------------
# ROTA PRINCIPAL (INSTITUIÇÕES)
# -----------------------------
@app.route("/", methods=["GET"])
@login_required
def index():
    termo = request.args.get("q")
    if termo:
        instituicoes = buscar_instituicoes_por_termo(termo)
    else:
        instituicoes = listar_instituicoes()
    return render_template("index.html", instituicoes=instituicoes)


# -----------------------------
# ESCOLHER TIPO DE CADASTRO
# -----------------------------
@app.route("/escolher_cadastro")
@login_required
def escolher_cadastro():
    return redirect(url_for("index"))


@app.route("/cadastros")
@login_required
def cadastros():
    return redirect(url_for("index"))


# -----------------------------
# ROTAS DE INSTITUIÇÃO
# -----------------------------
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        nome_oficial = valor_formulario("nome_oficial")
        if not nome_oficial:
            return render_template("add.html", erro="O nome oficial e obrigatorio."), 400

        dados = {
            "nome_oficial": nome_oficial,
            "email_oficial": valor_formulario("email_oficial"),
            "telefone_principal": valor_formulario("telefone_principal"),
            "site_url": valor_formulario("site_url"),
            "endereco_completo": valor_formulario("endereco_completo"),
            "status": "Ativo",
            "observacao": valor_formulario("observacao"),
        }

        adicionar_instituicao(dados)

        return redirect(url_for("index"))

    return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_instituicao(id):
    instituicao = buscar_instituicao(id)

    if not instituicao:
        return redirect(url_for("index"))

    if request.method == "POST":
        nome_oficial = valor_formulario("nome_oficial")
        if not nome_oficial:
            return render_template("edit.html", instituicao=instituicao,
                                   erro="O nome oficial e obrigatorio."), 400

        dados = {
            "nome_oficial": nome_oficial,
            "email_oficial": valor_formulario("email_oficial"),
            "telefone_principal": valor_formulario("telefone_principal"),
            "site_url": valor_formulario("site_url"),
            "endereco_completo": valor_formulario("endereco_completo"),
            "observacao": valor_formulario("observacao"),
        }
        atualizar_instituicao(id, dados)

        return redirect(url_for("index"))

    return render_template("edit.html", instituicao=instituicao)

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    excluir_instituicao(id)

    return redirect(url_for("index"))


@app.route("/delete-selected", methods=["POST"])
@login_required
def delete_selected_instituicoes():
    ids = []
    for value in request.form.getlist("instituicao_ids"):
        try:
            ids.append(int(value))
        except ValueError:
            continue

    if ids:
        excluir_instituicoes(ids)

    return redirect(url_for("index"))

@app.route("/view/<int:id>")
@login_required
def view(id):
    instituicao = buscar_instituicao(id)
    if not instituicao:
        return redirect(url_for("index"))
    return render_template("view.html", instituicao=instituicao)

# -----------------------------
# ROTAS DE PESSOAS
# -----------------------------
@app.route("/pessoas")
@login_required
def pessoas():
    query_term = request.args.get("q")
    todas_pessoas = listar_pessoas()

    if query_term:
        pessoas = [
            p for p in todas_pessoas
            if query_term.lower() in (p.nome or "").lower()
            or query_term.lower() in (p.email or "").lower()
        ]
    else:
        pessoas = todas_pessoas

    return render_template("pessoas.html", pessoas=pessoas, query_term=query_term)

@app.route("/pessoas/add", methods=["GET", "POST"])
@login_required
def add_pessoa():
    if request.method == "POST":
        nome = valor_formulario("nome")
        if not nome:
            return render_template("add_pessoas.html", erro="O nome e obrigatorio."), 400

        dados = {
            "nome": nome,
            "email": valor_formulario("email"),
            "telefone": valor_formulario("telefone"),
            "endereco": valor_formulario("endereco"),
            "instagram": valor_formulario("instagram"),
            "cargo": valor_formulario("cargo"),
            "observacao": valor_formulario("observacao"),
        }

        adicionar_pessoa(dados)

        return redirect(url_for("pessoas"))

    return render_template("add_pessoas.html")

@app.route("/pessoas/<int:id>")
@login_required
def view_pessoa(id):
    pessoa = buscar_pessoa(id)
    if not pessoa:
        return "Pessoa não encontrada", 404
    return render_template("view_pessoas.html", pessoa=pessoa)

@app.route("/pessoas/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_pessoa(id):
    pessoa = buscar_pessoa(id)
    if not pessoa:
        return "Pessoa não encontrada", 404

    if request.method == "POST":
        nome = valor_formulario("nome")
        if not nome:
            return render_template("edit_pessoas.html", pessoa=pessoa,
                                   erro="O nome e obrigatorio."), 400

        dados = {
            "nome": nome,
            "email": valor_formulario("email"),
            "telefone": valor_formulario("telefone"),
            "endereco": valor_formulario("endereco"),
            "instagram": valor_formulario("instagram"),
            "cargo": valor_formulario("cargo"),
            "observacao": valor_formulario("observacao"),
        }

        atualizar_pessoa(id, dados)

        return redirect(url_for("pessoas"))

    return render_template("edit_pessoas.html", pessoa=pessoa)

@app.route("/pessoas/delete/<int:id>", methods=["POST"])
@login_required
def delete_pessoa(id):
    excluir_pessoa(id)

    return redirect(url_for("pessoas"))


@app.route("/pessoas/delete-selected", methods=["POST"])
@login_required
def delete_selected_pessoas():
    ids = []
    for value in request.form.getlist("pessoa_ids"):
        try:
            ids.append(int(value))
        except ValueError:
            continue

    if ids:
        excluir_pessoas(ids)

    return redirect(url_for("pessoas"))

# -----------------------------
# RODAR O SERVIDOR
# -----------------------------
def criar_servidor():
    return make_server("0.0.0.0", int(os.environ.get("PORT", "8000")), app)

if __name__ == "__main__":
    servidor = criar_servidor()
    servidor.serve_forever()
