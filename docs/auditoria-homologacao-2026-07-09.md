# Auditoria e Homologacao - 2026-07-09

## Resultado

Status: reprovado para aprovacao final.

Motivo: existem bloqueios de seguranca, responsividade e consistencia de release. A base funcional principal passou nos testes automatizados e no fluxo manual local.

## Evidencias executadas

- `python -m pytest -q --basetemp .pytest_tmp`: 131 passed em 168.73s.
- `python -m compileall -q app`: OK.
- `python -m pip check`: OK.
- `docker compose config`: OK.
- `npm test --if-present` em `services/whatsapp-bridge`: sem script, exit 0.
- `npm audit --omit=dev` em `services/whatsapp-bridge`: falhou com 12 vulnerabilidades.
- Homologacao HTTP em `http://127.0.0.1:8010` com SQLite isolado:
  - `/health`: 200.
  - `/app`: 200.
  - `/docs` sem auth: 401.
  - `/docs` com master: 200.
  - login admin: 200.
  - API protegida sem token: 401.
  - CRUD de cliente, produto, praga e tecnico: OK.
  - OS com horario invalido: 400 esperado.
  - OS valida: OK.
  - baixa de estoque: OK.
  - financeiro gerado e pago: OK.
  - conclusao de OS: OK.
  - upload/leitura de foto: OK.
  - PDFs de OS, relatorio tecnico e certificados apos configuracao institucional: OK.
  - backup SQLite: OK.
- Homologacao UI via navegador:
  - login renderizado e funcional.
  - dashboard/menu renderizados.
  - screenshots: `syspragas-homologacao-dashboard.png`, `syspragas-homologacao-mobile.png`.

## Bloqueios

### B1 - Vulnerabilidades criticas no WhatsApp Bridge

Severidade: critica.

Local:
- `services/whatsapp-bridge/package.json`
- `services/whatsapp-bridge/package-lock.json`

Evidencia:
- `npm audit --omit=dev` retornou 12 vulnerabilidades.
- 2 criticas: `@whiskeysockets/baileys <6.7.22` e `protobufjs <=7.6.2`.
- 5 altas: `axios`, `form-data`, `path-to-regexp`, `ws` e dependencias relacionadas.

Impacto:
- Risco em componente que processa mensagens e payloads externos.
- Nao aprovar uso do bridge em producao antes de atualizar lockfile e reexecutar `npm audit`.

Acao necessaria:
- Rodar `npm audit fix` no bridge.
- Validar `package-lock.json`.
- Retestar QR, status, logout e envio.

### B2 - Webhook Focus NF-e publico sem validacao de segredo

Severidade: alta.

Local:
- `app/interfaces/api/routes/nfe.py:127`
- `app/interfaces/api/routes/nfe.py:132`
- `app/core/config.py:84`

Evidencia:
- Existe `focus_nfe_webhook_secret` na configuracao.
- A rota `POST /api/v1/nfe/webhooks/focus` aceita payload sem dependencia de auth e sem validar assinatura/segredo.

Impacto:
- Um cliente externo pode alterar status de NF-e se souber/descobrir referencias validas.

Acao necessaria:
- Validar header/token compartilhado ou assinatura HMAC.
- Recusar webhook quando segredo estiver configurado e ausente/invalido.
- Criar testes de webhook autorizado e rejeitado.

### B3 - Overflow horizontal em viewport mobile

Severidade: alta para homologacao visual.

Local:
- `app/interfaces/web/static/app.js`
- `app/interfaces/web/static/styles.css`
- `app/interfaces/web/templates/pages/app.html`

Evidencia:
- Em viewport `390x844`, snapshot mostrou blocos internos com largura aproximada de `599px` a `616px`.
- Screenshot gerada: `syspragas-homologacao-mobile.png`.

Impacto:
- Interface mobile fica com rolagem horizontal e componentes fora do viewport.

Acao necessaria:
- Ajustar grids/tabelas/cards do dashboard para `max-width: 100%`, `overflow-x: auto` onde necessario e colunas responsivas.
- Retestar mobile apos ajuste.

## Ajustes antes da aprovacao

### A1 - Versao visual inconsistente

Severidade: media.

Local:
- `VERSION:1`
- `pyproject.toml:7`
- `README.md:1`
- `app/interfaces/web/templates/base.html:6`
- `app/interfaces/web/templates/components/footer.html:2`

Evidencia:
- Release formal: `4.1.0`.
- UI mostra `SysPragas 3.1`.

Acao necessaria:
- Centralizar versao em settings/template.
- Atualizar titulo e footer.

### A2 - Header de hardening HTTP ausente no app

Severidade: media.

Local:
- `app/main.py:58`
- `app/main.py:157`

Evidencia:
- Nao foram encontrados `Content-Security-Policy`, `X-Frame-Options`/`frame-ancestors`, `X-Content-Type-Options` ou `Referrer-Policy` no app.

Impacto:
- Menor defesa contra XSS, clickjacking e MIME sniffing.

Acao necessaria:
- Adicionar middleware de headers.
- Definir CSP compativel com assets locais.

### A3 - JWT armazenado em localStorage

Severidade: media.

Local:
- `app/interfaces/web/static/app.js:2`
- `app/interfaces/web/static/app.js:2027`
- `app/interfaces/web/static/app.js:2243`

Evidencia:
- Token JWT fica em `localStorage` e e enviado como `Authorization: Bearer`.

Impacto:
- Qualquer XSS permite exfiltrar token.

Acao necessaria:
- Preferir cookie `HttpOnly` em producao ou reduzir TTL e fortalecer CSP.

### A4 - Favicon ausente

Severidade: baixa.

Local:
- `/favicon.ico`

Evidencia:
- Console do navegador registrou 404 para `http://127.0.0.1:8010/favicon.ico`.

Acao necessaria:
- Servir favicon ou ajustar template.

### A5 - Nome de container com typo

Severidade: baixa.

Local:
- `docker-compose.yml`

Evidencia:
- `container_name: CONTRLE_DE_PRAGAS_4.0`.

Acao necessaria:
- Corrigir para nome padronizado.

## Observacoes funcionais

- A primeira tentativa de gerar PDF retornou 400 porque dados regulatorios estavam incompletos. Apos configurar responsavel tecnico, licencas, endereco e CIT via API, os PDFs foram gerados corretamente.
- O ambiente `.venv_rebuilt` nao contem `pip` nem `pytest`. A homologacao foi executada com Python global, que possui dependencias validas.
- `scripts/run_local.ps1` aponta para `.venv\\Scripts\\python.exe`; no workspace atual esse caminho nao existe. Validar padrao de ambiente antes de distribuir instrucoes operacionais.

## Limitacoes da homologacao

- SEFAZ real, Focus NF-e real, Google Calendar real e WhatsApp real nao foram homologados ponta a ponta por falta de credenciais/sessao ativa.
- Docker build/up nao foi executado; somente `docker compose config` foi validado.
- Auditoria Python de CVEs via `pip-audit` nao foi executada porque `pip_audit` nao esta instalado.

## Criterio para aprovacao final

1. Corrigir B1, B2 e B3.
2. Reexecutar `pytest`, homologacao HTTP e navegador desktop/mobile.
3. Reexecutar `npm audit --omit=dev`.
4. Validar pelo menos uma integracao real configurada conforme escopo da release.
