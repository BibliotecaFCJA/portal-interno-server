import path from "path";

export const MAX_UPLOAD_BYTES = 1024 * 1024 * 1024;
export const MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 16 * 1024 * 1024;
export const MAX_UPLOAD_FILES = 5000;

const IGNORED_DIRS = new Set([
  ".git",
  "node_modules",
  ".next",
  ".venv",
  ".portal-venv",
  "venv",
  "__pycache__",
  "coverage"
]);

const SENSITIVE_FILE_PATTERNS = [
  /(^|[\\/])\.env(\.|$)/i,
  /\.(key|pem|p12|pfx|crt|cer)$/i
];

export function shouldSkipUploadFile(relativePath: string): boolean {
  const segments = relativePath.split(/[\\/]+/);
  return (
    segments.some((segment) => IGNORED_DIRS.has(segment.toLowerCase())) ||
    SENSITIVE_FILE_PATTERNS.some((pattern) => pattern.test(relativePath))
  );
}

/**
 * Converts a browser-provided relative path into a safe destination inside
 * the selected project. Returns null for ignored, sensitive or escaping paths.
 */
export function getUploadTarget(
  projectDir: string,
  rawRelativePath: string,
  folderName = ""
): string | null {
  if (!rawRelativePath || shouldSkipUploadFile(rawRelativePath)) return null;

  let relativePath = rawRelativePath.replace(/[\\/]+/g, path.sep);
  const folderPrefix = folderName.replace(/[\\/]+/g, path.sep);
  const segments = relativePath.split(path.sep);
  if (folderPrefix && segments[0].toLowerCase() === folderPrefix.toLowerCase()) {
    segments.shift();
  }
  relativePath = segments.join(path.sep);
  if (shouldSkipUploadFile(relativePath)) return null;

  if (!relativePath || relativePath === path.sep) return null;
  const resolvedRoot = path.resolve(projectDir);
  const resolved = path.resolve(resolvedRoot, relativePath);
  if (resolved === resolvedRoot || !resolved.startsWith(resolvedRoot + path.sep)) return null;
  return resolved;
}

export function exceedsUploadLimits(fileCount: number, totalBytes: number, nextSize: number): boolean {
  return fileCount >= MAX_UPLOAD_FILES || totalBytes + nextSize > MAX_UPLOAD_BYTES;
}
