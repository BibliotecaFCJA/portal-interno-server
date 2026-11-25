import { NextResponse } from "next/server";
import { getLocalSystem, start } from "@/server/local-systems";
import { isAdminAuthorized } from "@/server/auth";

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!(await isAdminAuthorized(request))) {
    return NextResponse.json(
      { ok: false, message: "Não autorizado. Faça login na Gestão primeiro." },
      { status: 403 }
    );
  }
  const { id } = await params;
  const runtime = await getLocalSystem(id);
  if (!runtime) {
    return NextResponse.json(
      { ok: false, message: "Sistema sem configuração local." },
      { status: 404 }
    );
  }

  const result = await start(id);
  return NextResponse.json({ ok: result.started, message: result.message ?? "Sistema iniciado." });
}