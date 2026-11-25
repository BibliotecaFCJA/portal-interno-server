import path from "path";

export function isValidPort(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 65535;
}

export function isValidStartCommand(value: unknown): value is string[] {
  return Array.isArray(value) && value.length > 0 && value.length <= 100 &&
    value.every((part) => typeof part === "string" && part.trim().length > 0 && part.length <= 500 && !part.includes("\0"));
}

export function isAllowedWebUrl(value: unknown): value is string {
  if (typeof value !== "string" || value === "") return false;
  try {
    return ["http:", "https:"].includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

export function isInsideProject(projectDir: string, workDir: string): boolean {
  const resolvedProject = path.resolve(projectDir);
  const resolvedWork = path.resolve(resolvedProject, workDir);
  return resolvedWork === resolvedProject || resolvedWork.startsWith(resolvedProject + path.sep);
}
