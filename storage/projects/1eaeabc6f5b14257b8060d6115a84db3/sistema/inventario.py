"""
Sistema de Inventário simples (Python + SQLite)
Uso: python inventario.py
"""

import math
import sqlite3
from contextlib import contextmanager
from datetime import date

DB_NOME = "inventario.db"
DEFINICOES_PUBLICACAO = {
    "Livro": "Publicação composta por páginas encadernadas, impressas ou digitais, que reúne textos, histórias, pesquisas, conhecimentos ou obras literárias.",
    "Cordel": "Publicação popular, geralmente em pequenos folhetos, com textos organizados em versos e rimas, abordando histórias, tradições, acontecimentos e temas culturais.",
    "Plaquete": "Publicação de pequeno formato e poucas páginas, geralmente dedicada a poemas, contos, ensaios ou outros textos literários.",
    "Jornal": "Publicação periódica que apresenta notícias, reportagens, entrevistas, artigos e informações sobre acontecimentos locais, nacionais ou internacionais.",
    "Periodico": "Publicação periódica que reúne matérias, entrevistas, artigos, reportagens e conteúdos especializados sobre determinados assuntos, como cultura, ciência, educação e atualidades.",
    "Revista": "Publicação periódica que reúne matérias, entrevistas, artigos, reportagens e conteúdos especializados sobre determinados assuntos, como cultura, ciência, educação e atualidades.",
    "Folheto": "Material impresso composto por poucas páginas, utilizado para divulgar informações, apresentar conteúdos, orientar o público ou promover eventos, serviços e produtos.",
}


@contextmanager
def conectar():
    conn = sqlite3.connect(DB_NOME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def criar_tabela():
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT,
                quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
                preco REAL NOT NULL DEFAULT 0 CHECK (preco >= 0),
                tipo TEXT NOT NULL DEFAULT 'Produto',
                autor TEXT NOT NULL DEFAULT '',
                definicao TEXT NOT NULL DEFAULT '',
                data_insercao TEXT NOT NULL DEFAULT '',
                ano TEXT NOT NULL DEFAULT '',
                edicao TEXT NOT NULL DEFAULT '',
                volume TEXT NOT NULL DEFAULT '',
                tipologia_material TEXT NOT NULL DEFAULT '',
                possui_carimbo TEXT NOT NULL DEFAULT '',
                numero_caixa TEXT NOT NULL DEFAULT '',
                observacoes TEXT NOT NULL DEFAULT '',
                volume_ano_periodo TEXT NOT NULL DEFAULT '',
                edicao_fasciculo TEXT NOT NULL DEFAULT '',
                numero TEXT NOT NULL DEFAULT '',
                periodicidade TEXT NOT NULL DEFAULT '',
                ano_publicacao TEXT NOT NULL DEFAULT '',
                imagem_capa TEXT NOT NULL DEFAULT '',
                editora TEXT NOT NULL DEFAULT '',
                local TEXT NOT NULL DEFAULT '',
                tema TEXT NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS planilhas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                arquivo TEXT NOT NULL UNIQUE,
                tamanho INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_exclusoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tamanho INTEGER NOT NULL DEFAULT 0,
                enviado_em TEXT NOT NULL,
                excluido_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                categoria TEXT,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL,
                tipo TEXT NOT NULL,
                autor TEXT NOT NULL,
                definicao TEXT NOT NULL DEFAULT '',
                data_insercao TEXT NOT NULL DEFAULT '',
                ano TEXT NOT NULL DEFAULT '',
                edicao TEXT NOT NULL DEFAULT '',
                volume TEXT NOT NULL DEFAULT '',
                tipologia_material TEXT NOT NULL DEFAULT '',
                possui_carimbo TEXT NOT NULL DEFAULT '',
                numero_caixa TEXT NOT NULL DEFAULT '',
                observacoes TEXT NOT NULL DEFAULT '',
                volume_ano_periodo TEXT NOT NULL DEFAULT '',
                edicao_fasciculo TEXT NOT NULL DEFAULT '',
                numero TEXT NOT NULL DEFAULT '',
                periodicidade TEXT NOT NULL DEFAULT '',
                ano_publicacao TEXT NOT NULL DEFAULT '',
                imagem_capa TEXT NOT NULL DEFAULT '',
                editora TEXT NOT NULL DEFAULT '',
                local TEXT NOT NULL DEFAULT '',
                tema TEXT NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                adicionado_em TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS migracoes (
                chave TEXT PRIMARY KEY
            )
            """
        )
        colunas_planilhas = {
            coluna["name"]
            for coluna in conn.execute("PRAGMA table_info(planilhas)").fetchall()
        }
        if "tamanho" not in colunas_planilhas:
            conn.execute(
                "ALTER TABLE planilhas ADD COLUMN tamanho INTEGER NOT NULL DEFAULT 0"
            )
        colunas = {
            coluna["name"]
            for coluna in conn.execute("PRAGMA table_info(produtos)").fetchall()
        }
        if "tipo" not in colunas:
            conn.execute(
                "ALTER TABLE produtos ADD COLUMN tipo TEXT NOT NULL DEFAULT 'Produto'"
            )
        if "autor" not in colunas:
            conn.execute(
                "ALTER TABLE produtos ADD COLUMN autor TEXT NOT NULL DEFAULT ''"
            )
        if "definicao" not in colunas:
            conn.execute(
                "ALTER TABLE produtos ADD COLUMN definicao TEXT NOT NULL DEFAULT ''"
            )
        colunas_catalogo = (
            "data_insercao",
            "ano",
            "edicao",
            "volume",
            "tipologia_material",
            "possui_carimbo",
            "numero_caixa",
            "observacoes",
            "volume_ano_periodo",
            "edicao_fasciculo",
            "numero",
            "periodicidade",
            "ano_publicacao",
            "imagem_capa",
            "editora",
            "local",
            "tema",
            "notas",
        )
        for coluna in colunas_catalogo:
            if coluna not in colunas:
                conn.execute(
                    f"ALTER TABLE produtos ADD COLUMN {coluna} TEXT NOT NULL DEFAULT ''"
                )
        colunas_historico = {
            coluna["name"]
            for coluna in conn.execute(
                "PRAGMA table_info(historico_produtos)"
            ).fetchall()
        }
        for coluna in ("definicao", *colunas_catalogo):
            if coluna not in colunas_historico:
                conn.execute(
                    f"ALTER TABLE historico_produtos ADD COLUMN {coluna} TEXT NOT NULL DEFAULT ''"
                )
        migracao_produtos = "historico_produtos_legado"
        if not conn.execute(
            "SELECT 1 FROM migracoes WHERE chave = ?", (migracao_produtos,)
        ).fetchone():
            conn.execute(
                """
                INSERT OR IGNORE INTO historico_produtos
                    (produto_id, nome, categoria, quantidade, preco, tipo, autor, definicao,
                     data_insercao, ano, edicao, volume, tipologia_material,
                     possui_carimbo, numero_caixa, observacoes,
                     volume_ano_periodo, edicao_fasciculo, numero,
                     periodicidade, ano_publicacao)
                SELECT id, nome, categoria, quantidade, preco, tipo, autor, definicao,
                       data_insercao, ano, edicao, volume, tipologia_material,
                       possui_carimbo, numero_caixa, observacoes,
                       volume_ano_periodo, edicao_fasciculo, numero,
                       periodicidade, ano_publicacao
                FROM produtos
                """
            )
            conn.execute(
                "INSERT INTO migracoes (chave) VALUES (?)", (migracao_produtos,)
            )
        for tipo, definicao in DEFINICOES_PUBLICACAO.items():
            conn.execute(
                "UPDATE produtos SET definicao = ? WHERE tipo = ? AND definicao = ''",
                (definicao, tipo),
            )
            conn.execute(
                "UPDATE historico_produtos SET definicao = ? WHERE tipo = ? AND definicao = ''",
                (definicao, tipo),
            )


def inserir_produto(
    nome,
    categoria,
    quantidade,
    preco,
    tipo="Produto",
    autor="",
    data_insercao="",
    ano="",
    edicao="",
    volume="",
    tipologia_material="",
    possui_carimbo="",
    numero_caixa="",
    observacoes="",
    volume_ano_periodo="",
    edicao_fasciculo="",
    numero="",
    periodicidade="",
    ano_publicacao="",
    imagem_capa="",
    editora="",
    local="",
    tema="",
    notas="",
):
    (
        nome,
        categoria,
        quantidade,
        preco,
        tipo,
        autor,
        data_insercao,
        ano,
        edicao,
        volume,
        tipologia_material,
        possui_carimbo,
        numero_caixa,
        observacoes,
        volume_ano_periodo,
        edicao_fasciculo,
        numero,
        periodicidade,
        ano_publicacao,
        imagem_capa,
        editora,
        local,
        tema,
        notas,
    ) = validar_produto(
        nome,
        categoria,
        quantidade,
        preco,
        tipo,
        autor,
        data_insercao,
        ano,
        edicao,
        volume,
        tipologia_material,
        possui_carimbo,
        numero_caixa,
        observacoes,
        volume_ano_periodo,
        edicao_fasciculo,
        numero,
        periodicidade,
        ano_publicacao,
        imagem_capa,
        editora,
        local,
        tema,
        notas,
    )
    definicao = DEFINICOES_PUBLICACAO.get(tipo, "")

    with conectar() as conn:
        cur = conn.execute(
            """
            INSERT INTO produtos
                (nome, categoria, quantidade, preco, tipo, autor, definicao,
                 data_insercao, ano, edicao, volume, tipologia_material,
                 possui_carimbo, numero_caixa, observacoes, volume_ano_periodo,
                 edicao_fasciculo, numero, periodicidade, ano_publicacao,
                 imagem_capa, editora, local, tema, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome, categoria, quantidade, preco, tipo, autor, definicao,
                data_insercao, ano, edicao, volume, tipologia_material,
                possui_carimbo, numero_caixa, observacoes, volume_ano_periodo,
                edicao_fasciculo, numero, periodicidade, ano_publicacao,
                imagem_capa, editora, local, tema, notas,
            ),
        )
        produto_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO historico_produtos
                (produto_id, nome, categoria, quantidade, preco, tipo, autor, definicao,
                 data_insercao, ano, edicao, volume, tipologia_material,
                 possui_carimbo, numero_caixa, observacoes, volume_ano_periodo,
                 edicao_fasciculo, numero, periodicidade, ano_publicacao,
                 imagem_capa, editora, local, tema, notas, adicionado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                produto_id, nome, categoria, quantidade, preco, tipo, autor, definicao,
                data_insercao, ano, edicao, volume, tipologia_material,
                possui_carimbo, numero_caixa, observacoes, volume_ano_periodo,
                edicao_fasciculo, numero, periodicidade, ano_publicacao,
                imagem_capa, editora, local, tema, notas,
            ),
        )
    return produto_id


def validar_produto(
    nome,
    categoria,
    quantidade,
    preco,
    tipo="Produto",
    autor="",
    data_insercao="",
    ano="",
    edicao="",
    volume="",
    tipologia_material="",
    possui_carimbo="",
    numero_caixa="",
    observacoes="",
    volume_ano_periodo="",
    edicao_fasciculo="",
    numero="",
    periodicidade="",
    ano_publicacao="",
    imagem_capa="",
    editora="",
    local="",
    tema="",
    notas="",
):
    nome = nome.strip()
    tipo = tipo.strip()
    autor = autor.strip()
    data_insercao = data_insercao.strip()
    possui_carimbo = possui_carimbo.strip()
    ano = ano.strip()
    edicao = edicao.strip()
    volume = volume.strip()
    tipologia_material = tipologia_material.strip()
    numero_caixa = numero_caixa.strip()
    observacoes = observacoes.strip()
    volume_ano_periodo = volume_ano_periodo.strip()
    edicao_fasciculo = edicao_fasciculo.strip()
    numero = numero.strip()
    periodicidade = periodicidade.strip()
    ano_publicacao = ano_publicacao.strip()
    imagem_capa = imagem_capa.strip()
    editora = editora.strip()
    local = local.strip()
    tema = tema.strip()
    notas = notas.strip()
    if not nome:
        raise ValueError("O nome do produto não pode ficar vazio.")
    tipos_validos = {
        "Produto",
        "Livro",
        "Cordel",
        "Plaquete",
        "Jornal",
        "Periodico",
        "Revista",
        "Folheto",
    }
    if tipo not in tipos_validos:
        raise ValueError("Escolha um tipo de publicação válido.")
    tipos_catalogo = {"Livro", "Plaquete", "Folheto"}
    tipos_sem_preco = {*tipos_catalogo, "Periodico", "Cordel"}
    if tipo in {"Livro", "Cordel", "Plaquete", "Folheto", "Periodico"} and not autor:
        raise ValueError("Informe o nome do autor.")
    if quantidade < 0:
        raise ValueError("A quantidade não pode ser negativa.")
    if tipo in tipos_sem_preco:
        if tipo == "Cordel":
            campos_obrigatorios = {
                "imagem_capa": ("Imagem da capa", imagem_capa),
                "autor": ("Autor", autor),
                "nome": ("Título", nome),
                "edicao": ("Edição", edicao),
                "editora": ("Editora", editora),
                "local": ("Local", local),
                "ano": ("Ano", ano),
                "tema": ("Tema", tema),
                "notas": ("Notas", notas),
            }
            ano_publicacao_validar = ano
        else:
            campos_obrigatorios = {
                "nome": ("Título", nome),
                "autor": ("Autor(es)", autor),
                "data_insercao": ("Data da inserção", data_insercao),
                "possui_carimbo": ("Possui carimbo", possui_carimbo),
                "numero_caixa": ("Número da caixa", numero_caixa),
                "observacoes": ("Observações", observacoes),
            }
        if tipo != "Cordel":
            if tipo in tipos_catalogo:
                campos_obrigatorios.update(
                    {
                        "ano": ("Ano", ano),
                        "edicao": ("Edição", edicao),
                        "volume": ("Volume", volume),
                        "tipologia_material": ("Tipologia do Material", tipologia_material),
                    }
                )
                ano_publicacao_validar = ano
            else:
                campos_obrigatorios.update(
                    {
                        "volume_ano_periodo": ("Volume/Ano/Período", volume_ano_periodo),
                        "edicao_fasciculo": ("Edição/Fascículo", edicao_fasciculo),
                        "numero": ("Número", numero),
                        "periodicidade": ("Periodicidade", periodicidade),
                        "ano_publicacao": ("Ano de Publicação", ano_publicacao),
                    }
                )
                ano_publicacao_validar = ano_publicacao
        campos_vazios = [
            rotulo for rotulo, valor in campos_obrigatorios.values() if not valor
        ]
        if campos_vazios:
            raise ValueError(
                "Preencha todos os campos obrigatórios: "
                + ", ".join(campos_vazios)
                + "."
            )
        if tipo != "Cordel":
            try:
                date.fromisoformat(data_insercao)
            except ValueError as erro:
                raise ValueError("Informe uma data de inserção válida.") from erro
            if possui_carimbo not in {"Sim", "Não"}:
                raise ValueError("Informe se a publicação possui carimbo.")
        try:
            if int(ano_publicacao_validar) < 0:
                raise ValueError
        except ValueError as erro:
            raise ValueError("Informe um ano válido.") from erro
        categoria = ""
        preco = 0
    elif not math.isfinite(preco) or preco < 0:
        raise ValueError("O preço deve ser um número finito e não negativo.")

    categoria = categoria.strip()
    if tipo not in tipos_sem_preco and not categoria:
        raise ValueError("Informe o gênero ou a categoria.")

    return (
        nome,
        categoria,
        quantidade,
        preco,
        tipo,
        autor,
        data_insercao,
        ano,
        edicao,
        volume,
        tipologia_material,
        possui_carimbo,
        numero_caixa,
        observacoes,
        volume_ano_periodo,
        edicao_fasciculo,
        numero,
        periodicidade,
        ano_publicacao,
        imagem_capa,
        editora,
        local,
        tema,
        notas,
    )


def inserir_planilha(nome, arquivo, tamanho=0):
    with conectar() as conn:
        cur = conn.execute(
            "INSERT INTO planilhas (nome, arquivo, tamanho) VALUES (?, ?, ?)",
            (nome, arquivo, tamanho),
        )
        planilha_id = cur.lastrowid
    return planilha_id


def listar_planilhas():
    with conectar() as conn:
        return conn.execute(
            "SELECT id, nome, arquivo, tamanho, criado_em FROM planilhas ORDER BY id DESC"
        ).fetchall()


def buscar_planilha(planilha_id):
    with conectar() as conn:
        return conn.execute(
            "SELECT id, nome, arquivo FROM planilhas WHERE id = ?", (planilha_id,)
        ).fetchone()


def excluir_planilha(planilha_id):
    with conectar() as conn:
        planilha = conn.execute(
            """
            SELECT nome, tamanho, criado_em
            FROM planilhas
            WHERE id = ?
            """,
            (planilha_id,),
        ).fetchone()
        if not planilha:
            return False
        conn.execute(
            """
            INSERT INTO historico_exclusoes (nome, tamanho, enviado_em)
            VALUES (?, ?, ?)
            """,
            (planilha["nome"], planilha["tamanho"], planilha["criado_em"]),
        )
        conn.execute("DELETE FROM planilhas WHERE id = ?", (planilha_id,))
    return True


def listar_exclusoes():
    with conectar() as conn:
        return conn.execute(
            """
            SELECT id, nome, tamanho, enviado_em, excluido_em
            FROM historico_exclusoes
            ORDER BY id DESC
            """
        ).fetchall()


def listar_historico_produtos():
    with conectar() as conn:
        return conn.execute(
            """
            SELECT produto_id, nome, categoria, quantidade, preco, tipo, autor, definicao,
                   data_insercao, ano, edicao, volume, tipologia_material,
                   possui_carimbo, numero_caixa, observacoes, volume_ano_periodo,
                   edicao_fasciculo, numero, periodicidade, ano_publicacao,
                   imagem_capa, editora, local, tema, notas, adicionado_em
            FROM historico_produtos
            ORDER BY id DESC
            """
        ).fetchall()


def adicionar_produto(nome, categoria, quantidade, preco=0):
    try:
        inserir_produto(nome, categoria, quantidade, preco)
    except ValueError as erro:
        print(erro)
        return
    print(f"OK - Produto '{nome}' adicionado.")


def listar_produtos():
    with conectar() as conn:
        produtos = conn.execute("SELECT * FROM produtos ORDER BY nome").fetchall()

    if not produtos:
        print("Inventário vazio.")
        return

    print(f"\n{'ID':<5}{'Nome':<25}{'Categoria':<15}{'Qtd':<8}")
    print("-" * 53)
    for p in produtos:
        print(
            f"{p['id']:<5}{p['nome']:<25}{(p['categoria'] or '-'):<15}"
            f"{p['quantidade']:<8}"
        )
    print()


def ajustar_estoque(produto_id, delta):
    """Aplica uma variação ao estoque e devolve a nova quantidade."""
    with conectar() as conn:
        produto = conn.execute(
            "SELECT quantidade FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        if not produto:
            raise LookupError("Produto não encontrado.")
        nova_qtd = produto["quantidade"] + delta
        if nova_qtd < 0:
            raise ValueError("Estoque insuficiente.")
        conn.execute(
            "UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, produto_id)
        )
    return nova_qtd


def atualizar_quantidade(produto_id, delta):
    """delta positivo = entrada, negativo = saída."""
    try:
        nova_qtd = ajustar_estoque(produto_id, delta)
    except (LookupError, ValueError) as erro:
        print(erro)
        return
    print(f"OK - Nova quantidade: {nova_qtd}")


def excluir_produto(produto_id):
    with conectar() as conn:
        cur = conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    return cur.rowcount > 0


def remover_produto(produto_id):
    if excluir_produto(produto_id):
        print("OK - Produto removido.")
    else:
        print("Produto não encontrado.")


def buscar_produto(termo):
    with conectar() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE nome LIKE ? OR categoria LIKE ?",
            (f"%{termo}%", f"%{termo}%"),
        ).fetchall()
    for p in produtos:
        print(f"[{p['id']}] {p['nome']} - {p['quantidade']} un.")
    if not produtos:
        print("Nenhum resultado.")


def ler_numero(msg, tipo=int, minimo=None):
    while True:
        try:
            valor = tipo(input(msg).replace(",", "."))
            if tipo is float and not math.isfinite(valor):
                raise ValueError
            if minimo is not None and valor < minimo:
                print(f"O valor deve ser maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("Valor inválido, tente novamente.")


def menu():
    criar_tabela()
    while True:
        print(
            """
=== INVENTÁRIO ===
1. Adicionar produto
2. Listar produtos
3. Entrada de estoque
4. Saída de estoque
5. Buscar produto
6. Remover produto
0. Sair
"""
        )
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            nome = input("Nome: ").strip()
            categoria = input("Categoria: ").strip()
            qtd = ler_numero("Quantidade: ", minimo=0)
            adicionar_produto(nome, categoria, qtd)
        elif opcao == "2":
            listar_produtos()
        elif opcao == "3":
            produto_id = ler_numero("ID: ", minimo=1)
            quantidade = ler_numero("Quantidade a adicionar: ", minimo=1)
            atualizar_quantidade(produto_id, quantidade)
        elif opcao == "4":
            produto_id = ler_numero("ID: ", minimo=1)
            quantidade = ler_numero("Quantidade a retirar: ", minimo=1)
            atualizar_quantidade(produto_id, -quantidade)
        elif opcao == "5":
            buscar_produto(input("Buscar por nome/categoria: ").strip())
        elif opcao == "6":
            remover_produto(ler_numero("ID: ", minimo=1))
        elif opcao == "0":
            print("Até logo!")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()