import type { SystemIconName } from "@/data/systems";

// Rótulos em português associados a cada ícone disponível.
// A lógica "lê o nome e escolhe" cruza o nome do sistema com estas palavras-chave.
const RULES: { icon: SystemIconName; keywords: string[] }[] = [
  { icon: "Wallet", keywords: ["finan", "caixa", "fiscal", "conta", "pagamento", "nfe", "nota"] },
  { icon: "BarChart3", keywords: ["dado", "dash", "relató", "indicador", "bi ", "grafic", "analític"] },
  { icon: "Users", keywords: ["crm", "cliente", "venda", "relacionamento", "pipeline"] },
  { icon: "UserPlus", keywords: ["rh", "pessoa", "funcionário", "colaborador", "folha", "férias", "admissão"] },
  { icon: "Boxes", keywords: ["estoque", "estoq", "inventário", "depósito", "almox", "produto", "mercado", "mercadinho", "loja", "comerci", "atacad", "varejo", "compra", "catalogo"] },
  { icon: "ClipboardCheck", keywords: ["projeto", "tarefa", "gestão", "linha", "plan", "agenda", "checklist"] },
  { icon: "LifeBuoy", keywords: ["suporte", "chamado", "ticket", "atendimento", "ajuda", "helpdesk"] },
  { icon: "Megaphone", keywords: ["marketing", "campanha", "divulga", "comunica", "midia", "propaganda"] },
  { icon: "ShieldCheck", keywords: ["conform", "auditor", "jurídic", "legal", "segurança", "política", "compliance"] },
  { icon: "MapPin", keywords: ["roteir", "enderec", "endereco", "endereço", "endera", "entrega", "localiza", "mapa", "geo", "frete", "cep"] },
  { icon: "FileImage", keywords: ["marca d", "água", "imagem", "foto", "imagens", "assinatura", "render"] },
  { icon: "Settings", keywords: ["sistema", "portal", "gestor", "interno", "config", "administra", "painel"] }
];

export function bestIconForName(name: string): SystemIconName {
  const normalized = name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase();
  for (const rule of RULES) {
    if (rule.keywords.some((keyword) => normalized.includes(keyword.normalize("NFD").replace(/[\u0300-\u036f]/g, "")))) {
      return rule.icon;
    }
  }
  return "Settings";
}