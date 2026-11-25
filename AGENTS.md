# Portal Interno — Memória de Trabalho

Este arquivo existe para que uma nova sessão de chat possa retomar o trabalho com contexto.
Leia este arquivo antes de tocar no projeto.
Histórico completo em `Documents\Relatório\Relatorio-Portal-Interno.txt` (fora do git).

## O que é o projeto
Portal interno (Next.js) que reúne sistemas locais da empresa numa vitrine pública (`/`) com
administração em `/gestao`. Sistemas **locais** são copiados para `storage/projects/<id>`, têm o
comando de iniciar descoberto (IA local), passam por um **Teste real** (sobe e fecha a porta) e só
depois podem ser **Publicados**.

## Stack (05/10/2026)
Next.js **16.3.8** + React **19.3.0** + TypeScript, Tailwind CSS, lucide-react.
`@types/react` e `@types/react-dom` na 19 (alinhadocom o React 19).
Node.js no Windows. IA local via Ollama (modelo `qwen2.5:3b`).

## Como rodar
- **Produção (uso no dia a dia):** `npm run build` e `npm run start`.
  O `start` roda com `-H 0.0.0.0` de propósito: o portal é acessado **na rede local**
  (ex.: `http://192.168.1.208:3000`). Proteções: tudo que mexe em dados pede a senha de admin.
- **Dev (só ao mexer no código):** `npm run dev` — roda preso em `127.0.0.1`.
- Logs em `%TEMP%\portal-dev.log` / `.err.log` (dev) e `%TEMP%\portal-prod.log` (produção).
  Não rodar `next build` com o servidor no ar.
- Checagem de type: `& "C:\Program Files\nodejs\npx.cmd" tsc --noEmit --incremental false`
  (o script `lint` do package.json aponta para este mesmo comando — o `next lint` foi
  removido no Next 16).
- Senha admin: em `.env.local` (não versionado): `PORTAL_ADMIN_PASSWORD=...`, header `x-admin-token`.
  Senha trocada em 30/09 para 32 chars; cópia em `Documents\backup-portal`. **Nunca documentar o valor.**
- IA local: Ollama (`%LOCALAPPDATA%\Programs\Ollama\ollama.exe`, porta 11434).
  1ª análise ~70–80s, seguintes ~30–40s. Internet lenta: não re-baixar modelo.

## Avisos importantes (já aprendidos, não repetir erros)
- **PowerShell 5.1 exibe UTF-8 errado** (`Endera��amento`): é artefato de console.
  Fonte da verdade é o **Node** (`node -e`), nunca `Get-Content`/`ConvertTo-Json`.
- `data/custom-systems.json` é **ignorado pelo git** (contém caminhos `C:\Users\T.I Primeira Chance\...`).
  É recriado pelo primeiro cadastro — não tente commitar.
- `storage/` é ignorado e **não** é servido ao navegador (só `public/` é).
- **Não criar guardas por header (`x-forwarded-for`)**: antivírus/firewall da máquina injetam
  esses headers até em acesso local e quebram o uso normal. A proteção é senha + binding.
- **O IP da rede muda por DHCP** (já foi .141, .208, .232). Por isso os links dos sistemas são
  montados na hora a partir do header `Host` (`requestHost` em `app/api/custom-systems/route.ts`):
  quem acessa pelo IP recebe link com IP; quem acessa por localhost recebe localhost.
  Não fixar IP no código.
- Next 16 usa `params` **assíncrono** (`Promise<{id}>`) nas rotas — não voltar a `params: {id}`.
- Agente não enxerga imagens; pedir descrição textual. Usuário não-técnico: linguagem simples.
- **Atualização e inicialização de sistemas locais:** não presuma que os arquivos novos continuam usando
  o mesmo comando, ambiente, host ou porta registrados no card. Antes de concluir que faltam dependências,
  confira `startCommand`, `workDir`, os nomes das variáveis de ambiente configuradas (nunca revele seus
  valores), o código real de inicialização e `portal-out.log`/`portal-err.log`. Compare a porta que o portal
  espera com a porta em que o processo realmente escuta. O portal define `PORT` com a porta cadastrada
  ao iniciar e testar; quando o sistema usa essa variável, deve respeitá-la. Sistemas que precisam ser
  acessados pela rede devem escutar em `0.0.0.0`, não numa porta aleatória ou apenas em `127.0.0.1`.
  Não corrija a validação para mascarar uma divergência do projeto. Depois da correção, faça o teste real
  na Gestão e confirme que iniciar/parar usa a mesma porta antes de orientar a publicação.

## Segurança (estado em 05/10/2026)
- **Iniciar/Parar exigem senha de admin** (`isAdminAuthorized` em `app/api/systems/[id]/start|stop`).
  No catálogo, a senha é solicitada em uma janela para cada ação e enviada somente naquela
  requisição; ela não é armazenada. A Gestão mantém login próprio em `sessionStorage`.
- Criar/editar/excluir/validar/ver rascunhos (`?all=1`) exigem admin → **403** sem senha.
- `server/auth.ts` compara com `timingSafeEqual`.
- **Path traversal barrado**: `server/storage-paths.ts` valida o id (`^[a-z0-9-]{1,32}$`) e
  resolve caminhos dentro de `storage/projects` (`resolveProjectDir`, `resolveInsideDir`).
- POST de projeto **inclui bancos de dados**; descarta `.env*` e chaves (`.key|pem|p12|...`)
  em 2 camadas (cliente e servidor).
- Público recebe só `{id, name, description, category, icon, url}` — sem caminhos/comandos.
- Testado via HTTP: `.env`, `.env.local`, `storage`, `data/custom-systems.json`, `.git/config` → **404**.
- Pendente conhecido: **firewall** — criar regras de entrada (TCP 3000, 8000, 5173; perfil Private)
  como admin, senão o outro PC não alcança. Só o admin cria regras.

## Estado atual (05/10/2026)
- Produção no ar em `0.0.0.0:3000`; 2 sistemas **publicados**:
  `4c0622e6810f4eeeb2642ed7` **Enderaçamento** (Operações, porta 8000) e
  `a765378fa18a43c0a39b699c` **Inventário** (Dados, porta 5173, `vite --host`).
  `accessUrl` gravados como `http://192.168.1.208:<porta>` (IP atual; pode mudar).
- Cópia do Enderaçamento em `storage/`: `app.run(host="0.0.0.0")` e sem abrir o navegador.
  Alterações em `storage/` não vão para o git.
- Visual/tema: título "Portal da Biblioteca Dumerval T.", fontes Sora/Inter/JetBrains Mono. Ver `design.md`.
- Correções relevantes: `listenerPidForPort` acha IPv6; `stop()` mata tracked + listener;
  spawn grava `portal-out/err.log`; rotas GET com `force-dynamic` (produção congelava `/api/systems`).

## Fluxo de trabalho do Gestão
Criar (pasta + nome/categoria opcionais) → IA descobre start/port/url → **Testar** abre e fecha de
verdade ("Funcionou! O projeto abriu e eu o fechei. Agora você pode publicar.") → **Publicar** só
aparece após teste OK → "Voltar a rascunho". Não existe botão "Abrir".

## O que falta para FINALIZAR o projeto
1. **Regras de firewall** (TCP 3000, 8000, 5173 no perfil Private) — bloqueia o acesso da rede.
2. **Criar o repositório privado no GitHub** + `git remote add origin` + push (hoje sem remoto).
3. **Subir o portal junto com o Windows** — atalho em `shell:startup`/Agendador para rodar
   `npm run start` automaticamente (ou service wrapper).
4. **Backup fora do git** de `.env.local` e da pasta `storage/` (pen drive).
5. **Teste final de ponta a ponta** pela rede, de outro PC: catálogo → login → Iniciar → abrir
   `:8000` / `:5173` → Parar.
6. Opcional: remover `X-Powered-By` e adicionar headers de segurança (só importa se expor além da LAN).

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
