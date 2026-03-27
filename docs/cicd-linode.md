# CI/CD para Linode

Este documento descreve o pipeline de integracao e entrega continua do SysPragas para ambientes `dev` e `production` em VPS Ubuntu na Linode.

## Visao geral

- branch `dev`: executa CI e publica automaticamente no ambiente de desenvolvimento;
- branch `main`: executa CI e publica automaticamente no ambiente de producao;
- qualquer falha em lint, seguranca, auditoria ou testes bloqueia o deploy;
- o deploy remoto usa SSH e `Docker Compose`, com health check e rollback automatico de codigo em caso de falha.

## Arquivos entregues

- `.github/workflows/ci-cd.yml`: pipeline principal de validacao e deploy.
- `deploy/deploy.sh`: script idempotente de deploy para Ubuntu.
- `deploy/rollback.sh`: rollback manual para um commit conhecido.
- `deploy/env/.env.dev.example`: exemplo de variaveis para ambiente de desenvolvimento.
- `deploy/env/.env.prod.example`: exemplo de variaveis para ambiente de producao.

## Etapas do workflow

### CI

Executa em `push` e `pull_request` para `dev` e `main`.

Inclui:

- instalacao de Python 3.11 e Node 20 com cache;
- instalacao das dependencias Python do projeto;
- instalacao das dependencias do `whatsapp-bridge`;
- lint Python com `flake8`;
- lint JavaScript com `eslint`;
- analise estatica de seguranca com `bandit`;
- auditoria de dependencias com `pip-audit`;
- checagem sintatica do bridge Node;
- execucao da suite `pytest -q`.

### Deploy DEV

Executa apenas em `push` para `dev`.

Fluxo:

- abre sessao SSH usando chave dedicada do ambiente;
- acessa o checkout remoto da aplicacao;
- executa `bash deploy/deploy.sh --env dev --branch dev`;
- faz `git fetch`, `git reset --hard origin/dev`, `docker compose up --build -d` e health check.

### Deploy PROD

Executa apenas em `push` para `main`.

Fluxo adicional de seguranca:

- usa `environment: production`, permitindo gate manual por reviewers no GitHub;
- gera backup preventivo do banco atual antes do deploy;
- publica `origin/main`;
- realiza health check em `http://127.0.0.1:8000/health`;
- se o deploy falhar depois da troca de codigo, tenta rollback automatico do commit.

## Segredos e variaveis no GitHub

Configure estes `Repository secrets` ou `Environment secrets`:

### Desenvolvimento

- `DEV_SSH_PRIVATE_KEY`
- `DEV_SSH_KNOWN_HOSTS`
- `DEV_HOST`
- `DEV_USER`
- `DEV_DEPLOY_PATH`

### Producao

- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`
- `PROD_HOST`
- `PROD_USER`
- `PROD_DEPLOY_PATH`

### Variaveis opcionais

- `PRODUCTION_APP_URL`: URL publica do ambiente produtivo, usada no bloco `environment`.

## Estrutura recomendada na Linode

Use diretorios isolados por ambiente:

```text
/opt/syspragas/dev
/opt/syspragas/prod
```

Estrutura sugerida em cada checkout:

```text
deploy/
deploy/backups/<env>/
deploy/releases/<env>/
.env
docker-compose.yml
```

## Preparacao da VPS Ubuntu

1. Instale `git`, `curl`, `docker` e `docker compose`.
2. Crie um usuario de deploy sem privilegios administrativos amplos.
3. Adicione esse usuario ao grupo `docker`.
4. Clone o repositorio em `/opt/syspragas/dev` e `/opt/syspragas/prod`.
5. Copie o template adequado de `deploy/env/` para `.env` em cada ambiente.
6. Ajuste secrets e variaveis especificas de cada VPS.
7. Execute manualmente um primeiro `docker compose up --build -d` para validar bootstrap.

## Backup, rollback e logs

- backups de producao sao salvos em `deploy/backups/prod/`;
- o ultimo deploy fica registrado em `deploy/releases/<env>/latest_release.env`;
- rollback manual:

```bash
bash ./deploy/rollback.sh --app-dir /opt/syspragas/prod --commit <sha>
```

Observacao: o rollback automatico restaura o codigo. O backup do banco e mantido para restauracao manual se uma migracao ou ajuste operacional exigir reversao de dados.

## Boas praticas operacionais

- mantenha `.env` separado por ambiente;
- use `GitHub Environments` para exigir aprovacao manual em producao;
- restrinja as chaves SSH por ambiente;
- monitore logs do workflow e os logs do container `syspragas` apos cada deploy;
- nao execute deploy manual direto em producao sem registrar o commit publicado.
