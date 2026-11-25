from openpyxl import Workbook
from io import BytesIO
from app.infra.database import get_session
from app.infra.tables.usuario_table import usuarios_table
from app.infra.tables.emprestimo_table import emprestimos_table
from app.infra.tables.livro_table import livros_table
from sqlalchemy import select


class ExcelExportService:

    @staticmethod
    def exportar_tudo():
        wb = Workbook()

        ws_usuarios = wb.active
        ws_usuarios.title = "Usuarios"

        ws_usuarios.append([
            "ID", "Matricula", "Nome", "Email", "Telefone",
            "Endereço", "Setor", "Tipo"
        ])

        ws_emprestimos = wb.create_sheet(title="Emprestimos")

        ws_emprestimos.append([
            "ID",
            "Usuário Nome", "Usuário Email",
            "Livro Título", "Livro Autor",
            "Editora", "Edição", "Ano",
            "Local", "Origem", "Observação",
            "Data Empréstimo",
            "Data Prevista",
            "Data Devolução",
            "Renovações"
        ])

        with get_session() as session:

            usuarios = session.execute(
                select(usuarios_table)
            ).mappings().all()

            for u in usuarios:
                ws_usuarios.append([
                    u["id"],
                    u["matricula"],
                    u["nome"],
                    u["email"],
                    u["telefone"],
                    u["endereco"],
                    u.get("setor"),
                    u.get("tipo"),
                ])

            stmt = (
                select(
                    emprestimos_table.c.id.label("e_id"),
                    emprestimos_table.c.data_emprestimo,
                    emprestimos_table.c.data_prevista_devolucao,
                    emprestimos_table.c.data_devolucao,
                    emprestimos_table.c.renovacoes,

                    usuarios_table.c.nome.label("usuario_nome"),
                    usuarios_table.c.email.label("usuario_email"),

                    livros_table.c.titulo.label("livro_titulo"),
                    livros_table.c.autor.label("livro_autor"),
                    livros_table.c.editora,
                    livros_table.c.edicao,
                    livros_table.c.ano,
                    livros_table.c.local,
                    livros_table.c.origem,
                    livros_table.c.observacao
                )
                .join(usuarios_table, usuarios_table.c.id == emprestimos_table.c.usuario_id)
                .join(livros_table, livros_table.c.id == emprestimos_table.c.livro_id)
            )

            resultados = session.execute(stmt).mappings().all()

            for r in resultados:
                ws_emprestimos.append([
                    r["e_id"],
                    r["usuario_nome"],
                    r["usuario_email"],
                    r["livro_titulo"],
                    r["livro_autor"],
                    r["editora"] or "",
                    r["edicao"] or "",
                    r["ano"] or "",
                    r["local"] or "",
                    r["origem"] or "",
                    r["observacao"] or "",
                    str(r["data_emprestimo"]) if r["data_emprestimo"] else "",
                    str(r["data_prevista_devolucao"]) if r["data_prevista_devolucao"] else "",
                    str(r["data_devolucao"]) if r["data_devolucao"] else "",
                    r["renovacoes"] or 0
                ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output