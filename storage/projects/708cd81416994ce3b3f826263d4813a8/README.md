# Digitaliza FCJA

**Sistema de Digitalização e Preservação Digital**
**Fundação Casa de José Américo (FCJA)**

Sistema web para o fluxo interno de **digitalização, organização, visualização,
processamento e aplicação de marca d'água** em obras raras digitalizadas.

---

## ⚠ Regras de ouro do sistema

1. **O arquivo original NUNCA é alterado.** O fluxo é sempre:

   ```
   ORIGINAL (uploads/originais/)
        │
        ▼
      LEITURA
        │
        ▼
   PROCESSAMENTO (em memória)
        │
        ▼
   NOVO ARQUIVO (uploads/processadas/)
   ```

   Nunca: `ORIGINAL → ALTERAR → SALVAR POR CIMA`.

2. **A qualidade é preservada**: uma página 4000×6000 permanece 4000×6000.
   A marca d'água é adicionada sem redimensionar a página; DPI e formato
   são mantidos (TIFF não é convertido para JPEG automaticamente).

3. **A preservação vem antes da estética**; a segurança do original vem
   antes da facilidade de implementação.

---

## Objetivo

Permitir que a equipe de digitalização:

1. Cadastre uma obra digitalizada com seus metadados (código, título, autor,
   ano, coleção, responsável).
2. Faça upload de uma ou várias páginas (JPG, JPEG, PNG, TIFF, TIF), com
   drag-and-drop e ordenação natural automática (1, 2, …, 10, 11).
3. Visualize as páginas antes do processamento (miniaturas com dimensões,
   formato e status).
4. Ajuste a marca d'água em pré-visualização em tempo real (tamanho,
   margem, opacidade, posição) e compare original × processada com
   controle deslizante.
5. Processe a obra inteira em lote, com barra de progresso, sem travar a
   interface e sem interromper o lote quando uma página falha.
6. Visualize o resultado, baixe página individual ou a obra completa em ZIP
   (`FCJA-OBR-XXXXXX_PROCESSADA.zip`, contendo apenas as processadas).
7. Acompanhe relatórios e logs de auditoria.

---

## Requisitos

- Python 3.10 ou superior
- Pip atualizado
- Navegador moderno (o sistema é usado principalmente em desktops: 1366×768,
  1440×900, 1920×1080; também funciona em tablets)

---

## Instalação

```bash
# 1. Entrar na pasta do projeto
cd sistema-digitalizacao-fcja

# 2. Criar o ambiente virtual
python -m venv .venv

# 3. Ativar o ambiente virtual
# Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 4. Instalar as dependências
pip install -r requirements.txt

# 5. Preparar as configurações de ambiente
cp .env.example .env
# (no Windows: copy .env.example .env)
# Edite o .env e defina uma SECRET_KEY forte:
#   python -c "import secrets; print(secrets.token_hex(32))"

# 6. Gerar a logo institucional (placeholder; substitua pela oficial)
python gerar_logo.py

# 7. Iniciar o sistema
python app.py
```

O sistema cria automaticamente as pastas `uploads/` (originais, processadas,
cache, tmp) e o banco SQLite na primeira execução, além do usuário
administrador inicial (`ADMIN_EMAIL` / `ADMIN_SENHA` do `.env` —
**altere a senha padrão após o primeiro acesso**).

Acesse: `http://127.0.0.1:5000`

---

## Configuração (.env)

| Variável | Descrição | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave das sessões (**obrigatória em produção**) | gerada localmente |
| `DATABASE_URL` | Caminho do banco SQLite | `instance/database.sqlite` |
| `UPLOAD_FOLDER` | Pasta do acervo digitalizado | `uploads` |
| `MAX_CONTENT_LENGTH` | Limite por requisição (bytes) | 1 GB |
| `MAX_TAMANHO_ARQUIVO` | Limite por arquivo (bytes) | 500 MB |
| `ADMIN_EMAIL` | E-mail do administrador inicial | `admin@fcja.pb.gov.br` |
| `ADMIN_SENHA` | Senha do administrador inicial | (definir!) |
| `FLASK_HOST` / `FLASK_PORT` / `FLASK_DEBUG` | Servidor | `127.0.0.1` / `5000` / `0` |

Nunca coloque a `SECRET_KEY` real no Git. O `.gitignore` já protege `.env`,
`instance/` e `uploads/`.

---

## Estrutura de diretórios

```
sistema-digitalizacao-fcja/
├── app.py                  # Fábrica da aplicação e ponto de entrada
├── config.py               # Configurações centrais (lê o .env)
├── gerar_logo.py           # Gera o placeholder da logo institucional
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── models/                 # Camada de dados (SQLite)
│   ├── database.py         # Conexões, esquema e inicialização
│   ├── obra.py             # Obras
│   ├── pagina.py           # Páginas
│   ├── processamento.py    # Histórico de processamentos
│   ├── configuracoes.py    # Configurações da marca d'água
│   ├── usuario.py          # Usuários e autenticação
│   └── logs.py             # Log de atividades
│
├── routes/                 # Rotas Flask (views)
│   ├── auth.py             # Login/logout e proteção de rotas
│   ├── dashboard.py        # Página inicial
│   ├── obras.py            # CRUD de obras, upload, visualizador, ZIP
│   ├── processamento.py    # Lote, pré-visualização, progresso
│   └── configuracoes.py    # Configurações e comparação
│
├── services/               # Regras de negócio
│   ├── watermark.py        # ★ Marca d'água (função central)
│   ├── image_processor.py  # Metadados, miniaturas, pré-visualizações
│   ├── processamento.py    # Orquestrador do lote (thread + progresso)
│   ├── obras_service.py    # Upload, substituição, exclusão segura
│   ├── zip_service.py      # Exportação ZIP
│   └── storage.py          # Pastas, nomes seguros, ordenação natural
│
├── templates/              # HTML (Jinja2)
├── static/
│   ├── css/style.css       # Identidade visual institucional
│   ├── js/                 # app, upload, processamento, visualizador
│   └── img/logo-fcja.png   # Logo institucional
│
├── uploads/                # (criado automaticamente)
│   ├── originais/          # ★ Digitalizações originais — NUNCA alteradas
│   │   └── FCJA-OBR-000001/ 001.tif 002.tif ...
│   ├── processadas/        # Cópia com marca d'água
│   │   └── FCJA-OBR-000001/ 001.tif 002.tif ...
│   ├── cache/              # Miniaturas e pré-visualizações
│   └── tmp/                # ZIPs temporários para download
│
├── instance/
│   └── database.sqlite     # Banco de metadados
│
└── tests/                  # Testes automatizados (pytest)
```

---

## Funcionamento da marca d'água

### Tamanho automático

O tamanho **não é fixo** — é calculado proporcionalmente a cada página:

```python
largura_logo = largura_imagem * 0.08   # 8% da largura da página
```

Com limites mínimo e máximo configuráveis (padrão: 80 px a 600 px) para
impedir resultados inadequados em páginas muito pequenas ou muito grandes.
A altura da logo acompanha sempre a **proporção original** (aspect ratio).

### Margem

Proporcional à menor dimensão da página (padrão 2,5%), com modo fixo opcional.
A logo nunca fica colada na borda.

### Opacidade

Padrão **85%**, ajustável de 0% a 100% na tela de processamento com
atualização imediata da pré-visualização.

### Posição

Padrão: **canto superior esquerdo**. Outras 8 posições disponíveis.

### Preservação do texto

- Logo discreta (8% da largura), opacidade controlada e margem proporcional;
- Resolução, dimensões e DPI da página são sempre preservados;
- A comparação "antes/depois" com controle deslizante permite conferir se
  algum texto importante foi prejudicado antes de processar todo o acervo.

### TIFF

O sistema preserva TIFF como TIFF (compressão deflate), mantendo dimensões,
DPI e perfil de cor ICC quando disponíveis. TIFF **não** é convertido para
JPEG automaticamente.

---

## Onde ficam os arquivos

| Tipo | Local |
|---|---|
| Originais (intocáveis) | `uploads/originais/CODIGO_DA_OBRA/` |
| Processadas (com marca d'água) | `uploads/processadas/CODIGO_DA_OBRA/` |
| Banco de metadados | `instance/database.sqlite` |
| ZIPs de download | `uploads/tmp/` (temporário) |

O download "Baixar obra" gera um ZIP **apenas com as páginas processadas**.
Os originais nunca entram no ZIP processado.

---

## Backup

1. **Pare o sistema** (ou garanta que não há processamento em execução).
2. Copie:
   - `uploads/originais/` (essencial — é o acervo);
   - `uploads/processadas/` (reprocessável, mas recomendado);
   - `instance/database.sqlite` (metadados);
   - `.env` (fora do Git, guardar em local seguro).
3. Restaure copiando os mesmos diretórios de volta.

Recomenda-se backup incremental diário da pasta `uploads/` para
servidor/NAS externo.

---

## Atualização do sistema

```bash
source .venv/bin/activate
git pull            # (quando versionado)
pip install -r requirements.txt
python app.py       # o banco é atualizado automaticamente (CREATE IF NOT EXISTS)
```

Faça backup antes de atualizar.

---

## Testes

```bash
source .venv/bin/activate
pytest -v
```

Cobrem: cálculo do tamanho da logo (regra de 8% com limites), margem,
posições, preservação de proporção, transparência/opacidade, preservação
das dimensões e DPI (TIFF), **integridade do original**, upload, cadastro
de obras, validação de arquivos inválidos, exclusão protegida, path
traversal, sanitização e geração do ZIP.

---

## Segurança

- Login obrigatório; perfis administrador/operador/visualizador preparados;
- Senhas com hash (Werkzeug); sessões assinadas com `SECRET_KEY`;
- Validação de extensão **e** conteúdo (Pillow verify) dos uploads;
- MIME types verificados; limite de tamanho por arquivo e por requisição;
- Nomes de arquivo normalizados no servidor (o nome enviado não é confiado);
- Proteção contra path traversal em todos os caminhos de arquivo;
- Exclusão de obra exige digitar o código da obra (proteção contra
  exclusão acidental dos originais);
- Log de atividades para auditoria.

---

## Funcionalidades futuras (arquitetura preparada)

OCR e PDF pesquisável, integração com Archivematica/repositórios digitais,
checksums (hash), controle de versões, permissões avançadas, relatórios e
estatísticas, exportação METS/ALTO, Dublin Core, PREMIS, integração com
sistemas de biblioteca, armazenamento em servidor/NAS e processamento
automático de grandes lotes. Nenhuma dessas está implementada para não
complicar o sistema atual; a separação em camadas (models/services/routes)
permite adicioná-las sem reescrita.