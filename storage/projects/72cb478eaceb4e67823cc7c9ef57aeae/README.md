# Sistema Biblioteca

Aplicação web local para catalogação e circulação de acervo. O código-fonte do executável original não veio no ZIP; este sistema foi reconstruído para usar os dados Excel encontrados no pacote.

## Requisitos

- Windows com Python 3.10 ou superior e o Python Launcher (`py -3 --version`).
- Navegador atualizado.
- Para acesso por outros computadores, todos precisam estar na rede interna da biblioteca.

Não há dependências Python externas: o servidor, a base SQLite e a leitura das planilhas usam a biblioteca padrão do Python.

## Iniciar

1. Execute **Iniciar sistema.bat**.
2. No computador servidor, abra `http://localhost:8000`.
3. No primeiro acesso, crie o usuário administrador. Senhas devem ter ao menos 10 caracteres.
4. Nos outros computadores da mesma rede, abra `http://IP-DO-COMPUTADOR-SERVIDOR:8000`.

### Início automático ao entrar no Windows

Para iniciar o servidor automaticamente na próxima vez que entrar na sua conta Windows, execute uma vez **Configurar início automático.bat**. Ele adiciona um atalho apenas na pasta Inicializar do usuário atual, inicia o servidor em segundo plano e abre o navegador na tela de login assim que o servidor estiver pronto. As sessões anteriores são encerradas sempre que o servidor reinicia, exigindo novo login. Mensagens de inicialização são gravadas em `dados/servidor.log`. Para desfazer, execute **Remover início automático.bat**. O computador servidor precisa permanecer ligado e com a sessão do Windows iniciada para que os demais computadores acessem o sistema.

O servidor escuta na rede local por padrão. O endereço IP pode ser consultado com `ipconfig`. O Firewall do Windows pode solicitar autorização para Python; autorize somente em redes privadas confiáveis. Para acesso pela internet ou por redes não confiáveis, não exponha esta aplicação diretamente: configure HTTPS, controle de acesso de rede e cópias de segurança primeiro.

Variáveis opcionais:

- `BIBLIOTECA_HOST`: endereço de escuta; o padrão `0.0.0.0` permite acesso pela rede.
- `BIBLIOTECA_PORT`: porta HTTP; o padrão é `8000`.
- `BIBLIOTECA_DB`: caminho alternativo para o arquivo SQLite.
- `BIBLIOTECA_COOKIE_SECURE=1`: habilita cookies Secure quando o acesso é feito por HTTPS.

## Funcionalidades

- Busca de catálogo por título, autor, registro, editora, assunto e localização.
- Cadastro e edição de itens, quantidade de exemplares e tipologia.
- Importação de várias planilhas XLSX; duplicatas bibliográficas são ignoradas.
- Filtros para consultar cada tipologia separadamente ou o catálogo inteiro, ordenado pela data de registro.
- Relatórios por tipologia e exportação CSV do catálogo.
- Contas com perfis de equipe e administrador. Só administradores gerenciam usuários e importam planilhas.
- Troca de senha e desativação de usuários.

Os dados iniciais são carregados uma única vez das planilhas na pasta `planilhas`. A base de dados criada e atualizada fica em `dados/biblioteca.sqlite3`. Para cópia de segurança, pare o servidor e copie esse arquivo para um local protegido. A senha inicial do administrador não é criada pelo sistema: ela é definida no primeiro acesso.

## Testes

Na pasta do sistema, execute:

```powershell
py -3 -m unittest discover -s tests -v
```
