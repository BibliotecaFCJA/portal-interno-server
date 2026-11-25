import { NextResponse } from "next/server";
import { getLocalSystemIds, isOnline } from "@/server/local-systems";

export const dynamic = "force-dynamic";

export async function GET() {
  const ids = await getLocalSystemIds();
  const entries = await Promise.all(ids.map(async (id) => [id, await isOnline(id)] as const));
  const statuses = Object.fromEntries(entries) as Record<string, boolean>;
  return NextResponse.json({ statuses });
}
