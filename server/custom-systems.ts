import { promises as fs } from "fs";
import path from "path";
import type { SystemIconName } from "@/data/systems";

export type CustomSystemStatus = "draft" | "published";

export type CustomSystem = {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: SystemIconName;
  type: "link" | "local";
  url?: string;
  sourceFolder?: string;
  workDir?: string;
  startCommand?: string[];
  accessUrl?: string;
  port?: number;
  // Variáveis de ambiente necessárias para iniciar o projeto
  // (capturadas do .env original; armazenadas localmente, fora do git).
  env?: Record<string, string>;
  status: CustomSystemStatus;
  validatedAt?: string;
  errorMessage?: string | null;
  createdBy?: string;
  createdAt?: string;
  updatedAt?: string;
};

const filePath = path.join(process.cwd(), "data", "custom-systems.json");

export async function listCustomSystems(): Promise<CustomSystem[]> {
  try {
    const raw = await fs.readFile(filePath, "utf8");
    const parsed = JSON.parse(raw) as CustomSystem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function listPublishedSystems(): Promise<CustomSystem[]> {
  const all = await listCustomSystems();
  return all.filter((system) => system.status === "published");
}

// Formato seguro para o catálogo público: não expõe caminhos do servidor,
// comandos ou dados internos de administração.
// O host recebido é o IP/hostname de quem acessou, para que os links dos
// sistemas locais funcionem tanto em 127.0.0.1 quanto na rede local.
export function toPublicSystem(system: CustomSystem, host?: string) {
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

export async function writeCustomSystems(items: CustomSystem[]): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(items, null, 2), "utf8");
}