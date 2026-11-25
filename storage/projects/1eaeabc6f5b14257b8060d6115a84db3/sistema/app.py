"""Interface web local para o sistema de inventário."""

import csv
import io
import math
import os
import secrets
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import ParseError

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from openpyxl import load_workbook
from openpyxl.utils.exceptions import IllegalCharacterError, InvalidFileException
from werkzeug.utils import secure_filename

import inventario


inventario.DB_NOME = str(
    Path(__file__).resolve().with_name(Path(inventario.DB_NOME).name)
)
PASTA_PLANILHAS = Path(__file__).resolve().with_name("planilhas")
PASTA_CAPAS = Path(__file__).resolve().with_name("static") / "capas"
LINHAS_POR_PAGINA = 30
COLUNAS_POR_PAGINA = 20

app = Flask(__name__)
app.secret_key = os.environ.get("INVENTARIO_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)


def gerar_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token
    return token


@app.before_request
def proteger_csrf():
    session.setdefault("csrf_token", secrets.token_hex(32))
    if request.method == "POST":
        token_enviado = request.form.get("csrf_token", "")
        token_esperado = session.get("csrf_token", "")
        if not token_enviado or not secrets.compare_digest(token_enviado, token_esperado):
            abort(403, description="Token CSRF inválido.")


@app.after_request
def aplicar_headers(resposta):
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "same-origin"
    resposta.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'"
    )
    return resposta


def formatar_reais(valor):
    formatado = f"{valor:,.2f}"
    formatado = formatado.replace(",", "temp").replace(".", ",").replace("temp", ".")
    return f"R$ {formatado}"


app.jinja_env.filters["reais"] = formatar_reais


def formatar_data(data):
    if not data:
        return ""
    data_formatada = date.fromisoformat(data)
    return (
        f"Dia: {data_formatada.day:02d} · "
        f"Mês: {data_formatada.month:02d} · "
        f"Ano: {data_formatada.year:04d}"
    )


app.jinja_env.filters["data_br"] = formatar_data


def formatar_tamanho(tamanho):
    valor = float(tamanho)
    for unidade in ("B", "KB", "MB", "GB"):
        if valor < 1024 or unidade == "GB":
            return f"{valor:.0f} {unidade}" if unidade == "B" else f"{valor:.1f} {unidade}"
        valor /= 1024


app.jinja_env.filters["tamanho"] = formatar_tamanho


def identificar_imagem_capa(conteudo):
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if len(conteudo) >= 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp"
    raise ValueError("A capa precisa ser uma imagem PNG, JPEG ou WebP válida.")


@app.get("/capas/<path:nome_arquivo>")
def capa_cordel(nome_arquivo):
    return send_from_directory(PASTA_CAPAS, nome_arquivo)


def decodificar_csv(conteudo):
    if conteudo.startswith((b"\xff\xfe", b"\xfe\xff")):
        codificacoes = ("utf-16",)
    elif conteudo.startswith(b"\xef\xbb\xbf"):
        codificacoes = ("utf-8-sig",)
    else:
        codificacoes = ("utf-8", "cp1252")
    for codificacao in codificacoes:
        try:
            return conteudo.decode(codificacao), codificacao
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível ler a codificação deste arquivo CSV.")


def delimitador_csv(texto):
    try:
        return csv.Sniffer().sniff(texto[:4096], delimiters=";,\t").delimiter
    except csv.Error:
        return ";" if texto.splitlines() and ";" in texto.splitlines()[0] else ","


def ler_csv(caminho):
    texto, codificacao = decodificar_csv(caminho.read_bytes())
    delimitador = delimitador_csv(texto)
    linhas = list(csv.reader(io.StringIO(texto, newline=""), delimiter=delimitador))
    return linhas, codificacao, delimitador


def abrir_planilha(planilha):
    caminho = PASTA_PLANILHAS / planilha["arquivo"]
    if Path(planilha["arquivo"]).suffix.lower() == ".csv":
        linhas, codificacao, delimitador = ler_csv(caminho)
        return "csv", linhas, codificacao, delimitador

    pasta = load_workbook(caminho, data_only=False)
    return "xlsx", pasta, None, None


def salvar_arquivo_atomico(caminho, conteudo):
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp", delete=False
        ) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(conteudo)
        temporario.replace(caminho)
    finally:
        if temporario:
            temporario.unlink(missing_ok=True)


def ler_pagina(planilha, indice_aba, pagina_linha, pagina_coluna):
    tipo, dados, codificacao, delimitador = abrir_planilha(planilha)
    if tipo == "csv":
        inicio_linha = pagina_linha * LINHAS_POR_PAGINA
        inicio_coluna = pagina_coluna * COLUNAS_POR_PAGINA
        max_linhas = len(dados)
        max_colunas = max((len(linha) for linha in dados), default=0)
        linhas = [
            (
                numero + 1,
                [
                    dados[numero][coluna]
                    if numero < len(dados) and coluna < len(dados[numero])
                    else ""
                    for coluna in range(
                        inicio_coluna,
                        min(inicio_coluna + COLUNAS_POR_PAGINA, max_colunas),
                    )
                ],
            )
            for numero in range(
                inicio_linha, min(inicio_linha + LINHAS_POR_PAGINA, max_linhas)
            )
        ]
        return {
            "tipo": tipo,
            "linhas": linhas,
            "colunas": list(
                range(
                    inicio_coluna + 1,
                    min(inicio_coluna + COLUNAS_POR_PAGINA, max_colunas) + 1,
                )
            ),
            "total_linhas": max_linhas,
            "total_colunas": max_colunas,
            "abas": [{"indice": 0, "nome": "Planilha"}],
            "aba_atual": 0,
            "codificacao": codificacao,
            "delimitador": delimitador,
        }

    try:
        if indice_aba < 0 or indice_aba >= len(dados.worksheets):
            abort(404)
        aba = dados.worksheets[indice_aba]
        max_linhas = aba.max_row or 0
        max_colunas = aba.max_column or 0
        inicio_linha = pagina_linha * LINHAS_POR_PAGINA
        inicio_coluna = pagina_coluna * COLUNAS_POR_PAGINA
        limite_linha = min(inicio_linha + LINHAS_POR_PAGINA, max_linhas)
        limite_coluna = min(inicio_coluna + COLUNAS_POR_PAGINA, max_colunas)
        linhas = [
            (
                numero,
                [
                    "" if (valor := aba.cell(numero, coluna).value) is None else str(valor)
                    for coluna in range(inicio_coluna + 1, limite_coluna + 1)
                ],
            )
            for numero in range(inicio_linha + 1, limite_linha + 1)
        ]
        return {
            "tipo": tipo,
            "linhas": linhas,
            "colunas": list(range(inicio_coluna + 1, limite_coluna + 1)),
            "total_linhas": max_linhas,
            "total_colunas": max_colunas,
            "abas": [
                {"indice": indice, "nome": nome}
                for indice, nome in enumerate(dados.sheetnames)
            ],
            "aba_atual": indice_aba,
            "codificacao": None,
            "delimitador": None,
        }
    finally:
        dados.close()


@app.get("/")
def inicio():
    termo = request.args.get("q", "").strip()
    with inventario.conectar() as conn:
        if termo:
            produtos = conn.execute(
                """
                SELECT * FROM produtos
                WHERE nome LIKE ? OR categoria LIKE ? OR autor LIKE ? OR tipo LIKE ?
                ORDER BY nome
                """,
                (f"%{termo}%", f"%{termo}%", f"%{termo}%", f"%{termo}%"),
            ).fetchall()
        else:
            produtos = conn.execute(
                "SELECT * FROM produtos ORDER BY nome"
            ).fetchall()
        resumo = conn.execute(
            """
            SELECT COUNT(*) AS produtos,
                   COALESCE(SUM(quantidade), 0) AS unidades
            FROM produtos
            """
        ).fetchone()

    planilhas = inventario.listar_planilhas()
    return render_template(
        "inventario.html",
        produtos=produtos,
        resumo=resumo,
        termo=termo,
        planilhas=planilhas,
        definicoes_publicacao=inventario.DEFINICOES_PUBLICACAO,
        data_insercao_hoje=date.today().isoformat(),
    )


@app.get("/arquivos")
def arquivos_enviados():
    arquivos = []
    for arquivo in inventario.listar_planilhas():
        dados = dict(arquivo)
        caminho = PASTA_PLANILHAS / dados["arquivo"]
        if dados["tamanho"] == 0 and caminho.exists():
            dados["tamanho"] = caminho.stat().st_size
        arquivos.append(dados)
    return render_template(
        "arquivos.html",
        arquivos=arquivos,
        exclusoes=inventario.listar_exclusoes(),
        produtos_adicionados=inventario.listar_historico_produtos(),
        csrf_token=session["csrf_token"],
    )


@app.post("/produtos")
def cadastrar():
    try:
        nome = request.form.get("nome", "")
        categoria = request.form.get("categoria", "")
        tipo = request.form.get("tipo", "")
        autor = request.form.get("autor", "")
        quantidade_enviada = request.form.get("quantidade", "").strip()
        if not quantidade_enviada:
            raise ValueError("Informe a quantidade.")
        quantidade = int(quantidade_enviada)
        preco = 0
        imagem_capa = ""
        caminho_capa = None
        if tipo == "Cordel":
            arquivo_capa = request.files.get("imagem_capa")
            if not arquivo_capa or not arquivo_capa.filename:
                raise ValueError("Selecione a imagem da capa do cordel.")
            conteudo_capa = arquivo_capa.read()
            extensao_capa = identificar_imagem_capa(conteudo_capa)
            imagem_capa = f"{secrets.token_hex(16)}.{extensao_capa}"
            PASTA_CAPAS.mkdir(parents=True, exist_ok=True)
            caminho_capa = PASTA_CAPAS / imagem_capa
            caminho_capa.write_bytes(conteudo_capa)

        cadastro_concluido = False
        try:
            inventario.inserir_produto(
                nome,
                categoria,
                quantidade,
                preco,
                tipo,
                autor,
                date.today().isoformat(),
                request.form.get("ano", ""),
                request.form.get("edicao", ""),
                request.form.get("volume", ""),
                request.form.get("tipologia_material", ""),
                request.form.get("possui_carimbo", ""),
                request.form.get("numero_caixa", ""),
                request.form.get("observacoes", ""),
                request.form.get("volume_ano_periodo", ""),
                request.form.get("edicao_fasciculo", ""),
                request.form.get("numero", ""),
                request.form.get("periodicidade", ""),
                request.form.get("ano_publicacao", ""),
                imagem_capa,
                request.form.get("editora", ""),
                request.form.get("local", ""),
                request.form.get("tema", ""),
                request.form.get("notas", ""),
            )
            cadastro_concluido = True
        finally:
            if caminho_capa is not None and not cadastro_concluido:
                caminho_capa.unlink(missing_ok=True)
    except ValueError as erro:
        flash(str(erro) or "Confira os valores informados.", "erro")
    else:
        flash("Produto cadastrado.", "sucesso")
    return redirect(url_for("inicio"))


@app.post("/planilhas")
def enviar_planilha():
    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo para enviar.", "erro")
        return redirect(url_for("arquivos_enviados"))

    nome_original = arquivo.filename.replace("\\", "/").rsplit("/", 1)[-1]
    extensao = Path(nome_original).suffix.lower()
    nome_seguro = secure_filename(nome_original) or f"arquivo{extensao}"
    nome_armazenado = f"{secrets.token_hex(16)}{extensao}"
    PASTA_PLANILHAS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_PLANILHAS / nome_armazenado
    arquivo.save(caminho)
    try:
        inventario.inserir_planilha(nome_seguro, nome_armazenado, caminho.stat().st_size)
    except Exception:
        caminho.unlink(missing_ok=True)
        raise
    flash("Arquivo enviado e salvo.", "sucesso")
    return redirect(url_for("arquivos_enviados"))


@app.get("/planilhas/<int:planilha_id>/baixar")
def baixar_planilha(planilha_id):
    planilha = inventario.buscar_planilha(planilha_id)
    if not planilha:
        abort(404)
    return send_from_directory(
        PASTA_PLANILHAS,
        planilha["arquivo"],
        as_attachment=True,
        download_name=planilha["nome"],
    )


@app.post("/planilhas/<int:planilha_id>/excluir")
def excluir_planilha(planilha_id):
    planilha = inventario.buscar_planilha(planilha_id)
    if not planilha:
        abort(404)

    caminho = PASTA_PLANILHAS / planilha["arquivo"]
    quarentena = PASTA_PLANILHAS / f".{secrets.token_hex(16)}.deleting"
    if caminho.exists():
        caminho.replace(quarentena)
    try:
        removida = inventario.excluir_planilha(planilha_id)
    except Exception:
        if quarentena.exists():
            quarentena.replace(caminho)
        raise
    if not removida:
        if quarentena.exists():
            quarentena.replace(caminho)
        abort(404)

    quarentena.unlink(missing_ok=True)
    flash("Planilha excluída.", "sucesso")
    return redirect(url_for("arquivos_enviados"))


@app.get("/planilhas/<int:planilha_id>")
def visualizar_planilha(planilha_id):
    planilha = inventario.buscar_planilha(planilha_id)
    if not planilha:
        abort(404)
    try:
        indice_aba = int(request.args.get("aba", "0"))
        pagina_linha = int(request.args.get("linha", "0"))
        pagina_coluna = int(request.args.get("coluna", "0"))
        if min(indice_aba, pagina_linha, pagina_coluna) < 0:
            raise ValueError
        pagina = ler_pagina(planilha, indice_aba, pagina_linha, pagina_coluna)
    except (
        OSError,
        ValueError,
        KeyError,
        EOFError,
        InvalidFileException,
        ParseError,
        zipfile.BadZipFile,
    ) as erro:
        flash(f"Não foi possível abrir a planilha: {erro}", "erro")
        return redirect(url_for("inicio"))

    total_paginas_linha = max(
        1, math.ceil(pagina["total_linhas"] / LINHAS_POR_PAGINA)
    )
    total_paginas_coluna = max(
        1, math.ceil(pagina["total_colunas"] / COLUNAS_POR_PAGINA)
    )
    if pagina_linha >= total_paginas_linha or pagina_coluna >= total_paginas_coluna:
        abort(404)
    return render_template(
        "planilha.html",
        planilha=planilha,
        pagina=pagina,
        pagina_linha=pagina_linha,
        pagina_coluna=pagina_coluna,
        total_paginas_linha=total_paginas_linha,
        total_paginas_coluna=total_paginas_coluna,
        csrf_token=session["csrf_token"],
    )


@app.post("/planilhas/<int:planilha_id>/editar")
def editar_planilha(planilha_id):
    planilha = inventario.buscar_planilha(planilha_id)
    if not planilha:
        abort(404)
    try:
        indice_aba = int(request.form.get("aba", "0"))
        pagina_linha = int(request.form.get("linha", "0"))
        pagina_coluna = int(request.form.get("coluna", "0"))
        if min(indice_aba, pagina_linha, pagina_coluna) < 0:
            raise ValueError
        pagina = ler_pagina(planilha, indice_aba, pagina_linha, pagina_coluna)
        linhas_visiveis = {numero for numero, _ in pagina["linhas"]}
        colunas_visiveis = set(pagina["colunas"])
        alteracoes = {}
        for chave, valor in request.form.items():
            if not chave.startswith("celula_"):
                continue
            _, linha, coluna = chave.split("_", 2)
            coordenada = int(linha), int(coluna)
            if coordenada[0] not in linhas_visiveis or coordenada[1] not in colunas_visiveis:
                abort(400)
            alteracoes[coordenada] = valor

        caminho = PASTA_PLANILHAS / planilha["arquivo"]
        if pagina["tipo"] == "csv":
            dados, codificacao, delimitador = ler_csv(caminho)
            alteracoes_reais = {}
            for (linha, coluna), valor in alteracoes.items():
                linha_atual = dados[linha - 1]
                valor_atual = linha_atual[coluna - 1] if coluna <= len(linha_atual) else ""
                if valor == valor_atual:
                    continue
                alteracoes_reais[(linha, coluna)] = valor
            if not alteracoes_reais:
                flash("Nenhuma célula foi alterada.", "sucesso")
                return redirect(
                    url_for(
                        "visualizar_planilha",
                        planilha_id=planilha_id,
                        aba=indice_aba,
                        linha=pagina_linha,
                        coluna=pagina_coluna,
                    )
                )
            for (linha, coluna), valor in alteracoes_reais.items():
                linha_atual = dados[linha - 1]
                linha_atual.extend([""] * (coluna - len(linha_atual)))
                linha_atual[coluna - 1] = valor
            saida = io.StringIO(newline="")
            escritor = csv.writer(saida, delimiter=delimitador)
            escritor.writerows(dados)
            salvar_arquivo_atomico(caminho, saida.getvalue().encode(codificacao))
        else:
            pasta = load_workbook(caminho, data_only=False)
            try:
                aba = pasta.worksheets[indice_aba]
                alterou = False
                for (linha, coluna), valor in alteracoes.items():
                    celula = aba.cell(linha, coluna)
                    valor_original = celula.value
                    exibido = "" if valor_original is None else str(valor_original)
                    if valor == exibido:
                        continue
                    if len(valor) > 32767:
                        raise ValueError(
                            f"A célula {celula.coordinate} excede o limite de 32.767 caracteres."
                        )
                    alterou = True
                    if isinstance(valor_original, bool):
                        if valor.lower() not in {"true", "false"}:
                            raise ValueError(
                                f"A célula {celula.coordinate} aceita apenas true ou false."
                            )
                        celula.value = valor.lower() == "true"
                    elif isinstance(valor_original, (int, float)):
                        try:
                            numero = float(valor)
                        except ValueError as erro:
                            raise ValueError(
                                f"A célula {celula.coordinate} precisa manter um valor numérico."
                            ) from erro
                        if not math.isfinite(numero):
                            raise ValueError(
                                f"A célula {celula.coordinate} precisa manter um valor numérico finito."
                            )
                        if isinstance(valor_original, int):
                            if not numero.is_integer():
                                raise ValueError(
                                    f"A célula {celula.coordinate} precisa manter um número inteiro."
                                )
                            celula.value = int(numero)
                        else:
                            celula.value = numero
                    else:
                        celula.value = valor
                if alterou:
                    saida = io.BytesIO()
                    pasta.save(saida)
                    salvar_arquivo_atomico(caminho, saida.getvalue())
            finally:
                pasta.close()
    except (
        OSError,
        ValueError,
        IndexError,
        KeyError,
        EOFError,
        InvalidFileException,
        IllegalCharacterError,
        ParseError,
        zipfile.BadZipFile,
    ) as erro:
        flash(f"Não foi possível salvar as alterações: {erro}", "erro")
        return redirect(
            url_for(
                "visualizar_planilha",
                planilha_id=planilha_id,
                aba=request.form.get("aba", "0"),
                linha=request.form.get("linha", "0"),
                coluna=request.form.get("coluna", "0"),
            )
        )

    flash("Alterações salvas na planilha.", "sucesso")
    return redirect(
        url_for(
            "visualizar_planilha",
            planilha_id=planilha_id,
            aba=indice_aba,
            linha=pagina_linha,
            coluna=pagina_coluna,
        )
    )


@app.post("/produtos/<int:produto_id>/estoque")
def movimentar(produto_id):
    try:
        quantidade = int(request.form.get("quantidade", ""))
        sentido = request.form.get("sentido", "")
        if quantidade < 1:
            raise ValueError("Informe uma quantidade maior que zero.")
        if sentido not in {"entrada", "saida"}:
            raise ValueError("Tipo de movimentação inválido.")
        delta = quantidade if sentido == "entrada" else -quantidade
        nova_quantidade = inventario.ajustar_estoque(produto_id, delta)
    except (LookupError, ValueError) as erro:
        flash(str(erro), "erro")
    else:
        flash(f"Estoque atualizado: {nova_quantidade} unidades.", "sucesso")
    return redirect(url_for("inicio"))


@app.post("/produtos/<int:produto_id>/remover")
def remover(produto_id):
    if inventario.excluir_produto(produto_id):
        flash("Produto removido.", "sucesso")
    else:
        flash("Produto não encontrado.", "erro")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    inventario.criar_tabela()
    use_https = (
        os.environ.get("INVENTARIO_USE_HTTPS", "").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    cert_path = Path(__file__).resolve().with_name("cert.pem")
    key_path = Path(__file__).resolve().with_name("key.pem")
    if use_https and cert_path.exists() and key_path.exists():
        app.run(
            host="0.0.0.0",
            port=5001,
            debug=False,
            ssl_context=(str(cert_path), str(key_path)),
        )
    else:
        app.run(host="0.0.0.0", port=5001, debug=False)