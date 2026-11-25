"use client";

import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  FolderOpen,
  Loader2,
  Lock,
  Play,
  Trash2,
  Upload,
  X,
  XCircle
} from "lucide-react";
import Link from "next/link";
import { categories } from "@/data/systems";
import { ThemeToggle } from "@/components/theme-toggle";

type CustomSystemView = {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  type: "link" | "local";
  url?: string;
  accessUrl?: string;
  port?: number;
  startCommand?: string[];
  status: "draft" | "published";
  validatedAt?: string | null;
  errorMessage?: string | null;
};

// Arquivos sensíveis que nunca são enviados ao portal: segredos (.env*)
// e chaves/certificados. Bancos de dados acompanham o sistema.
const SENSITIVE_FILE_PATTERNS: RegExp[] = [
  /(^|[\\/])\.env(\.|$)/,
  /\.(key|pem|p12|pfx|crt|cer)$/i
];
const IGNORED_UPLOAD_DIRS = new Set([".git", "node_modules", ".next", ".venv", ".portal-venv", "venv", "__pycache__", "coverage"]);
const MANAGEMENT_TOKEN_KEY = "portal:managementToken";

function isSensitiveFile(relativePath: string): boolean {
  return SENSITIVE_FILE_PATTERNS.some((pattern) => pattern.test(relativePath));
}

export default function Gestao() {
  const [token, setToken] = useState<string>("");
  const [authed, setAuthed] = useState(false);
  const [systems, setSystems] = useState<CustomSystemView[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [validatingIds, setValidatingIds] = useState<Set<string>>(new Set());

  // Novo projeto
  const [newCategory, setNewCategory] = useState("");
  const [newName, setNewName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const pendingSend = useRef<{
    event: React.ChangeEvent<HTMLInputElement>;
    category?: string;
    name?: string;
    id?: string;
  } | null>(null);

  // Edição em linha
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  const availableCategories = Array.from(
    new Set([...categories, ...systems.map((system) => system.category), newCategory].filter(Boolean))
  );
  const orderedSystems = [...systems].sort((left, right) => {
    const rank = (system: CustomSystemView) =>
      system.status === "published" ? 2 : system.validatedAt ? 1 : 0;
    return rank(left) - rank(right);
  });
  const publishedCount = systems.filter((system) => system.status === "published").length;
  const waitingTestCount = systems.filter((system) => system.status !== "published" && !system.validatedAt).length;

  useEffect(() => {
    sessionStorage.removeItem("portal:adminToken");
    const saved = sessionStorage.getItem(MANAGEMENT_TOKEN_KEY);
    if (saved) {
      setToken(saved);
      setAuthed(true);
    }
  }, []);

  useEffect(() => {
    if (authed) loadAll();
  }, [authed]);

  async function loadAll() {
    setLoadingList(true);
    try {
      const response = await fetch("/api/custom-systems?all=1", {
        headers: { "x-admin-token": token }
      });
      if (response.status === 403) {
        setAuthed(false);
        sessionStorage.removeItem(MANAGEMENT_TOKEN_KEY);
        return;
      }
      if (response.ok) {
        const data = (await response.json()) as { systems: CustomSystemView[] };
        setSystems(data.systems);
      }
    } finally {
      setLoadingList(false);
    }
  }

  function show(kind: "ok" | "error", text: string) {
    setFeedback({ kind, text });
  }

  async function handleLogin(value: string) {
    setToken(value);
    setAuthed(true);
    sessionStorage.setItem(MANAGEMENT_TOKEN_KEY, value);
    setFeedback(null);
  }

  function logout() {
    setAuthed(false);
    setToken("");
    sessionStorage.removeItem(MANAGEMENT_TOKEN_KEY);
    setSystems([]);
  }

  function onFolderPicked(event: React.ChangeEvent<HTMLInputElement>) {
    pendingSend.current = { event, category: newCategory, name: newName };
    sendUpload();
  }

  function onUpdateFolderPicked(event: React.ChangeEvent<HTMLInputElement>, systemId: string) {
    pendingSend.current = { event, id: systemId };
    sendUpload();
  }

  async function sendUpload() {
    const pending = pendingSend.current;
    if (!pending) return;
    pendingSend.current = null;
    const files = Array.from(pending.event.target.files ?? []);
    if (files.length === 0) return;

    setUploading(true);
    setFeedback(null);
    let skipped = 0;
    const form = new FormData();
    if (pending.category) form.append("category", pending.category);
    if (pending.name) form.append("name", pending.name);
    if (pending.id) form.append("id", pending.id);
    let envContent: string | null = null;
    for (const file of files) {
      const relative = (file as unknown as { webkitRelativePath?: string }).webkitRelativePath ?? file.name;
      if (relative.split(/[\\/]/).some((part) => IGNORED_UPLOAD_DIRS.has(part.toLowerCase()))) {
        skipped += 1;
        continue;
      }
      if (isSensitiveFile(relative)) {
        // O conteúdo dos arquivos .env vai como campo de texto (para o portal
        // injetar no processo ao iniciar), mas o arquivo nunca é copiado.
        const fileName = relative.split("/").pop()?.split("\\").pop() ?? "";
        if (fileName === ".env" && envContent === null) {
          envContent = await file.text();
        }
        skipped += 1;
        continue;
      }
      form.append(relative, file, relative);
    }
    if (envContent !== null) form.append("envContent", envContent);
    const firstRelative =
      (files[0] as unknown as { webkitRelativePath?: string }).webkitRelativePath ?? "";
    const folderName = firstRelative.split("/")[0] || firstRelative.split("\\")[0] || "";
    if (folderName) form.append("folderName", folderName);

    try {
      const response = await fetch("/api/custom-systems", {
        method: "POST",
        headers: { "x-admin-token": token },
        body: form
      });
      const data = (await response.json()) as { system?: CustomSystemView; error?: string };
      if (response.ok) {
        const note = skipped > 0 ? ` (${skipped} arquivo${skipped > 1 ? "s" : ""} ignorado${skipped > 1 ? "s" : ""}, incluindo dependências, segredos e certificados)` : "";
        show(
          "ok",
          pending.id
            ? `"${data.system?.name ?? "Sistema"}" atualizado. O card foi mantido; teste o sistema antes de publicar novamente.${note}`
            : `"${data.system?.name ?? "Projeto"}" adicionado. Confira os detalhes e faça o teste.${note}`
        );
        if (!pending.id) {
          setNewCategory("");
          setNewName("");
        }
        pending.event.target.value = "";
        loadAll();
      } else {
        show("error", data.error ?? "Falha ao copiar o projeto.");
      }
    } catch {
      show("error", "Erro de conexão ao copiar o projeto.");
    } finally {
      pending.event.target.value = "";
      setUploading(false);
    }
  }

  async function runAction(systemId: string, kind: "validate" | "publish" | "draft" | "delete") {
    const method = kind === "delete" ? "DELETE" : "POST";
    const endpoint =
      kind === "validate"
        ? `/api/custom-systems/${systemId}/validate`
        : `/api/custom-systems/${systemId}`;
    if (kind === "delete" && !confirm("Excluir este projeto definitivamente?")) return;

    if (kind === "validate") {
      setValidatingIds((current) => new Set(current).add(systemId));
      try {
        const response = await fetch(endpoint, { method, headers: { "x-admin-token": token } });
        const data = (await response.json()) as { ok?: boolean; message?: string; error?: string };
        show(response.ok && data.ok ? "ok" : "error", data.message ?? data.error ?? "Não foi possível testar o projeto.");
      } catch {
        show("error", "Erro de conexão ao testar o projeto.");
      } finally {
        setValidatingIds((current) => {
          const next = new Set(current);
          next.delete(systemId);
          return next;
        });
      }
    } else if (kind === "publish" || kind === "draft") {
      const response = await fetch(endpoint, {
        method: "PATCH",
        headers: { "content-type": "application/json", "x-admin-token": token },
        body: JSON.stringify({ status: kind === "publish" ? "published" : "draft" })
      });
      const data = (await response.json()) as { error?: string };
      if (!response.ok) {
        show("error", data.error ?? "Não foi possível salvar.");
      } else {
        show("ok", "Status atualizado.");
      }
    } else {
      await fetch(endpoint, { method, headers: { "x-admin-token": token } });
    }
    loadAll();
  }

  function startEdit(system: CustomSystemView) {
    setEditingId(system.id);
    setEditForm({
      name: system.name,
      description: system.description,
      category: system.category,
      executable: system.startCommand?.[0] ?? "",
      args: (system.startCommand?.slice(1) ?? []).join(" "),
      port: String(system.port ?? ""),
      accessUrl: system.accessUrl ?? ""
    });
  }

  async function saveEdit(systemId: string) {
    const payload = {
      name: editForm.name,
      description: editForm.description,
      category: editForm.category,
      startCommand: [editForm.executable, ...editForm.args.split(/\s+/).filter(Boolean)],
      port: editForm.port ? Number(editForm.port) : undefined,
      accessUrl: editForm.accessUrl
    };
    const response = await fetch(`/api/custom-systems/${systemId}`, {
      method: "PATCH",
      headers: { "content-type": "application/json", "x-admin-token": token },
      body: JSON.stringify(payload)
    });
    const data = (await response.json()) as { error?: string };
    if (!response.ok) {
      show("error", data.error ?? "Não foi possível salvar.");
    } else {
      show("ok", "Dados salvos.");
      setEditingId(null);
    }
    loadAll();
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto min-h-screen max-w-5xl px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight">Gestão</h1>
            {authed && <p className="mt-1 text-sm text-muted-foreground">{loadingList ? "Carregando projetos…" : `${systems.length} projetos · ${publishedCount} publicados · ${waitingTestCount} aguardando teste`}</p>}
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {authed && (
              <button
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:border-primary hover:text-primary"
                onClick={logout}
                type="button"
              >
                <Lock aria-hidden="true" size={14} />
                Sair
              </button>
            )}
            <Link
              className="inline-flex items-center border border-primary bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground transition hover:brightness-110"
              href="/"
            >
              Ver portal
            </Link>
          </div>
        </header>

        {!authed ? (
          <section className="mx-auto mt-16 max-w-md border border-border bg-card p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center border border-border text-primary">
              <Lock aria-hidden="true" size={22} />
            </div>
              <h2 className="font-display text-xl font-bold">Área reservada</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Digite a senha para gerenciar o portal. Se você não sabe a senha, fale com a pessoa que
              cuida do computador.
            </p>
            <div className="mt-6 flex gap-2">
              <input
                aria-label="Senha do administrador"
              className="flex-1 border border-border bg-background px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onChange={(event) => setToken(event.target.value)}
                placeholder="Senha do admin"
                type="password"
                value={token}
              />
              <button
                className="bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:brightness-110"
                onClick={() => handleLogin(token)}
                type="button"
              >
                Entrar
              </button>
            </div>
          </section>
        ) : (
          <>
            {feedback && (
              <div
                className={`mt-5 flex items-center gap-2 rounded-card border px-4 py-3 text-sm font-semibold ${
                  feedback.kind === "ok"
                    ? "border-primary/30 bg-primary/5 text-primary"
                    : "border-red-400/50 bg-red-500/10 text-red-600 dark:text-red-400"
                }`}
                role="alert"
              >
                {feedback.kind === "ok" ? (
                  <CheckCircle2 aria-hidden="true" size={16} />
                ) : (
                  <XCircle aria-hidden="true" size={16} />
                )}
                <span className="flex-1">{feedback.text}</span>
                <button aria-label="Fechar aviso" onClick={() => setFeedback(null)} type="button">
                  <X aria-hidden="true" size={14} />
                </button>
              </div>
            )}

            <section className="mt-6 border border-border bg-card p-5 sm:p-6">
              <h3 className="font-display text-lg font-bold">Adicionar sistema</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Primeiro escolha a pasta. Depois teste o sistema; quando o teste passar, você poderá publicá-lo.
              </p>
              <p className="mt-2 text-xs text-muted-foreground">Na primeira vez, a preparação pode levar alguns minutos.</p>

              <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-end">
                <label className="block flex-1">
                  <span className="mb-1 block text-xs font-bold text-muted-foreground">
                    Nome do projeto
                  </span>
                  <input
                    className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    onChange={(event) => setNewName(event.target.value)}
                    placeholder="Ex.: Endereçamento (se vazio, usa o nome da pasta)"
                    value={newName}
                  />
                </label>
                <label className="block flex-1">
                  <span className="mb-1 block text-xs font-bold text-muted-foreground">
                    Categoria (escolha ou escreva uma nova)
                  </span>
                  <input
                    list="categorias"
                    className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    onChange={(event) => setNewCategory(event.target.value)}
                    placeholder="Ex.: Operações"
                    value={newCategory}
                  />
                  <datalist id="categorias">
                    {availableCategories.map((category) => (
                      <option key={category} value={category} />
                    ))}
                  </datalist>
                </label>
                <div className="flex items-end">
                  <input
                    aria-hidden="true"
                    className="hidden"
                    id="folder-picker"
                    multiple
                    onChange={onFolderPicked}
                    ref={(input) => {
                      if (input) input.setAttribute("webkitdirectory", "");
                    }}
                    type="file"
                  />
                  <label
                    className="inline-flex w-full cursor-pointer items-center justify-center gap-2 border border-primary bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:brightness-110"
                    htmlFor="folder-picker"
                  >
                    {uploading ? (
                      <Loader2 aria-hidden="true" className="animate-spin" size={16} />
                    ) : (
                      <FolderOpen aria-hidden="true" size={16} />
                    )}
                    {uploading ? "Copiando e analisando…" : "Escolher pasta"}
                  </label>
                </div>
              </div>
            </section>

            <section className="mt-8">
              <h2 className="border-b border-border pb-3 font-display text-lg font-bold">
                Projetos {loadingList && <Loader2 aria-hidden="true" className="ml-1 inline animate-spin text-muted-foreground" size={16} />}
              </h2>

              {systems.length === 0 && !loadingList && (
                <p className="mt-3 border-l-2 border-primary pl-4 py-3 text-sm text-muted-foreground">
                  Nenhum projeto cadastrado. Escolha uma pasta acima para adicionar o primeiro.
                </p>
              )}

              <div className="mt-2">
                {orderedSystems.map((system) => {
                  const published = system.status === "published";
                  const tested = Boolean(system.validatedAt);
                  return (
                    <article
                      className="border-b border-border py-5 first:border-t"
                      key={system.id}
                    >
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <h3 className="font-display text-lg font-semibold">{system.name}</h3>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {system.category} · {published ? "Publicado no catálogo" : tested ? "Teste aprovado · pronto para publicar" : "Rascunho · precisa de teste"}
                          </p>
                          <p className="mt-2 text-sm text-muted-foreground">
                            {system.description || "Sem descrição"}
                          </p>
                          {system.errorMessage && (
                            <p className="mt-3 flex items-start gap-2 border-l-2 border-red-500 bg-red-500/5 px-3 py-2 text-xs text-red-700 dark:text-red-300">
                              <XCircle aria-hidden="true" size={12} />
                              {system.errorMessage}
                            </p>
                          )}
                        </div>

                        <div className="flex shrink-0 flex-wrap items-center gap-2">
                          {published ? (
                            <button
                              className="border border-border px-3 py-2 text-sm font-medium hover:border-foreground disabled:opacity-50"
                              disabled={uploading}
                              onClick={() => runAction(system.id, "draft")}
                              type="button"
                            >
                              Voltar a rascunho
                            </button>
                          ) : tested ? (
                            <button
                              className="inline-flex items-center gap-2 border border-primary bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:brightness-110 disabled:opacity-50"
                              disabled={uploading}
                              onClick={() => runAction(system.id, "publish")}
                              type="button"
                            >
                              <CheckCircle2 aria-hidden="true" size={15} />Publicar
                            </button>
                          ) : (
                            <button
                              className="inline-flex items-center gap-2 border border-primary bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:brightness-110 disabled:opacity-50"
                              disabled={uploading || validatingIds.has(system.id)}
                              onClick={() => runAction(system.id, "validate")}
                              type="button"
                            >
                              {validatingIds.has(system.id) ? <Loader2 aria-hidden="true" className="animate-spin" size={15} /> : <Play aria-hidden="true" size={15} />}
                              {validatingIds.has(system.id) ? "Preparando e testando…" : "Testar sistema"}
                            </button>
                          )}

                          <details className="relative">
                            <summary className="cursor-pointer border border-border px-3 py-2 text-sm text-muted-foreground hover:text-foreground">Mais ações</summary>
                            <div className="mt-2 flex flex-wrap items-center gap-2 border border-border bg-background p-3 sm:absolute sm:right-0 sm:z-10 sm:w-64 sm:shadow-md">
                              {system.type === "local" && (
                                <>
                                  <input
                                    aria-hidden="true"
                                    className="hidden"
                                    id={`update-folder-${system.id}`}
                                    multiple
                                    onChange={(event) => onUpdateFolderPicked(event, system.id)}
                                    ref={(input) => {
                                      if (input) input.setAttribute("webkitdirectory", "");
                                    }}
                                    type="file"
                                  />
                                  <label
                                    className={`cursor-pointer border border-border px-3 py-2 text-sm text-muted-foreground hover:text-foreground ${uploading ? "pointer-events-none opacity-50" : ""}`}
                                    htmlFor={`update-folder-${system.id}`}
                                    aria-disabled={uploading}
                                    tabIndex={uploading ? -1 : 0}
                                  >
                                    <Upload aria-hidden="true" className="mr-1 inline" size={14} />Atualizar arquivos
                                  </label>
                                </>
                              )}
                              <button
                                className="border border-border px-3 py-2 text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
                                disabled={uploading}
                                onClick={() => editingId === system.id ? saveEdit(system.id) : startEdit(system)}
                                type="button"
                              >
                                {editingId === system.id ? "Salvar edição" : "Editar detalhes"}
                              </button>
                              <button
                                className="border border-red-500/40 px-3 py-2 text-sm text-red-600 hover:border-red-500 disabled:opacity-50"
                                disabled={uploading}
                                onClick={() => runAction(system.id, "delete")}
                                type="button"
                              >
                                <Trash2 aria-hidden="true" className="mr-1 inline" size={14} />Excluir
                              </button>
                            </div>
                          </details>
                        </div>
                      </div>

                      {editingId === system.id && (
                        <div className="mt-4 border-t border-border pt-4">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <label className="block">
                              <span className="mb-1 block text-xs font-bold text-muted-foreground">Nome</span>
                              <input
                                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                onChange={(event) => setEditForm({ ...editForm, name: event.target.value })}
                                value={editForm.name}
                              />
                            </label>
                            <label className="block">
                              <span className="mb-1 block text-xs font-bold text-muted-foreground">Descrição</span>
                              <input
                                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                onChange={(event) => setEditForm({ ...editForm, description: event.target.value })}
                                value={editForm.description}
                              />
                            </label>
                            <label className="block">
                              <span className="mb-1 block text-xs font-bold text-muted-foreground">Categoria</span>
                              <input
                                list="categorias-edicao"
                                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                onChange={(event) => setEditForm({ ...editForm, category: event.target.value })}
                                value={editForm.category}
                              />
                              <datalist id="categorias-edicao">
                                {availableCategories.map((category) => (
                                  <option key={category} value={category} />
                                ))}
                              </datalist>
                            </label>
                          </div>

                          <div className="mt-4">
                            <button
                              className="text-xs font-bold text-muted-foreground underline underline-offset-2 transition hover:text-primary"
                              onClick={() => setShowAdvanced((show) => !show)}
                              type="button"
                            >
                              {showAdvanced ? "Ocultar opções avançadas" : "Ver opções avançadas"}
                            </button>
                            {showAdvanced && (
                              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                                <label className="block">
                                  <span className="mb-1 block text-xs font-bold text-muted-foreground">
                                    Programa/executável
                                  </span>
                                  <input
                                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                    onChange={(event) => setEditForm({ ...editForm, executable: event.target.value })}
                                    value={editForm.executable}
                                  />
                                </label>
                                <label className="block">
                                  <span className="mb-1 block text-xs font-bold text-muted-foreground">
                                    Argumentos (separados por espaço)
                                  </span>
                                  <input
                                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                    onChange={(event) => setEditForm({ ...editForm, args: event.target.value })}
                                    value={editForm.args}
                                  />
                                </label>
                                <label className="block">
                                  <span className="mb-1 block text-xs font-bold text-muted-foreground">Porta</span>
                                  <input
                                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                    onChange={(event) => setEditForm({ ...editForm, port: event.target.value })}
                                    value={editForm.port}
                                  />
                                </label>
                                <label className="block">
                                  <span className="mb-1 block text-xs font-bold text-muted-foreground">URL de acesso</span>
                                  <input
                                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                    onChange={(event) => setEditForm({ ...editForm, accessUrl: event.target.value })}
                                    value={editForm.accessUrl}
                                  />
                                </label>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
