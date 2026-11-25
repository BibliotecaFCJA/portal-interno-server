const app = document.getElementById("app");
const dialog = document.getElementById("dialog");
const dialogContent = document.getElementById("dialog-content");
const toast = document.getElementById("toast");
const columnFields = [
  ["registration", "Registro"],
  ["record_date", "Data do registro"],
  ["author", "Autor"],
  ["title", "Título"],
  ["place", "Local de publicação"],
  ["publisher", "Editora"],
  ["edition", "Edição"],
  ["volume", "Volume"],
  ["number", "Número"],
  ["year", "Ano"],
  ["copy", "Exemplar"],
  ["copies", "Quantidade de exemplares"],
  ["origin", "Origem"],
  ["cutter", "Cutter"],
  ["cdu", "Classificação CDU"],
  ["subjects", "Assuntos"],
  ["location", "Localização"],
  ["type", "Tipologia"],
  ["notes", "Observações"],
];
let currentUser = null;
let csrfToken = "";
let activeView = "dashboard";
let cachedItems = [];
let cachedTypes = [];
let selectedItemType = "";
let toastTimer;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.className = `toast visible${isError ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = "toast"; }, 4200);
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const method = (options.method || "GET").toUpperCase();
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    options.body = JSON.stringify(options.body);
  }
  if (!["GET", "HEAD"].includes(method) && csrfToken) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  const response = await fetch(path, { ...options, method, headers, credentials: "same-origin" });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    if (response.status === 401 && currentUser) {
      currentUser = null;
      csrfToken = "";
      renderLogin();
    }
    throw new Error(payload?.error || `Falha na requisição (${response.status}).`);
  }
  return payload;
}

function renderLogin() {
  app.innerHTML = `
    <main class="auth-wrap">
      <section class="auth-card">
        <div class="auth-mark" aria-hidden="true">▤</div>
        <h1>Acessar o sistema</h1>
        <p>Entre com seu usuário e senha para consultar o acervo.</p>
        <form data-form="login">
          <div class="field"><label for="username">Usuário</label><input id="username" name="username" autocomplete="username" required autofocus></div>
          <div class="field"><label for="password">Senha</label><input id="password" name="password" type="password" autocomplete="current-password" required></div>
          <button class="button full" type="submit">Entrar</button>
        </form>
      </section>
    </main>`;
}

function renderSetup() {
  app.innerHTML = `
    <main class="auth-wrap">
      <section class="auth-card">
        <div class="auth-mark" aria-hidden="true">▤</div>
        <h1>Configuração inicial</h1>
        <p>Crie o primeiro usuário administrador. Guarde a senha em local seguro.</p>
        <form data-form="setup">
          <div class="field"><label for="setup-name">Nome completo</label><input id="setup-name" name="displayName" autocomplete="name" required></div>
          <div class="field"><label for="setup-user">Usuário</label><input id="setup-user" name="username" autocomplete="username" minlength="3" maxlength="40" required></div>
          <div class="field"><label for="setup-password">Senha (mínimo 10 caracteres)</label><input id="setup-password" name="password" type="password" autocomplete="new-password" minlength="10" required></div>
          <button class="button full" type="submit">Criar administrador</button>
        </form>
      </section>
    </main>`;
}

const navigation = [
  ["dashboard", "⌂", "Visão geral"],
  ["items", "▤", "Catálogo"],
  ["reports", "▥", "Relatórios"],
];

function renderShell() {
  const adminNav = currentUser.role === "admin"
    ? `<button class="nav-button${activeView === "users" ? " active" : ""}" data-view="users"><span class="nav-icon">♙</span>Usuários</button>`
    : "";
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand"><img class="brand-logo" src="/fcja-logo.jpg" alt="FCJA"><span>Sistema Biblioteca</span></div>
        <div class="topbar-right">
          <div class="user-chip"><strong>${esc(currentUser.displayName)}</strong><span>${currentUser.role === "admin" ? "Administrador" : "Equipe"}</span></div>
          <button class="button secondary small" data-action="logout">Sair</button>
        </div>
      </header>
      <div class="layout">
        <nav class="sidebar" aria-label="Menu principal">
          ${navigation.map(([view, icon, label]) => `<button class="nav-button${activeView === view ? " active" : ""}" data-view="${view}"><span class="nav-icon">${icon}</span>${label}</button>`).join("")}
          ${adminNav}
        </nav>
        <main class="main-content" id="view-content"><div class="loading">Carregando...</div></main>
      </div>
    </div>`;
  loadView();
}

function pageHeading(title, description, actions = "") {
  return `<div class="page-heading"><div><h1>${title}</h1><p>${description}</p></div><div class="heading-actions">${actions}</div></div>`;
}

function stat(label, value, alert = false) {
  return `<article class="stat-card${alert ? " alert" : ""}"><span>${label}</span><strong>${value}</strong></article>`;
}

async function loadView() {
  const content = document.getElementById("view-content");
  if (!content) return;
  try {
    if (activeView === "dashboard") await renderDashboard(content);
    if (activeView === "items") await renderItems(content);
    if (activeView === "reports") await renderReports(content);
    if (activeView === "users") await renderUsers(content);
  } catch (error) {
    content.innerHTML = `<section class="panel"><p class="empty">${esc(error.message)}</p><button class="button secondary" data-action="reload-view">Tentar novamente</button></section>`;
  }
}

async function renderDashboard(content) {
  const data = await api("/api/dashboard");
  content.innerHTML = `
    ${pageHeading("Visão geral", "Acompanhe o acervo da biblioteca.")}
    <div class="stats-grid stats-grid-summary">
      ${stat("Títulos no catálogo", data.items)}
      ${stat("Exemplares cadastrados", data.copies)}
    </div>
    <section class="panel">
      <div class="panel-heading"><h3>Acervo por tipologia</h3><button class="action-link" data-view="items">Abrir catálogo →</button></div>
      <div class="category-list">${data.categories.map((row) => `<button class="category-card" data-view="items" data-type="${esc(row.type || "")}" aria-label="Abrir tipologia ${esc(row.type || "Sem tipologia")}"><span>${esc(row.type || "Sem tipologia")}</span><strong>${row.count} registro(s)</strong><span class="category-link">Ver esta tipologia →</span></button>`).join("") || `<div class="empty">Nenhum item cadastrado.</div>`}</div>
    </section>`;
}

function categoryTabs(selected = "") {
  const tabs = [`<button class="type-tab${selected ? "" : " active"}" data-action="select-type" data-type="" aria-pressed="${selected ? "false" : "true"}">Todas as tipologias</button>`];
  for (const type of cachedTypes) {
    const active = selected === type;
    tabs.push(`<button class="type-tab${active ? " active" : ""}" data-action="select-type" data-type="${esc(type)}" aria-pressed="${active}">${esc(type)}</button>`);
  }
  return `<div class="type-tabs" role="group" aria-label="Filtrar catálogo por tipologia">${tabs.join("")}</div>`;
}

async function renderItems(content, search = "", selectedType = selectedItemType) {
  const params = new URLSearchParams();
  if (search) params.set("q", search);
  if (selectedType) params.set("type", selectedType);
  const data = await api(`/api/items?${params}`);
  cachedItems = data.items;
  cachedTypes = data.types;
  selectedItemType = selectedType;
  const actions = `${currentUser.role === "admin" ? `<button class="button secondary" data-action="import">Importar planilhas</button>` : ""}<button class="button" data-action="new-item">+ Cadastrar obra</button>`;
  content.innerHTML = `
    ${pageHeading("Catálogo", "Pesquise, consulte e mantenha os registros bibliográficos.", actions)}
    <section class="panel">
      <div class="panel-heading">
        <h3>${data.items.length} registro(s)</h3>
        <div class="toolbar">
          <div class="field"><input id="catalog-search" type="search" placeholder="Título, autor, registro ou assunto" value="${esc(search)}" aria-label="Pesquisar catálogo"></div>
        </div>
      </div>
      ${categoryTabs(selectedType)}
      <div id="catalog-results">${groupedItemTables(data.items)}</div>
    </section>`;
}

function itemRows(items) {
  return items.length
    ? items.map((item) => `<tr>
        <td class="title-cell">${esc(item.title)}<span class="sub-cell">${esc(item.author || "Autor não informado")}</span></td>
        <td>${esc(item.registration || "—")}</td>
        <td>${esc(item.record_date || "—")}</td>
        <td>${esc(item.year || "—")}</td>
        <td>${esc(item.location || "—")}</td>
        <td><span class="badge${item.available < 1 ? " warning" : ""}">${item.available}/${item.copies}</span></td>
        <td class="actions-cell"><button class="action-link" data-action="edit-item" data-id="${item.id}">Editar</button>${currentUser.role === "admin" ? `<button class="action-link danger-text" data-action="delete-item" data-id="${item.id}">Excluir</button>` : ""}</td>
      </tr>`).join("")
    : `<tr><td colspan="7" class="empty">Nenhum registro encontrado.</td></tr>`;
}

function groupedItemTables(items) {
  const grouped = new Map();
  for (const item of items) {
    const type = item.type || "Sem tipologia";
    if (!grouped.has(type)) grouped.set(type, []);
    grouped.get(type).push(item);
  }
  if (!grouped.size) {
    return `<div class="empty">Nenhum registro encontrado.</div>`;
  }
  return [...grouped.entries()].map(([type, group]) => `
    <section class="catalog-group">
      <div class="panel-heading"><h3>${esc(type)}</h3><span class="badge">${group.length} registro(s)</span></div>
      <div class="table-wrap"><table>
        <thead><tr><th>Título / autor</th><th>Registro</th><th>Data do registro · crescente</th><th>Ano</th><th>Localização</th><th>Disponíveis</th><th>Ações</th></tr></thead>
        <tbody>${itemRows(group)}</tbody>
      </table></div>
    </section>`).join("");
}

async function refreshCatalogRows(search, selectedType) {
  const params = new URLSearchParams();
  if (search) params.set("q", search);
  if (selectedType) params.set("type", selectedType);
  const data = await api(`/api/items?${params}`);
  cachedItems = data.items;
  const content = document.getElementById("view-content");
  const results = content?.querySelector("#catalog-results");
  const count = content?.querySelector(".panel-heading h3");
  if (results && count) {
    results.innerHTML = groupedItemTables(data.items);
    count.textContent = `${data.items.length} registro(s)`;
  }
}

async function renderReports(content) {
  const data = await api("/api/reports");
  content.innerHTML = `
    ${pageHeading("Relatórios", "Resumo do acervo e exportação dos dados para planilhas.", `<a class="button" href="/api/reports/export?dataset=items">Exportar catálogo CSV</a>`)}
    <div class="stats-grid stats-grid-summary">${stat("Títulos", data.titles)}</div>
    <section class="panel">
      <div class="panel-heading"><h3>Acervo por tipologia</h3></div>
      <div class="table-wrap"><table><thead><tr><th>Tipologia</th><th>Títulos</th><th>Exemplares</th></tr></thead><tbody>${data.categories.map((row) => `<tr><td>${esc(row.type || "Sem tipologia")}</td><td>${row.titles}</td><td>${row.copies}</td></tr>`).join("") || `<tr><td colspan="3" class="empty">Sem dados disponíveis.</td></tr>`}</tbody></table></div>
    </section>`;
}

async function renderUsers(content) {
  const data = await api("/api/users");
  const rows = data.users.map((user) => `<tr>
    <td class="title-cell">${esc(user.display_name)}<span class="sub-cell">${esc(user.username)}</span></td>
    <td>${user.role === "admin" ? "Administrador" : "Equipe"}</td>
    <td><span class="badge${user.active ? "" : " warning"}">${user.active ? "Ativo" : "Desativado"}</span></td>
    <td>${formatDate(user.created_at)}</td>
    <td class="actions-cell"><button class="action-link" data-action="edit-user" data-id="${user.id}">Editar</button></td>
  </tr>`).join("");
  content.innerHTML = `
    ${pageHeading("Usuários", "Gerencie os acessos e os perfis da equipe.", `<button class="button" data-action="new-user">+ Novo usuário</button>`)}
    <section class="panel"><div class="table-wrap"><table><thead><tr><th>Nome / usuário</th><th>Perfil</th><th>Situação</th><th>Criado em</th><th>Ações</th></tr></thead><tbody>${rows || `<tr><td colspan="5" class="empty">Nenhum usuário cadastrado.</td></tr>`}</tbody></table></div></section>`;
}

function formatDate(value) {
  if (!value) return "—";
  const dateValue = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return Number.isNaN(dateValue.valueOf()) ? esc(value) : new Intl.DateTimeFormat("pt-BR").format(dateValue);
}

function openDialog(title, body) {
  dialogContent.innerHTML = `<h2 class="dialog-title" id="dialog-title">${title}</h2>${body}`;
  dialog.showModal();
}

function itemForm(item = {}) {
  const fields = columnFields.map(([key, label]) => {
    const wide = ["title", "subjects", "notes"].includes(key);
    const value = key === "copies" ? (item[key] ?? 1) : (item[key] ?? "");
    const input = key === "notes" || key === "subjects"
      ? `<textarea name="${key}"${key === "title" ? " required" : ""}>${esc(value)}</textarea>`
      : `<input name="${key}" value="${esc(value)}"${key === "title" ? " required" : ""}${key === "copies" ? ' type="number" min="1" max="10000"' : ""}>`;
    return `<div class="field${wide ? " wide" : ""}"><label>${label}${key === "title" ? " *" : ""}</label>${input}</div>`;
  }).join("");
  return `<form data-form="${item.id ? "edit-item" : "new-item"}" data-id="${item.id || ""}"><div class="form-grid">${fields}</div><div class="form-actions"><button class="button secondary" type="button" data-action="close-dialog">Cancelar</button><button class="button" type="submit">Salvar registro</button></div></form>`;
}

function openUserDialog(user = {}) {
  const passwordForm = user.id ? `
    <section class="panel password-panel">
      <div class="panel-heading"><h3>Alteração de senha</h3></div>
      <p class="muted">Defina uma nova senha para ${esc(user.display_name)}. A senha deve ter ao menos 10 caracteres.</p>
      <form data-form="reset-user-password" data-id="${user.id}">
        <div class="field"><label>Nova senha</label><input name="password" type="password" minlength="10" autocomplete="new-password" required></div>
        <div class="field"><label>Confirmar nova senha</label><input name="confirmPassword" type="password" minlength="10" autocomplete="new-password" required></div>
        <div class="form-actions"><button class="button secondary" type="button" data-action="close-dialog">Cancelar</button><button class="button" type="submit">Alterar senha</button></div>
      </form>
    </section>` : "";
  openDialog(user.id ? "Editar usuário" : "Novo usuário", `
    <form data-form="${user.id ? "edit-user" : "new-user"}" data-id="${user.id || ""}">
      ${user.id ? "" : `<div class="field"><label>Nome de usuário</label><input name="username" minlength="3" maxlength="40" autocomplete="off" required></div>`}
      <div class="field"><label>Nome completo</label><input name="displayName" maxlength="120" value="${esc(user.display_name || "")}" required></div>
      <div class="field"><label>Perfil</label><select name="role"><option value="staff"${user.role === "staff" ? " selected" : ""}>Equipe — catálogo</option><option value="admin"${user.role === "admin" ? " selected" : ""}>Administrador — inclui usuários e importação</option></select></div>
      ${user.id ? `<div class="field"><label>Situação</label><select name="active"><option value="true"${user.active ? " selected" : ""}>Ativo</option><option value="false"${!user.active ? " selected" : ""}>Desativado</option></select></div>` : `<div class="field"><label>Senha (mínimo 10 caracteres)</label><input name="password" type="password" minlength="10" autocomplete="new-password" required></div>`}
      <div class="form-actions"><button class="button secondary" type="button" data-action="close-dialog">Cancelar</button><button class="button" type="submit">Salvar usuário</button></div>
    </form>${passwordForm}`);
}

function formObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

document.addEventListener("click", async (event) => {
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) {
    activeView = viewButton.dataset.view;
    selectedItemType = activeView === "items" ? (viewButton.dataset.type || "") : "";
    renderShell();
    return;
  }
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const { action, id } = button.dataset;
  try {
    if (action === "logout") {
      await api("/api/logout", { method: "POST", body: {} });
      currentUser = null;
      csrfToken = "";
      renderLogin();
    } else if (action === "reload-view") {
      loadView();
    } else if (action === "new-item") {
      openDialog("Cadastrar obra", itemForm());
    } else if (action === "edit-item") {
      const item = cachedItems.find((entry) => entry.id === Number(id));
      if (item) openDialog("Editar obra", itemForm(item));
    } else if (action === "delete-item") {
      if (confirm("Excluir este registro do catálogo?")) {
        await api(`/api/items/${id}`, { method: "DELETE" });
        showToast("Registro excluído.");
        loadView();
      }
    } else if (action === "select-type") {
      selectedItemType = button.dataset.type || "";
      renderItems(
        document.getElementById("view-content"),
        document.getElementById("catalog-search")?.value || "",
        selectedItemType,
      );
    } else if (action === "import") {
      openDialog("Importar planilhas", `<p class="muted">Selecione uma ou mais planilhas XLSX com cabeçalho na primeira linha. Registros já existentes serão ignorados.</p><form data-form="import"><div class="field"><label>Arquivos .xlsx</label><input name="files" type="file" accept=".xlsx" multiple required></div><div class="form-actions"><button class="button secondary" type="button" data-action="close-dialog">Cancelar</button><button class="button" type="submit">Importar</button></div></form>`);
    } else if (action === "new-user") {
      openUserDialog();
    } else if (action === "edit-user") {
      const data = await api("/api/users");
      const user = data.users.find((entry) => entry.id === Number(id));
      if (user) openUserDialog(user);
    } else if (action === "refresh-app") {
      location.reload();
    } else if (action === "close-dialog") {
      dialog.close();
    }
  } catch (error) {
    showToast(error.message, true);
  }
});

app.addEventListener("input", (event) => {
  if (event.target.id === "catalog-search") {
    clearTimeout(event.target.searchTimer);
    const search = event.target.value;
    const type = selectedItemType;
    event.target.searchTimer = setTimeout(() => refreshCatalogRows(search, type), 250);
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-form]");
  if (!form) return;
  event.preventDefault();
  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton) submitButton.disabled = true;
  try {
    const values = formObject(form);
    const type = form.dataset.form;
    if (type === "setup") {
      await api("/api/setup", { method: "POST", body: values });
      await bootstrap();
    } else if (type === "login") {
      await api("/api/login", { method: "POST", body: values });
      await bootstrap();
    } else if (type === "new-item" || type === "edit-item") {
      const id = form.dataset.id;
      await api(id ? `/api/items/${id}` : "/api/items", { method: id ? "PUT" : "POST", body: values });
      dialog.close();
      showToast(id ? "Registro atualizado." : "Obra cadastrada.");
      loadView();
    } else if (type === "import") {
      const body = new FormData(form);
      const result = await api("/api/import", { method: "POST", body });
      dialog.close();
      const failures = result.errors?.length ? ` Há ${result.errors.length} aviso(s); consulte a mensagem detalhada.` : "";
      showToast(`${result.inserted} registro(s) importado(s), ${result.duplicates} duplicado(s) ignorado(s).${failures}`, result.errors?.length > 0);
      if (result.errors?.length) alert(result.errors.join("\n"));
      loadView();
    } else if (type === "new-user") {
      await api("/api/users", { method: "POST", body: values });
      dialog.close();
      showToast("Usuário criado.");
      loadView();
    } else if (type === "edit-user") {
      await api(`/api/users/${form.dataset.id}`, { method: "PATCH", body: { ...values, active: values.active === "true" } });
      dialog.close();
      showToast("Usuário atualizado.");
      loadView();
    } else if (type === "reset-user-password") {
      if (values.password !== values.confirmPassword) {
        throw new Error("A nova senha e a confirmação devem ser iguais.");
      }
      await api(`/api/users/${form.dataset.id}`, {
        method: "POST",
        body: { password: values.password },
      });
      dialog.close();
      if (Number(form.dataset.id) === currentUser.id) {
        currentUser = null;
        csrfToken = "";
        renderLogin();
        showToast("Senha alterada. Entre novamente com a nova senha.");
      } else {
        showToast("Senha alterada. A pessoa precisará entrar novamente.");
      }
    }
  } catch (error) {
    showToast(error.message, true);
    if (submitButton) submitButton.disabled = false;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && dialog.open) dialog.close();
});

async function bootstrap() {
  try {
    const data = await api("/api/me");
    if (data.setupRequired) {
      renderSetup();
      return;
    }
    currentUser = data.user;
    csrfToken = data.csrfToken || "";
    if (!currentUser) {
      renderLogin();
      return;
    }
    activeView = "dashboard";
    renderShell();
  } catch (error) {
    app.innerHTML = `<main class="auth-wrap"><section class="auth-card"><h1>Sistema indisponível</h1><p>${esc(error.message)}</p><button class="button" data-action="refresh-app">Tentar novamente</button></section></main>`;
  }
}

bootstrap();
