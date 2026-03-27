# Deploy DEV para Linode

Este documento descreve o workflow atualmente ativo no GitHub Actions para publicacao automatica do ambiente `dev` do SysPragas em VPS Ubuntu na Linode.

## Visao geral

- branch `dev`: publica automaticamente no ambiente de desenvolvimento;
- branch `main`: nao possui deploy automatico neste workflow simplificado;
- o deploy remoto usa SSH e delega a execucao para um script remoto na VPS;
- a validacao de CI deixou de fazer parte do workflow ativo e precisa ser executada separadamente no processo de entrega.

## Arquivos entregues

- `.github/workflows/ci-cd.yml`: workflow simplificado de deploy da branch `dev`.

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

## Segredos e variaveis no GitHub

Configure estes `Repository secrets`:

- `HOST`
- `SSH_USER`
- `SSH_PRIVATE_KEY`

## Estrutura recomendada na Linode

Use pelo menos um checkout isolado para desenvolvimento:

```text
/opt/syspragas/dev
```

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

## Preparacao da VPS Ubuntu

1. Instale `git`, `curl`, `docker` e `docker compose`.
2. Crie um usuario de deploy sem privilegios administrativos amplos.
3. Adicione esse usuario ao grupo `docker`.
4. Clone o repositorio em `/opt/syspragas/dev`.
5. Crie o script `/var/www/deploy_dev.sh` com permissao de execucao.
6. Garanta que o script use `git fetch/reset` e `docker compose up --build -d`.
7. Execute manualmente um primeiro deploy para validar bootstrap.

## Boas praticas operacionais

- mantenha `.env` separado por ambiente;
- restrinja a chave SSH ao ambiente de desenvolvimento;
- monitore logs do workflow e os logs do container `syspragas` apos cada deploy;
- rode `pytest -q` manualmente ou em workflow separado antes de promover alteracoes para `main`;
- se voltar a existir deploy de producao, documente em arquivo separado para evitar confusao operacional.
