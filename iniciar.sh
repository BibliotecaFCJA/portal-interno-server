#!/usr/bin/env bash
# Inicia o Portal da Biblioteca Dumerval T. em producao.
# Uso: ./iniciar.sh
# Funciona no Linux/macOS e no Git Bash do Windows.

set -euo pipefail

cd "$(dirname "$0")"

PORT="${PORT:-3000}"

# No Windows o npm e o npm.cmd; no Git Bash o "npm" sozinho pode falhar.
if command -v npm.cmd >/dev/null 2>&1; then
  NPM="npm.cmd"
elif command -v npm >/dev/null 2>&1; then
  NPM="npm"
else
  echo "ERRO: Node.js/NPM nao encontrado. Instale o Node.js 18 ou superior."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERRO: Node.js nao encontrado. Instale o Node.js 18 ou superior."
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "Instalando dependencias (primeira vez)..."
  "$NPM" install
fi

if [ ! -d .next ]; then
  echo "Gerando build de producao..."
  "$NPM" run build
fi

# IP da maquina na rede local, para mostrar o endereco de acesso.
# Linux/macOS usam "hostname -I"; no Git Bash isso nao existe, entao lemos o ipconfig.
LOCAL_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
if [ -z "$LOCAL_IP" ] && command -v ipconfig >/dev/null 2>&1; then
  LOCAL_IP="$(ipconfig 2>/dev/null \
    | iconv -f CP850 -t UTF-8 2>/dev/null \
    | grep -iE 'IPv4' \
    | grep -vE '127\.|169\.254' \
    | head -1 \
    | sed 's/.*: //' \
    | tr -d ' ' || true)"
fi

echo ""
echo "Portal da Biblioteca Dumerval T."
echo "  Nesta maquina: http://localhost:$PORT"
if [ -n "$LOCAL_IP" ]; then
  echo "  Na rede local: http://$LOCAL_IP:$PORT"
fi
echo ""
echo "Para encerrar: Ctrl+C"
echo ""

exec "$NPM" run start -- -p "$PORT"
