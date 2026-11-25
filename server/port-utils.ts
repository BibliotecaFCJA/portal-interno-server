import net from "net";

function canBindPort(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.listen(port, "127.0.0.1", () => {
      server.close((error) => resolve(!error));
    });
  });
}

/** Finds the first registered-free and OS-bindable port in the framework range. */
export async function findAvailableProjectPort(
  preferredPort: number | null | undefined,
  usedPorts: Iterable<number>,
  range: [number, number]
): Promise<number | null> {
  const used = new Set(usedPorts);
  const candidates = [
    ...(preferredPort != null && preferredPort >= 1 && preferredPort <= 65535 ? [preferredPort] : []),
    ...Array.from({ length: range[1] - range[0] + 1 }, (_, offset) => range[0] + offset)
  ];
  const visited = new Set<number>();
  for (const port of candidates) {
    if (visited.has(port) || used.has(port)) continue;
    visited.add(port);
    if (await canBindPort(port)) return port;
  }
  return null;
}

function setPortFlag(args: string[], port: number): string[] {
  const result: string[] = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--port" || arg === "-p") {
      index += 1;
      continue;
    }
    if (arg.startsWith("--port=")) continue;
    result.push(arg);
  }
  return [...result, "--port", String(port)];
}

/** Adds/replaces explicit port arguments for common development servers. */
export function commandWithProjectPort(command: string[], port: number): string[] {
  if (command.length === 0) return command;
  const program = command[0];
  const executable = program.split(/[\\/]/).at(-1)?.toLowerCase() ?? "";
  const args = command.slice(1);
  const commandText = args.join(" ").toLowerCase();

  if (/^python(?:3)?(?:\.exe)?$/.test(executable) && commandText.includes("http.server")) {
    const next = [...args];
    const portIndex = next.findIndex((arg, index) => index > 0 && /^\d{1,5}$/.test(arg));
    if (portIndex >= 0) next[portIndex] = String(port);
    else next.push(String(port));
    return [program, ...next];
  }

  if (executable === "php" && args.includes("-S")) {
    const next = [...args];
    const serverIndex = next.indexOf("-S") + 1;
    if (next[serverIndex]) next[serverIndex] = next[serverIndex].replace(/:\d+$/, `:${port}`);
    return [program, ...next];
  }

  if (["npm", "npm.cmd", "pnpm", "pnpm.cmd", "yarn", "yarn.cmd", "bun", "bun.exe"].includes(executable) && args[0] === "run") {
    const separator = args.indexOf("--");
    const scriptArgs = separator >= 0 ? args.slice(separator + 1) : [];
    const commandArgs = setPortFlag(scriptArgs, port);
    const runArgs = separator >= 0 ? args.slice(0, separator) : args;
    return [program, ...runArgs, "--", ...commandArgs];
  }

  if (/\buvicorn\b/.test(commandText) || /\bflask\b/.test(commandText) || /\b(?:next|vite)(?:\.cmd)?\b/.test(commandText)) {
    return [program, ...setPortFlag(args, port)];
  }

  const runserverIndex = args.findIndex((arg) => arg.toLowerCase() === "runserver");
  if (runserverIndex >= 0) {
    const next = [...args];
    if (next[runserverIndex + 1] && /:\d+$/.test(next[runserverIndex + 1])) {
      next[runserverIndex + 1] = next[runserverIndex + 1].replace(/:\d+$/, `:${port}`);
    } else {
      const host = process.platform === "win32" ? "127.0.0.1" : "0.0.0.0";
      next.splice(runserverIndex + 1, 0, `${host}:${port}`);
    }
    return [program, ...next];
  }

  return command;
}

/** Rewrites or adds the port argument in common Flask app.run(...) calls. */
export function setPythonRunPort(source: string, port: number): string {
  const runPattern = /\.run\s*\(/g;
  let result = "";
  let copiedThrough = 0;
  let match: RegExpExecArray | null;

  while ((match = runPattern.exec(source))) {
    const openParen = runPattern.lastIndex - 1;
    let depth = 1;
    let quote = "";
    let escaped = false;
    let closeParen = -1;
    for (let index = openParen + 1; index < source.length; index += 1) {
      const char = source[index];
      if (quote) {
        if (escaped) escaped = false;
        else if (char === "\\") escaped = true;
        else if (char === quote) quote = "";
        continue;
      }
      if (char === "'" || char === '"') {
        quote = char;
      } else if (char === "#") {
        const lineEnd = source.indexOf("\n", index);
        index = lineEnd < 0 ? source.length : lineEnd;
      } else if (char === "(") {
        depth += 1;
      } else if (char === ")") {
        depth -= 1;
        if (depth === 0) {
          closeParen = index;
          break;
        }
      }
    }
    if (closeParen < 0) continue;

    const callStart = match.index;
    const argsStart = openParen + 1;
    const args = source.slice(argsStart, closeParen);
    const portArgument = /\bport\s*=\s*([^,\n]*)/.exec(args);
    let replacement: string;
    if (portArgument) {
      const valueStart = argsStart + portArgument.index + portArgument[0].length - portArgument[1].length;
      const valueEnd = valueStart + portArgument[1].length;
      replacement = source.slice(callStart, valueStart) + String(port) + source.slice(valueEnd, closeParen + 1);
    } else {
      const trimmedArgs = args.trimEnd();
      const separator = trimmedArgs.length === 0 ? "" : trimmedArgs.endsWith(",") ? " " : ", ";
      replacement = source.slice(callStart, closeParen) + `${separator}port=${port})`;
    }
    result += source.slice(copiedThrough, callStart) + replacement;
    copiedThrough = closeParen + 1;
    runPattern.lastIndex = closeParen + 1;
  }

  const rewrittenRuns = copiedThrough === 0 ? source : result + source.slice(copiedThrough);
  return rewrittenRuns.replace(
    /(\b(?:PORT|port)\s*=\s*int\(\s*os\.(?:environ\.get|getenv)\(\s*["'][A-Z_][A-Z0-9_]*PORT["']\s*,\s*["'])(\d{1,5})(["']\s*\)\s*\))/gi,
    `$1${port}$3`
  );
}

/** Rewrites common hard-coded Node HTTP server port declarations. */
export function setNodeServerPort(source: string, port: number): string {
  return source
    .replace(/((?:const|let|var)\s+PORT\s*=\s*)\d{1,5}\b/g, `$1${port}`)
    .replace(/(\.listen\s*\(\s*)\d{1,5}\b/g, `$1${port}`);
}
