from flask import Blueprint, request, jsonify, send_file

from datetime import datetime

from app.services.administrador_service import AdministradorService
from app.services.excel_export_service import ExcelExportService

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")

@usuario_bp.route("", methods=["POST"])
def cadastrar_usuario():
    data = request.get_json()

    try:
        resultado = AdministradorService.cadastrar_usuario(
            matricula=data["matricula"],
            nome=data["nome"],
            email=data["email"],
            telefone=data["telefone"],
            endereco=data["endereco"],
            setor=data["setor"],
            tipo= data["tipo"]
        )
        return jsonify(resultado), 201

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400


@usuario_bp.route("/<email>", methods=["GET"])
def buscar_usuario(email):
    usuario = AdministradorService.buscar_usuario_por_email(email)

    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    return jsonify({
        "id": usuario.id,
        "matricula": usuario.matricula,
        "nome": usuario.nome,
        "email": usuario.email,
        "telefone": usuario.telefone,
        "endereco": usuario.endereco,
        "setor": usuario.setor,
        "tipo": usuario.tipo,
        "bloqueado": usuario.bloqueado
    })

@usuario_bp.route("", methods=["GET"])
def listar_usuarios():
    usuarios = AdministradorService.listar_usuarios()

    return jsonify(usuarios), 200


@usuario_bp.route("/<email>/bloquear", methods=["PATCH"])
def bloquear_usuario(email):
    usuario = AdministradorService.buscar_usuario_por_email(email)

    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    AdministradorService.bloquear_usuario(usuario)

    return jsonify({"mensagem": "Usuário bloqueado"})


@usuario_bp.route("/<email>/desbloquear", methods=["PATCH"])
def desbloquear_usuario(email):
    usuario = AdministradorService.buscar_usuario_por_email(email)

    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    AdministradorService.desbloquear_usuario(usuario)

    return jsonify({"mensagem": "Usuário desbloqueado"})


@usuario_bp.route("/<email>/emprestimos-ativos", methods=["GET"])
def emprestimos_ativos(email):
    usuario = AdministradorService.buscar_usuario_por_email(email)

    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    quantidade = AdministradorService.quantidade_emprestimos_ativos(usuario)

    return jsonify({
        "usuario": usuario.email,
        "emprestimos_ativos": quantidade
    })


@usuario_bp.route("/emprestimos/<int:emprestimo_id>/devolucao", methods=["PATCH"])
def registrar_devolucao(emprestimo_id):

    emprestimo = AdministradorService.buscar_emprestimo_por_id(
        emprestimo_id
    )

    if not emprestimo:
        return jsonify({"erro": "Empréstimo não encontrado"}), 404

    AdministradorService.registrar_devolucao(emprestimo)

    return jsonify({"mensagem": "Devolução registrada"})


@usuario_bp.route("/emprestimos/<int:id>/renovar", methods=["PATCH"])
def renovar_emprestimo(id):
    dias = 15

    AdministradorService.renovar_emprestimo(id, dias)

    return jsonify({"mensagem": "Empréstimo renovado com sucesso"}), 200
    
@usuario_bp.route("/emprestimos", methods=["GET"])
def listar_emprestimos():

    emprestimos = AdministradorService.listar_emprestimos()

    return jsonify([
        {
            "id": e.id,
            "usuario_nome": e.usuario.nome,
            "usuario_email": e.usuario.email,
            "livro_titulo": e.livro.titulo,
            "livro_autor": e.livro.autor,
            "data_emprestimo": e.data_emprestimo.isoformat(),
            "data_prevista_devolucao": e.data_prevista_devolucao.isoformat(),
            "data_devolucao": (
                e.data_devolucao.isoformat()
                if e.data_devolucao else None
            )
        }
        for e in emprestimos
    ])

@usuario_bp.route("/emprestimos/<int:id>", methods=["GET"])
def detalhes_emprestimo(id):

    emprestimo = AdministradorService.buscar_emprestimo_por_id(id)

    if not emprestimo:
        return jsonify({"erro": "Empréstimo não encontrado"}), 404

    return jsonify({
        "usuario":{
            "nome": emprestimo.usuario.nome,
            "email": emprestimo.usuario.email,
            "telefone": emprestimo.usuario.telefone,
            "endereco": emprestimo.usuario.endereco,
            "matricula": emprestimo.usuario.matricula,
            "tipo": emprestimo.usuario.tipo,
            "setor": emprestimo.usuario.setor,
        },

        "livro":{
            "titulo": emprestimo.livro.titulo,
            "autor": emprestimo.livro.autor,
            "editora": emprestimo.livro.editora,
            "edicao": emprestimo.livro.edicao,
            "local": emprestimo.livro.local,
            "origem": emprestimo.livro.origem,
            "ano": emprestimo.livro.ano,
            "observacao": emprestimo.livro.observacao
        },

        "data_prevista_devolucao":
            emprestimo.data_prevista_devolucao.isoformat()
    })


@usuario_bp.route("/exportar/completo", methods=["GET"])
def exportar_completo():
    arquivo = ExcelExportService.exportar_tudo()

    nome = f"Emprestimos_Bibliotecas_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

    return send_file(
        arquivo,
        as_attachment=True,
        download_name=nome,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )