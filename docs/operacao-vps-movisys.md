# Operacao VPS Movis Tecnologia

Data: 2026-07-10

## Ambientes publicados

Dominio base:

- `https://www.movisystecnologia.com.br`
- `https://movisystecnologia.com.br`

URLs operacionais:

- Producao: `https://www.movisystecnologia.com.br/PragSys/app`
- Teste/dev: `https://www.movisystecnologia.com.br/dev/app`

Observacao: usar `www` quando houver cache DNS local apontando o dominio raiz para IP antigo.

## DNS

Zona DNS esperada:

| Tipo | Nome | Dados |
| --- | --- | --- |
| A | `movisystecnologia.com.br` | `172.233.177.135` |
| A | `www.movisystecnologia.com.br` | `172.233.177.135` |

Nao configurar `/PragSys` no DNS. `/PragSys` e `/dev` sao caminhos tratados pelo Nginx e pela aplicacao.

## VPS

Host:

- IP: `172.233.177.135`
- SO validado: Ubuntu 24.04 LTS
- Usuario SSH atual: `root`

Dados criticos nao versionados:

- senha SSH/root;
- senha inicial do usuario `admin`;
- `JWT_SECRET`;
- `SETTINGS_ENCRYPTION_KEY`;
- `GOOGLE_OAUTH_CLIENT_SECRET`;
- `WHATSAPP_BRIDGE_API_KEY`.

Esses valores nao devem ser gravados neste repositorio. Manter em cofre de senha e/ou nos arquivos `.env` remotos protegidos.

## Layout remoto

Diretorios:

- Producao: `/opt/syspragas/prod`
- Dev/teste: `/opt/syspragas/dev`

Arquivos sensiveis remotos:

- `/opt/syspragas/prod/.env`
- `/opt/syspragas/dev/.env`

Esses arquivos ficam fora do Git.

## Containers e portas

Containers esperados:

| Ambiente | Container | Porta host | Porta interna |
| --- | --- | --- | --- |
| Producao | `syspragas-prod` | `8011` | `8000` |
| Dev | `syspragas-dev` | `8012` | `8000` |
| WhatsApp prod | `syspragas-whatsapp-bridge-prod` | `127.0.0.1:3111` | `3100` |
| WhatsApp dev | `syspragas-whatsapp-bridge-dev` | `127.0.0.1:3112` | `3100` |

Comando de verificacao:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## Nginx e HTTPS

Arquivo versionado de referencia:

- `deploy/nginx/movisystecnologia-pragsys.conf`

Arquivo remoto ativo:

- `/etc/nginx/sites-enabled/movisystecnologia-pragsys.conf`

Certificado:

- Let's Encrypt via Certbot
- Dominios: `movisystecnologia.com.br`, `www.movisystecnologia.com.br`

Comandos de verificacao:

```bash
nginx -t
systemctl status nginx --no-pager
certbot certificates
```

## Health checks

Aplicacao:

```bash
curl -fsS http://127.0.0.1:8011/health
curl -fsS http://127.0.0.1:8012/health
```

WhatsApp Bridge:

```bash
curl -fsS http://127.0.0.1:3111/health
curl -fsS http://127.0.0.1:3112/health
```

HTTPS publico:

```bash
curl -L https://www.movisystecnologia.com.br/PragSys/app -o /dev/null -w '%{http_code}\n'
curl -L https://www.movisystecnologia.com.br/dev/app -o /dev/null -w '%{http_code}\n'
```

## Google OAuth

Redirect URIs cadastrados/esperados no Google Cloud:

```text
https://movisystecnologia.com.br/PragSys/api/v1/google-calendar/oauth/callback
https://movisystecnologia.com.br/dev/api/v1/google-calendar/oauth/callback
```

Client ID pode ficar em configuracao operacional. Client Secret nao deve ser documentado.

## WhatsApp QR

Modo ativo:

- WhatsApp Web por QR Code via `services/whatsapp-bridge`;
- contrato HTTP interno compatvel com provider `evolution`;
- bridge exposto apenas em `127.0.0.1`, sem acesso publico direto.

Fluxo:

1. Entrar no sistema.
2. Abrir Configuracoes ou Agenda operacional.
3. Clicar em `Conectar WhatsApp` / `Conectar via QR`.
4. No celular: WhatsApp > Aparelhos conectados > Conectar aparelho.
5. Ler o QR Code.

## Deploy manual usado em 2026-07-10

Fluxo executado:

1. pacote local enviado para `/tmp/syspragas-whatsapp-bridge-update.tar.gz`;
2. extraido em `/opt/syspragas/prod` e `/opt/syspragas/dev`;
3. `.env` remoto ajustado por ambiente;
4. containers recriados com:

```bash
cd /opt/syspragas/prod
docker compose -p syspragas-prod --env-file .env --profile whatsapp-bridge up --build -d syspragas whatsapp-bridge

cd /opt/syspragas/dev
docker compose -p syspragas-dev --env-file .env --profile whatsapp-bridge up --build -d syspragas whatsapp-bridge
```

## Evidencias de validacao

Ultima validacao registrada em 2026-07-10:

- `syspragas-prod`: healthy
- `syspragas-dev`: healthy
- `syspragas-whatsapp-bridge-prod`: healthy
- `syspragas-whatsapp-bridge-dev`: healthy
- `https://www.movisystecnologia.com.br/PragSys/app`: HTTP 200
- `https://www.movisystecnologia.com.br/dev/app`: HTTP 200
- WhatsApp QR gerado em prod e dev
- Testes locais: `pytest tests/test_whatsapp_integration.py -q` -> `15 passed`

## Pendencias de seguranca

- Trocar senha root enviada em chat.
- Criar usuario de deploy sem login root direto.
- Usar chave SSH em vez de senha.
- Manter segredos em cofre externo.
- Revisar permissao dos `.env` remotos.
