import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { listCustomSystems, writeCustomSystems, type CustomSystem } from "@/server/custom-systems";
import { isAdminAuthorized } from "@/server/auth";
import { bestIconForName } from "@/server/icon-picker";
import { resolveProjectDir } from "@/server/storage-paths";
import { isAllowedWebUrl, isInsideProject, isValidPort, isValidStartCommand } from "@/server/admin-validation";
import { defaultPortRangeForProject } from "@/server/project-detector";

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!(await isAdminAuthorized(request))) {
    return NextResponse.json({ error: "Não autorizado." }, { status: 403 });
  }

  const { id } = await params;
  const all = await listCustomSystems();
  const index = all.findIndex((system) => system.id === id);
  if (index === -1) {
    return NextResponse.json({ error: "Sistema não encontrado." }, { status: 404 });
  }

  let body: Partial<CustomSystem>;
  try {
    body = (await request.json()) as Partial<CustomSystem>;
  } catch {
    return NextResponse.json({ error: "Dados inválidos." }, { status: 400 });
  }

  if (body.name !== undefined && !(typeof body.name === "string" && body.name.trim().length > 0 && body.name.length <= 100)) {
    return NextResponse.json({ error: "O nome deve ter entre 1 e 100 caracteres." }, { status: 400 });
  }
  if (body.description !== undefined && (typeof body.description !== "string" || body.description.length > 1000)) {
    return NextResponse.json({ error: "A descrição pode ter no máximo 1.000 caracteres." }, { status: 400 });
  }
  if (body.category !== undefined && !(typeof body.category === "string" && body.category.trim().length > 0 && body.category.length <= 60)) {
    return NextResponse.json({ error: "A categoria deve ter entre 1 e 60 caracteres." }, { status: 400 });
  }
  if (body.port !== undefined && !isValidPort(body.port)) {
    return NextResponse.json({ error: "A porta deve ser um número entre 1 e 65.535." }, { status: 400 });
  }
  const nextPort = body.port ?? all[index].port;
  const nextCommand = body.startCommand ?? all[index].startCommand;
  if (nextPort != null && all.some((system) => system.id !== id && system.type === "local" && system.port === nextPort)) {
    return NextResponse.json({ error: "Esta porta já está reservada para outro sistema. Escolha uma porta diferente." }, { status: 409 });
  }
  if (body.startCommand !== undefined && !isValidStartCommand(body.startCommand)) {
    return NextResponse.json({ error: "O comando de inicialização é inválido." }, { status: 400 });
  }
  if (body.url !== undefined && body.url !== "" && !isAllowedWebUrl(body.url)) {
    return NextResponse.json({ error: "A URL deve começar com http:// ou https://." }, { status: 400 });
  }
  if (body.accessUrl !== undefined && body.accessUrl !== "" && !isAllowedWebUrl(body.accessUrl)) {
    return NextResponse.json({ error: "A URL de acesso deve começar com http:// ou https://." }, { status: 400 });
  }
  if (body.workDir !== undefined) {
    if (typeof body.workDir !== "string") {
      return NextResponse.json({ error: "A pasta de trabalho é inválida." }, { status: 400 });
    }
    const projectDir = resolveProjectDir(id);
    if (!isInsideProject(projectDir, body.workDir)) {
      return NextResponse.json({ error: "A pasta de trabalho precisa ficar dentro do projeto." }, { status: 400 });
    }
  }
  if (body.status !== undefined && body.status !== "draft" && body.status !== "published") {
    return NextResponse.json({ error: "Status inválido." }, { status: 400 });
  }

  if (body.status === "published") {
    if (!all[index].validatedAt) {
      return NextResponse.json(
        { error: "Passe no teste de inicialização antes de publicar." },
        { status: 400 }
      );
    }
    if (all[index].type !== "local" && !all[index].url && !body.url) {
      return NextResponse.json({ error: "Sistema sem URL nem comando de iniciar." }, { status: 400 });
    }
  }

  if (body.startCommand !== undefined && body.port === undefined && all[index].port != null &&
      all.some((system) => system.id !== id && system.type === "local" && system.port === all[index].port)) {
    const [rangeStart, rangeEnd] = defaultPortRangeForProject({ startCommand: nextCommand, port: nextPort });
    const replacement = Array.from({ length: rangeEnd - rangeStart + 1 }, (_, offset) => rangeStart + offset)
      .find((port) => !all.some((system) => system.id !== id && system.type === "local" && system.port === port));
    if (replacement == null) return NextResponse.json({ error: "Não há portas disponíveis para este sistema." }, { status: 409 });
    body.port = replacement;
    body.accessUrl = `http://127.0.0.1:${replacement}`;
  }

  const updatable: (keyof CustomSystem)[] = [
    "name",
    "description",
    "category",
    "url",
    "startCommand",
    "port",
    "accessUrl",
    "workDir",
    "status"
  ];
  const previousName = all[index].name;
  const previousRuntime = JSON.stringify({ command: all[index].startCommand, port: all[index].port, workDir: all[index].workDir });
  for (const field of updatable) {
    if (body[field] !== undefined) {
      (all[index] as Record<string, unknown>)[field] = body[field];
    }
  }
  const nextRuntime = JSON.stringify({ command: all[index].startCommand, port: all[index].port, workDir: all[index].workDir });
  if (previousRuntime !== nextRuntime) {
    all[index].validatedAt = undefined;
    all[index].status = "draft";
  }
  // Se o nome mudou e o ícone não foi enviado, o portal escolhe o melhor ícone para o novo nome.
  if (body.name && body.name !== previousName && body.icon === undefined) {
    all[index].icon = bestIconForName(body.name);
  }
  all[index].updatedAt = new Date().toISOString();
  await writeCustomSystems(all);

  return NextResponse.json({ system: all[index] });
}

export async function DELETE(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!(await isAdminAuthorized(request))) {
    return NextResponse.json({ error: "Não autorizado." }, { status: 403 });
  }

  const { id } = await params;
  const all = await listCustomSystems();
  const index = all.findIndex((system) => system.id === id);
  if (index === -1) {
    return NextResponse.json({ error: "Sistema não encontrado." }, { status: 404 });
  }

  const [removed] = all.splice(index, 1);
  await writeCustomSystems(all);

  try {
    // O id vem do registro salvo; mesmo assim passa pela validação de caminho
    // para que um registro adulterado nunca apague nada fora da pasta de projetos.
    await fs.rm(resolveProjectDir(removed.id), { recursive: true, force: true });
  } catch {
    // pasta já removida, inacessível ou id inválido — o registro sai do catálogo de qualquer forma
  }

  return NextResponse.json({ ok: true });
}
