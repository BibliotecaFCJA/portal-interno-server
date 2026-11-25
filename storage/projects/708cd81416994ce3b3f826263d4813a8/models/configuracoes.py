"""
Configurações do sistema (marca d'água e processamento).

Armazenadas na tabela "configuracoes" como pares chave/valor, com
valores padrão definidos aqui e facilmente alteráveis pela interface.
"""

from models.database import banco

PADROES = {
    # Marca d'água -------------------------------------------------
    'wm_posicao': 'superior_esquerdo',
    'wm_tamanho_modo': 'automatico',      # automatico | fixo
    'wm_tamanho_percentual': '8',         # % da largura da página
    'wm_tamanho_minimo_px': '80',         # limite mínimo seguro
    'wm_tamanho_maximo_px': '600',        # limite máximo seguro
    'wm_tamanho_fixo_px': '200',          # usado no modo fixo
    'wm_margem_modo': 'automatico',       # automatico | fixo
    'wm_margem_percentual': '2.5',        # % da menor dimensão
    'wm_margem_fixa_px': '40',
    'wm_opacidade': '85',                 # 0 a 100
    'wm_modo_aplicacao': 'normal',        # normal | inteligente
    # Processamento ------------------------------------------------
    'proc_formato_saida': 'original',     # original | jpeg | png | tiff
    'proc_qualidade_jpeg': '95',
    'proc_preservar_resolucao': '1',      # 1 = preservar (recomendado)
    'proc_dimensao_maxima': '0',          # 0 = ilimitado
}

ROTULOS_POSICAO = {
    'superior_esquerdo': 'Superior esquerdo',
    'superior_centro': 'Superior centralizado',
    'superior_direito': 'Superior direito',
    'centro_esquerdo': 'Centro esquerdo',
    'centro': 'Centro',
    'centro_direito': 'Centro direito',
    'inferior_esquerdo': 'Inferior esquerdo',
    'inferior_centro': 'Inferior centralizado',
    'inferior_direito': 'Inferior direito',
}

ROTULOS_FORMATO = {
    'original': 'Manter original',
    'jpeg': 'JPEG',
    'png': 'PNG',
    'tiff': 'TIFF',
}


def obter_todas(caminho=None):
    """Retorna todas as configurações mescladas com os padrões."""
    valores = dict(PADROES)
    with banco(caminho) as conn:
        linhas = conn.execute('SELECT chave, valor FROM configuracoes').fetchall()
    for linha in linhas:
        valores[linha['chave']] = linha['valor']
    return valores


def salvar(valores, caminho=None):
    """Grava um dicionário de configurações (chave → valor)."""
    with banco(caminho) as conn:
        for chave, valor in valores.items():
            conn.execute(
                'INSERT INTO configuracoes (chave, valor) VALUES (?, ?) '
                'ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor',
                (chave, str(valor)),
            )


def validar(dados):
    """Valida um dicionário parcial de configurações.

    Retorna (limpos, erros): dicionário apenas com chaves conhecidas e
    valores válidos, e a lista de mensagens de erro.
    """
    limpos = {}
    erros = []

    def _num(chave, minimo, maximo, tipo=float):
        if chave not in dados:
            return
        bruto = str(dados[chave]).strip().replace(',', '.')
        try:
            valor = tipo(bruto)
        except (TypeError, ValueError):
            erros.append(f'Valor inválido para {chave}.')
            return
        if valor < minimo or valor > maximo:
            erros.append(f'{chave}: valor fora do intervalo permitido ({minimo} a {maximo}).')
            return
        limpos[chave] = str(valor)

    if 'wm_posicao' in dados:
        if dados['wm_posicao'] in ROTULOS_POSICAO:
            limpos['wm_posicao'] = dados['wm_posicao']
        else:
            erros.append('Posição da marca d\'água inválida.')
    if 'wm_tamanho_modo' in dados:
        if dados['wm_tamanho_modo'] in ('automatico', 'fixo'):
            limpos['wm_tamanho_modo'] = dados['wm_tamanho_modo']
        else:
            erros.append('Modo de tamanho inválido.')
    if 'wm_margem_modo' in dados:
        if dados['wm_margem_modo'] in ('automatico', 'fixo'):
            limpos['wm_margem_modo'] = dados['wm_margem_modo']
        else:
            erros.append('Modo de margem inválido.')
    if 'wm_modo_aplicacao' in dados:
        if dados['wm_modo_aplicacao'] in ('normal', 'inteligente'):
            limpos['wm_modo_aplicacao'] = dados['wm_modo_aplicacao']
        else:
            erros.append('Modo de aplicação inválido.')
    if 'proc_formato_saida' in dados:
        if dados['proc_formato_saida'] in ROTULOS_FORMATO:
            limpos['proc_formato_saida'] = dados['proc_formato_saida']
        else:
            erros.append('Formato de saída inválido.')
    if 'proc_preservar_resolucao' in dados:
        limpos['proc_preservar_resolucao'] = '1' if str(dados['proc_preservar_resolucao']) in ('1', 'on', 'true', 'True') else '0'
    _num('wm_tamanho_percentual', 1, 50)
    _num('wm_tamanho_minimo_px', 10, 2000, int)
    _num('wm_tamanho_maximo_px', 50, 5000, int)
    _num('wm_tamanho_fixo_px', 20, 5000, int)
    _num('wm_margem_percentual', 0, 20)
    _num('wm_margem_fixa_px', 0, 2000, int)
    _num('wm_opacidade', 0, 100, int)
    _num('proc_qualidade_jpeg', 1, 100, int)
    _num('proc_dimensao_maxima', 0, 50000, int)

    if 'wm_tamanho_maximo_px' in limpos and 'wm_tamanho_minimo_px' in limpos:
        if float(limpos['wm_tamanho_maximo_px']) < float(limpos['wm_tamanho_minimo_px']):
            erros.append('O tamanho máximo da logo deve ser maior ou igual ao mínimo.')
            limpos.pop('wm_tamanho_maximo_px', None)

    return limpos, erros


def descrever_tamanho(cfg):
    """Descrição legível do modo de tamanho (para relatórios)."""
    if str(cfg.get('wm_tamanho_modo', 'automatico')) == 'fixo':
        return f"Fixo ({cfg.get('wm_tamanho_fixo_px', 200)} px)"
    return f"Automático ({cfg.get('wm_tamanho_percentual', 8)}% da largura)"


def descrever_margem(cfg):
    if str(cfg.get('wm_margem_modo', 'automatico')) == 'fixo':
        return f"Fixa ({cfg.get('wm_margem_fixa_px', 40)} px)"
    return f"Automática ({cfg.get('wm_margem_percentual', 2.5)}% da página)"


def descrever_posicao(cfg):
    return ROTULOS_POSICAO.get(str(cfg.get('wm_posicao', 'superior_esquerdo')), 'Superior esquerdo')