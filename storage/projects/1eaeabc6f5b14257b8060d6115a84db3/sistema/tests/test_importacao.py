import io
import json
import re
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook, load_workbook

import app as aplicacao
import inventario


class TestEnvioPlanilhas(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(
            inventario, "DB_NOME", str(Path(self.diretorio.name) / "teste.db")
        )
        self.patch_pasta = patch.object(
            aplicacao, "PASTA_PLANILHAS", Path(self.diretorio.name) / "planilhas"
        )
        self.patch_capas = patch.object(
            aplicacao, "PASTA_CAPAS", Path(self.diretorio.name) / "capas"
        )
        self.patch_db.start()
        self.patch_pasta.start()
        self.patch_capas.start()
        inventario.criar_tabela()
        aplicacao.app.testing = True
        self.cliente = aplicacao.app.test_client()
        self.cliente.get("/")
        with self.cliente.session_transaction() as sessao:
            self.csrf_token = sessao["csrf_token"]

    def tearDown(self):
        self.patch_pasta.stop()
        self.patch_capas.stop()
        self.patch_db.stop()
        self.diretorio.cleanup()

    def enviar(self, conteudo, nome):
        return self.cliente.post(
            "/planilhas",
            data={
                "csrf_token": self.csrf_token,
                "arquivo": (io.BytesIO(conteudo), nome),
            },
            follow_redirects=True,
        )

    def planilhas_cadastradas(self):
        return inventario.listar_planilhas()

    def test_envia_csv_sem_exigir_cabecalho_ou_conteudo_especifico(self):
        conteudo = b"qualquer conteudo de planilha,sem colunas padrao\n"

        resposta = self.enviar(conteudo, "minha-planilha.csv")

        planilhas = self.planilhas_cadastradas()
        self.assertIn(b"Arquivo enviado e salvo.", resposta.data)
        self.assertEqual(len(planilhas), 1)
        self.assertIn(b"minha-planilha.csv", resposta.data)
        download = self.cliente.get(f"/planilhas/{planilhas[0]['id']}/baixar")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, conteudo)
        self.assertIn("attachment", download.headers["Content-Disposition"])
        download.close()

    def test_guarda_arquivo_xlsx_sem_validar_seu_conteudo(self):
        conteudo = b"arquivo excel nao interpretado"

        resposta = self.enviar(conteudo, "planilha.xlsx")

        planilhas = self.planilhas_cadastradas()
        self.assertIn(b"Arquivo enviado e salvo.", resposta.data)
        self.assertEqual(len(planilhas), 1)
        download = self.cliente.get(f"/planilhas/{planilhas[0]['id']}/baixar")
        self.assertEqual(download.data, conteudo)
        download.close()

    def test_nao_altera_produtos_ao_enviar_planilha(self):
        self.enviar(b"titulo,autor\nqualquer valor", "dados.csv")

        with inventario.conectar() as conn:
            produtos = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        self.assertEqual(produtos, 0)

    def test_guarda_arquivo_de_qualquer_formato_no_historico(self):
        conteudo = b"arquivo PDF ou outro formato"
        resposta = self.enviar(conteudo, "documento.pdf")

        arquivos = self.planilhas_cadastradas()
        self.assertIn(b"Arquivo enviado e salvo.", resposta.data)
        self.assertEqual(len(arquivos), 1)
        pagina = self.cliente.get("/arquivos")
        self.assertIn(b"documento.pdf", pagina.data)
        self.assertNotIn(b">Ver / editar</a>", pagina.data)
        self.assertEqual(arquivos[0]["tamanho"], len(conteudo))
        download = self.cliente.get(f"/planilhas/{arquivos[0]['id']}/baixar")
        self.assertEqual(download.data, conteudo)
        download.close()

    def test_tela_de_arquivos_informa_que_nao_exige_modelo_de_planilha(self):
        resposta = self.cliente.get("/arquivos")

        self.assertIn(b"Todos os formatos podem ser baixados", resposta.data)
        self.assertNotIn(b"accept=", resposta.data)

    def test_produto_adicionado_aparece_no_historico_mesmo_apos_remocao(self):
        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "nome": "Livro de teste",
                "tipo": "Livro",
                "autor": "Autora",
                "quantidade": "3",
                "data_insercao": "2026-10-22",
                "ano": "2024",
                "edicao": "2ª",
                "volume": "I",
                "tipologia_material": "Impresso",
                "possui_carimbo": "Sim",
                "numero_caixa": "CX-04",
                "observacoes": "Conservado",
            },
            follow_redirects=True,
        )

        self.assertIn(b"Produto cadastrado.", resposta.data)
        produto = inventario.listar_historico_produtos()[0]
        self.assertEqual(produto["nome"], "Livro de teste")
        self.assertEqual(produto["categoria"], "")
        self.assertEqual(produto["quantidade"], 3)
        self.assertEqual(produto["preco"], 0)
        self.assertEqual(produto["tipo"], "Livro")
        self.assertEqual(produto["autor"], "Autora")
        self.assertEqual(produto["data_insercao"], date.today().isoformat())
        self.assertEqual(produto["ano"], "2024")
        self.assertEqual(produto["edicao"], "2ª")
        self.assertEqual(produto["volume"], "I")
        self.assertEqual(produto["tipologia_material"], "Impresso")
        self.assertEqual(produto["possui_carimbo"], "Sim")
        self.assertEqual(produto["numero_caixa"], "CX-04")
        self.assertEqual(produto["observacoes"], "Conservado")
        self.assertEqual(
            produto["definicao"], inventario.DEFINICOES_PUBLICACAO["Livro"]
        )
        self.assertTrue(produto["adicionado_em"])

        acervo = self.cliente.get("/")
        self.assertIn(
            (
                f"Inserção: Dia: {date.today().day:02d} · "
                f"Mês: {date.today().month:02d} · Ano: {date.today().year:04d}"
            ).encode(),
            acervo.data,
        )
        self.assertIn(b"Tipologia: Impresso", acervo.data)
        historico = self.cliente.get("/arquivos")
        self.assertIn(
            (
                f"Data da inserção: Dia: {date.today().day:02d} · "
                f"Mês: {date.today().month:02d} · Ano: {date.today().year:04d}"
            ).encode(),
            historico.data,
        )

        pagina = self.cliente.get("/arquivos")
        self.assertIn(b"Produtos adicionados", pagina.data)
        self.assertIn(b"Livro de teste", pagina.data)
        self.assertIn(b"Autora", pagina.data)
        self.assertIn(
            (
                f"Data da inserção: Dia: {date.today().day:02d} · "
                f"Mês: {date.today().month:02d} · Ano: {date.today().year:04d}"
            ).encode(),
            pagina.data,
        )
        self.assertIn(b"N\xc3\xbamero da Caixa: CX-04", pagina.data)
        self.assertIn(b"Observa\xc3\xa7\xc3\xb5es: Conservado", pagina.data)
        self.assertIn(b"Produto adicionado", pagina.data)

        self.assertTrue(inventario.excluir_produto(produto["produto_id"]))
        pagina_apos_remocao = self.cliente.get("/arquivos")
        self.assertIn(b"Livro de teste", pagina_apos_remocao.data)

    def test_definicao_e_preenchida_no_formulario_e_salva_a_partir_do_tipo(self):
        definicao = inventario.DEFINICOES_PUBLICACAO["Periodico"]
        pagina = self.cliente.get("/")

        self.assertIn(
            b'<label for="definicao">Defini\xc3\xa7\xc3\xa3o</label>', pagina.data
        )
        self.assertIn(inventario.DEFINICOES_PUBLICACAO["Livro"].encode(), pagina.data)
        correspondencia = re.search(
            rb"const definicoesPublicacao = (.*);", pagina.data
        )
        self.assertIsNotNone(correspondencia)
        definicoes = json.loads(correspondencia.group(1))
        self.assertEqual(definicoes["Periodico"], definicao)
        self.assertIn(
            b"campoDefinicao.value = definicoesPublicacao[tipoPublicacao.value]",
            pagina.data,
        )

        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "nome": "Revista de teste",
                "tipo": "Periodico",
                "autor": "Autoria de teste",
                "quantidade": "1",
                "data_insercao": "2026-10-22",
                "volume_ano_periodo": "Volume 4, ano 2025, janeiro-março",
                "edicao_fasciculo": "Edição 2, fascículo 1",
                "numero": "8",
                "periodicidade": "Trimestral",
                "ano_publicacao": "2025",
                "possui_carimbo": "Não",
                "numero_caixa": "P-22",
                "observacoes": "Coleção completa",
                "preco": "999.99",
                "definicao": "Definição enviada pelo navegador",
            },
            follow_redirects=True,
        )

        self.assertIn(b"Produto cadastrado.", resposta.data)
        produto = inventario.listar_historico_produtos()[0]
        self.assertEqual(produto["nome"], "Revista de teste")
        self.assertEqual(produto["tipo"], "Periodico")
        self.assertEqual(produto["autor"], "Autoria de teste")
        self.assertEqual(produto["definicao"], definicao)
        self.assertEqual(produto["categoria"], "")
        self.assertEqual(produto["preco"], 0)
        self.assertEqual(produto["data_insercao"], date.today().isoformat())
        self.assertEqual(produto["volume_ano_periodo"], "Volume 4, ano 2025, janeiro-março")
        self.assertEqual(produto["edicao_fasciculo"], "Edição 2, fascículo 1")
        self.assertEqual(produto["numero"], "8")
        self.assertEqual(produto["periodicidade"], "Trimestral")
        self.assertEqual(produto["ano_publicacao"], "2025")
        self.assertEqual(produto["possui_carimbo"], "Não")
        self.assertEqual(produto["numero_caixa"], "P-22")
        self.assertEqual(produto["observacoes"], "Coleção completa")

        acervo = self.cliente.get("/")
        self.assertIn(b"Titulo do Peri\xc3\xb3dico", acervo.data)
        self.assertIn(b"Volume/Ano/Per\xc3\xadodo: Volume 4", acervo.data)
        self.assertIn(b"Edi\xc3\xa7\xc3\xa3o/Fasc\xc3\xadculo: Edi\xc3\xa7\xc3\xa3o 2", acervo.data)
        self.assertIn(b"Periodicidade: Trimestral", acervo.data)

        historico = self.cliente.get("/arquivos")
        self.assertIn(b"Volume/Ano/Per\xc3\xadodo: Volume 4", historico.data)
        self.assertIn(b"Edi\xc3\xa7\xc3\xa3o/Fasc\xc3\xadculo: Edi\xc3\xa7\xc3\xa3o 2", historico.data)
        self.assertIn(b"Periodicidade: Trimestral", historico.data)
        self.assertIn(b"Ano de Publica\xc3\xa7\xc3\xa3o: 2025", historico.data)

    def test_formulario_mostra_campos_de_catalogacao_para_tipos_de_publicacao(self):
        pagina = self.cliente.get("/")

        self.assertIn(b'<option value="Livro">Livro</option>', pagina.data)
        self.assertIn(b'<option value="Plaquete">Plaquete</option>', pagina.data)
        self.assertIn(b'<option value="Periodico">Peri\xc3\xb3dico</option>', pagina.data)
        self.assertNotIn(b'<option value="Revista">', pagina.data)
        self.assertIn(b'<option value="Folheto">Folheto</option>', pagina.data)
        self.assertIn(b'<option value="Cordel">Cordel</option>', pagina.data)
        self.assertNotIn(b'<option value="Jornal">', pagina.data)
        self.assertNotIn("Preço unitário".encode(), pagina.data)
        self.assertNotIn(b'name="preco"', pagina.data)
        self.assertNotIn(b"Valor total em estoque", pagina.data)
        self.assertNotIn(b"Valor em estoque", pagina.data)
        for nome_campo in (
            "tipo",
            "definicao",
            "nome",
            "autor",
            "data_insercao",
            "quantidade",
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
        ):
            with self.subTest(campo_obrigatorio=nome_campo):
                campos = re.findall(
                    rb"<(?:input|select|textarea)\b[^>]*name=\""
                    + nome_campo.encode()
                    + rb"\"[^>]*>",
                    pagina.data,
                )
                self.assertTrue(campos, f"Campo ausente: {nome_campo}")
                if nome_campo == "data_insercao":
                    self.assertEqual(len(campos), 1)
                    self.assertIn(b"readonly", campos[0])
                    self.assertIn(
                        f'value="{date.today().isoformat()}"'.encode(), campos[0]
                    )
                else:
                    self.assertTrue(
                        all(b"required" in campo for campo in campos),
                        f"Campo não marcado como obrigatório: {nome_campo}",
                    )
        self.assertEqual(pagina.data.count(b"Data da inser\xc3\xa7\xc3\xa3o"), 1)
        self.assertIn(b'<label for="data-dia">Dia</label>', pagina.data)
        self.assertIn(b'<label for="data-mes">M\xc3\xaas</label>', pagina.data)
        self.assertIn(b'<label for="data-ano">Ano</label>', pagina.data)
        self.assertIn(f'value="{date.today().day:02d}"'.encode(), pagina.data)
        self.assertIn(f'value="{date.today().month:02d}"'.encode(), pagina.data)
        self.assertIn(f'value="{date.today().year:04d}"'.encode(), pagina.data)
        self.assertLess(
            pagina.data.index(b'name="autor"'),
            pagina.data.index(b'name="data_insercao"'),
        )
        self.assertLess(
            pagina.data.index(b'name="data_insercao"'),
            pagina.data.index(b'name="quantidade"'),
        )

        for rotulo in (
            "Autor (es)",
            "Titulo/Subtitulo",
            "Quantidade de Exemplar",
            "Ano",
            "Edição",
            "Volume",
            "Tipologia do Material",
            "Possui Carimbo?",
            "Número da Caixa",
            "Observações",
        ):
            with self.subTest(rotulo=rotulo):
                self.assertIn(rotulo.encode(), pagina.data)
        self.assertIn(b'<option value="Sim">Sim</option>', pagina.data)
        self.assertIn(b'<option value="N\xc3\xa3o">N\xc3\xa3o</option>', pagina.data)
        for rotulo in (
            "Titulo do Periódico",
            "Volume/Ano/Período",
            "Edição/Fascículo",
            "Número",
            "Periodicidade",
            "Ano de Publicação",
            "Possui carimbo?",
            "Número da caixa",
        ):
            with self.subTest(rotulo_periodico=rotulo):
                self.assertIn(rotulo.encode(), pagina.data)
        self.assertIn(
            b'["Livro", "Plaquete", "Folheto"].includes(tipoPublicacao.value)',
            pagina.data,
        )
        self.assertIn(b'tipoPublicacao.value === "Periodico"', pagina.data)
        self.assertIn(b'tipoPublicacao.value === "Cordel"', pagina.data)
        campos_cordel = (
            (
                b"imagem-capa-cordel",
                b"Imagem da capa",
                b"Nome do autor ou cordelista.",
            ),
            (
                b"autor-cordel",
                b"Autor",
                b"T\xc3\xadtulo completo da obra.",
            ),
            (
                b"nome-cordel",
                b"T\xc3\xadtulo",
                b"N\xc3\xbamero ou indica\xc3\xa7\xc3\xa3o da edi\xc3\xa7\xc3\xa3o.",
            ),
            (
                b"edicao-cordel",
                b"Edi\xc3\xa7\xc3\xa3o",
                b"Nome da editora respons\xc3\xa1vel.",
            ),
            (
                b"editora-cordel",
                b"Editora",
                b"Cidade de publica\xc3\xa7\xc3\xa3o.",
            ),
            (
                b"local-cordel",
                b"Local",
                b"Ano de publica\xc3\xa7\xc3\xa3o.",
            ),
            (
                b"ano-cordel",
                b"Ano",
                b"Assunto(s) atribu\xc3\xaddo(s) \xc3\xa0 obra por meio da indexa\xc3\xa7\xc3\xa3o tem\xc3\xa1tica realizada.",
            ),
            (
                b"tema-cordel",
                b"Tema",
                b"Informa\xc3\xa7\xc3\xb5es complementares sobre a obra.",
            ),
            (
                b"notas-cordel",
                b"Notas",
                b"Reprodu\xc3\xa7\xc3\xa3o digital da capa do folheto.",
            ),
        )
        for campo_id, rotulo, descricao in campos_cordel:
            with self.subTest(campo=campo_id):
                padrao = (
                    rb'<label for="'
                    + re.escape(campo_id)
                    + rb'">'
                    + re.escape(rotulo)
                    + rb'</label>\s*<(?:input|textarea)\b[^>]*id="'
                    + re.escape(campo_id)
                    + rb'"[^>]*>(?:\s*</textarea>)?\s*<small class="form-help">'
                    + re.escape(descricao)
                    + rb"</small>"
                )
                self.assertRegex(pagina.data, padrao)
        self.assertLess(
            pagina.data.index(b'id="imagem-capa-cordel"'),
            pagina.data.index(b'id="autor-cordel"'),
        )
        self.assertLess(
            pagina.data.index(b'id="autor-cordel"'),
            pagina.data.index(b'id="nome-cordel"'),
        )
        grupo_cordel = re.search(
            rb'<div data-publicacao-cordel hidden>(.*?)</div>',
            pagina.data,
            re.DOTALL,
        )
        self.assertIsNotNone(grupo_cordel)
        campos_cordel_html = grupo_cordel.group(1)
        self.assertNotIn(b'name="data_insercao"', campos_cordel_html)

    def test_cadastro_e_historico_de_cordel_com_capa_e_metadados(self):
        capa = b"\x89PNG\r\n\x1a\nimagem de teste"
        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "nome": "A peleja do exemplo",
                "tipo": "Cordel",
                "autor": "Cordelista de teste",
                "quantidade": "2",
                "data_insercao": "2000-01-01",
                "edicao": "2ª edição",
                "editora": "Editora Popular",
                "local": "Campina Grande",
                "ano": "2025",
                "tema": "Cultura popular",
                "notas": "Exemplar ilustrado",
                "imagem_capa": (io.BytesIO(capa), "capa.png"),
            },
            follow_redirects=True,
        )

        self.assertIn(b"Produto cadastrado.", resposta.data)
        produto = inventario.listar_historico_produtos()[0]
        self.assertEqual(produto["tipo"], "Cordel")
        self.assertEqual(produto["nome"], "A peleja do exemplo")
        self.assertEqual(produto["autor"], "Cordelista de teste")
        self.assertEqual(produto["categoria"], "")
        self.assertEqual(produto["preco"], 0)
        self.assertEqual(produto["data_insercao"], date.today().isoformat())
        self.assertEqual(produto["ano"], "2025")
        self.assertEqual(produto["edicao"], "2ª edição")
        self.assertEqual(produto["editora"], "Editora Popular")
        self.assertEqual(produto["local"], "Campina Grande")
        self.assertEqual(produto["tema"], "Cultura popular")
        self.assertEqual(produto["notas"], "Exemplar ilustrado")
        self.assertTrue(produto["imagem_capa"].endswith(".png"))
        self.assertEqual(
            (aplicacao.PASTA_CAPAS / produto["imagem_capa"]).read_bytes(), capa
        )
        self.assertIn(b"Capa do cordel: A peleja do exemplo", resposta.data)
        self.assertIn(
            (
                f"Inserção: Dia: {date.today().day:02d} · "
                f"Mês: {date.today().month:02d} · Ano: {date.today().year:04d}"
            ).encode(),
            resposta.data,
        )
        self.assertIn(b"Editora: Editora Popular", resposta.data)

        pagina_historico = self.cliente.get("/arquivos")
        self.assertIn(b"Capa do cordel: A peleja do exemplo", pagina_historico.data)
        self.assertIn(
            (
                f"Data da inserção: Dia: {date.today().day:02d} · "
                f"Mês: {date.today().month:02d} · Ano: {date.today().year:04d}"
            ).encode(),
            pagina_historico.data,
        )
        self.assertIn(b"Tema: Cultura popular", pagina_historico.data)
        imagem = self.cliente.get(f"/capas/{produto['imagem_capa']}")
        self.assertEqual(imagem.status_code, 200)
        self.assertEqual(imagem.data, capa)
        imagem.close()

    def test_cadastro_rejeita_capa_que_nao_seja_imagem_suportada(self):
        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "nome": "Cordel sem imagem válida",
                "tipo": "Cordel",
                "autor": "Cordelista",
                "quantidade": "1",
                "edicao": "1",
                "editora": "Editora",
                "local": "Cidade",
                "ano": "2025",
                "tema": "Tema",
                "notas": "Notas",
                "imagem_capa": (io.BytesIO(b"nao e uma imagem"), "capa.png"),
            },
            follow_redirects=True,
        )

        self.assertIn(b"PNG, JPEG ou WebP", resposta.data)
        self.assertEqual(inventario.listar_historico_produtos(), [])

    def test_campos_de_catalogacao_sao_salvos_para_plaquete_e_folheto(self):
        for tipo in ("Plaquete", "Folheto"):
            with self.subTest(tipo=tipo):
                resposta = self.cliente.post(
                    "/produtos",
                    data={
                        "csrf_token": self.csrf_token,
                        "nome": f"{tipo} de teste",
                        "tipo": tipo,
                        "autor": "Autoria coletiva",
                        "quantidade": "2",
                        "data_insercao": "2026-10-21",
                        "ano": "2023",
                        "edicao": "1",
                        "volume": "2",
                        "tipologia_material": "Folheto impresso",
                        "possui_carimbo": "Não",
                        "numero_caixa": "12",
                        "observacoes": "Sem observações",
                    },
                    follow_redirects=True,
                )

                self.assertIn(b"Produto cadastrado.", resposta.data)
                produto = inventario.listar_historico_produtos()[0]
                self.assertEqual(produto["tipo"], tipo)
                self.assertEqual(produto["categoria"], "")
                self.assertEqual(produto["preco"], 0)
                self.assertEqual(produto["possui_carimbo"], "Não")
                self.assertEqual(produto["numero_caixa"], "12")

    def test_validacao_rejeita_cada_campo_obrigatorio_vazio(self):
        campos_comuns = {
            "nome": "Publicação de teste",
            "categoria": "",
            "quantidade": 2,
            "preco": 0,
            "autor": "Autoria de teste",
            "data_insercao": "2026-10-22",
            "possui_carimbo": "Sim",
            "numero_caixa": "CX-01",
            "observacoes": "Sem observações",
            "ano": "2024",
            "edicao": "1",
            "volume": "2",
            "tipologia_material": "Impresso",
            "volume_ano_periodo": "Volume 2, ano 2024",
            "edicao_fasciculo": "Edição 1, fascículo 1",
            "numero": "5",
            "periodicidade": "Mensal",
            "ano_publicacao": "2024",
        }
        campos_por_tipo = {
            "Livro": (
                "nome", "autor", "quantidade", "data_insercao", "ano",
                "edicao", "volume", "tipologia_material", "possui_carimbo",
                "numero_caixa", "observacoes",
            ),
            "Plaquete": (
                "nome", "autor", "quantidade", "data_insercao", "ano",
                "edicao", "volume", "tipologia_material", "possui_carimbo",
                "numero_caixa", "observacoes",
            ),
            "Folheto": (
                "nome", "autor", "quantidade", "data_insercao", "ano",
                "edicao", "volume", "tipologia_material", "possui_carimbo",
                "numero_caixa", "observacoes",
            ),
            "Periodico": (
                "nome", "autor", "quantidade", "data_insercao",
                "volume_ano_periodo", "edicao_fasciculo", "numero",
                "periodicidade", "ano_publicacao", "possui_carimbo",
                "numero_caixa", "observacoes",
            ),
        }
        for tipo, campos in campos_por_tipo.items():
            for campo in campos:
                with self.subTest(tipo=tipo, campo=campo):
                    dados = {
                        **campos_comuns,
                        "tipo": tipo,
                        campo: 0 if campo == "quantidade" else "",
                    }
                    if campo == "quantidade":
                        continue
                    mensagem = (
                        "nome do produto não pode ficar vazio"
                        if campo == "nome"
                        else "Informe o nome do autor"
                        if campo == "autor"
                        else "obrigatórios"
                    )
                    with self.assertRaisesRegex(ValueError, mensagem):
                        inventario.validar_produto(**dados)

    def test_cadastro_rejeita_periodico_sem_periodicidade(self):
        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "tipo": "Periodico",
                "nome": "Periódico incompleto",
                "autor": "Autoria de teste",
                "quantidade": "1",
                "data_insercao": "2026-10-22",
                "volume_ano_periodo": "Volume 1, ano 2025",
                "edicao_fasciculo": "Edição 1",
                "numero": "3",
                "periodicidade": "",
                "ano_publicacao": "2025",
                "possui_carimbo": "Não",
                "numero_caixa": "CX-01",
                "observacoes": "Sem observações",
            },
            follow_redirects=True,
        )

        self.assertIn("Periodicidade".encode(), resposta.data)
        self.assertIn("obrigatórios".encode(), resposta.data)
        self.assertEqual(inventario.listar_historico_produtos(), [])

    def test_cadastro_rejeita_quantidade_vazia(self):
        resposta = self.cliente.post(
            "/produtos",
            data={
                "csrf_token": self.csrf_token,
                "tipo": "Livro",
                "nome": "Livro sem quantidade",
                "autor": "Autoria de teste",
                "quantidade": "",
                "data_insercao": "2026-10-22",
                "ano": "2024",
                "edicao": "1",
                "volume": "1",
                "tipologia_material": "Impresso",
                "possui_carimbo": "Não",
                "numero_caixa": "CX-01",
                "observacoes": "Sem observações",
            },
            follow_redirects=True,
        )

        self.assertIn("Informe a quantidade.".encode(), resposta.data)
        self.assertEqual(inventario.listar_historico_produtos(), [])

    def test_visualiza_e_edita_celulas_csv_sem_alterar_as_demais(self):
        conteudo = "Nome;Observação\nLivro;Edição 1\n".encode("utf-8")
        self.enviar(conteudo, "dados.csv")
        planilha = self.planilhas_cadastradas()[0]

        previa = self.cliente.get(f"/planilhas/{planilha['id']}")
        self.assertIn(b"Edi\xc3\xa7\xc3\xa3o 1", previa.data)
        self.assertIn(
            b'href="/arquivos">Voltar aos arquivos enviados</a>', previa.data
        )
        resposta = self.cliente.post(
            f"/planilhas/{planilha['id']}/editar",
            data={
                "csrf_token": self.csrf_token,
                "aba": "0",
                "linha": "0",
                "coluna": "0",
                "celula_2_2": "Edição 2",
                "celula_2_1": "Livro",
            },
            follow_redirects=True,
        )

        self.assertIn(b"Altera\xc3\xa7\xc3\xb5es salvas", resposta.data)
        download = self.cliente.get(f"/planilhas/{planilha['id']}/baixar")
        self.assertEqual(
            download.data.decode("utf-8"),
            "Nome;Observação\r\nLivro;Edição 2\r\n",
        )
        download.close()

    def test_visualiza_as_abas_e_edita_excel_preservando_numeros(self):
        pasta = Workbook()
        primeira = pasta.active
        primeira.title = "Livros"
        primeira.append(["Título", "Quantidade"])
        primeira.append(["A obra", 3])
        segunda = pasta.create_sheet("Revistas")
        segunda.append(["Nome"])
        segunda.append(["Revista A"])
        conteudo = io.BytesIO()
        pasta.save(conteudo)
        self.enviar(conteudo.getvalue(), "acervo.xlsx")
        planilha = self.planilhas_cadastradas()[0]

        previa = self.cliente.get(f"/planilhas/{planilha['id']}")
        self.assertIn(b"Livros", previa.data)
        self.assertIn(b"Revistas", previa.data)
        resposta = self.cliente.post(
            f"/planilhas/{planilha['id']}/editar",
            data={
                "csrf_token": self.csrf_token,
                "aba": "0",
                "linha": "0",
                "coluna": "0",
                "celula_2_1": "Outra obra",
                "celula_2_2": "4",
            },
            follow_redirects=True,
        )

        self.assertIn(b"Altera\xc3\xa7\xc3\xb5es salvas", resposta.data)
        caminho = aplicacao.PASTA_PLANILHAS / inventario.buscar_planilha(planilha["id"])["arquivo"]
        atualizada = load_workbook(caminho, data_only=False)
        self.assertEqual(atualizada["Livros"]["A2"].value, "Outra obra")
        self.assertEqual(atualizada["Livros"]["B2"].value, 4)
        self.assertEqual(atualizada["Revistas"]["A2"].value, "Revista A")
        atualizada.close()

    def test_planilha_grande_pode_ser_visualizada_e_editada_por_pagina(self):
        linhas = ["nome;valor"] + [f"Linha {i};{i}" for i in range(1, 36)]
        self.enviar("\n".join(linhas).encode("utf-8"), "grande.csv")
        planilha = self.planilhas_cadastradas()[0]

        pagina_dois = self.cliente.get(
            f"/planilhas/{planilha['id']}?linha=1"
        )
        self.assertIn(b"Linha 31", pagina_dois.data)
        resposta = self.cliente.post(
            f"/planilhas/{planilha['id']}/editar",
            data={
                "csrf_token": self.csrf_token,
                "aba": "0",
                "linha": "1",
                "coluna": "0",
                "celula_32_2": "valor atualizado",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Altera\xc3\xa7\xc3\xb5es salvas", resposta.data)

        caminho = aplicacao.PASTA_PLANILHAS / inventario.buscar_planilha(planilha["id"])["arquivo"]
        dados = caminho.read_text(encoding="utf-8")
        self.assertIn("Linha 31;valor atualizado", dados)

    def test_planilha_excel_invalida_exibe_erro_sem_interromper_site(self):
        self.enviar(b"nao e uma planilha excel", "invalida.xlsx")
        planilha = self.planilhas_cadastradas()[0]

        resposta = self.cliente.get(
            f"/planilhas/{planilha['id']}", follow_redirects=True
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"N\xc3\xa3o foi poss\xc3\xadvel abrir a planilha", resposta.data)

    def test_exclui_planilha_arquivo_e_registro_com_confirmacao_csrf(self):
        self.enviar(b"nome;valor\nItem;1\n", "remover.csv")
        planilha = self.planilhas_cadastradas()[0]
        registro = inventario.buscar_planilha(planilha["id"])
        caminho = aplicacao.PASTA_PLANILHAS / registro["arquivo"]
        self.assertTrue(caminho.exists())

        pagina_edicao = self.cliente.get(f"/planilhas/{planilha['id']}")
        pagina_arquivos = self.cliente.get("/arquivos")
        self.assertIn(b"Excluir este arquivo enviado", pagina_arquivos.data)
        self.assertIn(b"Esta a\xc3\xa7\xc3\xa3o n\xc3\xa3o pode ser desfeita", pagina_arquivos.data)
        self.assertIn(b"Excluir planilha", pagina_edicao.data)
        self.assertIn(b"Hist\xc3\xb3rico de exclus\xc3\xb5es", pagina_arquivos.data)

        resposta = self.cliente.post(
            f"/planilhas/{planilha['id']}/excluir",
            data={"csrf_token": self.csrf_token},
            follow_redirects=True,
        )

        self.assertIn(b"Planilha exclu\xc3\xadda.", resposta.data)
        self.assertEqual(inventario.buscar_planilha(planilha["id"]), None)
        self.assertFalse(caminho.exists())
        exclusoes = inventario.listar_exclusoes()
        self.assertEqual(len(exclusoes), 1)
        self.assertEqual(exclusoes[0]["nome"], "remover.csv")
        self.assertEqual(exclusoes[0]["tamanho"], len(b"nome;valor\nItem;1\n"))
        self.assertTrue(exclusoes[0]["enviado_em"])
        self.assertTrue(exclusoes[0]["excluido_em"])
        historico = self.cliente.get("/arquivos")
        self.assertIn(b"remover.csv", historico.data)
        self.assertIn(b"Arquivo exclu\xc3\xaddo", historico.data)
        self.assertIn(b"Exclu\xc3\xaddo:", historico.data)
        self.assertEqual(
            self.cliente.get(f"/planilhas/{planilha['id']}/baixar").status_code, 404
        )

    def test_excluir_planilha_exige_token_csrf(self):
        self.enviar(b"dados", "segura.csv")
        planilha = self.planilhas_cadastradas()[0]

        resposta = self.cliente.post(f"/planilhas/{planilha['id']}/excluir")

        self.assertEqual(resposta.status_code, 403)
        self.assertIsNotNone(inventario.buscar_planilha(planilha["id"]))
        self.assertEqual(inventario.listar_exclusoes(), [])

    def test_excluir_planilha_inexistente_retorna_404(self):
        resposta = self.cliente.post(
            "/planilhas/99999/excluir",
            data={"csrf_token": self.csrf_token},
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(inventario.listar_exclusoes(), [])

    def test_pagina_arquivos_tem_navegacao_historico_e_modo_escuro(self):
        resposta = self.cliente.get("/arquivos")
        css = self.cliente.get("/static/style.css")

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Arquivos enviados", resposta.data)
        self.assertIn(b"Acervo", resposta.data)
        self.assertIn(b"alternar-tema", resposta.data)
        self.assertIn(b"--muted: #d0c5c9", css.data)
        self.assertIn(b"--row-surface: #211d20", css.data)
        self.assertIn(b"Desenvolvedor:", resposta.data)
        self.assertIn(b"Gabriel Bruno Costa De Lima", resposta.data)
        css.close()

    def test_identificacao_do_desenvolvedor_aparece_no_acervo(self):
        resposta = self.cliente.get("/")

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Desenvolvedor:", resposta.data)
        self.assertIn(b"Gabriel Bruno Costa De Lima", resposta.data)

    def test_migracao_adiciona_tamanho_aos_arquivos_ja_salvos(self):
        banco_antigo = Path(self.diretorio.name) / "legado.db"
        conexao = sqlite3.connect(banco_antigo)
        try:
            conexao.execute(
                """
                CREATE TABLE planilhas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    arquivo TEXT NOT NULL UNIQUE,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conexao.execute(
                "INSERT INTO planilhas (nome, arquivo) VALUES (?, ?)",
                ("antiga.csv", "arquivo-antigo.csv"),
            )
            conexao.commit()
        finally:
            conexao.close()
        with patch.object(inventario, "DB_NOME", str(banco_antigo)):
            inventario.criar_tabela()
            antigas = inventario.listar_planilhas()

        self.assertEqual(len(antigas), 1)
        self.assertEqual(antigas[0]["nome"], "antiga.csv")
        self.assertEqual(antigas[0]["tamanho"], 0)

    def test_migracao_registra_produtos_existentes_sem_data_conhecida(self):
        banco_antigo = Path(self.diretorio.name) / "produtos-legado.db"
        conexao = sqlite3.connect(banco_antigo)
        try:
            conexao.execute(
                """
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    categoria TEXT,
                    quantidade INTEGER NOT NULL DEFAULT 0,
                    preco REAL NOT NULL DEFAULT 0
                )
                """
            )
            conexao.execute(
                """
                INSERT INTO produtos (nome, categoria, quantidade, preco)
                VALUES (?, ?, ?, ?)
                """,
                ("Produto antigo", "Categoria", 2, 4.5),
            )
            conexao.commit()
        finally:
            conexao.close()

        with patch.object(inventario, "DB_NOME", str(banco_antigo)):
            inventario.criar_tabela()
            historico = inventario.listar_historico_produtos()

        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["nome"], "Produto antigo")
        self.assertEqual(historico[0]["tipo"], "Produto")
        self.assertEqual(historico[0]["autor"], "")
        self.assertIsNone(historico[0]["adicionado_em"])

    def test_migracao_nao_recria_historico_depois_de_limpo(self):
        inventario.inserir_produto("Produto", "Categoria", 1, 2.0)
        with inventario.conectar() as conn:
            conn.execute("DELETE FROM historico_produtos")

        inventario.criar_tabela()

        self.assertEqual(inventario.listar_historico_produtos(), [])


if __name__ == "__main__":
    unittest.main()
