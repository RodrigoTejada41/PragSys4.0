# Deploy DEV e Production para Linode

Este documento descreve os workflows ativos no GitHub Actions para publicacao dos ambientes `dev` e `production` do SysPragas em VPS Ubuntu na Linode.

## Visao geral

- branch `dev`: publica automaticamente no ambiente de desenvolvimento;
- branch `main`: publica no ambiente de producao;
- o deploy remoto usa SSH e delega a execucao para um script remoto na VPS;
- o workflow de producao tambem aceita disparo manual com `workflow_dispatch`;
- a validacao de CI precisa ser executada separadamente antes da promocao para `main`.

## Arquivos entregues

- `.github/workflows/ci-cd.yml`: workflow de deploy da branch `dev`.
- `.github/workflows/deploy.yml`: workflow de deploy da branch `main` para `production`.
- `deploy/bootstrap_prod_vps.sh.example`: bootstrap inicial da VPS Ubuntu para producao.
- `deploy/deploy.sh`: script versionado de deploy remoto com backup preventivo e health check.
- `deploy/rollback.sh`: script versionado de rollback manual por commit.
- `deploy/remote/deploy_prod.sh.example`: exemplo do script remoto que a VPS de producao deve executar.

## Etapas do workflow

### Deploy DEV

Executa apenas em `push` para `dev`.

Fluxo:

- abre sessao SSH com `appleboy/ssh-action`;
- conecta usando `HOST`, `SSH_USER` e `SSH_PRIVATE_KEY`;
- executa o script remoto:

```bash
bash /var/www/deploy_dev.sh
```

### Deploy Production

Executa em `push` para `main` e tambem por disparo manual.

Fluxo:

- usa o GitHub Environment `production`;
- abre sessao SSH com `appleboy/ssh-action`;
- conecta usando `PROD_HOST`, `PROD_SSH_USER` e `PROD_SSH_PRIVATE_KEY`;
- executa o script remoto:

```bash
bash /var/www/deploy_prod.sh
```

## Segredos e variaveis no GitHub

Configure estes `Repository secrets`:

- `HOST`
- `SSH_USER`
- `SSH_PRIVATE_KEY`
- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_PRIVATE_KEY`

Configure o `Environment` chamado `production` no GitHub e mova para ele os segredos de producao, caso queira aprovacao manual antes da execucao.

## Estrutura recomendada na Linode

Use pelo menos um checkout isolado para desenvolvimento:

```text
/opt/syspragas/dev
```

E um checkout isolado para producao:

```text
/opt/syspragas/prod
```

## Topologia ativa Movis Tecnologia

VPS ativa:

- IP: `172.233.177.135`
- dominio: `movisystecnologia.com.br`
- producao: `/opt/syspragas/prod`
- dev/teste: `/opt/syspragas/dev`

URLs:

- Producao: `https://www.movisystecnologia.com.br/PragSys/app`
- Dev/teste: `https://www.movisystecnologia.com.br/dev/app`

Portas:

- `8011`: app producao, proxy Nginx `/PragSys`;
- `8012`: app dev, proxy Nginx `/dev`;
- `3111`: WhatsApp Bridge producao, bind local;
- `3112`: WhatsApp Bridge dev, bind local.

Nginx:

- referencia versionada: `deploy/nginx/movisystecnologia-pragsys.conf`;
- ativo remoto: `/etc/nginx/sites-enabled/movisystecnologia-pragsys.conf`.

Segredos permanecem nos `.env` remotos e nao devem ser versionados.

Script remoto sugerido:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/syspragas/dev
git fetch origin dev
git checkout dev
git reset --hard origin/dev
docker compose up --build -d syspragas whatsapp-bridge
```

Script remoto sugerido para producao:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/syspragas/prod
SERVICES="${SERVICES:-syspragas}"
if [[ -f ".env.prod" ]]; then
  cp .env.prod .env
fi
bash ./deploy/deploy.sh \
  --env prod \
  --branch main \
  --app-dir /opt/syspragas/prod \
  --compose-file docker-compose.yml \
  --services "$SERVICES" \
  --health-url http://127.0.0.1:8000/health
```

Por padrao o deploy sobe apenas `syspragas`. Se a producao tambem hospedar o bridge local de WhatsApp na mesma VPS, execute com:

```bash
SERVICES="syspragas,whatsapp-bridge" bash /var/www/deploy_prod.sh
```

## Preparacao da VPS Ubuntu

1. Instale `git`, `curl`, `docker` e `docker compose`.
2. Crie um usuario de deploy sem privilegios administrativos amplos.
3. Adicione esse usuario ao grupo `docker`.
4. Clone o repositorio em `/opt/syspragas/dev`.
5. Clone o repositorio tambem em `/opt/syspragas/prod`.
6. Crie os scripts `/var/www/deploy_dev.sh` e `/var/www/deploy_prod.sh` com permissao de execucao.
7. Crie `.env.dev` e `.env.prod` fora do Git com segredos e configuracoes de cada ambiente.
8. Garanta que o script de producao copie `.env.prod` para `.env` antes do deploy versionado.
9. Execute manualmente um primeiro deploy para validar bootstrap e permissoes.

Opcionalmente, use o bootstrap versionado:

```bash
sudo DEPLOY_USER=syspragas \
  APP_DIR=/opt/syspragas/prod \
  REPO_URL=git@github.com:SEU_USUARIO/SEU_REPOSITORIO.git \
  bash ./deploy/bootstrap_prod_vps.sh.example
```

## Sequencia recomendada para a primeira publicacao em producao

1. Ajuste `.env.prod` com `APP_ENV=production`, `JWT_SECRET` forte, senha inicial segura e integracoes reais.
2. Instale o script remoto em `/var/www/deploy_prod.sh` usando `deploy/remote/deploy_prod.sh.example` como base.
3. Valide manualmente na VPS:

```bash
bash /var/www/deploy_prod.sh
curl --fail http://127.0.0.1:8000/health
```

4. Configure os segredos `PROD_*` no GitHub.
5. Proteja a branch `main` e, se possivel, exija revisao antes do merge.
6. Execute um `workflow_dispatch` de teste no workflow de producao.

## Boas praticas operacionais

- mantenha `.env` separado por ambiente;
- mantenha `.env.dev` e `.env.prod` fora do controle de versao;
- restrinja a chave SSH ao ambiente de desenvolvimento;
- restrinja a chave SSH de producao a um usuario e host exclusivos;
- monitore logs do workflow e os logs do container `syspragas` apos cada deploy;
- rode `pytest -q` manualmente ou em workflow separado antes de promover alteracoes para `main`;
- use `deploy/rollback.sh` para rollback de codigo por commit quando necessario;
- preserve backup do banco antes de cada publicacao de producao.
