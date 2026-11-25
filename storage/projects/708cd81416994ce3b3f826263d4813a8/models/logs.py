"""Log de atividades para auditoria das ações do sistema."""

from datetime import datetime, timedelta

from models.database import banco


def _agora():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def registrar(usuario, acao, detalhes='', caminho=None):
    """Registra uma ação importante (obra criada, upload, processamento...)."""
    try:
        with banco(caminho) as conn:
            conn.execute(
                'INSERT INTO logs (data, usuario, acao, detalhes) VALUES (?, ?, ?, ?)',
                (_agora(), usuario or 'sistema', acao, detalhes or ''),
            )
    except Exception:
        # O log nunca deve interromper a operação principal.
        pass


def listar(pagina=1, por_pagina=50, caminho=None):
    """Retorna (linhas, total) com paginação, mais recentes primeiro."""
    with banco(caminho) as conn:
        total = conn.execute('SELECT COUNT(*) AS c FROM logs').fetchone()['c']
        offset = (max(1, pagina) - 1) * por_pagina
        linhas = conn.execute(
            'SELECT * FROM logs ORDER BY id DESC LIMIT ? OFFSET ?',
            (por_pagina, offset),
        ).fetchall()
    return linhas, total


# ============================================================================
# Consulta da área de atividades: filtros e agrupamento por mês
# (acima, `registrar` e `listar` seguem intactos — `listar` é usada no
# dashboard e nos testes.)
# ============================================================================

# Teto de registros exibidos por mês. Evita carregar dezenas de milhares de
# linhas no navegador; o corte é sempre declarado na tela, nunca silencioso.
LIMITE_MES = 300

MESES = (
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
)


def nome_do_mes(valor):
    """'2026-10' ou '2026-10-01 00:00:00' -> 'outubro de 2026'."""
    try:
        ano, mes = str(valor).strip()[:7].split('-')
        return f'{MESES[int(mes) - 1]} de {ano}'
    except (ValueError, IndexError, TypeError):
        return str(valor)


def mes_atual():
    """Mês corrente no formato usado para agrupar ('AAAA-MM')."""
    return datetime.now().strftime('%Y-%m')


def _limpar_data(valor):
    """Aceita apenas 'AAAA-MM-DD'; devolve '' para qualquer outra entrada."""
    try:
        datetime.strptime(str(valor).strip(), '%Y-%m-%d')
    except (ValueError, TypeError):
        return ''
    return str(valor).strip()


def _limpar_mes(valor):
    """Aceita apenas 'AAAA-MM'; devolve '' para qualquer outra entrada."""
    try:
        datetime.strptime(str(valor).strip(), '%Y-%m')
    except (ValueError, TypeError):
        return ''
    return str(valor).strip()


def normalizar_filtros(brutos=None):
    """Valida e normaliza os filtros vindos da query string.

    Se 'data_de' vier depois de 'data_ate', as duas são trocadas — mais útil
    para o usuário do que devolver uma lista vazia sem explicação.
    """
    brutos = brutos or {}
    filtros = {
        'usuario': str(brutos.get('usuario') or '').strip()[:120],
        'acao': str(brutos.get('acao') or '').strip()[:120],
        'data_de': _limpar_data(brutos.get('data_de')),
        'data_ate': _limpar_data(brutos.get('data_ate')),
    }
    if (filtros['data_de'] and filtros['data_ate']
            and filtros['data_de'] > filtros['data_ate']):
        filtros['data_de'], filtros['data_ate'] = (
            filtros['data_ate'], filtros['data_de'],
        )
    return filtros


def _condicoes(filtros):
    """Monta a cláusula WHERE e os parâmetros dos filtros."""
    onde, params = [], []
    if filtros['usuario']:
        onde.append('usuario = ?')
        params.append(filtros['usuario'])
    if filtros['acao']:
        onde.append('acao = ?')
        params.append(filtros['acao'])
    if filtros['data_de']:
        # 'data' é texto 'AAAA-MM-DD HH:MM:SS', então a comparação
        # lexicográfica equivale à cronológica.
        onde.append('data >= ?')
        params.append(filtros['data_de'] + ' 00:00:00')
    if filtros['data_ate']:
        # Dia final é inclusivo: compara com o início do dia seguinte.
        seguinte = datetime.strptime(filtros['data_ate'], '%Y-%m-%d') + timedelta(days=1)
        onde.append('data < ?')
        params.append(seguinte.strftime('%Y-%m-%d %H:%M:%S'))
    return (' WHERE ' + ' AND '.join(onde) if onde else ''), params


def contar(filtros=None, caminho=None):
    """Total de registros que atendem aos filtros."""
    onde, params = _condicoes(normalizar_filtros(filtros))
    with banco(caminho) as conn:
        return conn.execute(
            'SELECT COUNT(*) AS c FROM logs' + onde, params,
        ).fetchone()['c']


def listar_meses(filtros=None, caminho=None):
    """Meses com registros, do mais recente para o mais antigo.

    Cada item é {'mes': 'AAAA-MM', 'total': N, 'rotulo': 'outubro de 2026'}.
    """
    onde, params = _condicoes(normalizar_filtros(filtros))
    with banco(caminho) as conn:
        linhas = conn.execute(
            'SELECT substr(data, 1, 7) AS mes, COUNT(*) AS total FROM logs'
            + onde + ' GROUP BY mes ORDER BY mes DESC',
            params,
        ).fetchall()
    return [
        {'mes': linha['mes'], 'total': linha['total'],
         'rotulo': nome_do_mes(linha['mes'])}
        for linha in linhas
    ]


def listar_por_mes(mes, filtros=None, limite=LIMITE_MES, caminho=None):
    """Registros de um único mês, mais recentes primeiro.

    Devolve (linhas, total_do_mes). Se o mês passar de `limite`, as linhas
    vêm truncadas e o total devolvido permite avisar na tela.
    """
    alvo = _limpar_mes(mes)
    if not alvo:
        return [], 0
    onde, params = _condicoes(normalizar_filtros(filtros))
    onde += (' AND ' if onde else ' WHERE ') + 'substr(data, 1, 7) = ?'
    params.append(alvo)
    with banco(caminho) as conn:
        total = conn.execute(
            'SELECT COUNT(*) AS c FROM logs' + onde, params,
        ).fetchone()['c']
        linhas = conn.execute(
            'SELECT * FROM logs' + onde + ' ORDER BY id DESC LIMIT ?',
            params + [max(1, int(limite))],
        ).fetchall()
    return linhas, total


def usuarios_distintos(caminho=None):
    """Nomes de usuário que já aparecem no log, para montar o filtro."""
    with banco(caminho) as conn:
        linhas = conn.execute(
            'SELECT DISTINCT usuario FROM logs '
            "WHERE usuario IS NOT NULL AND usuario <> '' ORDER BY usuario",
        ).fetchall()
    return [linha['usuario'] for linha in linhas]


def acoes_distintas(caminho=None):
    """Ações já registradas, para montar o filtro."""
    with banco(caminho) as conn:
        linhas = conn.execute(
            'SELECT DISTINCT acao FROM logs WHERE acao <> "" ORDER BY acao',
        ).fetchall()
    return [linha['acao'] for linha in linhas]