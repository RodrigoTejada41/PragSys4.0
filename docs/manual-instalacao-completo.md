# Manual Completo De Instalacao SysPragas

Data: 2026-07-10
Versao: SysPragas 4.1.0

Este manual cobre instalacao local, Docker, VPS, comandos de manutencao e problemas comuns. Nao registre senhas reais no Git.

## 1. Requisitos

### Windows local

Instalar:

- Python 3.11 ou superior;
- Git for Windows;
- PowerShell;
- navegador Chrome, Edge ou Firefox.

Opcional:

- Docker Desktop;
- Node.js, somente para manter `services/whatsapp-bridge`.

### VPS Linux

Instalar:

- Ubuntu 24.04 LTS ou equivalente;
- Git;
- Docker;
- Docker Compose plugin;
- Nginx;
- Certbot, se usar HTTPS publico.

## 2. Baixar o projeto

No Windows, abrir PowerShell:

```powershell
cd E:\Projetos
git clone git@github.com:RodrigoTejada41/PragSys4.0.git
cd PragSys4.0
```

Se nao tiver chave SSH no GitHub:

```powershell
git clone https://github.com/RodrigoTejada41/PragSys4.0.git
cd PragSys4.0
```

## 3. Instalar localmente no Windows

Criar ambiente Python:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Se o PowerShell bloquear scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Feche e abra o PowerShell, depois ative novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Configurar `.env` local

Copiar o exemplo:

```powershell
Copy-Item .env.example .env
```

Editar `.env` e conferir pelo menos:

```text
DATABASE_URL=sqlite:///./syspragas.db
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
JWT_SECRET=troque-por-um-valor-longo-e-aleatorio
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=troque-por-senha-forte
```

Para gerar um segredo simples no PowerShell:

```powershell
[guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
```

Use o resultado em `JWT_SECRET`.

## 5. Inicializar banco local

```powershell
python scripts\manage_db.py init
python scripts\manage_db.py status
```

Opcional, criar base de demonstracao:

```powershell
python scripts\manage_db.py seed-demo
```

## 6. Rodar localmente

Modo recomendado:

```powershell
.\scripts\run_local.ps1
```

Alternativa direta:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Acessar:

- aplicacao: `http://127.0.0.1:8000/app`;
- API docs: `http://127.0.0.1:8000/docs`;
- health check: `http://127.0.0.1:8000/health`.

Login inicial:

- usuario: valor de `DEFAULT_ADMIN_USERNAME`;
- senha: valor de `DEFAULT_ADMIN_PASSWORD`.

## 7. Rodar em rede interna

No servidor local:

```powershell
.\scripts\run_network.ps1 -HostAddress 0.0.0.0 -Port 8000
```

Em outra maquina da rede:

```text
http://IP_DO_SERVIDOR:8000/app
```

Liberar porta no firewall do Windows se necessario.

## 8. Rodar com Docker

Criar `.env` para Docker:

```powershell
Copy-Item deploy\env\.env.dev.example .env
```

Editar `.env` e preencher obrigatoriamente:

```text
JWT_SECRET=valor-longo-e-aleatorio
DEFAULT_ADMIN_PASSWORD=senha-forte
```

Subir aplicacao:

```powershell
docker compose up --build -d syspragas
```

Ver logs:

```powershell
docker compose logs -f syspragas
```

Validar:

```powershell
docker ps
curl http://127.0.0.1:8012/health
```

Acessar:

```text
http://127.0.0.1:8012/dev/app
```

Parar:

```powershell
docker compose down
```

## 9. Rodar WhatsApp QR no Docker

Subir app com bridge:

```powershell
docker compose --profile whatsapp-bridge up --build -d syspragas whatsapp-bridge
```

Validar bridge:

```powershell
curl http://127.0.0.1:3112/health
```

Fluxo no sistema:

1. Entrar no SysPragas.
2. Abrir area de WhatsApp ou Configuracoes.
3. Clicar em conectar por QR Code.
4. No celular, abrir WhatsApp > Aparelhos conectados.
5. Ler o QR Code.

## 10. Instalar ou atualizar na VPS

Usar chave SSH cadastrada na maquina local:

```powershell
ssh pragsys4-vps
```

Diretorios remotos atuais:

```bash
/opt/syspragas/prod
/opt/syspragas/dev
```

Antes de atualizar, fazer backup:

```bash
mkdir -p /opt/syspragas/backups
docker cp syspragas-prod:/data/syspragas.db /opt/syspragas/backups/syspragas-prod-$(date +%Y%m%d-%H%M%S).db
docker cp syspragas-dev:/data/syspragas.db /opt/syspragas/backups/syspragas-dev-$(date +%Y%m%d-%H%M%S).db
```

Atualizar codigo no ambiente dev:

```bash
cd /opt/syspragas/dev
git remote set-url origin git@github.com:RodrigoTejada41/PragSys4.0.git
git fetch origin main
git checkout main
git reset --hard origin/main
docker compose -p syspragas-dev --env-file .env --profile whatsapp-bridge up --build -d syspragas whatsapp-bridge
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -fsS http://127.0.0.1:8012/health
```

Atualizar producao depois de validar dev:

```bash
cd /opt/syspragas/prod
git remote set-url origin git@github.com:RodrigoTejada41/PragSys4.0.git
git fetch origin main
git checkout main
git reset --hard origin/main
docker compose -p syspragas-prod --env-file .env --profile whatsapp-bridge up --build -d syspragas whatsapp-bridge
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -fsS http://127.0.0.1:8011/health
```

Validar URLs publicas:

```bash
curl -L https://www.movisystecnologia.com.br/dev/app -o /dev/null -w '%{http_code}\n'
curl -L https://www.movisystecnologia.com.br/PragSys/app -o /dev/null -w '%{http_code}\n'
```

## 11. Comandos uteis

### Git

```powershell
git status
git pull
git log --oneline -5
```

### Testes

```powershell
python -m pytest -q
python -m pytest tests/test_auth.py -q
python -m pytest tests/test_whatsapp_integration.py -q
```

### Banco

```powershell
python scripts\manage_db.py init
python scripts\manage_db.py status
python scripts\manage_db.py seed-demo
```

### Docker

```powershell
docker compose config
docker compose ps
docker compose logs -f syspragas
docker compose restart syspragas
docker compose down
```

### VPS

```powershell
ssh pragsys4-vps
```

No Linux:

```bash
docker ps
docker logs --tail=200 syspragas-dev
docker logs --tail=200 syspragas-prod
nginx -t
systemctl status nginx --no-pager
```

## 12. Backup e restauracao

Backup local:

```powershell
Copy-Item .\syspragas.db .\backup-syspragas.db
```

Backup Docker:

```powershell
docker cp syspragas:/data/syspragas.db .\backup-syspragas.db
```

Restauracao Docker:

```powershell
docker compose stop syspragas
docker cp .\backup-syspragas.db syspragas:/data/syspragas.db
docker compose start syspragas
```

Na VPS, sempre parar ou recriar containers com cuidado e manter copia do banco antes de restaurar.

## 13. Problemas comuns

### Credenciais invalidas no login

Verificar:

- usuario digitado igual a `DEFAULT_ADMIN_USERNAME`;
- senha digitada igual a `DEFAULT_ADMIN_PASSWORD` no primeiro bootstrap;
- se o banco ja existia, a senha do `.env` nao troca automaticamente o usuario antigo;
- em dev, resetar a senha pelo procedimento administrativo ou recriar a base somente se puder perder dados.

### Porta ocupada

Windows:

```powershell
netstat -ano | findstr :8000
```

Trocar porta:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### PowerShell nao executa script

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Docker nao sobe

Validar:

```powershell
docker compose config
docker compose logs -f syspragas
```

Erros comuns:

- `JWT_SECRET` vazio;
- `DEFAULT_ADMIN_PASSWORD` vazio;
- Docker Desktop desligado;
- porta `8012` ou `8011` ocupada.

### API docs pede login

Use usuario MASTER. Por padrao, o usuario inicial `admin` deve ter permissao MASTER no bootstrap.

### Google Agenda nao conecta

Validar no `.env`:

```text
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=
```

O redirect deve bater exatamente com o cadastrado no Google Cloud.

### WhatsApp QR nao aparece

Validar:

```powershell
docker compose ps
docker compose logs -f whatsapp-bridge
```

Conferir no `.env`:

```text
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=evolution
WHATSAPP_API_BASE_URL=http://whatsapp-bridge:3100
WHATSAPP_BRIDGE_API_KEY=
```

## 14. Regras de seguranca

- nunca versionar `.env` real;
- nunca colocar senha, token, certificado ou chave privada em documento;
- usar senha forte para `DEFAULT_ADMIN_PASSWORD`;
- trocar senha padrao antes de producao;
- manter backup antes de atualizar;
- testar em `/dev/app` antes de publicar em `/PragSys/app`;
- manter `main` limpo e publicado somente apos Quality Gate.

## 15. Ordem recomendada para leigo

1. Instalar Python e Git.
2. Baixar o projeto.
3. Criar `.venv`.
4. Instalar dependencias.
5. Copiar `.env.example` para `.env`.
6. Preencher `JWT_SECRET` e `DEFAULT_ADMIN_PASSWORD`.
7. Rodar `python scripts\manage_db.py init`.
8. Rodar `.\scripts\run_local.ps1`.
9. Abrir `http://127.0.0.1:8000/app`.
10. Entrar com o usuario configurado.
11. Rodar `python -m pytest -q` antes de alterar codigo.
