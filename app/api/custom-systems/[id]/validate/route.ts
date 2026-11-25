import { NextResponse } from "next/server";
import { listCustomSystems, writeCustomSystems } from "@/server/custom-systems";
import { isAdminAuthorized } from "@/server/auth";
import { validateSystem } from "@/server/local-systems";

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!(await isAdminAuthorized(request))) {
    return NextResponse.json({ error: "Não autorizado." }, { status: 403 });
  }

  const { id } = await params;
  const beforeValidation = await listCustomSystems();
  if (!beforeValidation.some((system) => system.id === id)) {
    return NextResponse.json({ error: "Sistema não encontrado." }, { status: 404 });
  }

  const result = await validateSystem(id);

  // validateSystem pode descobrir e persistir uma nova porta livre.
  const all = await listCustomSystems();
  const index = all.findIndex((system) => system.id === id);
  if (index === -1) {
    return NextResponse.json({ error: "Sistema removido durante o teste." }, { status: 404 });
  }
  const system = all[index];
  system.validatedAt = result.ok ? new Date().toISOString() : undefined;
  system.errorMessage = result.ok ? null : result.message;
  system.updatedAt = new Date().toISOString();
  await writeCustomSystems(all);

  return NextResponse.json({
    ok: result.ok,
    message: result.message,
    validatedAt: system.validatedAt ?? null,
    errorMessage: system.errorMessage
  });
}
