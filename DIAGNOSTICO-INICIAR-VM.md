# Relatório técnico — Adaptação do portal-interno para máquina virtual Linux

**Destinatário:** programador responsável pela correção  
**Data:** 24/11/2026  
**Status:** diagnóstico encerrado; melhorias de código aplicadas nesta cópia; ajustes de dados da VM pendentes  
**Substitui:** `DIAGNOSTICO-INICIAR-VM.md` (versão anterior, apenas de hipóteses)

## Estado da implementação nesta cópia

Já aplicado aqui (o programador deve apenas revisar e testar):

- **Passo 1 — erro visível:** `start()` agora espera até 8 s pela abertura da porta, captura o erro do
  `spawn` e devolve mensagem; `catalog.tsx` mantém o diálogo aberto e mostra o erro se o estado não
  for alcançado. Arquivos: `server/local-systems.ts`, `components/catalog.tsx`.
- **Passo 2 — compatibilidade Linux:** `cmd.exe` só no Windows; venv procurado em `bin/python` no
  Linux; `stop()` usa `lsof` + `process.kill` no Linux e mantém `taskkill` no Windows; detectores de
  Node/Python e prompt da IA geram comandos POSIX; Django sem host explícito usa `0.0.0.0` no Linux.
  Arquivos: `server/local-systems.ts`, `server/project-detector.ts`, `server/port-utils.ts`,
  `server/ai-detector.ts`.

Ainda **não aplicado** porque depende de informações da VM: Passos 3 a 6 (inventário e edição de
`data/custom-systems.json`, recriação de venvs/portas, firewall). O Passo 7 (build/restart/teste)
deve ser executado na VM depois desses ajustes.

---

## 1. Contexto e fatos confirmados

- O projeto é o `portal-interno` (Next.js 16 + React 19 + TypeScript), registrado em
  `Documents\GitHub\portal-interno` na máquina original.
- O portal foi copiado para uma **máquina virtual Linux** e a interface abre normalmente.
- **Autenticação OK:** digitar senha errada mostra “Senha incorreta” normalmente; com a senha
  correta a janela fecha e nada mais acontece. Logo o problema está depois da validação.
- Sintoma na interface: o botão “Iniciar” fecha o diálogo, o card fica “Iniciando” por até ~15 s e
  volta a “Offline”, sem mensagem de erro.
- Não foi possível acessar a VM durante o diagnóstico. As causas abaixo vêm da leitura do código e
  devem ser confirmadas no ambiente pelo programador.

## 2. Objetivo

Fazer o botão “Iniciar” funcionar na VM Linux para **qualquer tipo de sistema cadastrado**, não
apenas para os dois projetos originais, e fazer com que falhas futuras apareçam na tela em vez de
ficarem silenciosas.

## 3. Causa provável (resumo)

O núcleo do portal (Node/Next) é portátil e roda em Linux. Os **sistemas cadastrados**, porém, foram
gravados com configuração do Windows em `data/custom-systems.json`: comandos `.exe`, `.cmd`, `.bat`,
`cmd.exe`, pastas `C:\Users\...` e virtualenvs com `Scripts\python.exe`. No Linux esses caminhos e
executáveis não existem, o `spawn` falha com `ENOENT`, e o portal devolve sucesso antes de saber
disso. O erro real fica apenas em `storage/projects/<id>/portal-err.log`.

Cadeia do sintoma, com evidência no código:

1. `app/api/systems/[id]/start/route.ts:6-11` valida a senha e passa.
2. `app/api/systems/[id]/start/route.ts:21-22` devolve HTTP 200 com `ok: true`.
3. `server/local-systems.ts:214-224` dispara o filho e retorna sucesso sem confirmar a abertura da
   porta; `child.on("error")` em `:222` só limpa o mapa interno.
4. `components/catalog.tsx:207-209` fecha o diálogo e `components/catalog.tsx:149-155` desiste da
   espera sem avisar. A falha nunca chega ao usuário.

---

## 4. Plano de execução (seguir em ordem)

### Passo 0 — Backup e segurança

1. Copiar para fora da VM, antes de mexer: `.env.local`, `data/custom-systems.json` e `storage/`.
2. **Não anexar esses arquivos a tickets ou e-mails sem remover senhas, tokens e chaves.**
   `data/custom-systems.json` contém valores capturados de projetos antigos.
3. Confirmar versão do Node na VM (`node -v`) e manter a mesma linha da máquina original (Node 24,
   conforme `package.json:10`, que usa `--experimental-strip-types`).
4. Não editar arquivos de sistema com o portal rodando. Parar o portal antes das mudanças de código.
   Não rodar `next build` com o servidor no ar (`AGENTS.md:24`).

### Passo 1 — Fazer o erro aparecer (implementar antes das correções de compatibilidade)

Sem isso qualquer nova tentativa continuará parecendo “nada acontece”.

1. Em `server/local-systems.ts:214-224`: após o `spawn`, aguardar 1 a 2 s e verificar a porta com o
   helper já existente `tryConnect` / `isPortOpen` (`:122-143`). Se a porta não abrir, devolver
   `{ started: false, message }` lendo as últimas linhas de
   `storage/projects/<id>/portal-err.log`.
2. Tratar `child.on("error")` e `child.on("exit")` com código diferente de zero como falha, com
   mensagem. Não responder `{ started: true }` antes dessa confirmação.
3. Em `components/catalog.tsx:149-155`: quando a espera expirar, mostrar mensagem de falha em vez de
   retornar em silêncio.
4. Em `components/catalog.tsx:141-144`: não engolir completamente o erro de `refreshStatuses()`;
   pelo menos sinalizar “não foi possível consultar o estado”.
5. Se não for possível abrir `portal-err.log`, também devolver mensagem — hoje `server/local-systems.ts:90-99`
   cai em `stdio: "ignore"` e esconde o erro.

Trecho ilustrativo para o item 1 (adaptar imports e nomes ao estilo do arquivo):

```ts
const child = spawnSystemCommand(command[0], command.slice(1), {
  cwd: runtime.cwd,
  env: { ...process.env, ...runtime.env, PORT: String(runtime.port) },
  logId: id
});
processes.set(id, child);
await new Promise((resolve) => setTimeout(resolve, 1500));
if (!(await isPortOpen(runtime.port))) {
  processes.delete(id);
  return { started: false, message: readLastError(id) ?? "O processo não abriu a porta." };
}
return { started: true };
```

`readLastError(id)` deve ler o fim de `resolveProjectDir(id)/portal-err.log` (`server/storage-paths.ts:5`)
e retornar `null` se o arquivo não existir.

### Passo 2 — Tornar o código do portal multiplataforma

Corrigir os pontos que ainda assumem Windows. Manter o comportamento atual no Windows usando
`process.platform === "win32"`.

| Arquivo | Problema | Ajuste |
|---------|----------|--------|
| `server/local-systems.ts:67-77`, `:108-116` | `.cmd`/`.bat` sempre rodam via `cmd.exe` | Só usar `cmd.exe` no Windows. No Linux, chamar `spawn(program, args, base)` diretamente; para scripts `.sh`, usar `bash` com argumentos separados, sem montar linha de comando com aspas do Windows. |
| `server/local-systems.ts:34-37` | Venv gerenciado procurado em `.portal-venv/Scripts/python.exe` | No Linux procurar `.portal-venv/bin/python`; no Windows manter `Scripts/python.exe`. |
| `server/local-systems.ts:145-175`, `:243-263` | PID de porta via `netstat -ano` e morte via `taskkill /T /F` | No Linux usar `lsof -ti tcp:<porta>` ou `ss -ltnp` e `process.kill(pid, "SIGTERM")`, com escalonamento para `SIGKILL`. Verificar o resultado e devolver mensagem se falhar. Instalar `lsof` na VM ou usar `ss`. |
| `server/local-systems.ts:265-288`, `:384-463` | Preparação/validação usam comandos e `taskkill` do Windows | Aplicar o mesmo critério de plataforma; não marcar validação como OK se o comando de preparação falhou. |
| `server/local-systems.ts:465-490` | Reescrita de porta em arquivos `.py`, `.js`, `.ts` e PowerShell | Manter, mas envolver em `try/catch` com mensagem; no Linux ignorar o trecho de PowerShell sem tratar como erro. |
| `server/port-utils.ts:33-94` | Reescrita de `--port`, `-p`, uvicorn, vite, Django etc. | Confirmar que cobre os comandos que serão usados na VM. Se o sistema usar outra flag, passar `--port <porta>` explicitamente no cadastro ou fazer a aplicação ler `PORT`. |
| `server/project-detector.ts:64-103`, `:219`, `:291-295` | Detecta `npm.cmd`, `python.exe`, `py.exe`, `LOCALAPPDATA`, `C:\Program Files` | Detectar `npm`, `node`, `python3`, `pip3`, `bin/python` e caminhos `/usr/bin`, `/usr/local/bin`. |
| `server/ai-detector.ts:251-258` | Prompt da IA sugere comandos do Windows | Tornar o prompt dependente de `process.platform` ou pedir sempre comandos POSIX na VM. |
| `server/custom-systems.ts:52-61`, `components/catalog.tsx:30-39` | Já usam o host de quem acessa para montar a URL | Manter. Atualizar o `accessUrl` salvo apenas para evitar confusão na Gestão. |
| `server/auth.ts:3` | Senha é lida no carregamento do módulo | Após alterar `.env.local`, reiniciar o portal. |

Trecho ilustrativo para `spawnSystemCommand`:

```ts
const useCmd = process.platform === "win32" && isScriptShim(program);
if (useCmd) {
  const commandLine = [cmdQuote(program), ...args.map(cmdQuote)].join(" ");
  child = spawn("cmd.exe", ["/d", "/s", "/c", commandLine], {
    ...base,
    windowsVerbatimArguments: true
  });
} else {
  child = spawn(program, args, base);
}
```

### Passo 3 — Inventariar os sistemas cadastrados

Para cada item de `data/custom-systems.json`, anotar em uma planilha de revisão:

- `id` e `name` (identificam a pasta `storage/projects/<id>`);
- `type` e `status` (somente `type: "local"` e `status: "published"` ganham botão “Iniciar” —
  `server/local-systems.ts:23-51`);
- `startCommand` (array: primeiro elemento é o programa, o resto são argumentos);
- `workDir` e `sourceFolder`;
- `port` e `accessUrl`;
- `env` (nomes das variáveis; **não copiar valores**).

Marcar cada sistema como: **OK Linux**, **precisa trocar comando**, **precisa trocar pasta** ou
**precisa recriar dependências**.

### Passo 4 — Adaptar cada sistema (matriz por linguagem)

O portal define a variável `PORT` com a porta escolhida e tenta reescrever `--port` / `-p` no comando
(`server/local-systems.ts:216`, `server/port-utils.ts:33-94`). Use `<porta>` abaixo como essa porta.
Se a aplicação não aceitar `--port`, faça-a ler `process.env.PORT` / `$PORT`.

| Tipo / linguagem | Ajuste na VM Linux | Comando de exemplo para `startCommand` | Atenções |
|------------------|--------------------|----------------------------------------|----------|
| Python (Flask, FastAPI, uvicorn) | Recriar venv em `bin/python` e instalar `requirements.txt` | `["python3", "app.py"]` ou `["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "<porta>"]` | Obrigatório `--host 0.0.0.0` para acesso pela rede. Evitar `.exe` e `.venv\Scripts`. |
| Python (Django) | Recriar venv e rodar migrações antes | `["python3", "manage.py", "runserver", "0.0.0.0:<porta>"]` | `port-utils.ts:82-90` reescreve `runserver`, mas se não houver host ele insere `127.0.0.1:<porta>` (`:88`); deixar `0.0.0.0` explícito no cadastro. |
| Node / Next | `npm install` na pasta do projeto | `["npm", "start"]` com `PORT=<porta>` no `env`, ou `["node", "server.js"]` | Trocar `npm.cmd` por `npm`. `npm run start` do portal usa `-H 0.0.0.0` (`package.json:8`). |
| Vite / React | `npm install` | `["npx", "vite", "--host", "0.0.0.0", "--port", "<porta>"]` | Sem `--host`, o Vite escuta só no localhost. |
| Express / Node puro | `npm install` | `["node", "index.js"]` com `PORT=<porta>` | A aplicação precisa usar `process.env.PORT`. |
| Java / Spring Boot | Instalar JDK e gerar o `.jar` na VM | `["java", "-jar", "app.jar", "--server.port=<porta>"]` | Esquecer o `--server.port` faz a app usar 8080 e o card ficar offline. |
| Go | Compilar na VM (`go build`) | `["./app", "-port", "<porta>"]` | Binários `.exe` do Windows não rodam; recompilar para Linux. |
| PHP | Instalar PHP CLI | `["php", "-S", "0.0.0.0:<porta>", "-t", "public"]` | `port-utils.ts:63-68` já trata `php -S`; conferir. |
| .NET | Instalar SDK/runtime | `["dotnet", "app.dll", "--urls", "http://0.0.0.0:<porta>"]` | Publicar/buildar na VM. |
| Ruby / Rails | `bundle install` | `["bundle", "exec", "rails", "server", "-b", "0.0.0.0", "-p", "<porta>"]` | Instalar gemas nativas na VM. |
| Docker / Compose | Instalar Docker e construir imagem na VM | `["docker", "compose", "up", "--build"]` | O portal não consegue reescrever a porta dentro do compose: mapear `"<porta>:<porta>"` e usar `PORT`. |
| Site estático | Nenhuma dependência | `["python3", "-m", "http.server", "<porta>", "--bind", "0.0.0.0"]` | Confirmar o diretório em `workDir`. |
| Script `.bat` / `.cmd` / `.ps1` | Converter para `.sh` com `#!/bin/bash` e permissão de execução | `["bash", "iniciar.sh"]` | Depois do Passo 2, `cmd.exe` não é mais usado no Linux. |
| Executável `.exe` do Windows | Substituir por versão Linux ou recompilar | depends do projeto | Não há compatibilidade direta; SEMPRE trocar. |

Regras gerais para o cadastro:

- Preferir `workDir` e `sourceFolder` **vazios**, para o portal usar `storage/projects/<id>`.
  Se precisar de caminho absoluto, usar apenas caminhos existentes na VM.
- Nunca deixar `C:\...` em nenhum campo.
- O programa indicado em `startCommand[0]` precisa existir no `PATH` da VM ou ser caminho absoluto Linux.
- Para alterar o cadastro, usar a tela “Gestão” da própria VM sempre que possível; edição manual do
  JSON deve ser feita com portal parado e backup anterior.

### Passo 5 — Recriar dependências dentro de `storage/`

Para cada sistema com Python:

1. Entrar em `storage/projects/<id>/`.
2. Apagar `.portal-venv`, `.venv`, `.venv-1` e outros venvs trazidos do Windows.
3. Rodar `python3 -m venv .portal-venv`.
4. Rodar `.portal-venv/bin/pip install -r requirements.txt` (se existir `requirements.txt`).
5. Conferir que `pyvenv.cfg` não contém `home = C:\...`.

Para Node: rodar `npm install` na pasta do projeto e conferir que `node_modules` é da VM.  
Para Java, Go, .NET, Ruby e Docker: gerar artefatos/binários na VM, nunca reaproveitar `.exe`.

### Passo 6 — Porta, rede e firewall

1. Verificar portas ocupadas na VM com `ss -ltnp` antes de cadastrar/alterar cada sistema.
2. Cada sistema deve escutar em `0.0.0.0` e respeitar a variável `PORT` enviada pelo portal
   (`server/local-systems.ts:216`).
3. Abrir no firewall da VM: TCP 3000 (portal) e todas as portas dos sistemas publicados.
4. O card “Abrir” já monta a URL com o host de quem acessa (`server/custom-systems.ts:52-61`), mas o
   `accessUrl` salvo pode estar com `192.168.1.208`; atualizar para evitar confusão na Gestão.
5. Se o “Parar” não liberar a porta, encerrar o processo órfão na VM e aplicar o Passo 2 (item
   `netstat`/`taskkill`).

### Passo 7 — Build, restart e teste

1. Na VM, dentro da pasta do projeto: apagar `.next` e rodar `npm install` (ou `npm ci`), depois
   `npm run build`.
2. Conferir `.env.local` com `PORTAL_ADMIN_PASSWORD` e reiniciar o portal com `npm run start`
   (já usa `-H 0.0.0.0`, `package.json:8`).
3. Se for ficar permanente, criar serviço `systemd` para o `npm run start`.
4. Testar um sistema de cada linguagem cadastrada, um por vez.
5. Verificar `storage/projects/<id>/portal-out.log` e `portal-err.log` após cada teste.
6. Confirmar a senha errada ainda mostra “Senha incorreta” (regressão de autenticação).

---

## 5. Validação e critérios de aceite

- [ ] Com senha correta, o card muda para **Online** em até ~15 s.
- [ ] Com senha errada, aparece “Senha incorreta” (não regrediu).
- [ ] Se o sistema falhar, aparece mensagem na tela — não apenas volta para “Offline”.
- [ ] “Abrir” funciona usando o IP/hostname da VM, não o IP antigo.
- [ ] `curl http://<ip-da-vm>:<porta>/` responde para cada sistema publicado.
- [ ] `portal-err.log` sem novas linhas de erro após o início.
- [ ] “Parar” realmente libera a porta (conferir com `ss -ltnp`).
- [ ] Ollama não é necessário para “Iniciar”; só é usado na descoberta/validação por IA
      (`server/ai-detector.ts`). Instalar apenas se essa função for usada.
- [ ] `npm run lint` equivalente (o projeto usa `tsc --noEmit --incremental false`,
      `AGENTS.md:25-27`) passa sem erros após as mudanças.

## 6. Riscos e observações para o programador

- **Segredo:** `data/custom-systems.json` e `RELATORIO-CHECAGEM.md` têm valores sensíveis capturados.
  Não circular sem remover senhas/tokens/chaves.
- **Versionamento:** `.next`, `.env.local`, `node_modules`, `tsconfig.tsbuildinfo`, `iniciar.cmd` e
  `iniciar.sh` são ignorados pelo git (`.gitignore`). Não commitar build nem segredo.
- **Ordem importa:** corrigir o Passo 1 antes dos demais, senão o programador continuará sem saber
  qual foi o erro real.
- **Regressão no Windows:** todas as mudanças de plataforma devem usar `process.platform === "win32"`
  para preservar o funcionamento da máquina original.
- **Pendência antiga:** firewall e inicialização automática do portal ainda estão listados como
  pendentes em `AGENTS.md:88-96`; conferir se já foram resolvidos na VM.
- **Não usar arquivos do Windows:** `.exe`, `.cmd`, `.bat`, `.ps1`, `pyvenv.cfg` com `C:\...` e
  `node_modules` compilado no Windows devem ser substituídos na VM.
