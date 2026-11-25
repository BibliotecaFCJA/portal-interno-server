import { promises as fs } from "fs";
import path from "path";

export type AIDetection = {
  startCommand: string[];
  port: number | null;
  accessUrl: string | null;
};

const OLLAMA_BASE = process.env.OLLAMA_BASE ?? "http://127.0.0.1:11434";
const AI_MODEL = process.env.AI_MODEL ?? "qwen2.5:3b";
const AI_TIMEOUT_MS = Number(process.env.AI_TIMEOUT_MS ?? 240000);

const SKIP_DIRS = new Set([
  ".git",
  "node_modules",
  ".venv",
  ".portal-venv",
  "venv",
  "__pycache__",
  "dist",
  "build",
  ".next",
  ".idea",
  ".vscode",
  "coverage",
  ".pytest_cache",
  ".mypy_cache",
  "out"
]);

const SKIP_EXTENSIONS = new Set([
  ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp", ".svg",
  ".pdf", ".doc", ".docx", ".xls", ".xlsx",
  ".exe", ".dll", ".so", ".dylib", ".jar", ".war",
  ".zip", ".rar", ".7z", ".tar", ".gz",
  ".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".pyd",
  ".woff", ".woff2", ".ttf", ".otf", ".eot",
  ".mp3", ".mp4", ".avi", ".mov", ".webm", ".wav",
  ".min.js", ".min.css", ".map",
  ".class", ".o", ".obj"
]);

const KEY_FILES = [
  "package.json",
  "requirements.txt",
  "pyproject.toml",
  "Pipfile",
  "manage.py",
  "app.py",
  "main.py",
  "server.js",
  "server.ts",
  "index.js",
  "index.ts",
  "tsconfig.json",
  "vite.config.ts",
  "next.config.js",
  "next.config.mjs",
  "composer.json",
  "Gemfile",
  "Cargo.toml",
  "go.mod",
  "pom.xml",
  "build.gradle",
  "docker-compose.yml",
  "Dockerfile",
  "Makefile",
  "Procfile",
  "README.md",
  "README.txt"
];

const MAX_TOTAL_CHARS = 10000;
const MAX_FILES = 45;
const MAX_DEPTH = 6;
const MAX_FILE_BYTES = 300 * 1024;
const MAX_FILE_CHARS = 2000;
const MAX_FILE_LINES = 60;

function shouldSkipFile(name: string, size: number): boolean {
  const lower = name.toLowerCase();
  if (size > MAX_FILE_BYTES) return true;
  for (const ext of SKIP_EXTENSIONS) {
    if (lower.endsWith(ext)) return true;
  }
  return false;
}

function shouldSkipDirectory(name: string): boolean {
  const lower = name.toLowerCase();
  return SKIP_DIRS.has(lower) || /^(?:\.?venv|env)(?:[-_.].*)?$/.test(lower);
}

type FileEntry = { rel: string; abs: string; size: number };

async function collectFiles(root: string): Promise<FileEntry[]> {
  const entries: FileEntry[] = [];
  let totalSize = 0;

  async function walk(dir: string, depth: number) {
    if (depth > MAX_DEPTH) return;
    let children;
    try {
      children = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const child of children) {
      if (shouldSkipDirectory(child.name)) continue;
      const abs = path.join(dir, child.name);
      const rel = path.relative(root, abs);
      if (child.isDirectory()) {
        await walk(abs, depth + 1);
      } else {
        let size = 0;
        try {
          size = (await fs.stat(abs)).size;
        } catch {
          continue;
        }
        if (shouldSkipFile(child.name, size)) continue;
        entries.push({ rel, abs, size });
        totalSize += size;
        if (entries.length >= MAX_FILES * 2) return;
      }
    }
  }

  await walk(root, 1);

  // Os arquivos-chave primeiro, depois o restante, para caber no limite de tamanho.
  const scored = entries
    .map((entry) => {
      const base = path.basename(entry.rel).toLowerCase();
      const score = KEY_FILES.includes(base) ? 0 : 1;
      return { entry, score, totalSize };
    })
    .sort((a, b) => a.score - b.score || a.entry.rel.localeCompare(b.entry.rel));
  return scored.slice(0, MAX_FILES).map((item) => item.entry);
}

async function buildProjectSummary(root: string): Promise<string> {
  const files = await collectFiles(root);
  const lines: string[] = [];
  let budget = MAX_TOTAL_CHARS;

  lines.push("ARQUIVOS DA PASTA:");
  for (const file of files) {
    lines.push(`- ${file.rel} (${file.size} bytes)`);
  }

  lines.push("");
  lines.push("CONTEUDO DOS ARQUIVOS MAIS RELEVANTES:");
  for (const file of files) {
    if (budget <= 0) break;
    const base = path.basename(file.rel).toLowerCase();
    if (!KEY_FILES.includes(base)) continue;
    let content = "";
    try {
      content = await fs.readFile(file.abs, "utf8");
    } catch {
      continue;
    }
    const truncated = content.slice(0, MAX_FILE_CHARS).split("\n").slice(0, MAX_FILE_LINES).join("\n");
    lines.push(`===== ${file.rel} =====`);
    lines.push(truncated);
    budget -= truncated.length + file.rel.length + 16;
  }

  let summary = lines.join("\n");
  if (summary.length > MAX_TOTAL_CHARS + 4000) {
    summary = summary.slice(0, MAX_TOTAL_CHARS + 4000);
  }
  return summary;
}

export async function isOllamaAvailable(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const response = await fetch(`${OLLAMA_BASE}/api/tags`, { signal: controller.signal });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

function sanitizeProgram(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const program = value.trim();
  if (!program || program.length > 120) return null;
  // Aceita apenas um nome de programa simples (ex.: python.exe, npm.cmd, node.exe, php).
  if (!/^[a-zA-Z0-9][a-zA-Z0-9 ._-]*$/.test(program)) return null;
  if (program.includes("/") || program.includes("\\")) return null;
  return program;
}

function sanitizeArgs(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter((item) => item.length > 0 && item.length <= 200)
    .filter((item) => !item.includes("\0"));
}

function sanitizePort(value: unknown): number | null {
  if (typeof value === "number" && Number.isInteger(value) && value > 0 && value < 65536) {
    return value;
  }
  if (typeof value === "string" && /^\d{1,5}$/.test(value.trim())) {
    const port = Number(value.trim());
    if (port > 0 && port < 65536) return port;
  }
  return null;
}

function sanitizeUrl(value: unknown, port: number | null): string | null {
  if (typeof value === "string" && /^https?:\/\//.test(value.trim())) {
    const url = value.trim();
    if (url.length <= 200) return url;
  }
  return port != null ? `http://127.0.0.1:${port}` : null;
}

export function sanitizeAIDetection(parsed: unknown): AIDetection | null {
  if (typeof parsed !== "object" || parsed === null) return null;
  const record = parsed as Record<string, unknown>;

  const program = sanitizeProgram(record.program ?? record.command ?? record.executable);
  let args: string[] = [];
  if (Array.isArray(record.args) || Array.isArray(record.arguments)) {
    args = sanitizeArgs(record.args ?? record.arguments);
  }

  const startCommand = program ? [program, ...args] : [];
  const port = sanitizePort(record.port);
  const accessUrl = sanitizeUrl(record.accessUrl ?? record.url, port);

  return { startCommand, port, accessUrl };
}

const PYTHON_PROGRAM = process.platform === "win32" ? "python.exe" : "python3";
const NODE_PROGRAM = process.platform === "win32" ? "npm.cmd" : "npm";
const BIND_HOST = process.platform === "win32" ? "127.0.0.1" : "0.0.0.0";

const PROMPT = `
Você e um especialista em descobrir como iniciar projetos de software a partir dos arquivos deles.
Abaixo estao os arquivos de uma pasta de projeto.

Responda APENAS com um JSON valido, sem nenhum texto antes ou depois. Nao invente caminhos absolutos:
{
  "program": "nome do programa que inicia o projeto (apenas o nome base, ex.: ${PYTHON_PROGRAM}, ${NODE_PROGRAM}, node, php, dotnet)",
  "args": ["argumento 1", "argumento 2"],
  "port": numero da porta em que o servidor abre (null se impossivel saber),
  "accessUrl": "endereco completo para abrir no navegador, ex.: http://127.0.0.1:8000, ou null"
}
Se o projeto for Python: use ${PYTHON_PROGRAM} (ou o nome do venv) + o arquivo principal (ex.: app.py). 
Se for Node.js/Next.js: use ${NODE_PROGRAM} com os argumentos do script de desenvolvimento (ex.: ["run","dev"]) e porta 3000.
Se for Vite (package.json com "vite" no script \"dev\" ou nas dependencias): use ${NODE_PROGRAM} run dev e porta 5173 (ou a porta definida no vite.config).
Use ${BIND_HOST} como host de escuta quando o comando aceitar --host, -H ou -b.
Se nao for possivel dizer, use "program": null, "args": [] e "port": null.

ARQUIVOS DA PASTA:
`;

async function generateJson(prompt: string): Promise<unknown | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), AI_TIMEOUT_MS);
  try {
    const response = await fetch(`${OLLAMA_BASE}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model: AI_MODEL,
        prompt,
        stream: false,
        format: "json",
        options: { temperature: 0, num_predict: 256 }
      }),
      signal: controller.signal
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as { response?: string };
    if (typeof payload.response !== "string") return null;
    return JSON.parse(payload.response) as unknown;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export async function detectWithAI(root: string): Promise<AIDetection | null> {
  const summary = await buildProjectSummary(root);
  const data = await generateJson(PROMPT + summary);
  return sanitizeAIDetection(data);
}
