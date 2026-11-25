from flask import Flask, render_template
from app.routes.auth_routes import auth_bp
from app.routes.admin_routes import admin_bp
from app.routes.usuarios_routes import usuario_bp
from app.routes.livros_routes import livro_bp

from app.infra.database import engine, metadata

import os
import sys
import webbrowser
import threading

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS # type: ignore
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_app():
    app = Flask(
        __name__,
        template_folder=resource_path("templates"),
        static_folder=resource_path("static")
    )

    metadata.create_all(engine)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(livro_bp)

    @app.route("/")
    def login_page():
        return render_template("login.html")

    @app.route("/usuarios-listagem")
    def usuarios_page():
        return render_template("listagem_usuarios.html")
    
    @app.route("/adm/cadastro")
    def admin_page():
        return render_template("cadastro_admin.html")
    
    @app.route("/usuarios/novo")
    def novo_usuario_page():
        return render_template("cadastro_usuario.html")
    
    @app.route("/emprestimos-listagem")
    def emprestimos_page():
        return render_template("emprestimos_listagem.html")
    
    @app.route("/emprestimos/novo/<int:usuario_id>")
    def novo_emprestimo_page(usuario_id):
        return render_template("novo_emprestimo.html",usuario_id=usuario_id)
    
    return app

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")
    
if __name__ == "__main__":
    app = create_app()

    threading.Timer(1.0, open_browser).start()
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )