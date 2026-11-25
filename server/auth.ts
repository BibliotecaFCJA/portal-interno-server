import { timingSafeEqual } from "crypto";

const ADMIN_PASSWORD = process.env.PORTAL_ADMIN_PASSWORD;

export function isAdminConfigured(): boolean {
  return Boolean(ADMIN_PASSWORD);
}

export function isAdminTokenAuthorized(token: string, expectedPassword = ADMIN_PASSWORD): boolean {
  if (!expectedPassword) return false;
  const expected = Buffer.from(expectedPassword);
  const received = Buffer.from(token);
  return received.length === expected.length && timingSafeEqual(received, expected);
}

export async function isAdminAuthorized(request: Request): Promise<boolean> {
  const token = request.headers.get("x-admin-token") ?? "";
  return isAdminTokenAuthorized(token);
}
