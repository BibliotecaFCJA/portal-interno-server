"""Modelo de obras digitalizadas."""

from datetime import datetime

from models.database import banco

STATUS_VALIDOS = ('pendente', 'processando', 'processada', 'parcial', 'erro')

ROTULOS_STATUS = {
    'pendente': 'Pendente',
    'processando': 'Processando',
    'processada': 'Processada',
    'parcial': 'Parcialmente processada',
    'erro': 'Erro',
}


def _agora():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def gerar_proximo_codigo(caminho=None):
    """Gera o próximo código sequencial no padrão FCJA-OBR-000001."""
    with banco(caminho) as conn:
        linhas = conn.execute(
            "SELECT codigo FROM obras WHERE codigo LIKE 'FCJA-OBR-%'"
        ).fetchall()
    maior = 0
    for linha in linhas:
        sufixo = linha['codigo'].rsplit('-', 1)[-1]
        if sufixo.isdigit():
            maior = max(maior, int(sufixo))
    return f'FCJA-OBR-{maior + 1:06d}'


def criar(dados, caminho=None):
    """Cadastra uma obra. Levanta ValueError se o código já existir.

    Se o código vier vazio, gera automaticamente o próximo sequencial
    (FCJA-OBR-000001, FCJA-OBR-000002, ...).
    """
    dados = dict(dados)
    if not (dados.get('codigo') or '').strip():
        dados['codigo'] = gerar_proximo_codigo(caminho)
    with banco(caminho) as conn:
        existente = conn.execute(
            'SELECT id FROM obras WHERE codigo = ?', (dados['codigo'],)
        ).fetchone()
        if existente:
            raise ValueError('Já existe uma obra com este código.')
        cursor = conn.execute(
            'INSERT INTO obras (codigo, titulo, autor, ano, colecao, descricao, '
            'responsavel, data_cadastro, quantidade_paginas, status) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)',
            (
                dados['codigo'],
                dados['titulo'],
                dados.get('autor') or None,
                dados.get('ano') or None,
                dados.get('colecao') or None,
                dados.get('descricao') or None,
                dados.get('responsavel') or None,
                _agora(),
                'pendente',
            ),
        )
        return cursor.lastrowid


def buscar_por_id(obra_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM obras WHERE id = ?', (obra_id,)
        ).fetchone()


def buscar_por_codigo(codigo, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM obras WHERE codigo = ?', (codigo,)
        ).fetchone()


def listar(busca=None, status=None, ordenar='recentes', pagina=1, por_pagina=20, caminho=None):
    """Lista obras com busca, filtro, ordenação e paginação."""
    where = []
    params = []
    if busca:
        where.append(
            '(titulo LIKE ? OR autor LIKE ? OR codigo LIKE ? OR colecao LIKE ?)'
        )
        termo = f'%{busca}%'
        params.extend([termo, termo, termo, termo])
    if status:
        where.append('status = ?')
        params.append(status)
    clausula = f' WHERE {" AND ".join(where)}' if where else ''

    ordens = {
        'recentes': 'data_cadastro DESC, id DESC',
        'antigas': 'data_cadastro ASC, id ASC',
        'codigo': 'codigo ASC',
        'titulo': 'titulo COLLATE NOCASE ASC',
        'ano': 'ano ASC',
        'status': 'status ASC',
    }
    ordem = ordens.get(ordenar, ordens['recentes'])

    with banco(caminho) as conn:
        total = conn.execute(
            'SELECT COUNT(*) AS c FROM obras' + clausula, params
        ).fetchone()['c']
        offset = (max(1, pagina) - 1) * por_pagina
        linhas = conn.execute(
            'SELECT obras.*, COALESCE(p.processadas, 0) AS quantidade_processada '
            'FROM obras '
            'LEFT JOIN (SELECT obra_id, COUNT(*) AS processadas FROM paginas '
            "           WHERE status_processamento = 'processada' GROUP BY obra_id) p "
            '  ON p.obra_id = obras.id'
            + clausula
            + f' ORDER BY {ordem} LIMIT ? OFFSET ?',
            params + [por_pagina, offset],
        ).fetchall()
    return linhas, total


def listar_todas(caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM obras ORDER BY data_cadastro DESC, id DESC LIMIT 200'
        ).fetchall()


def atualizar_status(obra_id, status, data_processamento=None, caminho=None):
    if status not in STATUS_VALIDOS:
        raise ValueError('Status inválido.')
    with banco(caminho) as conn:
        if data_processamento:
            conn.execute(
                'UPDATE obras SET status = ?, data_processamento = ? WHERE id = ?',
                (status, data_processamento, obra_id),
            )
        else:
            conn.execute(
                'UPDATE obras SET status = ? WHERE id = ?', (status, obra_id)
            )


def atualizar_quantidade(obra_id, caminho=None):
    with banco(caminho) as conn:
        conn.execute(
            'UPDATE obras SET quantidade_paginas = '
            '(SELECT COUNT(*) FROM paginas WHERE obra_id = ?) WHERE id = ?',
            (obra_id, obra_id),
        )


def excluir(obra_id, caminho=None):
    with banco(caminho) as conn:
        conn.execute('DELETE FROM obras WHERE id = ?', (obra_id,))


def estatisticas(caminho=None):
    """Números exibidos no dashboard."""
    with banco(caminho) as conn:
        total = conn.execute('SELECT COUNT(*) AS c FROM obras').fetchone()['c']
        processadas = conn.execute(
            "SELECT COUNT(*) AS c FROM obras WHERE status = 'processada'"
        ).fetchone()['c']
        processando = conn.execute(
            "SELECT COUNT(*) AS c FROM obras WHERE status = 'processando'"
        ).fetchone()['c']
        paginas = conn.execute('SELECT COUNT(*) AS c FROM paginas').fetchone()['c']
        paginas_processadas = conn.execute(
            "SELECT COUNT(*) AS c FROM paginas WHERE status_processamento = 'processada'"
        ).fetchone()['c']
    return {
        'total_obras': total,
        'obras_processadas': processadas,
        'obras_processando': processando,
        'obras_pendentes': max(0, total - processadas - processando),
        'total_paginas': paginas,
        'paginas_processadas': paginas_processadas,
    }


def recentes(limite=8, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT obras.*, COALESCE(p.processadas, 0) AS quantidade_processada '
            'FROM obras '
            'LEFT JOIN (SELECT obra_id, COUNT(*) AS processadas FROM paginas '
            "           WHERE status_processamento = 'processada' GROUP BY obra_id) p "
            '  ON p.obra_id = obras.id '
            'ORDER BY data_cadastro DESC, id DESC LIMIT ?',
            (limite,),
        ).fetchall()