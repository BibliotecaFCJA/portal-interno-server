import {
  Loader2,
  Play,
  Square,
  Star
} from "lucide-react";
import type { System } from "@/data/systems";

export type SystemStatus = "online" | "offline" | "loading";

type SystemCardProps = {
  system: System;
  status?: SystemStatus;
  statusReady?: boolean;
  canManage?: boolean;
  isFavorite?: boolean;
  onStart?: () => void;
  onStop?: () => void;
  onToggleFavorite?: () => void;
};

function StatusLabel({ status }: { status?: SystemStatus }) {
  if (status === "loading") {
    return <span className="inline-flex items-center gap-2 text-xs text-muted-foreground"><Loader2 aria-hidden="true" className="animate-spin" size={13} />Iniciando</span>;
  }
  if (!status) return <span className="text-xs text-muted-foreground">Verificando estado</span>;
  const online = status === "online";
  return (
    <span className={`inline-flex items-center gap-2 text-xs ${online ? "text-emerald-700 dark:text-emerald-400" : "text-muted-foreground"}`}>
      <span aria-hidden="true" className={`status-dot h-2 w-2 rounded-full ${online ? "bg-emerald-500" : "bg-muted-foreground/50"}`} />
      {online ? "Online" : "Offline"}
    </span>
  );
}

export function SystemCard({
  system,
  status,
  statusReady = false,
  canManage = false,
  isFavorite = false,
  onStart,
  onStop,
  onToggleFavorite
}: SystemCardProps) {
  const isLocal = canManage;

  return (
    <article
      className="flex min-h-[200px] flex-col border border-border bg-card p-5 transition-colors hover:border-foreground/35"
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">{system.category}</p>
          <h3 className="mt-2 line-clamp-2 break-words font-display text-xl font-bold leading-tight">{system.name}</h3>
        </div>
        <button
          aria-label={isFavorite ? `Remover ${system.name} dos favoritos` : `Adicionar ${system.name} aos favoritos`}
          aria-pressed={isFavorite}
          className="shrink-0 p-1 text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          onClick={onToggleFavorite}
          type="button"
        >
          <Star aria-hidden="true" className={isFavorite ? "fill-current text-primary" : ""} size={16} />
        </button>
      </header>

      <div className="mt-4 min-h-[3.5rem] text-muted-foreground">
        <p className="line-clamp-3 text-sm leading-6">{system.description}</p>
      </div>

      <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3">
        {isLocal ? <StatusLabel status={status} /> : statusReady ? <span /> : <StatusLabel />}
        <div className="ml-auto flex items-center gap-3">
          {isLocal ? (
            status === "online" ? (
              <>
                <a
                  className="border border-border px-3 py-1.5 text-sm font-medium hover:border-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  href={system.url ?? "#"}
                  onClick={!system.url ? (event) => event.preventDefault() : undefined}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  Abrir
                </a>
                <button
                  aria-label={`Parar sistema: ${system.name}`}
                  className="inline-flex items-center gap-1 border border-border px-2 py-1.5 text-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  onClick={onStop}
                  type="button"
                >
                  <Square aria-hidden="true" size={12} />Parar
                </button>
              </>
            ) : (
              <button
                className="bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
                disabled={!statusReady || status === "loading"}
                onClick={onStart}
                type="button"
              >
                {status === "loading" ? "Iniciando…" : statusReady ? <><Play aria-hidden="true" className="mr-1 inline" size={13} />Iniciar</> : "Aguarde…"}
              </button>
            )
          ) : system.url ? (
            <a
              className="border border-border px-3 py-1.5 text-sm font-medium hover:border-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              href={system.url}
              rel="noopener noreferrer"
              target="_blank"
            >
              Abrir
            </a>
          ) : (
            <span className="text-xs text-muted-foreground">Sem endereço</span>
          )}
        </div>
      </div>
    </article>
  );
}
