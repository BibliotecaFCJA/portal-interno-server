import { promises as fs } from "fs";
import path from "path";
import { PROJECTS_ROOT } from "@/server/storage-paths";

export type ProjectSuggestion = {
  name?: string;
  startCommand?: string[];
  port?: number;
  accessUrl?: string;
};

const DEFAULT_PORT_RANGES: Record<string, [number, number]> = {
  next: [3000, 3999],
  vite: [5173, 5999],
  python: [8000, 8999],
  node: [9000, 9999]
};

export function allocateProjectPort(
  preferredPort: number | null | undefined,
  usedPorts: Iterable<number>,
  range: [number, number] = DEFAULT_PORT_RANGES.python
): number {
  const used = new Set(usedPorts);
  if (preferredPort != null && !used.has(preferredPort)) return preferredPort;
  for (let port = range[0]; port <= range[1]; port += 1) {
    if (!used.has(port)) return port;
  }
  throw new Error("Não há portas disponíveis para este tipo de sistema.");
}

export function defaultPortRangeForProject(project: { startCommand?: string[]; port?: number }): [number, number] {
  const command = project.startCommand?.map((part) => part.toLowerCase()).join(" ") ?? "";
  if (/\b(?:next|next\.cmd)\b/.test(command) || project.port === 3000) return DEFAULT_PORT_RANGES.next;
  if (/\b(?:vite|vite\.cmd)\b/.test(command) || project.port === 5173 || project.port === 4173) return DEFAULT_PORT_RANGES.vite;
  if (/\bpython(?:3)?(?:\.exe)?\b|\buvicorn\b|\bflask\b/.test(command) || (project.port != null && project.port >= 5000 && project.port < 9000)) {
    return DEFAULT_PORT_RANGES.python;
  }
  return DEFAULT_PORT_RANGES.node;
}

type PackageManifest = {
  name?: string;
  packageManager?: string;
  scripts?: Record<string, string>;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
};

type PackageManager = { executable: string; name: "npm" | "pnpm" | "yarn" | "bun" };

function managerExecutable(name: PackageManager["name"]): string {
  if (process.platform !== "win32") return name;
  return name === "bun" ? "bun.exe" : `${name}.cmd`;
}

function defaultPythonCommand(): string {
  return process.platform === "win32" ? "python.exe" : "python3";
}

function inProject(projectId: string, ...parts: string[]): string {
  return path.join(PROJECTS_ROOT, projectId, ...parts);
}

async function readText(projectId: string, ...parts: string[]): Promise<string | null> {
  try {
    return await fs.readFile(inProject(projectId, ...parts), "utf8");
  } catch {
    return null;
  }
}

async function packageManager(projectId: string, manifest: PackageManifest): Promise<PackageManager> {
  const declared = manifest.packageManager?.split("@")[0]?.toLowerCase();
  if (declared === "npm" || declared === "pnpm" || declared === "yarn" || declared === "bun") {
    return { name: declared, executable: managerExecutable(declared) };
  }

  if (await fileExists(projectId, "pnpm-lock.yaml")) return { name: "pnpm", executable: managerExecutable("pnpm") };
  if (await fileExists(projectId, "yarn.lock")) return { name: "yarn", executable: managerExecutable("yarn") };
  if (await fileExists(projectId, "bun.lock") || await fileExists(projectId, "bun.lockb")) {
    return { name: "bun", executable: managerExecutable("bun") };
  }
  return { name: "npm", executable: managerExecutable("npm") };
}

export async function getDependencyInstallCommand(projectId: string, ...subdir: string[]): Promise<string[] | null> {
  if (!(await fileExists(projectId, ...subdir, "package.json"))) return null;
  const packageRaw = await readText(projectId, ...subdir, "package.json");
  if (!packageRaw) return null;
  try {
    const manifest = JSON.parse(packageRaw) as PackageManifest;
    const manager = await packageManager(projectId, manifest);
    if (manager.name === "npm") {
      const locked = await fileExists(projectId, "package-lock.json") || await fileExists(projectId, "npm-shrinkwrap.json");
      return [manager.executable, locked ? "ci" : "install"];
    }
    if (manager.name === "pnpm") {
      return [manager.executable, "install", ...(await fileExists(projectId, "pnpm-lock.yaml") ? ["--frozen-lockfile"] : [])];
    }
    if (manager.name === "yarn") {
      return [manager.executable, "install", ...(await fileExists(projectId, "yarn.lock") ? ["--frozen-lockfile"] : [])];
    }
    const bunLock = await fileExists(projectId, "bun.lock") || await fileExists(projectId, "bun.lockb");
    return [manager.executable, "install", ...(bunLock ? ["--frozen-lockfile"] : [])];
  } catch {
    return null;
  }
}

function scriptCommand(manager: PackageManager, scriptName: string): string[] {
  return [manager.executable, "run", scriptName];
}

export async function getRequiredBuildCommand(projectId: string, startupScript?: string, ...subdir: string[]): Promise<string[] | null> {
  const packageRaw = await readText(projectId, ...subdir, "package.json");
  if (!packageRaw || !startupScript) return null;
  try {
    const manifest = JSON.parse(packageRaw) as PackageManifest;
    const scripts = manifest.scripts ?? {};
    if (!scripts.build) return null;
    const launchScript = scripts[startupScript] ?? "";
    const dependencies = { ...manifest.dependencies, ...manifest.devDependencies };
    const needsNextBuild = Boolean(dependencies.next && /\bnext\s+start\b/.test(launchScript)) &&
      !(await fileExists(projectId, ...subdir, ".next"));
    const usesVitePreview = /\bvite\s+preview\b/.test(launchScript) &&
      !(await fileExists(projectId, ...subdir, "dist"));
    if (!needsNextBuild && !usesVitePreview) return null;
    const manager = await packageManager(projectId, manifest);
    return scriptCommand(manager, "build");
  } catch {
    return null;
  }
}

function scriptPort(script: string): number | null {
  const match = script.match(/(?:--port(?:=|\s+)|(?:^|\s)-p\s+|\bPORT=)(\d{1,5})\b/i);
  if (!match) return null;
  const port = Number(match[1]);
  return port > 0 && port < 65536 ? port : null;
}

export async function detectProject(projectId: string): Promise<ProjectSuggestion> {
  const suggestion: ProjectSuggestion = {};
  const packageRaw = await readText(projectId, "package.json");
  if (packageRaw) {
    try {
      const manifest = JSON.parse(packageRaw) as PackageManifest;
      suggestion.name = manifest.name;
      const scripts = manifest.scripts ?? {};
      const dependencies = { ...manifest.dependencies, ...manifest.devDependencies };
      const hasVite = Boolean(dependencies.vite || Object.values(scripts).some((script) => /(^|\s)vite(?:\s|$)/i.test(script)));
      const hasNext = Boolean(dependencies.next);
      const chosenScript = ["dev", "start", "serve", "preview"].find((name) =>
        typeof scripts[name] === "string" && scripts[name].trim().length > 0
      );

      if (chosenScript) {
        const manager = await packageManager(projectId, manifest);
        suggestion.startCommand = scriptCommand(manager, chosenScript);
        const detectedScriptPort = scriptPort(scripts[chosenScript]);
        if (detectedScriptPort !== null) suggestion.port = detectedScriptPort;

        if (suggestion.port == null && hasVite) {
          const detectedVitePort = await detectVitePort(projectId, chosenScript === "preview" ? "preview" : "server");
          suggestion.port = detectedVitePort ?? (chosenScript === "preview" ? 4173 : 5173);
        } else if (suggestion.port == null && hasNext) {
          suggestion.port = 3000;
        } else if (suggestion.port == null) {
          const detectedNodePort = await detectNodePort(projectId);
          if (detectedNodePort !== null) suggestion.port = detectedNodePort;
        }

        if (suggestion.port != null) {
          suggestion.accessUrl = `http://127.0.0.1:${suggestion.port}`;
        }
      }
    } catch {
      // Manifesto inválido: tenta reconhecer outro tipo de projeto.
    }
  }

  const pythonResult = await detectPythonProject(projectId);
  if (pythonResult.startCommand) {
    return { ...suggestion, ...pythonResult, name: suggestion.name ?? pythonResult.name };
  }
  return { ...suggestion, name: suggestion.name ?? pythonResult.name ?? projectId };
}

export async function detectProjectPort(projectDir: string): Promise<number | null> {
  const read = async (...parts: string[]) => {
    try { return await fs.readFile(path.join(projectDir, ...parts), "utf8"); } catch { return null; }
  };
  for (const relative of ["app.py", "main.py", "sistema/app.py", "sistema/main.py"]) {
    const source = await read(...relative.split("/"));
    if (!source) continue;
    const matches = [...source.matchAll(/\.run\s*\([\s\S]*?\bport\s*=\s*(\d{1,5})/g)];
    const simple = [...source.matchAll(/\bport\s*=\s*(\d{1,5})/g)].at(-1);
    const match = matches.at(-1) ?? simple;
    const port = match ? Number(match[1]) : NaN;
    if (Number.isInteger(port) && port > 0 && port <= 65535) return port;
  }
  const manifestRaw = await read("package.json");
  if (manifestRaw) {
    try {
      const manifest = JSON.parse(manifestRaw) as PackageManifest;
      const scripts = manifest.scripts ?? {};
      const script = scripts.dev ?? scripts.start ?? scripts.serve ?? "";
      const explicit = scriptPort(script);
      if (explicit != null) return explicit;
      const hasVite = Boolean(manifest.dependencies?.vite || manifest.devDependencies?.vite);
      if (hasVite) {
        const raw = await read("vite.config.ts") ?? await read("vite.config.js") ?? "";
        const match = raw.match(/server\s*:\s*\{[\s\S]*?\bport\s*:\s*(\d{1,5})/);
        if (match) return Number(match[1]);
      }
    } catch { /* usa os demais marcadores */ }
  }
  return null;
}

async function detectPythonProject(projectId: string): Promise<ProjectSuggestion> {
  const bindHost = process.platform === "win32" ? "127.0.0.1" : "0.0.0.0";
  const hasPythonMarker = await hasAnyFile(projectId, [
    "pyproject.toml", "requirements.txt", "manage.py", "app.py", "main.py"
  ]);
  if (!hasPythonMarker) return {};

  const python = (await firstExistingPython(projectId)) ?? defaultPythonCommand();
  const manage = await fileExists(projectId, "manage.py");
  if (manage) {
    const port = (await detectPythonPort(projectId)) ?? 8000;
    return {
      name: projectId,
      startCommand: [python, "manage.py", "runserver", `${bindHost}:${port}`],
      port,
      accessUrl: `http://127.0.0.1:${port}`
    };
  }

  for (const relative of ["main.py", "app.py", "src/main.py", "src/app.py"]) {
    const code = await readText(projectId, ...relative.split("/"));
    if (!code) continue;
    const hasFastApi = /\bFastAPI\s*\(/.test(code);
    const hasFlask = /(?:\bFlask\s*\(|\bflask\.Flask\s*\(|from\s+flask\s+import)/i.test(code);
    const hasUvicorn = /uvicorn/i.test((await readText(projectId, "requirements.txt")) ?? "") ||
      /uvicorn/i.test((await readText(projectId, "pyproject.toml")) ?? "");
    const detectedPort = await detectPythonPort(projectId);
    const port = detectedPort ?? (hasFastApi && hasUvicorn ? 8000 : hasFlask ? 5000 : undefined);

    if (hasFlask) {
      const module = relative.replace(/\.py$/, "").replace(/\//g, ".");
      const startCommand = /\bapp\.run\s*\(/.test(code)
        ? [python, relative]
        : [python, "-m", "flask", "--app", module, "run", "--host", bindHost, "--port", String(port ?? 5000)];
      return {
        name: projectId,
        startCommand,
        port: port ?? 5000,
        accessUrl: `http://127.0.0.1:${port ?? 5000}`
      };
    }

    if (hasFastApi && hasUvicorn) {
      const module = relative.replace(/\.py$/, "").replace(/\//g, ".");
      return {
        name: projectId,
        startCommand: [python, "-m", "uvicorn", `${module}:app`, "--host", bindHost, "--port", String(port)],
        port,
        accessUrl: `http://127.0.0.1:${port}`
      };
    }

    return {
      name: projectId,
      startCommand: [python, relative],
      port,
      accessUrl: port ? `http://127.0.0.1:${port}` : undefined
    };
  }

  return { name: projectId };
}

async function fileExists(projectId: string, ...parts: string[]): Promise<boolean> {
  try {
    await fs.access(inProject(projectId, ...parts));
    return true;
  } catch {
    return false;
  }
}

async function hasAnyFile(projectId: string, names: string[]): Promise<boolean> {
  for (const name of names) {
    if (await fileExists(projectId, ...name.split("/"))) return true;
  }
  return false;
}

async function firstExistingPython(projectId: string): Promise<string | null> {
  const candidates = process.platform === "win32"
    ? [".venv/Scripts/python.exe", "venv/Scripts/python.exe"]
    : [".venv/bin/python", "venv/bin/python", ".portal-venv/bin/python"];
  for (const relative of candidates) {
    if (await fileExists(projectId, ...relative.split("/"))) return inProject(projectId, ...relative.split("/"));
  }
  return null;
}

async function detectPythonPort(projectId: string): Promise<number | null> {
  for (const relative of ["app.py", "main.py", "src/app.py", "src/main.py"]) {
    const code = await readText(projectId, ...relative.split("/"));
    if (!code) continue;
    const matches = [
      code.match(/run\([^)]*\bport\s*=\s*(\d{1,5})/),
      code.match(/\bport\s*=\s*(\d{1,5})/),
      code.match(/--port[=\s]+["']?(\d{1,5})/i)
    ];
    const raw = matches.find(Boolean)?.[1];
    if (raw) {
      const port = Number(raw);
      if (port > 0 && port < 65536) return port;
    }
  }
  return null;
}

async function detectNodePort(projectId: string): Promise<number | null> {
  for (const relative of ["server.js", "index.js", "app.js", "src/server.js", "src/index.js", "src/app.js", "server.ts", "index.ts", "src/server.ts", "src/index.ts"]) {
    const code = await readText(projectId, ...relative.split("/"));
    if (!code) continue;
    const match = code.match(/\b(?:const|let|var)\s+PORT\s*=\s*(\d{1,5})/) ?? code.match(/\.listen\s*\(\s*(\d{1,5})/);
    if (match) {
      const port = Number(match[1]);
      if (port > 0 && port < 65536) return port;
    }
  }
  return null;
}

async function detectVitePort(projectId: string, section: "server" | "preview"): Promise<number | null> {
  for (const name of ["vite.config.ts", "vite.config.mts", "vite.config.js", "vite.config.mjs"]) {
    const raw = await readText(projectId, name);
    if (!raw) continue;
    const block = raw.match(new RegExp(`${section}\\s*:\\s*\\{([\\s\\S]*?)\\n\\s*\\}`));
    const match = (block?.[1] ?? "").match(/\bport\s*:\s*(\d{1,5})/);
    if (match) {
      const port = Number(match[1]);
      if (port > 0 && port < 65536) return port;
    }
  }
  return null;
}

