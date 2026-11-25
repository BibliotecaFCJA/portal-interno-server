#!/usr/bin/env bash
set -euo pipefail

# Corrige no Linux os caminhos Windows gravados no cadastro dos sistemas locais.
# Execute da raiz do portal, depois de copiar/atualizar o repositório na VM.

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este script deve ser executado na máquina Linux." >&2
  exit 1
fi

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$ROOT/data/custom-systems.json"

if [[ ! -f "$CONFIG" ]]; then
  echo "Não encontrei data/custom-systems.json em $ROOT" >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js é necessário para atualizar o cadastro JSON." >&2
  exit 1
fi

BACKUP_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/portal-interno/backups"
mkdir -p -- "$BACKUP_DIR"
chmod 700 -- "$BACKUP_DIR"
BACKUP="$BACKUP_DIR/custom-systems.json.$(date +%Y%m%d-%H%M%S).bak"
cp -p -- "$CONFIG" "$BACKUP"

PORTAL_ROOT="$ROOT" node <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const root = process.env.PORTAL_ROOT;
const configFile = path.join(root, "data", "custom-systems.json");
const systems = JSON.parse(fs.readFileSync(configFile, "utf8"));
if (!Array.isArray(systems)) throw new Error("O cadastro não contém uma lista de sistemas.");

const updates = [];
for (const system of systems) {
  if (system.type !== "local") continue;
  if (!/^[a-z0-9-]{1,32}$/.test(system.id)) {
    throw new Error(`ID inválido no cadastro: ${system.id}`);
  }

  const projectDir = path.resolve(root, "storage", "projects", system.id);
  if (!fs.existsSync(projectDir) || !fs.statSync(projectDir).isDirectory()) {
    throw new Error(`Pasta do projeto não encontrada: ${system.id}`);
  }

  const oldRoots = [system.workDir, system.sourceFolder].filter(
    (value) => typeof value === "string" && path.win32.isAbsolute(value)
  );

  const rebaseWindowsPath = (value) => {
    if (typeof value !== "string" || !path.win32.isAbsolute(value)) return value;
    for (const oldRoot of oldRoots) {
      const relative = path.win32.relative(oldRoot, value);
      if (relative === "" || (!relative.startsWith("..") && !path.win32.isAbsolute(relative))) {
        return path.resolve(projectDir, ...relative.split(/[\\/]+/).filter(Boolean));
      }
    }
    return value;
  };

  system.sourceFolder = projectDir;
  system.workDir = projectDir;

  if (Array.isArray(system.startCommand) && system.startCommand.length > 0) {
    // local-systems.ts seleciona .portal-venv/bin/python automaticamente,
    // quando existir; caso contrário usa o python3 instalado no Linux.
    system.startCommand = ["python3", ...system.startCommand.slice(1).map(rebaseWindowsPath)];
  }

  if (system.env && typeof system.env === "object") {
    for (const [key, value] of Object.entries(system.env)) {
      system.env[key] = rebaseWindowsPath(value);
    }
  }

  updates.push({ name: system.name, id: system.id, projectDir });
}

if (updates.length === 0) throw new Error("Não há sistemas locais para atualizar.");
fs.writeFileSync(configFile, `${JSON.stringify(systems, null, 2)}\n`, "utf8");
for (const item of updates) console.log(`${item.name}: ${item.projectDir}`);
NODE

echo "Cadastro atualizado. Cópia de segurança: $BACKUP"
echo "O script corrige caminhos; não instala Python nem as dependências dos projetos."
