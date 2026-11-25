module.exports = [
"[externals]/child_process [external] (child_process, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("child_process", () => require("child_process"));

module.exports = mod;
}),
"[externals]/crypto [external] (crypto, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("crypto", () => require("crypto"));

module.exports = mod;
}),
"[externals]/fs [external] (fs, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("fs", () => require("fs"));

module.exports = mod;
}),
"[externals]/net [external] (net, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("net", () => require("net"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/action-async-storage.external.js [external] (next/dist/server/app-render/action-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/action-async-storage.external.js", () => require("next/dist/server/app-render/action-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/runtime-reacts.external.js [external] (next/dist/server/runtime-reacts.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/runtime-reacts.external.js", () => require("next/dist/server/runtime-reacts.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/node:stream [external] (node:stream, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("node:stream", () => require("node:stream"));

module.exports = mod;
}),
"[externals]/path [external] (path, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("path", () => require("path"));

module.exports = mod;
}),
"[project]/app/api/systems/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET,
    "dynamic",
    ()=>dynamic
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$local$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/local-systems.ts [app-route] (ecmascript)");
;
;
const dynamic = "force-dynamic";
async function GET() {
    const ids = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$local$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getLocalSystemIds"])();
    const entries = await Promise.all(ids.map(async (id)=>[
            id,
            await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$local$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["isOnline"])(id)
        ]));
    const statuses = Object.fromEntries(entries);
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
        statuses
    });
}
}),
"[project]/server/custom-systems.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "listCustomSystems",
    ()=>listCustomSystems,
    "listPublishedSystems",
    ()=>listPublishedSystems,
    "toPublicSystem",
    ()=>toPublicSystem,
    "writeCustomSystems",
    ()=>writeCustomSystems
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
;
const filePath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.cwd(), "data", "custom-systems.json");
async function listCustomSystems() {
    try {
        const raw = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(filePath, "utf8");
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch  {
        return [];
    }
}
async function listPublishedSystems() {
    const all = await listCustomSystems();
    return all.filter((system)=>system.status === "published");
}
function toPublicSystem(system, host) {
    const localUrl = host && system.port ? `http://${host}:${system.port}` : system.accessUrl;
    return {
        id: system.id,
        name: system.name,
        description: system.description,
        category: system.category,
        icon: system.icon,
        url: system.url ?? localUrl
    };
}
async function writeCustomSystems(items) {
    await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].mkdir(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].dirname(filePath), {
        recursive: true
    });
    await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].writeFile(filePath, JSON.stringify(items, null, 2), "utf8");
}
}),
"[project]/server/local-systems.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getLocalSystem",
    ()=>getLocalSystem,
    "getLocalSystemIds",
    ()=>getLocalSystemIds,
    "isOnline",
    ()=>isOnline,
    "start",
    ()=>start,
    "stop",
    ()=>stop,
    "validateSystem",
    ()=>validateSystem,
    "writeRuntimePortToProject",
    ()=>writeRuntimePortToProject
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/child_process [external] (child_process, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$net__$5b$external$5d$__$28$net$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/net [external] (net, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/custom-systems.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$storage$2d$paths$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/storage-paths.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$project$2d$detector$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/project-detector.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/port-utils.ts [app-route] (ecmascript)");
;
;
;
;
;
;
;
;
const builtinRuntimes = {};
async function getRuntimes() {
    const runtimes = {
        ...builtinRuntimes
    };
    try {
        const custom = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["listPublishedSystems"])();
        for (const system of custom){
            if (system.type !== "local") continue;
            if (!system.startCommand || system.startCommand.length === 0) continue;
            if (system.port == null) continue;
            const cwd = system.workDir ?? system.sourceFolder ?? process.cwd();
            let command = system.startCommand[0];
            const baseCommand = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].basename(command).toLowerCase();
            const managedPython = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(cwd, ".portal-venv", "Scripts", "python.exe");
            if ([
                "python",
                "python.exe",
                "python3",
                "python3.exe",
                "py.exe"
            ].includes(baseCommand) && (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(managedPython)) {
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
    } catch  {
    // ignora falhas na leitura do arquivo de sistemas custom
    }
    return runtimes;
}
async function getLocalSystem(id) {
    return (await getRuntimes())[id] ?? null;
}
async function getLocalSystemIds() {
    return Object.keys(await getRuntimes());
}
function fileExists(filePath) {
    return (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(filePath);
}
const processes = new Map();
// Node nesta máquina (v24) lança spawn EINVAL ao executar .cmd/.bat direto.
// Contorno confiável: rodar via cmd.exe /d /s /c com aspas corretas (padrão
// usado por cross-spawn/npm). Para programas normais (.exe/.py/venv) usa spawn puro.
function isScriptShim(program) {
    return /\.(cmd|bat)$/i.test(program);
}
function cmdQuote(arg) {
    if (arg && !/[\s"&|<>^%]/.test(arg)) return arg;
    return '"' + arg.replace(/"/g, '""') + '"';
}
function spawnSystemCommand(program, args, options) {
    // A saída NUNCA é descartada ("ignore" trava Flask/Vite no Windows: o filho
    // fica vivo sem abrir a porta). Vai para portal-out.log / portal-err.log
    // dentro da pasta do sistema, que também ajuda a diagnosticar.
    let stdio = "ignore";
    let outFd = -1;
    let errFd = -1;
    if (options.logId) {
        try {
            const dir = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$storage$2d$paths$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["resolveProjectDir"])(options.logId);
            (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["mkdirSync"])(dir, {
                recursive: true
            });
            outFd = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["openSync"])(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(dir, "portal-out.log"), "a");
            errFd = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["openSync"])(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(dir, "portal-err.log"), "a");
            stdio = [
                "ignore",
                outFd,
                errFd
            ];
        } catch  {
            stdio = "ignore";
        }
    }
    const base = {
        cwd: options.cwd,
        env: options.env,
        stdio,
        windowsHide: options.windowsHide ?? true
    };
    let child;
    if (isScriptShim(program)) {
        const commandLine = [
            cmdQuote(program),
            ...args.map(cmdQuote)
        ].join(" ");
        child = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["spawn"])("cmd.exe", [
            "/d",
            "/s",
            "/c",
            commandLine
        ], {
            ...base,
            windowsVerbatimArguments: true
        });
    } else {
        child = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["spawn"])(program, args, base);
    }
    if (outFd >= 0) (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["closeSync"])(outFd);
    if (errFd >= 0) (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["closeSync"])(errFd);
    return child;
}
function tryConnect(host, port, timeoutMs) {
    return new Promise((resolve)=>{
        const socket = __TURBOPACK__imported__module__$5b$externals$5d2f$net__$5b$external$5d$__$28$net$2c$__cjs$29$__["default"].createConnection({
            host,
            port
        });
        const finish = (open)=>{
            socket.destroy();
            resolve(open);
        };
        socket.setTimeout(timeoutMs, ()=>finish(false));
        socket.once("connect", ()=>finish(true));
        socket.once("error", ()=>finish(false));
    });
}
async function isPortOpen(port, host = "127.0.0.1", timeoutMs = 1500) {
    // Servidores amarram no loopback IPv4 (127.0.0.1) ou IPv6 (::1) conforme o
    // runtime — o Vite, por exemplo, usa "localhost" e sobe em ::1. Testa as duas.
    const candidates = host === "127.0.0.1" ? [
        "127.0.0.1",
        "::1"
    ] : [
        host
    ];
    for (const candidate of candidates){
        if (await tryConnect(candidate, port, timeoutMs)) return true;
    }
    return false;
}
function listenerPidForPort(port) {
    try {
        // Sem "-p tcp": esse filtro esconde linhas IPv6 como [::1]:5173 (Vite).
        const output = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["execFileSync"])("netstat", [
            "-ano"
        ], {
            encoding: "utf8",
            windowsHide: true
        });
        for (const line of output.split(/\r?\n/)){
            const parts = line.trim().split(/\s+/);
            if (parts.length < 5) continue;
            const proto = parts[0];
            if (proto !== "TCP" && proto !== "TCPv6") continue;
            if (parts[3] !== "LISTENING") continue;
            const local = parts[1];
            const portMatch = local.match(/:(\d+)$/);
            if (!portMatch || Number(portMatch[1]) !== port) continue;
            // Só endereços locais: 127.0.0.1, ::1 ou todas as interfaces.
            if (local.startsWith("127.0.0.1:") || local.startsWith("[::1]:") || local.startsWith("0.0.0.0:") || local.startsWith("[::]:")) {
                return Number(parts[4]);
            }
        }
    } catch  {
        return null;
    }
    return null;
}
async function isOnline(id) {
    const runtime = (await getRuntimes())[id];
    if (!runtime) return false;
    return isPortOpen(runtime.port);
}
async function start(id) {
    const runtime = (await getRuntimes())[id];
    if (!runtime) {
        return {
            started: false,
            message: "Sistema sem configuração local."
        };
    }
    const tracked = processes.get(id);
    if (tracked && tracked.exitCode === null) {
        return {
            started: false,
            message: "Sistema já está em execução."
        };
    }
    const systems = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["listCustomSystems"])();
    const system = systems.find((item)=>item.id === id);
    const range = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$project$2d$detector$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["defaultPortRangeForProject"])({
        startCommand: system?.startCommand,
        port: runtime.port
    });
    const port = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["findAvailableProjectPort"])(runtime.port, systems.filter((item)=>item.id !== id && item.type === "local").map((item)=>item.port).filter((value)=>value != null), range);
    if (port == null) return {
        started: false,
        message: "Não encontrei uma porta livre para iniciar este sistema."
    };
    if (system) {
        if (port !== runtime.port) {
            system.port = port;
            system.accessUrl = `http://127.0.0.1:${port}`;
            await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["writeCustomSystems"])(systems);
            runtime.port = port;
        }
        await writeRuntimePortToProject(system, port);
    }
    const command = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["commandWithProjectPort"])([
        runtime.command,
        ...runtime.args
    ], runtime.port);
    const child = spawnSystemCommand(command[0], command.slice(1), {
        cwd: runtime.cwd,
        env: {
            ...process.env,
            ...runtime.env,
            PORT: String(runtime.port)
        },
        logId: id
    });
    processes.set(id, child);
    child.on("exit", ()=>processes.delete(id));
    child.on("error", ()=>processes.delete(id));
    return {
        started: true
    };
}
async function stop(id) {
    const runtime = (await getRuntimes())[id];
    if (!runtime) {
        return {
            stopped: false,
            message: "Sistema sem configuração local."
        };
    }
    const tracked = processes.get(id);
    const listenerPid = listenerPidForPort(runtime.port);
    const pids = new Set();
    if (tracked?.pid) pids.add(tracked.pid);
    if (listenerPid) pids.add(listenerPid);
    if (pids.size === 0) {
        return {
            stopped: false,
            message: "Nenhum processo do sistema foi encontrado."
        };
    }
    for (const pid of pids){
        (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["spawnSync"])("taskkill", [
            "/PID",
            String(pid),
            "/T",
            "/F"
        ], {
            stdio: "ignore",
            windowsHide: true
        });
    }
    processes.delete(id);
    return {
        stopped: true
    };
}
async function killProcessTree(pid) {
    try {
        (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["spawnSync"])("taskkill", [
            "/PID",
            String(pid),
            "/T",
            "/F"
        ], {
            stdio: "ignore",
            windowsHide: true
        });
    } catch  {
    // processo já encerrado
    }
}
async function runPreparationCommand(command, cwd, env, logId, timeoutMs = 300000) {
    return new Promise((resolve)=>{
        let finished = false;
        const child = spawnSystemCommand(command[0], command.slice(1), {
            cwd,
            env,
            logId
        });
        const finish = (ok)=>{
            if (finished) return;
            finished = true;
            clearTimeout(timer);
            resolve(ok);
        };
        const timer = setTimeout(()=>{
            if (child.pid) void killProcessTree(child.pid);
            finish(false);
        }, timeoutMs);
        child.once("error", ()=>finish(false));
        child.once("exit", (code)=>finish(code === 0));
    });
}
async function prepareProjectDependencies(system, cwd) {
    const env = {
        ...process.env,
        ...system.env
    };
    const command = [
        ...system.startCommand ?? []
    ];
    const projectRoot = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$storage$2d$paths$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["resolveProjectDir"])(system.id);
    const manifestDir = await findProjectRoot(cwd, projectRoot);
    const nodeMarker = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, ".portal-node-dependencies-installed");
    if (await fileExists(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, "package.json")) && (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(nodeMarker) || !(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, "node_modules")))) {
        const installCommand = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$project$2d$detector$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getDependencyInstallCommand"])(system.id, __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].relative(projectRoot, manifestDir));
        if (!installCommand) return {
            command,
            error: "Não consegui identificar como preparar as dependências do Node.js."
        };
        const installed = await runPreparationCommand(installCommand, manifestDir, env, system.id);
        if (!installed) return {
            command,
            error: "Não consegui instalar as dependências do Node.js. Confira portal-err.log na pasta do projeto."
        };
        (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["writeFileSync"])(nodeMarker, new Date().toISOString(), "utf8");
    }
    const requirements = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, "requirements.txt");
    const pyproject = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, "pyproject.toml");
    const baseCommandName = command.length > 0 ? __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].basename(command[0]).toLowerCase() : "";
    const isPythonCommand = /^(python(3)?(\.exe)?|py\.exe)$/.test(baseCommandName);
    if (isPythonCommand) {
        const commandPath = command[0];
        const configuredPythonWorks = await runPreparationCommand([
            commandPath,
            "--version"
        ], manifestDir, env, system.id, 10000);
        if (!configuredPythonWorks) {
            const windowsPython = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.env.LOCALAPPDATA ?? "", "Programs", "Python");
            const candidates = [
                __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(windowsPython, "Python314", "python.exe"),
                __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(windowsPython, "Python313", "python.exe"),
                __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(windowsPython, "Python312", "python.exe"),
                "C:\\Program Files\\Python314\\python.exe",
                "C:\\Program Files\\Python313\\python.exe",
                "C:\\Program Files\\Python312\\python.exe"
            ];
            const installedPython = candidates.find((candidate)=>(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(candidate));
            if (!installedPython) return {
                command,
                error: "Python não está instalado ou o caminho configurado não funciona. Instale o Python e tente novamente."
            };
            command[0] = installedPython;
        }
    }
    const hasPythonDependencies = ((0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(requirements) || (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(pyproject)) && /^(python(3)?(\.exe)?|py\.exe)$/.test(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].basename(command[0]).toLowerCase());
    if (hasPythonDependencies) {
        const managedEnv = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(manifestDir, ".portal-venv");
        const managedPython = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(managedEnv, "Scripts", "python.exe");
        const marker = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(managedEnv, ".portal-dependencies-installed");
        if (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(marker) || !(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(managedPython)) {
            if (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(managedPython)) {
                const baseName = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].basename(command[0]).toLowerCase();
                const isPythonName = /^(python(3)?(\.exe)?|py\.exe)$/.test(baseName);
                const basePython = isPythonName && (__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].dirname(command[0]) === "." || (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(command[0])) ? command[0] : "python.exe";
                const created = await runPreparationCommand([
                    basePython,
                    "-m",
                    "venv",
                    ".portal-venv"
                ], manifestDir, env, system.id);
                if (!created || !(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(managedPython)) {
                    return {
                        command,
                        error: "Não consegui criar o ambiente Python. Confira se o Python está instalado e veja portal-err.log."
                    };
                }
            }
            const install = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(requirements) ? [
                managedPython,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt"
            ] : [
                managedPython,
                "-m",
                "pip",
                "install",
                "-e",
                "."
            ];
            const installed = await runPreparationCommand(install, manifestDir, env, system.id);
            if (!installed) return {
                command,
                error: "Não consegui instalar as dependências Python. Confira portal-err.log na pasta do projeto."
            };
            (0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["writeFileSync"])(marker, new Date().toISOString(), "utf8");
        }
        const baseName = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].basename(command[0]).toLowerCase();
        if (/^(python(3)?(\.exe)?|py\.exe)$/.test(baseName)) command[0] = managedPython;
    }
    const startupScript = system.startCommand?.[1] === "run" ? system.startCommand[2] : undefined;
    const buildCommand = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$project$2d$detector$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getRequiredBuildCommand"])(system.id, startupScript, __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].relative(projectRoot, manifestDir));
    if (buildCommand) {
        const built = await runPreparationCommand(buildCommand, manifestDir, env, system.id);
        if (!built) return {
            command,
            error: "Não consegui gerar a versão de execução do projeto. Confira portal-err.log na pasta do projeto."
        };
    }
    return {
        command
    };
}
async function findProjectRoot(startDir, projectRoot) {
    const markers = [
        "package.json",
        "requirements.txt",
        "pyproject.toml"
    ];
    const boundary = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(projectRoot);
    let current = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(startDir);
    const startRelative = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].relative(boundary, current);
    if (startRelative.startsWith("..") || __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].isAbsolute(startRelative)) return current;
    for(let depth = 0; depth < 4; depth += 1){
        if ((await Promise.all(markers.map((marker)=>fileExists(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(current, marker))))).some(Boolean)) return current;
        if (current === boundary) break;
        const parent = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].dirname(current);
        if (parent === current) break;
        current = parent;
    }
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(startDir);
}
async function validateSystem(id, timeoutMs = 20000) {
    const all = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["listCustomSystems"])();
    const system = all.find((item)=>item.id === id);
    if (!system) return {
        ok: false,
        message: "Projeto não encontrado."
    };
    if (system.type !== "local" || !system.startCommand || system.startCommand.length === 0) {
        return {
            ok: false,
            message: "Ainda não sei ligar este projeto. Pode ser que ele precise de instalação."
        };
    }
    const range = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$project$2d$detector$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["defaultPortRangeForProject"])(system);
    const selectedPort = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["findAvailableProjectPort"])(system.port, all.filter((item)=>item.id !== id && item.type === "local").map((item)=>item.port).filter((value)=>value != null), range);
    if (selectedPort == null) return {
        ok: false,
        message: "Não encontrei uma porta livre para testar este projeto."
    };
    if (system.port !== selectedPort) {
        system.port = selectedPort;
        system.accessUrl = `http://127.0.0.1:${selectedPort}`;
        system.validatedAt = undefined;
        system.status = "draft";
        await (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$custom$2d$systems$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["writeCustomSystems"])(all);
    }
    await writeRuntimePortToProject(system, selectedPort);
    const cwd = system.workDir ?? system.sourceFolder ?? process.cwd();
    // Só conta como teste aprovado se a porta estava livre ANTES: assim temos
    // certeza de que foi o projeto que abriu, e não outro programa já rodando.
    const wasOpenBefore = await isPortOpen(system.port, "127.0.0.1", 1200);
    if (wasOpenBefore) {
        return {
            ok: false,
            message: "O teste não pôde confirmar: essa porta já estava ocupada antes de começar. Feche o programa e tente de novo."
        };
    }
    const prepared = await prepareProjectDependencies(system, cwd);
    if (prepared.error) return {
        ok: false,
        message: prepared.error
    };
    if (prepared.command.length === 0) return {
        ok: false,
        message: "Comando de inicialização inválido."
    };
    const command = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["commandWithProjectPort"])(prepared.command, system.port);
    const child = spawnSystemCommand(command[0], command.slice(1), {
        cwd,
        env: {
            ...process.env,
            ...system.env,
            PORT: String(system.port)
        },
        logId: id
    });
    processes.set(id, child);
    child.on("exit", ()=>processes.delete(id));
    child.on("error", ()=>processes.delete(id));
    const startedAt = Date.now();
    let opened = false;
    while(Date.now() - startedAt < timeoutMs){
        if (child.exitCode !== null) break;
        if (await isPortOpen(system.port, "127.0.0.1", 1200)) {
            opened = true;
            break;
        }
        await new Promise((resolve)=>setTimeout(resolve, 700));
    }
    const pid = child.pid ?? listenerPidForPort(system.port);
    if (pid) await killProcessTree(pid);
    processes.delete(id);
    if (opened) {
        return {
            ok: true,
            message: "Funcionou! O projeto abriu e eu o fechei. Agora você pode publicar."
        };
    }
    return {
        ok: false,
        message: "Não consegui abrir o projeto. Verifique se ele precisa de alguma instalação ou se liga por outro programa."
    };
}
async function writeRuntimePortToProject(system, port) {
    const cwd = system.workDir ?? system.sourceFolder;
    if (!cwd) return;
    const { readFile, writeFile } = await __turbopack_context__.A("[externals]/fs/promises [external] (fs/promises, cjs, async loader)");
    for (const relative of [
        "app.py",
        "main.py",
        "src/app.py",
        "src/main.py",
        "sistema/app.py"
    ]){
        const appPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(cwd, relative);
        if (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(appPath)) continue;
        const source = await readFile(appPath, "utf8");
        const updated = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["setPythonRunPort"])(source, port);
        if (updated !== source) await writeFile(appPath, updated, "utf8");
    }
    for (const relative of [
        "server.js",
        "index.js",
        "app.js",
        "src/server.js",
        "src/index.js",
        "src/app.js",
        "server.ts",
        "index.ts",
        "src/server.ts",
        "src/index.ts"
    ]){
        const appPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(cwd, relative);
        if (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(appPath)) continue;
        const source = await readFile(appPath, "utf8");
        const updated = (0, __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$port$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["setNodeServerPort"])(source, port);
        if (updated !== source) await writeFile(appPath, updated, "utf8");
    }
    for (const relative of [
        "iniciar_sistema.ps1",
        "sistema/iniciar_sistema.ps1"
    ]){
        const scriptPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(cwd, relative);
        if (!(0, __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["existsSync"])(scriptPath)) continue;
        const source = await readFile(scriptPath, "utf8");
        const updated = source.replace(/(-LocalPort\s+)\d{1,5}\b/g, `$1${port}`);
        if (updated !== source) await writeFile(scriptPath, updated, "utf8");
    }
}
}),
"[project]/server/port-utils.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "commandWithProjectPort",
    ()=>commandWithProjectPort,
    "findAvailableProjectPort",
    ()=>findAvailableProjectPort,
    "setNodeServerPort",
    ()=>setNodeServerPort,
    "setPythonRunPort",
    ()=>setPythonRunPort
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$net__$5b$external$5d$__$28$net$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/net [external] (net, cjs)");
;
function canBindPort(port) {
    return new Promise((resolve)=>{
        const server = __TURBOPACK__imported__module__$5b$externals$5d2f$net__$5b$external$5d$__$28$net$2c$__cjs$29$__["default"].createServer();
        server.once("error", ()=>resolve(false));
        server.listen(port, "127.0.0.1", ()=>{
            server.close((error)=>resolve(!error));
        });
    });
}
async function findAvailableProjectPort(preferredPort, usedPorts, range) {
    const used = new Set(usedPorts);
    const candidates = [
        ...preferredPort != null && preferredPort >= 1 && preferredPort <= 65535 ? [
            preferredPort
        ] : [],
        ...Array.from({
            length: range[1] - range[0] + 1
        }, (_, offset)=>range[0] + offset)
    ];
    const visited = new Set();
    for (const port of candidates){
        if (visited.has(port) || used.has(port)) continue;
        visited.add(port);
        if (await canBindPort(port)) return port;
    }
    return null;
}
function setPortFlag(args, port) {
    const result = [];
    for(let index = 0; index < args.length; index += 1){
        const arg = args[index];
        if (arg === "--port" || arg === "-p") {
            index += 1;
            continue;
        }
        if (arg.startsWith("--port=")) continue;
        result.push(arg);
    }
    return [
        ...result,
        "--port",
        String(port)
    ];
}
function commandWithProjectPort(command, port) {
    if (command.length === 0) return command;
    const program = command[0];
    const executable = program.split(/[\\/]/).at(-1)?.toLowerCase() ?? "";
    const args = command.slice(1);
    const commandText = args.join(" ").toLowerCase();
    if (/^python(?:3)?(?:\.exe)?$/.test(executable) && commandText.includes("http.server")) {
        const next = [
            ...args
        ];
        const portIndex = next.findIndex((arg, index)=>index > 0 && /^\d{1,5}$/.test(arg));
        if (portIndex >= 0) next[portIndex] = String(port);
        else next.push(String(port));
        return [
            program,
            ...next
        ];
    }
    if (executable === "php" && args.includes("-S")) {
        const next = [
            ...args
        ];
        const serverIndex = next.indexOf("-S") + 1;
        if (next[serverIndex]) next[serverIndex] = next[serverIndex].replace(/:\d+$/, `:${port}`);
        return [
            program,
            ...next
        ];
    }
    if ([
        "npm",
        "npm.cmd",
        "pnpm",
        "pnpm.cmd",
        "yarn",
        "yarn.cmd",
        "bun",
        "bun.exe"
    ].includes(executable) && args[0] === "run") {
        const separator = args.indexOf("--");
        const scriptArgs = separator >= 0 ? args.slice(separator + 1) : [];
        const commandArgs = setPortFlag(scriptArgs, port);
        const runArgs = separator >= 0 ? args.slice(0, separator) : args;
        return [
            program,
            ...runArgs,
            "--",
            ...commandArgs
        ];
    }
    if (/\buvicorn\b/.test(commandText) || /\bflask\b/.test(commandText) || /\b(?:next|vite)(?:\.cmd)?\b/.test(commandText)) {
        return [
            program,
            ...setPortFlag(args, port)
        ];
    }
    const runserverIndex = args.findIndex((arg)=>arg.toLowerCase() === "runserver");
    if (runserverIndex >= 0) {
        const next = [
            ...args
        ];
        if (next[runserverIndex + 1] && /:\d+$/.test(next[runserverIndex + 1])) {
            next[runserverIndex + 1] = next[runserverIndex + 1].replace(/:\d+$/, `:${port}`);
        } else {
            next.splice(runserverIndex + 1, 0, `127.0.0.1:${port}`);
        }
        return [
            program,
            ...next
        ];
    }
    return command;
}
function setPythonRunPort(source, port) {
    const runPattern = /\.run\s*\(/g;
    let result = "";
    let copiedThrough = 0;
    let match;
    while(match = runPattern.exec(source)){
        const openParen = runPattern.lastIndex - 1;
        let depth = 1;
        let quote = "";
        let escaped = false;
        let closeParen = -1;
        for(let index = openParen + 1; index < source.length; index += 1){
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
        let replacement;
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
    return rewrittenRuns.replace(/(\b(?:PORT|port)\s*=\s*int\(\s*os\.(?:environ\.get|getenv)\(\s*["'][A-Z_][A-Z0-9_]*PORT["']\s*,\s*["'])(\d{1,5})(["']\s*\)\s*\))/gi, `$1${port}$3`);
}
function setNodeServerPort(source, port) {
    return source.replace(/((?:const|let|var)\s+PORT\s*=\s*)\d{1,5}\b/g, `$1${port}`).replace(/(\.listen\s*\(\s*)\d{1,5}\b/g, `$1${port}`);
}
}),
"[project]/server/project-detector.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "allocateProjectPort",
    ()=>allocateProjectPort,
    "defaultPortRangeForProject",
    ()=>defaultPortRangeForProject,
    "detectProject",
    ()=>detectProject,
    "detectProjectPort",
    ()=>detectProjectPort,
    "getDependencyInstallCommand",
    ()=>getDependencyInstallCommand,
    "getRequiredBuildCommand",
    ()=>getRequiredBuildCommand
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$server$2f$storage$2d$paths$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/server/storage-paths.ts [app-route] (ecmascript)");
;
;
;
const DEFAULT_PORT_RANGES = {
    next: [
        3000,
        3999
    ],
    vite: [
        5173,
        5999
    ],
    python: [
        8000,
        8999
    ],
    node: [
        9000,
        9999
    ]
};
function allocateProjectPort(preferredPort, usedPorts, range = DEFAULT_PORT_RANGES.python) {
    const used = new Set(usedPorts);
    if (preferredPort != null && !used.has(preferredPort)) return preferredPort;
    for(let port = range[0]; port <= range[1]; port += 1){
        if (!used.has(port)) return port;
    }
    throw new Error("Não há portas disponíveis para este tipo de sistema.");
}
function defaultPortRangeForProject(project) {
    const command = project.startCommand?.map((part)=>part.toLowerCase()).join(" ") ?? "";
    if (/\b(?:next|next\.cmd)\b/.test(command) || project.port === 3000) return DEFAULT_PORT_RANGES.next;
    if (/\b(?:vite|vite\.cmd)\b/.test(command) || project.port === 5173 || project.port === 4173) return DEFAULT_PORT_RANGES.vite;
    if (/\bpython(?:\.exe)?\b|\buvicorn\b|\bflask\b/.test(command) || project.port != null && project.port >= 5000 && project.port < 9000) {
        return DEFAULT_PORT_RANGES.python;
    }
    return DEFAULT_PORT_RANGES.node;
}
function inProject(projectId, ...parts) {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(__TURBOPACK__imported__module__$5b$project$5d2f$server$2f$storage$2d$paths$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["PROJECTS_ROOT"], projectId, ...parts);
}
async function readText(projectId, ...parts) {
    try {
        return await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(inProject(projectId, ...parts), "utf8");
    } catch  {
        return null;
    }
}
async function packageManager(projectId, manifest) {
    const declared = manifest.packageManager?.split("@")[0]?.toLowerCase();
    if (declared === "npm" || declared === "pnpm" || declared === "yarn" || declared === "bun") {
        return {
            name: declared,
            executable: declared === "npm" ? "npm.cmd" : declared === "bun" ? "bun.exe" : `${declared}.cmd`
        };
    }
    if (await fileExists(projectId, "pnpm-lock.yaml")) return {
        name: "pnpm",
        executable: "pnpm.cmd"
    };
    if (await fileExists(projectId, "yarn.lock")) return {
        name: "yarn",
        executable: "yarn.cmd"
    };
    if (await fileExists(projectId, "bun.lock") || await fileExists(projectId, "bun.lockb")) {
        return {
            name: "bun",
            executable: "bun.exe"
        };
    }
    return {
        name: "npm",
        executable: "npm.cmd"
    };
}
async function getDependencyInstallCommand(projectId, ...subdir) {
    if (!await fileExists(projectId, ...subdir, "package.json")) return null;
    const packageRaw = await readText(projectId, ...subdir, "package.json");
    if (!packageRaw) return null;
    try {
        const manifest = JSON.parse(packageRaw);
        const manager = await packageManager(projectId, manifest);
        if (manager.name === "npm") {
            const locked = await fileExists(projectId, "package-lock.json") || await fileExists(projectId, "npm-shrinkwrap.json");
            return [
                manager.executable,
                locked ? "ci" : "install"
            ];
        }
        if (manager.name === "pnpm") {
            return [
                manager.executable,
                "install",
                ...await fileExists(projectId, "pnpm-lock.yaml") ? [
                    "--frozen-lockfile"
                ] : []
            ];
        }
        if (manager.name === "yarn") {
            return [
                manager.executable,
                "install",
                ...await fileExists(projectId, "yarn.lock") ? [
                    "--frozen-lockfile"
                ] : []
            ];
        }
        const bunLock = await fileExists(projectId, "bun.lock") || await fileExists(projectId, "bun.lockb");
        return [
            manager.executable,
            "install",
            ...bunLock ? [
                "--frozen-lockfile"
            ] : []
        ];
    } catch  {
        return null;
    }
}
function scriptCommand(manager, scriptName) {
    return [
        manager.executable,
        "run",
        scriptName
    ];
}
async function getRequiredBuildCommand(projectId, startupScript, ...subdir) {
    const packageRaw = await readText(projectId, ...subdir, "package.json");
    if (!packageRaw || !startupScript) return null;
    try {
        const manifest = JSON.parse(packageRaw);
        const scripts = manifest.scripts ?? {};
        if (!scripts.build) return null;
        const launchScript = scripts[startupScript] ?? "";
        const dependencies = {
            ...manifest.dependencies,
            ...manifest.devDependencies
        };
        const needsNextBuild = Boolean(dependencies.next && /\bnext\s+start\b/.test(launchScript)) && !await fileExists(projectId, ...subdir, ".next");
        const usesVitePreview = /\bvite\s+preview\b/.test(launchScript) && !await fileExists(projectId, ...subdir, "dist");
        if (!needsNextBuild && !usesVitePreview) return null;
        const manager = await packageManager(projectId, manifest);
        return scriptCommand(manager, "build");
    } catch  {
        return null;
    }
}
function scriptPort(script) {
    const match = script.match(/(?:--port(?:=|\s+)|(?:^|\s)-p\s+|\bPORT=)(\d{1,5})\b/i);
    if (!match) return null;
    const port = Number(match[1]);
    return port > 0 && port < 65536 ? port : null;
}
async function detectProject(projectId) {
    const suggestion = {};
    const packageRaw = await readText(projectId, "package.json");
    if (packageRaw) {
        try {
            const manifest = JSON.parse(packageRaw);
            suggestion.name = manifest.name;
            const scripts = manifest.scripts ?? {};
            const dependencies = {
                ...manifest.dependencies,
                ...manifest.devDependencies
            };
            const hasVite = Boolean(dependencies.vite || Object.values(scripts).some((script)=>/(^|\s)vite(?:\s|$)/i.test(script)));
            const hasNext = Boolean(dependencies.next);
            const chosenScript = [
                "dev",
                "start",
                "serve",
                "preview"
            ].find((name)=>typeof scripts[name] === "string" && scripts[name].trim().length > 0);
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
        } catch  {
        // Manifesto inválido: tenta reconhecer outro tipo de projeto.
        }
    }
    const pythonResult = await detectPythonProject(projectId);
    if (pythonResult.startCommand) {
        return {
            ...suggestion,
            ...pythonResult,
            name: suggestion.name ?? pythonResult.name
        };
    }
    return {
        ...suggestion,
        name: suggestion.name ?? pythonResult.name ?? projectId
    };
}
async function detectProjectPort(projectDir) {
    const read = async (...parts)=>{
        try {
            return await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(projectDir, ...parts), "utf8");
        } catch  {
            return null;
        }
    };
    for (const relative of [
        "app.py",
        "main.py",
        "sistema/app.py",
        "sistema/main.py"
    ]){
        const source = await read(...relative.split("/"));
        if (!source) continue;
        const matches = [
            ...source.matchAll(/\.run\s*\([\s\S]*?\bport\s*=\s*(\d{1,5})/g)
        ];
        const simple = [
            ...source.matchAll(/\bport\s*=\s*(\d{1,5})/g)
        ].at(-1);
        const match = matches.at(-1) ?? simple;
        const port = match ? Number(match[1]) : NaN;
        if (Number.isInteger(port) && port > 0 && port <= 65535) return port;
    }
    const manifestRaw = await read("package.json");
    if (manifestRaw) {
        try {
            const manifest = JSON.parse(manifestRaw);
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
        } catch  {}
    }
    return null;
}
async function detectPythonProject(projectId) {
    const hasPythonMarker = await hasAnyFile(projectId, [
        "pyproject.toml",
        "requirements.txt",
        "manage.py",
        "app.py",
        "main.py"
    ]);
    if (!hasPythonMarker) return {};
    const python = await firstExistingPython(projectId) ?? "python.exe";
    const manage = await fileExists(projectId, "manage.py");
    if (manage) {
        const port = await detectPythonPort(projectId) ?? 8000;
        return {
            name: projectId,
            startCommand: [
                python,
                "manage.py",
                "runserver",
                `127.0.0.1:${port}`
            ],
            port,
            accessUrl: `http://127.0.0.1:${port}`
        };
    }
    for (const relative of [
        "main.py",
        "app.py",
        "src/main.py",
        "src/app.py"
    ]){
        const code = await readText(projectId, ...relative.split("/"));
        if (!code) continue;
        const hasFastApi = /\bFastAPI\s*\(/.test(code);
        const hasFlask = /(?:\bFlask\s*\(|\bflask\.Flask\s*\(|from\s+flask\s+import)/i.test(code);
        const hasUvicorn = /uvicorn/i.test(await readText(projectId, "requirements.txt") ?? "") || /uvicorn/i.test(await readText(projectId, "pyproject.toml") ?? "");
        const detectedPort = await detectPythonPort(projectId);
        const port = detectedPort ?? (hasFastApi && hasUvicorn ? 8000 : hasFlask ? 5000 : undefined);
        if (hasFlask) {
            const module = relative.replace(/\.py$/, "").replace(/\//g, ".");
            const startCommand = /\bapp\.run\s*\(/.test(code) ? [
                python,
                relative
            ] : [
                python,
                "-m",
                "flask",
                "--app",
                module,
                "run",
                "--host",
                "127.0.0.1",
                "--port",
                String(port ?? 5000)
            ];
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
                startCommand: [
                    python,
                    "-m",
                    "uvicorn",
                    `${module}:app`,
                    "--host",
                    "127.0.0.1",
                    "--port",
                    String(port)
                ],
                port,
                accessUrl: `http://127.0.0.1:${port}`
            };
        }
        return {
            name: projectId,
            startCommand: [
                python,
                relative
            ],
            port,
            accessUrl: port ? `http://127.0.0.1:${port}` : undefined
        };
    }
    return {
        name: projectId
    };
}
async function fileExists(projectId, ...parts) {
    try {
        await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].access(inProject(projectId, ...parts));
        return true;
    } catch  {
        return false;
    }
}
async function hasAnyFile(projectId, names) {
    for (const name of names){
        if (await fileExists(projectId, ...name.split("/"))) return true;
    }
    return false;
}
async function firstExistingPython(projectId) {
    for (const relative of [
        ".venv/Scripts/python.exe",
        "venv/Scripts/python.exe"
    ]){
        if (await fileExists(projectId, ...relative.split("/"))) return inProject(projectId, ...relative.split("/"));
    }
    return null;
}
async function detectPythonPort(projectId) {
    for (const relative of [
        "app.py",
        "main.py",
        "src/app.py",
        "src/main.py"
    ]){
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
async function detectNodePort(projectId) {
    for (const relative of [
        "server.js",
        "index.js",
        "app.js",
        "src/server.js",
        "src/index.js",
        "src/app.js",
        "server.ts",
        "index.ts",
        "src/server.ts",
        "src/index.ts"
    ]){
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
async function detectVitePort(projectId, section) {
    for (const name of [
        "vite.config.ts",
        "vite.config.mts",
        "vite.config.js",
        "vite.config.mjs"
    ]){
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
}),
"[project]/server/storage-paths.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PROJECTS_ROOT",
    ()=>PROJECTS_ROOT,
    "isSafeProjectId",
    ()=>isSafeProjectId,
    "resolveInsideDir",
    ()=>resolveInsideDir,
    "resolveProjectDir",
    ()=>resolveProjectDir
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
const PROJECTS_ROOT = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(process.cwd(), "storage", "projects");
// Só minúsculas, números e hífen, até 32 caracteres — o tamanho exato do
// randomUUID sem hifens usado como id padrão. Isso impede "..", barras
// absolutas e caminhos do Windows sem rejeitar ids gerados pelo próprio portal.
const SAFE_ID = /^[a-z0-9-]{1,32}$/;
function isSafeProjectId(id) {
    return SAFE_ID.test(id);
}
function resolveProjectDir(id) {
    if (!isSafeProjectId(id)) {
        throw new Error(`Id de projeto inválido: ${JSON.stringify(id)}`);
    }
    const resolved = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(PROJECTS_ROOT, id);
    const withinRoot = resolved.startsWith(PROJECTS_ROOT + __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].sep);
    if (!withinRoot) {
        throw new Error("Caminho fora da pasta de projetos.");
    }
    return resolved;
}
function resolveInsideDir(rootDir, relativePath) {
    const normalized = relativePath.replace(/[\\/]+/g, __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].sep).replace(/^([/\\])+/, "");
    if (!normalized || normalized === __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].sep) {
        throw new Error("Caminho de arquivo vazio.");
    }
    const resolvedRoot = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(rootDir);
    const resolved = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(resolvedRoot, normalized);
    if (resolved !== resolvedRoot && !resolved.startsWith(resolvedRoot + __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].sep)) {
        throw new Error(`Caminho de arquivo fora do projeto: ${relativePath}`);
    }
    if (resolved === resolvedRoot) {
        throw new Error("Caminho de arquivo aponta para a própria pasta do projeto.");
    }
    return resolved;
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__18ixpnc._.js.map