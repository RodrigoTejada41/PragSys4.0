# WhatsApp QR Bridge

## Objetivo

O SysPragas agora suporta autenticacao por QR Code para WhatsApp usando um conector local baseado em `Baileys`, sem depender obrigatoriamente de API paga.

Esse conector roda como um servico Node separado e conversa com o backend Python por HTTP, no contrato que o modulo de WhatsApp do sistema ja utiliza.

## Motivo da escolha tecnica

- `Baileys` evita dependencia de navegador automatizado e Puppeteer.
- encaixa melhor em execucao local, rede interna e Docker.
- reduz fragilidade operacional em comparacao a uma sessao controlada por Chromium.
- preserva a arquitetura atual do SysPragas, que ja consome um provedor HTTP de WhatsApp.

## Endpoints do bridge

- `GET /health`
- `GET /instance/connect/{instance}`
- `GET /instance/connectionState/{instance}`
- `DELETE /instance/logout/{instance}`
- `POST /message/sendText/{instance}`

## Execucao local

```powershell
.\scripts\run_whatsapp_bridge.ps1
```

Por padrao o bridge sobe em:

- `http://127.0.0.1:3100`

## Configuracao no SysPragas

Use no `.env`:

```env
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=evolution
WHATSAPP_API_BASE_URL=http://127.0.0.1:3100
WHATSAPP_API_KEY=syspragas-local-key
WHATSAPP_INSTANCE_NAME=syspragas
```

Observacao:

- o backend Python usa o driver `evolution` como contrato HTTP por compatibilidade com os endpoints do bridge;
- isso nao significa dependencia da Evolution API, apenas reaproveitamento do mesmo padrao de rotas.

## Fluxo de uso

1. Ative o WhatsApp nas configuracoes do sistema.
2. Suba o bridge local.
3. Clique em `Conectar WhatsApp` ou `Conectar via QR`.
4. Leia o QR Code com o WhatsApp do numero da empresa.
5. O status deve mudar para ativo e o numero conectado passa a aparecer na tela.
6. Agendamentos passam a poder enviar mensagens automaticas e manuais.

## Comportamento operacional

- o bridge aguarda alguns segundos pela emissao do QR antes de responder, reduzindo o caso em que a API retornava `connecting` sem `qr_code`;
- se a sessao estiver travada, expirada ou com credenciais persistidas corrompidas, o fluxo de conexao pode regenerar a sessao e limpar os arquivos de autenticacao automaticamente;
- o endpoint de logout remove a sessao ativa e purga as credenciais persistidas para permitir nova autenticacao limpa;
- o backend Python faz tentativas curtas adicionais para obter o QR, inclusive pedindo regeneracao quando o conector sinaliza expiracao;
- logs foram adicionados no bridge e no backend para geracao do QR, status da conexao, logout e envio de mensagens.

## Persistencia da sessao

As credenciais ficam em:

- `services/whatsapp-bridge/sessions/`

Essa pasta deve ser preservada para manter a sessao autenticada.

Quando for necessario forcar uma nova autenticacao, o proprio logout do sistema ou a regeneracao de sessao limpa esses arquivos para evitar reuso de estado inconsistente.

## Docker opcional

O `docker-compose.yml` inclui um servico opcional `whatsapp-bridge` via profile `whatsapp-bridge`.

Subida:

```powershell
docker compose --profile whatsapp-bridge up --build -d
```
