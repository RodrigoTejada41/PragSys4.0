# Segredos do GitHub Actions

Para o pipeline `CI/CD` funcionar com separacao entre `dev` e `production`, configure os segredos abaixo.

## Desenvolvimento

- `DEV_SSH_PRIVATE_KEY`: chave privada do usuario de deploy.
- `DEV_SSH_KNOWN_HOSTS`: saida do `ssh-keyscan` da VPS de desenvolvimento.
- `DEV_HOST`: 172.233.183.241
- `DEV_USER`: root
- `DEV_DEPLOY_PATH`:/opt/syspragas/dev

## Producao

- `PROD_SSH_PRIVATE_KEY`: chave privada do usuario de deploy.
- `PROD_SSH_KNOWN_HOSTS`: saida do `ssh-keyscan` da VPS de producao.
- `PROD_HOST`: hostname ou IP da VPS de producao.
- `PROD_USER`: usuario SSH de deploy.
- `PROD_DEPLOY_PATH`: caminho do checkout da aplicacao na VPS, por exemplo `/opt/syspragas/prod`.

## Variaveis opcionais

- `PRODUCTION_APP_URL`: URL do ambiente produtivo exibida no GitHub Environment `production`.

## Recomendacoes de seguranca

- use uma chave SSH diferente para cada ambiente;
- conceda acesso apenas ao diretorio do deploy;
- proteja o environment `production` com aprovadores;
- nao reutilize credenciais locais de desenvolvimento nas VPS.
