"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { LockKeyhole, Search } from "lucide-react";
import { categories, systems, type System, type SystemIconName } from "@/data/systems";
import { SystemCard, type SystemStatus } from "@/components/system-card";

function normalizeText(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

type Statuses = Record<string, SystemStatus>;
type PendingSystemAction = {
  id: string;
  name: string;
  action: "start" | "stop";
};

type CustomSystemData = {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: SystemIconName;
  url?: string;
  accessUrl?: string;
  port?: number;
};

// O IP da máquina muda pelo DHCP. Em vez de gravar um IP fixo no catálogo,
// montamos a URL de acesso com o host de quem abriu a página — assim o
// botão "Abrir" funciona de qualquer PC da rede, atual ou futuro.
function resolveAccessUrl(system: CustomSystemData): string | undefined {
  const fallback = system.url ?? system.accessUrl;
  if (typeof window === "undefined") return fallback;
  if (!system.port) return fallback;
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  return `${protocol}//${window.location.hostname}:${system.port}`;
}

export function Catalog() {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("Todos");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [statuses, setStatuses] = useState<Statuses>({});
  const [statusesLoaded, setStatusesLoaded] = useState(false);
  const [customSystems, setCustomSystems] = useState<CustomSystemData[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const actionDialogRef = useRef<HTMLDialogElement>(null);
  const actionPasswordRef = useRef<HTMLInputElement>(null);
  const [pendingAction, setPendingAction] = useState<PendingSystemAction | null>(null);
  const [actionPassword, setActionPassword] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionSubmitting, setActionSubmitting] = useState(false);

  const allSystems = useMemo<System[]>(
    () => [
      ...systems,
      ...customSystems.map((custom) => ({
        id: custom.id,
        name: custom.name,
        description: custom.description,
        category: custom.category,
        icon: custom.icon,
        url: resolveAccessUrl(custom)
      }))
    ],
    [customSystems]
  );

  const allCategories = useMemo(
    () => Array.from(new Set(allSystems.map((system) => system.category))),
    [allSystems]
  );

  const filteredSystems = useMemo(() => {
    const normalizedQuery = normalizeText(query.trim());
    const matched = allSystems.filter((system) => {
      if (activeCategory !== "Todos" && system.category !== activeCategory) return false;
      if (!normalizedQuery) return true;
      return (
        normalizeText(system.name).includes(normalizedQuery) ||
        normalizeText(system.description).includes(normalizedQuery) ||
        normalizeText(system.category).includes(normalizedQuery)
      );
    });
    const featured = matched.filter((system) => system.featured);
    const rest = matched
      .filter((system) => !system.featured)
      .sort((a, b) => Number(favorites.has(b.id)) - Number(favorites.has(a.id)));
    return [...featured, ...rest];
  }, [query, activeCategory, favorites, allSystems]);

  function toggleFavorite(id: string) {
    setFavorites((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      try {
        localStorage.setItem("portal:favorites", JSON.stringify([...next]));
      } catch {
        // armazenamento indisponível
      }
      return next;
    });
  }

  const hasFilters = query.trim().length > 0 || activeCategory !== "Todos";

  const sections = useMemo(() => {
    const ordered = (categories as readonly string[]).filter((category) =>
      filteredSystems.some((system) => system.category === category)
    );
    const extra = Array.from(new Set(filteredSystems.map((system) => system.category))).filter(
      (category) => !(categories as readonly string[]).includes(category)
    );
    const wanted = activeCategory === "Todos" ? [...ordered, ...extra] : [activeCategory];
    return wanted
      .map((category) => ({
        category,
        cards: filteredSystems.filter((system) => system.category === category)
      }))
      .filter((section) => section.cards.length > 0);
  }, [filteredSystems, activeCategory]);

  async function refreshStatuses(): Promise<Statuses | null> {
    try {
      const response = await fetch("/api/systems");
      if (!response.ok) return null;
      const data = (await response.json()) as { statuses: Record<string, boolean> };
      const next: Statuses = {};
      for (const [id, online] of Object.entries(data.statuses)) {
        next[id] = online ? "online" : "offline";
      }
      setStatuses(next);
      setStatusesLoaded(true);
      return next;
    } catch {
      // servidor indisponível: mantém o estado atual
      return null;
    }
  }

  // Fica verificando a cada instante até o sistema alcançar o estado esperado
  // (o projeto pode demorar alguns segundos para abrir a porta).
  async function awaitStatus(id: string, want: "online" | "offline"): Promise<boolean> {
    for (let attempt = 0; attempt < 10; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      const statuses = await refreshStatuses();
      if (statuses?.[id] === want) return true;
    }
    return false;
  }

  useEffect(() => {
    const dialog = actionDialogRef.current;
    if (!dialog) return;
    if (pendingAction && !dialog.open) {
      dialog.showModal();
      actionPasswordRef.current?.focus();
    } else if (!pendingAction && dialog.open) {
      dialog.close();
    }
  }, [pendingAction]);

  function requestSystemAction(action: "start" | "stop", id: string, name: string) {
    setActionPassword("");
    setActionError("");
    setPendingAction({ action, id, name });
  }

  function closeActionDialog() {
    if (actionSubmitting) return;
    setActionPassword("");
    setActionError("");
    setPendingAction(null);
  }

  async function submitSystemAction(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!pendingAction || !actionPassword || actionSubmitting) return;

    const action = pendingAction;
    const password = actionPassword;
    setActionPassword("");
    setActionError("");
    setActionSubmitting(true);

    try {
      const response = await fetch(`/api/systems/${action.id}/${action.action}`, {
        method: "POST",
        headers: { "x-admin-token": password }
      });
      const result = (await response.json()) as { ok?: boolean; message?: string };

      if (response.status === 403) {
        setActionError("Senha incorreta. Confira e tente novamente.");
        return;
      }
      if (!response.ok || !result.ok) {
        setActionError(result.message ?? "Não foi possível executar a ação.");
        return;
      }

      setStatuses((current) => ({ ...current, [action.id]: "loading" }));
      const reached = await awaitStatus(action.id, action.action === "start" ? "online" : "offline");
      if (!reached) {
        setActionError(
          action.action === "start"
            ? "O sistema não chegou a ficar online. Confira o erro em portal-err.log na pasta do sistema."
            : "O sistema não chegou a parar. Verifique o processo na VM."
        );
        return;
      }
      if (action.action === "stop") await refreshStatuses();
      setPendingAction(null);
    } catch {
      setActionError("Não foi possível conectar ao portal. Verifique a conexão e tente novamente.");
    } finally {
      setActionSubmitting(false);
    }
  }

  function clearFilters() {
    setQuery("");
    setActiveCategory("Todos");
    searchInputRef.current?.focus();
  }

  useEffect(() => {
    refreshStatuses();
    const interval = setInterval(refreshStatuses, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetch("/api/custom-systems")
      .then((response) => (response.ok ? response.json() : null))
      .then((data: { systems?: CustomSystemData[] } | null) => {
        if (data?.systems) setCustomSystems(data.systems);
      })
      .catch(() => {
        // servidor indisponível: mantém os sistemas padrão
      });
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("portal:favorites");
      if (raw) {
        const ids = JSON.parse(raw) as string[];
        if (Array.isArray(ids)) setFavorites(new Set(ids));
      }
    } catch {
      // entrada inválida: ignora
    }
  }, []);

  return (
    <section id="sistemas" className="py-6 sm:py-8">
      <div className="search-field relative border border-border bg-card">
        <Search aria-hidden="true" className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
        <input
          id="busca"
          ref={searchInputRef}
          aria-label="Pesquisar sistemas"
          className="w-full bg-transparent py-3 pl-10 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar por nome, categoria ou descrição"
          value={query}
        />
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2" role="group" aria-label="Filtrar por categoria">
        {["Todos", ...allCategories].map((category) => {
          const active = activeCategory === category;
          return (
            <button
              aria-label={`Filtrar por ${category}`}
              aria-pressed={active}
              className={`border-b py-1 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${active ? "border-foreground font-semibold text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
              key={category}
              onClick={() => setActiveCategory(category)}
              type="button"
            >
              {category}
            </button>
          );
        })}
      </div>

      <p className="mb-5 mt-4 text-sm text-muted-foreground" aria-live="polite">
        {filteredSystems.length} {filteredSystems.length === 1 ? "sistema encontrado" : "sistemas encontrados"}
      </p>

      {sections.length > 0 ? (
        <div className="flex flex-col gap-10">
          {sections.map((section) => {
            const sectionId = `section-${section.category.replace(/\s+/g, "").toLowerCase()}`;
            return (
              <section aria-labelledby={sectionId} key={section.category}>
                <div className="flex items-baseline justify-between gap-3 pb-2">
                  <h3 className="font-display text-[15px] font-bold tracking-tight text-foreground" id={sectionId}>
                    {section.category}
                  </h3>
                </div>
                <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {section.cards.map((system) => (
                    <SystemCard
                      isFavorite={favorites.has(system.id)}
                      key={system.id}
                      onStart={() => requestSystemAction("start", system.id, system.name)}
                      onStop={() => requestSystemAction("stop", system.id, system.name)}
                      onToggleFavorite={() => toggleFavorite(system.id)}
                      status={statuses[system.id]}
                      statusReady={statusesLoaded}
                      canManage={statusesLoaded && Object.prototype.hasOwnProperty.call(statuses, system.id)}
                      system={system}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        <div className="border-t border-border py-10">
          <p className="font-display text-lg font-semibold">
            {hasFilters ? "Nenhum sistema corresponde à busca" : "Nenhum sistema publicado ainda"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {hasFilters ? "Tente outro termo ou remova os filtros." : "Os sistemas disponíveis aparecerão aqui."}
          </p>
          {hasFilters && (
            <button
              className="mt-4 border-b border-foreground pb-1 text-sm font-medium hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              onClick={clearFilters}
              type="button"
            >
              Limpar filtros
            </button>
          )}
        </div>
      )}

      <dialog
        aria-labelledby="system-action-title"
        className="fixed inset-0 m-0 h-dvh w-screen max-h-none max-w-none border-0 bg-transparent p-4 backdrop:bg-black/60"
        onCancel={(event) => {
          event.preventDefault();
          closeActionDialog();
        }}
        ref={actionDialogRef}
      >
        {pendingAction && (
          <form
            className="mx-auto mt-[min(20vh,8rem)] w-full max-w-sm border border-border bg-card p-6 text-foreground shadow-xl"
            onSubmit={submitSystemAction}
          >
            <div className="mb-4 flex h-11 w-11 items-center justify-center border border-border text-primary">
              <LockKeyhole aria-hidden="true" size={20} />
            </div>
            <h2 className="font-display text-lg font-bold" id="system-action-title">
              Confirme sua senha
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Digite a senha para {pendingAction.action === "start" ? "iniciar" : "parar"}{" "}
              <strong className="text-foreground">{pendingAction.name}</strong>.
            </p>
            <label className="mt-5 block text-sm font-medium" htmlFor="system-action-password">
              Senha do administrador
            </label>
            <input
              autoComplete="new-password"
              className="mt-2 w-full border border-border bg-background px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
              id="system-action-password"
              onChange={(event) => setActionPassword(event.target.value)}
              ref={actionPasswordRef}
              type="password"
              value={actionPassword}
            />
            {actionError && (
              <p className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
                {actionError}
              </p>
            )}
            <div className="mt-6 flex justify-end gap-2">
              <button
                className="border border-border px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-muted disabled:opacity-60"
                disabled={actionSubmitting}
                onClick={closeActionDialog}
                type="button"
              >
                Cancelar
              </button>
              <button
                className="inline-flex items-center justify-center bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!actionPassword || actionSubmitting}
                type="submit"
              >
                {actionSubmitting ? "Verificando…" : "Continuar"}
              </button>
            </div>
          </form>
        )}
      </dialog>
    </section>
  );
}
