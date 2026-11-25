# CHECAGEM BRUTA — portal-interno

Data: 11/09/2026

## Visão geral

Projeto Next.js 14 (App Router) + TypeScript + Tailwind. Catálogo interno de sistemas da empresa com painel de administração `/gestao`. IA local (Ollama) para detectar como iniciar projetos. Binding `127.0.0.1`. Código surpreendentemente limpo para um projeto feito com ajuda de IA.

## CRÍTICOS (corrigir)

### 1. `.env.local` com senha fraca e exposta no repo

- `server/auth.ts:3` lê `PORTAL_ADMIN_PASSWORD` direto do `process.env`.
- A senha `9c617758b7f8f68095` está em `.local`, mas o `.gitignore` a protege. Porém, ela é fraca (16 chars hex, sem símbolos) e está na `AGENTS.md` exposta em texto plano. Qualquer pessoa com acesso ao repo lê.
- **Recomendação:** usar variável de ambiente sem fallback e nunca documentar o valor.

### 2. Race condition no `local-systems.ts:103` — `processes.set(id, child)` sem proteção

- Se alguém chamar `start()` duas vezes rápido, pode spawnar 2 processos para o mesmo ID antes do registro ser atualizado.
- **Fix:** `processes.has(id)` antes do spawn, ou usar um lock por ID.

### 3. Path traversal no upload (`app/api/custom-systems/route.ts:69`)

- `relativePath` vem do `FormData` key (nome do arquivo). Embora `path.sep` seja usado, se um attacker enviar `../../etc/passwd`, o `path.join(projectDir, file.relativePath)` pode escapar do diretório de projeto.
- **Fix:** Validar que o resultado final começa com `storageRoot`:

```ts
const resolved = path.resolve(projectDir, file.relativePath);
if (!resolved.startsWith(path.resolve(storageRoot))) continue;
```

### 4. Start/Stop sem autenticação

- `POST /api/systems/[id]/start` e `/stop` não verificam admin. Qualquer pessoa no PC pode iniciar/parar processos. Segundo o AGENTS.md, isso é "aceitável" por ser `127.0.0.1`, mas é um risco se o binding mudar.

## MÉDIOS

### 5. `gestao/page.tsx:108` — Token em `sessionStorage`

- O token fica na memória da sessão. Se alguém abrir DevTools, lê. Não é um bug grave (é localhost), mas pode ser melhorado com httpOnly cookie via API route intermediária.

### 6. `api/systems/route.ts:8` — Status de TODOS os sistemas sequencialmente

- `isOnline(id)` faz `net.createConnection` para cada ID. Se tiver 50 sistemas, são 50 conexões TCP sequenciais. Poderia usar `Promise.all` ou cache.

### 7. `gestao/page.tsx:218` — `editForm.args.split(/\s+/)` quebra com aspas

- Se o args for `"run" "dev"`, o split por espaço bagunça. Deveria ser um parser mais robusto.

### 8. `server/ai-detector.ts:276` — `JSON.parse` sem try/catch

- Se o Ollama retornar JSON inválido, dá crash. Está dentro de um `try/catch` maior do `generateJson`, mas se o JSON for parcialmente válido pode dar `SyntaxError`.

### 9. `local-systems.ts:123` — `taskkill /F` sem confirmação

- Matar processo com `/F` é bruto. Poderia tentar SIGTERM antes e usar `/F` como fallback.

### 10. `catalog.tsx:148` — Polling a cada 10s para status

- Funcional mas ineficiente. Melhor usar Server-Sent Events (SSE) ou WebSockets se o número de sistemas crescer.

## BAIXOS (melhorias)

### 11. `globals.css:27` — `* { box-sizing: border-box }` desnecessário

- Tailwind já inclui isso no `base`. Redundante.

### 12. `app/page.tsx:31` — Botão "Entrar" com `href="#"`

- Não faz nada. Pode confundir o usuário.

### 13. `data/systems.ts` — Sistemas hardcoded

- São 11 sistemas fictícios (ERP Pro, CRM Connect, etc.) que nunca aparecem no catálogo real (não são publicados). Poluição visual no código.

### 14. `theme-toggle.tsx:13` — `window.matchMedia?.(...)` com optional chaining

- É client component, `window` sempre existe. `?.` é desnecessário mas não causa dano.

### 15. `ai-detector.ts:131` — `totalSize` recebido como propriedade de um objeto que não é usado

- `scored` inclui `totalSize` na Closure mas não é usado em nenhum lugar depois.

## ESTRUTURA / ARQUITETURA

| Ponto | Nota |
|---|---|
| **TypeScript** | Zero erros. Tipagem consistente. |
| **Segurança geral** | Boa. `timingSafeEqual`, sanitização de input da IA, `.env` ignorado, `storage/` fora do git. |
| **Separação** | Clara: `server/` (lógica), `components/` (UI), `app/` (rotas). |
| **Documentação** | `AGENTS.md` excelentemente escrito. |
| **Testes** | Não existem. Nenhum arquivo de teste. |
| **Lint** | `next lint` existe no `package.json` mas não foi configurado (sem `.eslintrc`). |

## VEREDICTO

**Nota: 7.5/10** para um projeto interno feito com IA.

Pontos fortes: segurança acima da média para um app local, boa organização, código legível, sanitização robusta da IA.
Pontos fracos: ausência total de testes, race conditions em processos, path traversal no upload, e nenhuma autenticação nos endpoints de start/stop.
Os 3 primeiros críticos valem a pena corrigir antes de considerar "finalizado".