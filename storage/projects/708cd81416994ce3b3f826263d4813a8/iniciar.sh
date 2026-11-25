#!/bin/bash
# ============================================
#  COMO LIGAR O SISTEMA — só isso! 🚀
#  Dê dois cliques neste arquivo, ou rode pelo terminal:
#      ./iniciar.sh
# ============================================

cd "$(dirname "$0")" || exit 1

# Ativa o ambiente virtual (se existir)
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
elif [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Garante que existe um Python disponível
if ! command -v python >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
        alias python=python3 2>/dev/null || PYTHON_CMD=python3
    fi
fi
PYTHON_CMD="${PYTHON_CMD:-python}"

# Descobre a porta configurada no .env (padrão: 5000)
PORTA=5000
if [ -f .env ]; then
    PORTA_ENV=$(grep -E '^FLASK_PORT=' .env | head -n1 | cut -d= -f2 | tr -d ' "')
    [ -n "$PORTA_ENV" ] && PORTA=$PORTA_ENV
fi

# Verifica se a porta já está ocupada ANTES de iniciar
if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -q ":${PORTA} "; then
    echo ""
    echo "⚠️  A porta ${PORTA} já está em uso."
    echo ""
    echo "   Provavelmente o sistema JÁ ESTÁ RODANDO em outro terminal."
    echo "   Nesse caso, basta abrir o navegador em: http://127.0.0.1:${PORTA}"
    echo ""
    echo "   Se NÃO estiver rodando, feche o processo antigo com:"
    echo "       pkill -f \"python app.py\""
    echo ""
    read -rp "Pressione ENTER para fechar esta janela..."
    exit 0
fi

echo "=========================================="
echo "  Ligando o sistema... aguarde um pouco."
echo "  Quando aparecer 'Running on', abra o"
echo "  navegador em: http://127.0.0.1:${PORTA}"
echo "  Para DESLIGAR: aperte CTRL+C aqui."
echo "=========================================="

"$PYTHON_CMD" app.py
STATUS=$?

# Se chegou aqui, o servidor foi encerrado (CTRL+C ou erro)
echo ""
if [ $STATUS -ne 0 ] && [ $STATUS -ne 130 ]; then
    echo "❌ O servidor parou com um ERRO (código ${STATUS})."
    echo "   Role a janela para cima, tire um print da mensagem"
    echo "   e procure ajuda com esse print."
else
    echo "✅ Sistema desligado."
fi

# Mantém a janela aberta quando executado por duplo clique,
# para o usuário conseguir ler a mensagem antes de fechar.
read -rp "Pressione ENTER para fechar esta janela..."