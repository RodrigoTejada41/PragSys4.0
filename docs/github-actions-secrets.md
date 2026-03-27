# Segredos do GitHub Actions

O repositorio mantem workflows separados para `dev` e `production`. Configure segredos distintos para evitar reaproveitamento indevido entre ambientes.

## Segredos obrigatorios para `dev`

- `HOST`: hostname ou IP da VPS de desenvolvimento.
- `SSH_USER`: usuario SSH de deploy na VPS de desenvolvimento.
- `SSH_PRIVATE_KEY`: chave privada OpenSSH usada pelo GitHub Actions para `dev`.

## Segredos obrigatorios para `production`

- `PROD_HOST`: hostname ou IP da VPS de producao.
- `PROD_SSH_USER`: usuario SSH dedicado ao deploy de producao.
- `PROD_SSH_PRIVATE_KEY`: chave privada OpenSSH usada pelo GitHub Actions para `production`.

## Scripts remotos esperados

Workflow `dev`:

```bash
bash /var/www/deploy_dev.sh
```

Workflow `production`:

```bash
bash /var/www/deploy_prod.sh
```

## Recomendacoes de seguranca

- nao versione valores reais de host, fingerprint, usuarios ou chaves neste repositorio;
- use uma chave SSH exclusiva por ambiente;
- proteja o workflow de producao com GitHub Environment `production` e aprovacao manual quando aplicavel;
- conceda ao usuario de deploy acesso apenas ao checkout e ao runtime necessarios;
- se possivel, substitua `root` por um usuario dedicado de deploy;
- mantenha backup e rollback no script remoto da VPS, ja que o workflow dispara apenas o comando remoto.
