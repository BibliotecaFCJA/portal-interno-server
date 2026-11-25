"""Modelo de registros de processamento (histórico/relatórios)."""

from datetime import datetime

from models.database import banco


def _agora():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def registrar(dados, caminho=None):
    """Inicia um registro de processamento. Retorna o id criado."""
    with banco(caminho) as conn:
        cursor = conn.execute(
            'INSERT INTO processamentos (obra_id, data, tamanho_logo, opacidade, '
            'margem, posicao, quantidade_processada, quantidade_erros, status, '
            'mensagem_erro) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, NULL)',
            (
                dados['obra_id'],
                _agora(),
                dados.get('tamanho_logo'),
                dados.get('opacidade'),
                dados.get('margem'),
                dados.get('posicao'),
                dados.get('status', 'processando'),
            ),
        )
        return cursor.lastrowid


def concluir(processamento_id, status, quantidade_processada, quantidade_erros,
             mensagem=None, caminho=None):
    with banco(caminho) as conn:
        conn.execute(
            'UPDATE processamentos SET status = ?, quantidade_processada = ?, '
            'quantidade_erros = ?, mensagem_erro = ? WHERE id = ?',
            (status, quantidade_processada, quantidade_erros, mensagem,
             processamento_id),
        )


def ultimo_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM processamentos WHERE obra_id = ? ORDER BY id DESC LIMIT 1',
            (obra_id,),
        ).fetchone()


def listar_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT * FROM processamentos WHERE obra_id = ? ORDER BY id DESC',
            (obra_id,),
        ).fetchall()


def excluir_por_obra(obra_id, caminho=None):
    with banco(caminho) as conn:
        conn.execute('DELETE FROM processamentos WHERE obra_id = ?', (obra_id,))