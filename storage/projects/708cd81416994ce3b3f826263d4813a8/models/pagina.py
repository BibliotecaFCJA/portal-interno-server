"""Modelo de páginas digitalizadas de uma obra."""

from datetime import datetime

from models.database import banco

ROTULOS_STATUS = {
    'original': 'Original',
    'processando': 'Processando',
    'processada': 'Processada',
    'erro': 'Erro',
}


def _agora():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def inserir(dados, caminho=None):
    """Insere uma página. Levanta ValueError em caso de duplicidade."""
    with banco(caminho) as conn:
        try:
            cursor = conn.execute(
                'INSERT INTO paginas (obra_id, numero, nome_original, '
                'arquivo_original, largura, altura, formato, resolucao, '
                'tamanho_bytes, status_processamento) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    dados['obra_id'],
                    dados['numero'],
                    dados['nome_original'],
                    dados['arquivo_original'],
                    dados.get('largura'),
                    dados.get('altura'),
                    dados.get('formato'),
                    dados.get('resolucao'),
                    dados.get('tamanho_bytes'),
                    'original',
                ),
            )
            return cursor.lastrowid
        except Exception as exc:
            raise ValueError('Página duplicada ou dados inválidos.') from exc


def buscar_por_id(pagina_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM paginas WHERE id = ?', (pagina_id,)
        ).fetchone()


def buscar_por_nome(obra_id, nome_original, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM paginas WHERE obra_id = ? AND lower(nome_original) = lower(?)',
            (obra_id, nome_original),
        ).fetchone()


def listar_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM paginas WHERE obra_id = ? ORDER BY numero ASC',
            (obra_id,),
        ).fetchall()


def contar_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT COUNT(*) AS c FROM paginas WHERE obra_id = ?', (obra_id,)
        ).fetchone()['c']


def contar_por_status(obra_id, caminho=None):
    """Retorna {status: quantidade} das páginas da obra."""
    with banco(caminho) as conn:
        linhas = conn.execute(
            'SELECT status_processamento AS status, COUNT(*) AS c '
            'FROM paginas WHERE obra_id = ? GROUP BY status_processamento',
            (obra_id,),
        ).fetchall()
    contagens = {status: 0 for status in ROTULOS_STATUS}
    for linha in linhas:
        contagens[linha['status']] = linha['c']
    return contagens


def proximo_numero(obra_id, caminho=None):
    with banco(caminho) as conn:
        resultado = conn.execute(
            'SELECT COALESCE(MAX(numero), 0) + 1 AS proximo FROM paginas WHERE obra_id = ?',
            (obra_id,),
        ).fetchone()
    return resultado['proximo']


def definir_status(pagina_id, status, mensagem=None, caminho=None):
    with banco(caminho) as conn:
        conn.execute(
            'UPDATE paginas SET status_processamento = ?, erro_mensagem = ? WHERE id = ?',
            (status, mensagem, pagina_id),
        )


def atualizar_processamento(pagina_id, arquivo_processado, largura, altura,
                            resolucao, status='processada', caminho=None):
    with banco(caminho) as conn:
        conn.execute(
            'UPDATE paginas SET arquivo_processado = ?, largura = ?, altura = ?, '
            'resolucao = ?, status_processamento = ?, erro_mensagem = NULL, '
            'data_processamento = ? WHERE id = ?',
            (arquivo_processado, largura, altura, resolucao, status,
             _agora(), pagina_id),
        )


def excluir(pagina_id, caminho=None):
    with banco(caminho) as conn:
        conn.execute('DELETE FROM paginas WHERE id = ?', (pagina_id,))


def excluir_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        conn.execute('DELETE FROM paginas WHERE obra_id = ?', (obra_id,))