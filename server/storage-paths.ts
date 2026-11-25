import path from "path";

// Raiz única onde os projetos copiados pelo portal podem existir. Qualquer
// caminho usado em escrita/leitura/exclusão precisa passar por resolveProjectDir.
export const PROJECTS_ROOT = path.resolve(process.cwd(), "storage", "projects");

// Só minúsculas, números e hífen, até 32 caracteres — o tamanho exato do
// randomUUID sem hifens usado como id padrão. Isso impede "..", barras
// absolutas e caminhos do Windows sem rejeitar ids gerados pelo próprio portal.
const SAFE_ID = /^[a-z0-9-]{1,32}$/;

export function isSafeProjectId(id: string): boolean {
  return SAFE_ID.test(id);
}

/**
 * Resolve o diretório de um projeto garantindo que ele fique dentro de
 * PROJECTS_ROOT. Lança se o id for inválido ou tentar escapar da raiz
 * (path traversal via "..", caminho absoluto ou prefixo enganoso como
 * "storage/projectsX").
 */
export function resolveProjectDir(id: string): string {
  if (!isSafeProjectId(id)) {
    throw new Error(`Id de projeto inválido: ${JSON.stringify(id)}`);
  }
  const resolved = path.resolve(PROJECTS_ROOT, id);
  const withinRoot = resolved.startsWith(PROJECTS_ROOT + path.sep);
  if (!withinRoot) {
    throw new Error("Caminho fora da pasta de projetos.");
  }
  return resolved;
}

/**
 * Confirma que um caminho de arquivo vindo do upload não escapa da pasta do
 * projeto. Também bloqueia "..", caminhos absolutos e a segmentação em
 * Windows, que o path.posix do Linux não pegaria.
 */
export function resolveInsideDir(rootDir: string, relativePath: string): string {
  const normalized = relativePath.replace(/[\\/]+/g, path.sep).replace(/^([/\\])+/, "");
  if (!normalized || normalized === path.sep) {
    throw new Error("Caminho de arquivo vazio.");
  }
  const resolvedRoot = path.resolve(rootDir);
  const resolved = path.resolve(resolvedRoot, normalized);
  if (resolved !== resolvedRoot && !resolved.startsWith(resolvedRoot + path.sep)) {
    throw new Error(`Caminho de arquivo fora do projeto: ${relativePath}`);
  }
  if (resolved === resolvedRoot) {
    throw new Error("Caminho de arquivo aponta para a própria pasta do projeto.");
  }
  return resolved;
}