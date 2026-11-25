import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import path from "path";
import {
  listCustomSystems,
  listPublishedSystems,
  toPublicSystem,
  writeCustomSystems,
  type CustomSystem
} from "@/server/custom-systems";
import { isAdminAuthorized } from "@/server/auth";
import { defaultPortRangeForProject, detectProject, detectProjectPort, type ProjectSuggestion } from "@/server/project-detector";
import { detectWithAI, isOllamaAvailable } from "@/server/ai-detector";
import { bestIconForName } from "@/server/icon-picker";
import { isSafeProjectId, resolveProjectDir } from "@/server/storage-paths";
import { isOnline, stop } from "@/server/local-systems";
import {
  exceedsUploadLimits,
  getUploadTarget,
  MAX_UPLOAD_BYTES,
  MAX_UPLOAD_FILES,
  MAX_UPLOAD_REQUEST_BYTES
} from "@/server/upload-policy";
import { findAvailableProjectPort } from "@/server/port-utils";
import { writeRuntimePortToProject } from "@/server/local-systems";

export const dynamic = "force-dynamic";

// Converte o conteúdo de um .env em um objeto de variáveis de ambiente.
// Limita o tamanho para evitar abuso e só aceita chaves simples.
function parseEnvContent(raw: string): Record<string, string> | undefined {
  if (!raw || raw.length > 20000) return undefined;
  const env: Record<string, string> = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!match) continue;
    const key = match[1];
    let value = match[2].trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    env[key] = value;
  }
  return Object.keys(env).length > 0 ? env : undefined;
}

// Host real de quem acessou (Host ou X-Forwarded-Host), sem a porta.
// O request.url usaria o bind do servidor (0.0.0.0) e quebraria os links.
function requestHost(request: Request): string | undefined {
  const raw = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  if (!raw) return undefined;
  const host = raw.split(",")[0].trim().replace(/:\d+$/, "");
  if (!host || host === "0.0.0.0" || host === "[::]" || host === "::") return undefined;
  return host;
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  if (url.searchParams.get("all") === "1") {
    if (!(await isAdminAuthorized(request))) {
      return NextResponse.json({ error: "Não autorizado." }, { status: 403 });
    }
    const systems = await listCustomSystems();
    return NextResponse.json({ systems });
  }
  const host = requestHost(request);
  const systems = (await listPublishedSystems()).map((system) => toPublicSystem(system, host));
  return NextResponse.json({ systems });
}

export async function POST(request: Request) {
  if (!(await isAdminAuthorized(request))) {
    return NextResponse.json({ error: "Não autorizado." }, { status: 403 });
  }

  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (contentLength > MAX_UPLOAD_REQUEST_BYTES) {
    return NextResponse.json({ error: "A pasta excede o limite de 1 GB." }, { status: 413 });
  }

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json({ error: "Não foi possível ler os arquivos enviados." }, { status: 400 });
  }
  const name = String(form.get("name") ?? "").trim();
  const category = String(form.get("category") ?? "").trim();
  if (name.length > 100 || category.length > 60) {
    return NextResponse.json({ error: "Nome ou categoria excede o tamanho permitido." }, { status: 400 });
  }
  const rawFolderName = String(form.get("folderName") ?? "").trim();
  const folderName = rawFolderName
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const requestedId = String(form.get("id") ?? "").trim();
  const projectId =
    requestedId === ""
      ? randomUUID().replace(/-/g, "")
      : requestedId.toLowerCase();
  if (!isSafeProjectId(projectId)) {
    return NextResponse.json({ error: "Id de projeto inválido." }, { status: 400 });
  }

  let projectDir: string;
  try {
    projectDir = resolveProjectDir(projectId);
  } catch {
    return NextResponse.json({ error: "Id de projeto inválido." }, { status: 400 });
  }

  const existing = await listCustomSystems();
  const existingIndex = existing.findIndex((item) => item.id === projectId);
  if (requestedId && existingIndex === -1) {
    return NextResponse.json({ error: "Sistema não encontrado para atualização." }, { status: 404 });
  }
  if (requestedId && existing[existingIndex].type !== "local") {
    return NextResponse.json({ error: "Somente sistemas locais podem receber arquivos." }, { status: 400 });
  }

  const files: { target: string; file: Blob }[] = [];
  let totalBytes = 0;
  for (const [key, value] of form.entries()) {
    if (value instanceof Blob) {
      const target = getUploadTarget(projectDir, key, rawFolderName);
      if (!target) continue;
      totalBytes += value.size;
      if (exceedsUploadLimits(files.length, totalBytes - value.size, value.size)) {
        return NextResponse.json({ error: "A pasta excede os limites de envio (1 GB ou 5.000 arquivos)." }, { status: 413 });
      }
      files.push({ target, file: value });
    }
  }

  if (files.length === 0) {
    return NextResponse.json({ error: "Nenhum arquivo foi recebido." }, { status: 400 });
  }

  // O cliente envia o conteúdo do .env original como campo de texto
  // (o arquivo em si nunca é copiado para a pasta do portal).
  const env = parseEnvContent(String(form.get("envContent") ?? ""));

  if (requestedId) {
    const system = existing[existingIndex];
    if (await isOnline(projectId)) {
      const stopped = await stop(projectId);
      if (!stopped.stopped || (await isOnline(projectId))) {
        return NextResponse.json(
          { error: "Não foi possível parar o sistema. Pare-o pelo portal e tente atualizar novamente." },
          { status: 409 }
        );
      }
    }
    system.status = "draft";
    system.validatedAt = undefined;
    system.errorMessage = null;
    system.updatedAt = new Date().toISOString();
    await writeCustomSystems(existing);
    for (const file of files) {
      await fs.mkdir(path.dirname(file.target), { recursive: true });
      await fs.writeFile(file.target, Buffer.from(await file.file.arrayBuffer()));
    }
    if (env) system.env = env;
    system.updatedAt = new Date().toISOString();
    await writeCustomSystems(existing);
    return NextResponse.json({ system });
  }

  for (const file of files) {
    await fs.mkdir(path.dirname(file.target), { recursive: true });
    await fs.writeFile(file.target, Buffer.from(await file.file.arrayBuffer()));
  }

  // Usa o Ollama somente quando as regras locais não encontraram todos os dados.
  // A sugestão determinística permanece preferida; a IA preenche apenas lacunas.
  const fallback = await detectProject(projectId);
  const needsAI = !fallback.startCommand?.length || fallback.port == null;
  const ai = needsAI && (await isOllamaAvailable()) ? await detectWithAI(projectDir) : null;

  const suggestion: ProjectSuggestion = { name: fallback.name };
  suggestion.startCommand = fallback.startCommand?.length
    ? fallback.startCommand
    : ai && ai.startCommand.length > 0 ? ai.startCommand : undefined;
  suggestion.port = fallback.port ?? ai?.port ?? undefined;
  suggestion.accessUrl = fallback.accessUrl ?? ai?.accessUrl ??
    (suggestion.port != null ? `http://127.0.0.1:${suggestion.port}` : undefined);
  if (!suggestion.name) suggestion.name = path.basename(projectDir);

  const preferredPort = await detectProjectPort(projectDir) ?? suggestion.port;
  if (suggestion.startCommand?.length) {
    const range = defaultPortRangeForProject({ startCommand: suggestion.startCommand, port: preferredPort });
    const port = await findAvailableProjectPort(
      preferredPort,
      existing.filter((item) => item.id !== projectId && item.type === "local").map((item) => item.port).filter((value): value is number => value != null),
      range
    );
    if (port == null) {
      return NextResponse.json({ error: "Não encontrei uma porta livre para este sistema." }, { status: 409 });
    }
    suggestion.port = port;
    suggestion.accessUrl = `http://127.0.0.1:${port}`;
    if (port !== preferredPort) {
      await writeRuntimePortToProject({ workDir: projectDir, startCommand: suggestion.startCommand }, port);
    }
  }

  // O nome é escolhido pelo usuário (ou, se vazio, vem do nome da pasta).
  const finalName = name || folderName || suggestion.name || "Sistema sem nome";
  const now = new Date().toISOString();
  const system: CustomSystem = {
    id: projectId,
    name: finalName,
    description: `Sistema local gerenciado pelo portal: ${finalName}.`,
    category: category.trim() || "TI",
    icon: bestIconForName(finalName),
    type: "local",
    sourceFolder: projectDir,
    workDir: projectDir,
    startCommand: suggestion.startCommand ?? [],
    port: suggestion.port,
    accessUrl:
      suggestion.accessUrl ??
      (suggestion.port != null ? `http://127.0.0.1:${suggestion.port}` : undefined),
    env,
    status: "draft",
    errorMessage: null,
    createdAt: now,
    updatedAt: now
  };

  const all = existing.filter((item) => item.id !== projectId);
  all.push(system);
  await writeCustomSystems(all);

  return NextResponse.json({ system }, { status: 201 });
}
