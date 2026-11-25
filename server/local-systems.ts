import { execFileSync, spawn, spawnSync, type ChildProcess, type StdioOptions } from "child_process";
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, writeFileSync } from "fs";
import net from "net";
import path from "path";
import { listCustomSystems, listPublishedSystems, writeCustomSystems, type CustomSystem } from "@/server/custom-systems";
import { resolveProjectDir } from "@/server/storage-paths";
import { defaultPortRangeForProject, getDependencyInstallCommand, getRequiredBuildCommand } from "@/server/project-detector";
import { commandWithProjectPort, findAvailableProjectPort, setNodeServerPort, setPythonRunPort } from "@/server/port-utils";

// Registro local dos sistemas gerenciados pelo portal (somente durante a etapa local).
// Em produção isso vira o modelo do schema: repo_url + branch + porta dentro de container.
export type LocalSystemRuntime = {
  id: string;
  command: string;
  args: string[];
  cwd: string;
  port: number;
  env?: Record<string, string>;
};

const builtinRuntimes: Record<string, LocalSystemRuntime> = {};

async function getRuntimes(): Promise<Record<string, LocalSystemRuntime>> {
  const runtimes: Record<string, LocalSystemRuntime> = { ...builtinRuntimes };
  try {
    const custom = await listPublishedSystems();
    for (const system of custom) {
      if (system.type !== "local") continue;
      if (!system.startCommand || system.startCommand.length === 0) continue;
      if (system.port == null) continue;
      const cwd = system.workDir ?? system.sourceFolder ?? process.cwd();
      let command = system.startCommand[0];
      const baseCommand = path.basename(command).toLowerCase();
      const managedPython = managedPythonPath(cwd);
      if (["python", "python.exe", "python3", "python3.exe", "py.exe"].includes(baseCommand) && existsSync(managedPython)) {
        command = managedPython;
      }
      runtimes[system.id] = {
        id: system.id,
        command,
        args: system.startCommand.slice(1),
        cwd,
        port: system.port,
        env: system.env
      };
    }
  } catch {
    // ignora falhas na leitura do arquivo de sistemas custom
  }
  return runtimes;
}

export async function getLocalSystem(id: string): Promise<LocalSystemRuntime | null> {
  return (await getRuntimes())[id] ?? null;
}

export async function getLocalSystemIds(): Promise<string[]> {
  return Object.keys(await getRuntimes());
}

function fileExists(filePath: string): boolean {
  return existsSync(filePath);
}

const processes = new Map<string, ChildProcess>();

function managedPythonPath(projectDir: string): string {
  return process.platform === "win32"
    ? path.join(projectDir, ".portal-venv", "Scripts", "python.exe")
    : path.join(projectDir, ".portal-venv", "bin", "python");
}

// Node nesta máquina (v24) lança spawn EINVAL ao executar .cmd/.bat direto.
// Contorno confiável: rodar via cmd.exe /d /s /c com aspas corretas (padrão
// usado por cross-spawn/npm). Para programas normais (.exe/.py/venv) usa spawn puro.
function isScriptShim(program: string): boolean {
  return /\.(cmd|bat)$/i.test(program);
}

function cmdQuote(arg: string): string {
  if (arg && !/[\s"&|<>^%]/.test(arg)) return arg;
  return '"' + arg.replace(/"/g, '""') + '"';
}

function spawnSystemCommand(
  program: string,
  args: string[],
  options: { cwd: string; env?: NodeJS.ProcessEnv; windowsHide?: boolean; logId?: string }
): ChildProcess {
  // A saída NUNCA é descartada ("ignore" trava Flask/Vite no Windows: o filho
  // fica vivo sem abrir a porta). Vai para portal-out.log / portal-err.log
  // dentro da pasta do sistema, que também ajuda a diagnosticar.
  let stdio: StdioOptions = "ignore";
  let outFd = -1;
  let errFd = -1;
  if (options.logId) {
    try {
      const dir = resolveProjectDir(options.logId);
      mkdirSync(dir, { recursive: true });
      outFd = openSync(path.join(dir, "portal-out.log"), "a");
      errFd = openSync(path.join(dir, "portal-err.log"), "a");
      stdio = ["ignore", outFd, errFd];
    } catch {
      stdio = "ignore";
    }
  }
  const base = {
    cwd: options.cwd,
    env: options.env,
    stdio,
    windowsHide: options.windowsHide ?? true
  };
  let child: ChildProcess;
  if (process.platform === "win32" && isScriptShim(program)) {
    const commandLine = [cmdQuote(program), ...args.map(cmdQuote)].join(" ");
    child = spawn("cmd.exe", ["/d", "/s", "/c", commandLine], {
      ...base,
      windowsVerbatimArguments: true
    });
  } else {
    child = spawn(program, args, base);
  }
  if (outFd >= 0) closeSync(outFd);
  if (errFd >= 0) closeSync(errFd);
  return child;
}

function tryConnect(host: string, port: number, timeoutMs: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    const finish = (open: boolean) => {
      socket.destroy();
      resolve(open);
    };
    socket.setTimeout(timeoutMs, () => finish(false));
    socket.once("connect", () => finish(true));
    socket.once("error", () => finish(false));
  });
}

async function isPortOpen(port: number, host = "127.0.0.1", timeoutMs = 1500): Promise<boolean> {
  // Servidores amarram no loopback IPv4 (127.0.0.1) ou IPv6 (::1) conforme o
  // runtime — o Vite, por exemplo, usa "localhost" e sobe em ::1. Testa as duas.
  const candidates = host === "127.0.0.1" ? ["127.0.0.1", "::1"] : [host];
  for (const candidate of candidates) {
    if (await tryConnect(candidate, port, timeoutMs)) return true;
  }
  return false;
}

function listenerPidForPort(port: number): number | null {
  try {
    // Sem "-p tcp": esse filtro esconde linhas IPv6 como [::1]:5173 (Vite).
    const output = execFileSync("netstat", ["-ano"], {
      encoding: "utf8",
      windowsHide: true
    });
    for (const line of output.split(/\r?\n/)) {
      const parts = line.trim().split(/\s+/);
      if (parts.length < 5) continue;
      const proto = parts[0];
      if (proto !== "TCP" && proto !== "TCPv6") continue;
      if (parts[3] !== "LISTENING") continue;
      const local = parts[1];
      const portMatch = local.match(/:(\d+)$/);
      if (!portMatch || Number(portMatch[1]) !== port) continue;
      // Só endereços locais: 127.0.0.1, ::1 ou todas as interfaces.
      if (
        local.startsWith("127.0.0.1:") ||
        local.startsWith("[::1]:") ||
        local.startsWith("0.0.0.0:") ||
        local.startsWith("[::]:")
      ) {
        return Number(parts[4]);
      }
    }
  } catch {
    return null;
  }
  return null;
}

function readStartError(id: string): string | undefined {
  try {
    const content = readFileSync(path.join(resolveProjectDir(id), "portal-err.log"), "utf8");
    const lines = content.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const last = lines.at(-1);
    return last ? last.slice(0, 300) : undefined;
  } catch {
    return undefined;
  }
}

function terminateProcess(pid: number): boolean {
  if (process.platform === "win32") {
    const result = spawnSync("taskkill", ["/PID", String(pid), "/T", "/F"], {
      stdio: "ignore",
      windowsHide: true
    });
    return result.status === 0;
  }
  try {
    process.kill(pid, "SIGTERM");
    return true;
  } catch {
    return false;
  }
}

function listenerPidsForPort(port: number): number[] {
  if (process.platform !== "win32") {
    try {
      const output = execFileSync("lsof", ["-ti", `tcp:${port}`], { encoding: "utf8" });
      return output
        .split(/\r?\n/)
        .map((line) => Number(line.trim()))
        .filter((pid) => Number.isInteger(pid) && pid > 0);
    } catch {
      return [];
    }
  }
  const pid = listenerPidForPort(port);
  return pid == null ? [] : [pid];
}

export async function isOnline(id: string): Promise<boolean> {
  const runtime = (await getRuntimes())[id];
  if (!runtime) return false;
  return isPortOpen(runtime.port);
}

export async function start(id: string): Promise<{ started: boolean; message?: string }> {
  const runtime = (await getRuntimes())[id];
  if (!runtime) {
    return { started: false, message: "Sistema sem configuração local." };
  }

  const tracked = processes.get(id);
  if (tracked && tracked.exitCode === null) {
    return { started: false, message: "Sistema já está em execução." };
  }

  const systems = await listCustomSystems();
  const system = systems.find((item) => item.id === id);
  const range = defaultPortRangeForProject({ startCommand: system?.startCommand, port: runtime.port });
  const port = await findAvailableProjectPort(
    runtime.port,
    systems.filter((item) => item.id !== id && item.type === "local").map((item) => item.port).filter((value): value is number => value != null),
    range
  );
  if (port == null) return { started: false, message: "Não encontrei uma porta livre para iniciar este sistema." };
  if (system) {
    if (port !== runtime.port) {
      system.port = port;
      system.accessUrl = `http://127.0.0.1:${port}`;
      await writeCustomSystems(systems);
      runtime.port = port;
    }
    await writeRuntimePortToProject(system, port);
  }

  const command = commandWithProjectPort([runtime.command, ...runtime.args], runtime.port);
  const child = spawnSystemCommand(command[0], command.slice(1), {
    cwd: runtime.cwd,
    env: { ...process.env, ...runtime.env, PORT: String(runtime.port) },
    logId: id
  });

  let spawnError: string | undefined;
  processes.set(id, child);
  child.on("exit", () => processes.delete(id));
  child.on("error", (error) => {
    spawnError = error.message;
    processes.delete(id);
  });

  const startedAt = Date.now();
  let opened = false;
  while (!spawnError && child.pid && Date.now() - startedAt < 8000) {
    if (child.exitCode !== null || child.signalCode !== null) break;
    if (await isPortOpen(runtime.port, "127.0.0.1", 500)) {
      opened = true;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  if (!opened) {
    if (child.pid && !spawnError) terminateProcess(child.pid);
    processes.delete(id);
    return {
      started: false,
      message: spawnError ?? readStartError(id) ?? "O processo iniciou mas não abriu a porta."
    };
  }

  return { started: true };
}

export async function stop(id: string): Promise<{ stopped: boolean; message?: string }> {
  const runtime = (await getRuntimes())[id];
  if (!runtime) {
    return { stopped: false, message: "Sistema sem configuração local." };
  }

  const tracked = processes.get(id);
  const pids = new Set<number>();
  if (tracked?.pid) pids.add(tracked.pid);
  for (const pid of listenerPidsForPort(runtime.port)) pids.add(pid);

  if (pids.size === 0) {
    return { stopped: false, message: "Nenhum processo do sistema foi encontrado." };
  }

  const failed: number[] = [];
  for (const pid of pids) {
    if (!terminateProcess(pid)) failed.push(pid);
  }
  processes.delete(id);

  if (failed.length > 0) {
    return { stopped: false, message: `Não consegui encerrar o processo ${failed.join(", ")}.` };
  }
  return { stopped: true };
}

async function killProcessTree(pid: number): Promise<void> {
  terminateProcess(pid);
}

async function runPreparationCommand(
  command: string[],
  cwd: string,
  env: NodeJS.ProcessEnv,
  logId: string,
  timeoutMs = 300000
): Promise<boolean> {
  return new Promise((resolve) => {
    let finished = false;
    const child = spawnSystemCommand(command[0], command.slice(1), { cwd, env, logId });
    const finish = (ok: boolean) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(ok);
    };
    const timer = setTimeout(() => {
      if (child.pid) void killProcessTree(child.pid);
      finish(false);
    }, timeoutMs);
    child.once("error", () => finish(false));
    child.once("exit", (code) => finish(code === 0));
  });
}

async function prepareProjectDependencies(
  system: CustomSystem,
  cwd: string
): Promise<{ command: string[]; error?: string }> {
  const env = { ...process.env, ...system.env };
  const command = [...(system.startCommand ?? [])];
  const projectRoot = resolveProjectDir(system.id);
  const manifestDir = await findProjectRoot(cwd, projectRoot);

  const nodeMarker = path.join(manifestDir, ".portal-node-dependencies-installed");
  if (await fileExists(path.join(manifestDir, "package.json")) && (!existsSync(nodeMarker) || !existsSync(path.join(manifestDir, "node_modules")))) {
    const installCommand = await getDependencyInstallCommand(system.id, path.relative(projectRoot, manifestDir));
    if (!installCommand) return { command, error: "Não consegui identificar como preparar as dependências do Node.js." };
    const installed = await runPreparationCommand(installCommand, manifestDir, env, system.id);
    if (!installed) return { command, error: "Não consegui instalar as dependências do Node.js. Confira portal-err.log na pasta do projeto." };
    writeFileSync(nodeMarker, new Date().toISOString(), "utf8");
  }

  const requirements = path.join(manifestDir, "requirements.txt");
  const pyproject = path.join(manifestDir, "pyproject.toml");
  const baseCommandName = command.length > 0 ? path.basename(command[0]).toLowerCase() : "";
  const isPythonCommand = /^(python(3)?(\.exe)?|py\.exe)$/.test(baseCommandName);
  if (isPythonCommand) {
    const commandPath = command[0];
    const configuredPythonWorks = await runPreparationCommand([commandPath, "--version"], manifestDir, env, system.id, 10000);
    if (!configuredPythonWorks) {
      const windowsPython = path.join(process.env.LOCALAPPDATA ?? "", "Programs", "Python");
      const candidates = process.platform === "win32"
        ? [
            path.join(windowsPython, "Python314", "python.exe"),
            path.join(windowsPython, "Python313", "python.exe"),
            path.join(windowsPython, "Python312", "python.exe"),
            "C:\\Program Files\\Python314\\python.exe",
            "C:\\Program Files\\Python313\\python.exe",
            "C:\\Program Files\\Python312\\python.exe"
          ]
        : ["python3", "python"];
      const installedPython = candidates.find((candidate) => existsSync(candidate));
      if (!installedPython) return { command, error: "Python não está instalado ou o caminho configurado não funciona. Instale o Python e tente novamente." };
      command[0] = installedPython;
    }
  }
  const hasPythonDependencies = (existsSync(requirements) || existsSync(pyproject)) && /^(python(3)?(\.exe)?|py\.exe)$/.test(path.basename(command[0]).toLowerCase());
  if (hasPythonDependencies) {
    const managedEnv = path.join(manifestDir, ".portal-venv");
    const managedPython = managedPythonPath(manifestDir);
    const marker = path.join(managedEnv, ".portal-dependencies-installed");
    if (!existsSync(marker) || !existsSync(managedPython)) {
      if (!existsSync(managedPython)) {
        const baseName = path.basename(command[0]).toLowerCase();
        const isPythonName = /^(python(3)?(\.exe)?|py\.exe)$/.test(baseName);
        const fallbackPython = process.platform === "win32" ? "python.exe" : "python3";
        const basePython = isPythonName && (path.dirname(command[0]) === "." || existsSync(command[0])) ? command[0] : fallbackPython;
        const created = await runPreparationCommand([basePython, "-m", "venv", ".portal-venv"], manifestDir, env, system.id);
        if (!created || !existsSync(managedPython)) {
          return { command, error: "Não consegui criar o ambiente Python. Confira se o Python está instalado e veja portal-err.log." };
        }
      }
      const install = existsSync(requirements)
        ? [managedPython, "-m", "pip", "install", "-r", "requirements.txt"]
        : [managedPython, "-m", "pip", "install", "-e", "."];
      const installed = await runPreparationCommand(install, manifestDir, env, system.id);
      if (!installed) return { command, error: "Não consegui instalar as dependências Python. Confira portal-err.log na pasta do projeto." };
      writeFileSync(marker, new Date().toISOString(), "utf8");
    }
    const baseName = path.basename(command[0]).toLowerCase();
    if (/^(python(3)?(\.exe)?|py\.exe)$/.test(baseName)) command[0] = managedPython;
  }

  const startupScript = system.startCommand?.[1] === "run" ? system.startCommand[2] : undefined;
  const buildCommand = await getRequiredBuildCommand(system.id, startupScript, path.relative(projectRoot, manifestDir));
  if (buildCommand) {
    const built = await runPreparationCommand(buildCommand, manifestDir, env, system.id);
    if (!built) return { command, error: "Não consegui gerar a versão de execução do projeto. Confira portal-err.log na pasta do projeto." };
  }

  return { command };
}

async function findProjectRoot(startDir: string, projectRoot: string): Promise<string> {
  const markers = ["package.json", "requirements.txt", "pyproject.toml"];
  const boundary = path.resolve(projectRoot);
  let current = path.resolve(startDir);
  const startRelative = path.relative(boundary, current);
  if (startRelative.startsWith("..") || path.isAbsolute(startRelative)) return current;
  for (let depth = 0; depth < 4; depth += 1) {
    if ((await Promise.all(markers.map((marker) => fileExists(path.join(current, marker))))).some(Boolean)) return current;
    if (current === boundary) break;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return path.resolve(startDir);
}

// Teste obrigatório de inicialização (funciona também para rascunhos):
// inicia o sistema, aguarda a porta abrir e encerra o processo.
export async function validateSystem(
  id: string,
  timeoutMs = 20000
): Promise<{ ok: boolean; message: string }> {
  const all = await listCustomSystems();
  const system = all.find((item) => item.id === id);
  if (!system) return { ok: false, message: "Projeto não encontrado." };
  if (system.type !== "local" || !system.startCommand || system.startCommand.length === 0) {
    return {
      ok: false,
      message: "Ainda não sei ligar este projeto. Pode ser que ele precise de instalação."
    };
  }
  const range = defaultPortRangeForProject(system);
  const selectedPort = await findAvailableProjectPort(
    system.port,
    all.filter((item) => item.id !== id && item.type === "local").map((item) => item.port).filter((value): value is number => value != null),
    range
  );
  if (selectedPort == null) return { ok: false, message: "Não encontrei uma porta livre para testar este projeto." };
  if (system.port !== selectedPort) {
    system.port = selectedPort;
    system.accessUrl = `http://127.0.0.1:${selectedPort}`;
    system.validatedAt = undefined;
    system.status = "draft";
    await writeCustomSystems(all);
  }
  await writeRuntimePortToProject(system, selectedPort);

  const cwd = system.workDir ?? system.sourceFolder ?? process.cwd();

  // Só conta como teste aprovado se a porta estava livre ANTES: assim temos
  // certeza de que foi o projeto que abriu, e não outro programa já rodando.
  const wasOpenBefore = await isPortOpen(system.port, "127.0.0.1", 1200);
  if (wasOpenBefore) {
    return {
      ok: false,
      message:
        "O teste não pôde confirmar: essa porta já estava ocupada antes de começar. Feche o programa e tente de novo."
    };
  }

  const prepared = await prepareProjectDependencies(system, cwd);
  if (prepared.error) return { ok: false, message: prepared.error };
  if (prepared.command.length === 0) return { ok: false, message: "Comando de inicialização inválido." };

  const command = commandWithProjectPort(prepared.command, system.port);
  const child = spawnSystemCommand(command[0], command.slice(1), {
    cwd,
    env: { ...process.env, ...system.env, PORT: String(system.port) },
    logId: id
  });
  processes.set(id, child);
  child.on("exit", () => processes.delete(id));
  child.on("error", () => processes.delete(id));

  const startedAt = Date.now();
  let opened = false;
  while (Date.now() - startedAt < timeoutMs) {
    if (child.exitCode !== null) break;
    if (await isPortOpen(system.port, "127.0.0.1", 1200)) {
      opened = true;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 700));
  }

  const pid = child.pid ?? listenerPidForPort(system.port);
  if (pid) await killProcessTree(pid);
  processes.delete(id);

  if (opened) {
    return { ok: true, message: "Funcionou! O projeto abriu e eu o fechei. Agora você pode publicar." };
  }
  return {
    ok: false,
    message:
      "Não consegui abrir o projeto. Verifique se ele precisa de alguma instalação ou se liga por outro programa."
  };
}

export async function writeRuntimePortToProject(system: Pick<CustomSystem, "workDir" | "sourceFolder" | "startCommand">, port: number): Promise<void> {
  const cwd = system.workDir ?? system.sourceFolder;
  if (!cwd) return;
  const { readFile, writeFile } = await import("fs/promises");
  for (const relative of ["app.py", "main.py", "src/app.py", "src/main.py", "sistema/app.py"]) {
    const appPath = path.join(cwd, relative);
    if (!existsSync(appPath)) continue;
    const source = await readFile(appPath, "utf8");
    const updated = setPythonRunPort(source, port);
    if (updated !== source) await writeFile(appPath, updated, "utf8");
  }
  for (const relative of ["server.js", "index.js", "app.js", "src/server.js", "src/index.js", "src/app.js", "server.ts", "index.ts", "src/server.ts", "src/index.ts"]) {
    const appPath = path.join(cwd, relative);
    if (!existsSync(appPath)) continue;
    const source = await readFile(appPath, "utf8");
    const updated = setNodeServerPort(source, port);
    if (updated !== source) await writeFile(appPath, updated, "utf8");
  }
  if (process.platform === "win32") {
    for (const relative of ["iniciar_sistema.ps1", "sistema/iniciar_sistema.ps1"]) {
      const scriptPath = path.join(cwd, relative);
      if (!existsSync(scriptPath)) continue;
      const source = await readFile(scriptPath, "utf8");
      const updated = source.replace(/(-LocalPort\s+)\d{1,5}\b/g, `$1${port}`);
      if (updated !== source) await writeFile(scriptPath, updated, "utf8");
    }
  }
}
