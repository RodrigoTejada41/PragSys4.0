# Segredos do GitHub Actions

Para o workflow simplificado de deploy da branch `dev`, configure os segredos abaixo.

## Segredos obrigatorios

- `HOST`: hostname ou IP da VPS de desenvolvimento.
- `SSH_USER`: usuario SSH de deploy na VPS.
- `SSH_PRIVATE_KEY`: chave privada OpenSSH usada pelo GitHub Actions.

## Script remoto esperado

O workflow atual executa este comando na VPS:

```bash
bash /var/www/deploy_dev.sh
```

## Recomendacoes de seguranca

- nao versione valores reais de host, fingerprint, usuarios ou chaves neste repositrio;
- use uma chave exclusiva para o GitHub Actions;
- conceda ao usuario acesso apenas ao checkout e ao runtime necessarios;
- se possivel, substitua `root` por um usuario dedicado de deploy;
- mantenha backup e rollback no script remoto da VPS, ja que o workflow atual so dispara o comando remoto.
