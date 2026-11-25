export type SystemIconName =
  | "Settings"
  | "Users"
  | "BarChart3"
  | "Wallet"
  | "Boxes"
  | "ClipboardCheck"
  | "UserPlus"
  | "LifeBuoy"
  | "Megaphone"
  | "ShieldCheck"
  | "MapPin"
  | "FileImage";

export type System = {
  id: string;
  name: string;
  description: string;
  icon: SystemIconName;
  category: string;
  url?: string;
  featured?: boolean;
};

export const categories = [
  "Operações",
  "Serviços",
  "Dados",
  "Finanças",
  "Produtividade",
  "Pessoas",
  "TI",
  "Marketing",
  "Jurídico"
] as const;

// Lista vazia de propósito: o catálogo mostra apenas os sistemas reais
// publicados (data/custom-systems.json), não sistemas fictícios.
export const systems: System[] = [];