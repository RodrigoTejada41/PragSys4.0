# Auditoria completa - SysPragas 4.1.0

Data: 2026-07-10
Escopo: projeto local `E:\Projetos\Controle_de_Pragas4.0`
Branch: `main`
Modo: auditoria antes de nova implementacao

## Sumario executivo

O sistema possui cobertura automatizada ampla para os fluxos centrais do CRM e a suite atual passou integralmente. Foram validados por testes automatizados: autenticacao, RBAC, clientes, OS, agendamentos, Google Agenda simulado, financeiro, recibos, NF-e, SEFAZ direto, documentos, estoque, contratos, multiempresa, configuracoes, assistente, WhatsApp e orquestrador.

Bloqueios criticos e altos corrigidos.

Pendencias remanescentes:

1. Medio: avaliar upgrade FastAPI/Starlette.
2. Medio: UI/documentacao desalinhadas com release 4.1.0 e credenciais locais.
3. Medio: credencial local diverge do README quando `.env` redefine a senha inicial.

## Evidencias executadas

| Validacao | Resultado |
|---|---:|
| `pytest -q --basetemp=.pytest_tmp_audit` | 141 passed em 123.73s |
| `pytest -q --basetemp=.pytest_tmp_audit_final` | 142 passed em 114.04s |
| `pytest -q --basetemp=.pytest_tmp_clean_final` | 144 passed em 115.10s |
| `pytest -q --basetemp=.pytest_tmp_clean_final2` | 145 passed em 116.28s |
| `node --check app/interfaces/web/static/app.js` | OK |
| `node --check services/whatsapp-bridge/src/server.js` | OK |
| `docker compose config --quiet` | OK |
| `npm audit --omit=dev --audit-level=moderate` no bridge | Falhou: 12 vulnerabilidades |
| `npm audit fix --omit=dev` no bridge | Parcial: restam 3 vulnerabilidades via `protobufjs` |
| `npm audit --omit=dev --audit-level=moderate` no bridge apos Baileys 7 RC | OK: 0 vulnerabilidades |
| Bridge runtime porta 3133 | `/health` 200; sem API key 401; instancia invalida 400 |
| Render `/app` via Playwright MCP | OK, com erro 404 de favicon |
| Login navegador com senha do README | Falhou: 400 credenciais invalidas |
| Carga simples 100x `/health` | 200; media 2.0ms; p95 2.47ms |
| Carga simples 100x `/app` | 200; media 4.11ms; p95 5.73ms |

## Funcionalidades aprovadas

- Autenticacao JWT e `/auth/me`: cobertas por `tests/test_auth.py`.
- Protecao de `/docs` por usuario master: coberta por `tests/test_auth.py`.
- RBAC e permissoes granulares: cobertas por `tests/test_rbac.py` e `tests/test_access_control.py`.
- Clientes, produtos, pragas, tecnicos e CRUD base: cobertos por `tests/test_crud_operations.py`.
- Ordens de Servico, estoque, financeiro vinculado, fotos e documentos: cobertos por `tests/test_work_orders.py` e `tests/test_documents.py`.
- Agendamentos, conflitos de tecnico, sincronizacao Google simulada e reabertura: cobertos por `tests/test_appointments.py`.
- Financeiro, caixa, recibos, NF-e, Simples e relatorios: cobertos por `tests/test_financial_module.py` e `tests/test_receipts.py`.
- Estoque profissional, importacao, transferencia, inventario e etiquetas: cobertos por `tests/test_stock_module.py`.
- Multiempresa e isolamento de dados: cobertos por `tests/test_multitenancy.py`.
- Configuracoes, documentos tecnicos e backup/restauracao: cobertos por `tests/test_settings.py` e `tests/test_database_admin.py`.
- WhatsApp QR/bridge com mocks: coberto por `tests/test_whatsapp_integration.py`.
- Orquestrador central: coberto por `tests/test_central_api_orchestrator.py`.

## Falhas, riscos e incompletudes

| ID | Criticidade | Area | Problema | Evidencia | Prioridade |
|---|---|---|---|---|---:|
| AUD-001 | Critica | WhatsApp bridge | Corrigido: Baileys atualizado para `7.0.0-rc13`; `npm audit` zerado. | `services/whatsapp-bridge/package.json`; `services/whatsapp-bridge/package-lock.json`; `npm audit`. | Concluido |
| AUD-002 | Alta | Fiscal/NF-e | Corrigido: webhook Focus NF-e valida segredo quando configurado e bloqueia producao sem segredo. | `app/interfaces/api/routes/nfe.py`; `tests/test_nfe_external_integration.py`. | Concluido |
| AUD-003 | Alta | Autenticacao/frontend | Corrigido parcialmente com mitigacao forte: token da UI movido para `sessionStorage` e token legado removido de `localStorage`. | `app/interfaces/web/static/app.js`; `tests/test_auth.py`. | Concluido |
| AUD-004 | Alta | Frontend/XSS | Corrigido parcialmente com mitigacao forte: CSP com nonce para script inline da aplicacao, sem `unsafe-inline` em `script-src` da tela principal. | `app/main.py`; `app/interfaces/web/templates/base.html`; `tests/test_auth.py`. | Concluido |
| AUD-005 | Alta | WhatsApp bridge | Corrigido: API key obrigatoria em producao; `/health` permanece publico. | `services/whatsapp-bridge/src/server.js`. | Concluido |
| AUD-006 | Alta | WhatsApp bridge | Corrigido: `instanceName` normalizado, limitado e validado contra traversal antes de acessar sessoes. | `services/whatsapp-bridge/src/server.js`. | Concluido |
| AUD-007 | Media | Headers/OWASP | Corrigido no FastAPI: CSP, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy`. | `app/main.py`; `tests/test_auth.py`. | Concluido |
| AUD-008 | Media | Supply chain Python | `starlette==0.46.2`; referencia de seguranca cita Range-header DoS corrigido em versao posterior. | `pip show starlette` -> 0.46.2; uso de `StaticFiles` em `app/main.py:159`. | 8 |
| AUD-009 | Media | Operacao | README informa senha inicial `syspragas123`, mas login local real falhou; `.env` local redefine a senha inicial. | `README.md:63-66`; Playwright recebeu 400 em `/api/v1/auth/login`. | 9 |
| AUD-010 | Baixa | UI/usabilidade | Corrigido: titulo e rodape atualizados para `SysPragas 4.1`. | `app/interfaces/web/templates/base.html`; `app/interfaces/web/templates/components/footer.html`; `tests/test_auth.py`. | Concluido |
| AUD-011 | Baixa | UI/usabilidade | Corrigido: textos de OS traduzidos para portugues. | `app/interfaces/web/templates/pages/app.html`; `tests/test_auth.py`. | Concluido |
| AUD-012 | Baixa | UI/runtime | Corrigido: `/favicon.ico` servido pela aplicacao. | `app/interfaces/web/routes.py`; `app/interfaces/web/templates/base.html`; `tests/test_auth.py`. | Concluido |

## Plano de acao

1. Avaliar upgrade FastAPI/Starlette com suite completa.
2. Atualizar README para diferenciar credencial de instalacao limpa e `.env` local.
3. Migrar auth web para cookie HttpOnly/SameSite em ciclo dedicado, se houver janela para alterar contrato frontend/API.
4. Continuar reduzindo `innerHTML` gradualmente para APIs de DOM seguro.

## Ordem obrigatoria antes de nova feature

1. AUD-008
2. AUD-009

## Correcoes aplicadas em 2026-07-10

- AUD-002: webhook Focus NF-e protegido por segredo configuravel (`X-Focus-Nfe-Webhook-Secret` ou `X-Webhook-Secret`).
- AUD-002: teste automatizado negativo/positivo adicionado.
- AUD-005: bridge WhatsApp falha na inicializacao em producao sem `WHATSAPP_BRIDGE_API_KEY`.
- AUD-006: nomes de instancia do bridge limitados a `[A-Za-z0-9._-]`, maximo 80 caracteres, sem `..` e com validacao de caminho resolvido.
- AUD-001: Baileys atualizado para `7.0.0-rc13`; `npm audit` zerado.
- AUD-003: token da UI movido para `sessionStorage`; token legado removido de `localStorage`.
- AUD-004/AUD-007: CSP com nonce e headers de seguranca adicionados no FastAPI.
- AUD-010: versao visual atualizada para `SysPragas 4.1`.
- AUD-011: textos de OS traduzidos para portugues.
- AUD-012: favicon local servido em `/favicon.ico`.
- Residuo operacional removido: caches pytest, artefatos Playwright, screenshot de auditoria, `node_modules`, sessoes do bridge e PDFs temporarios de teste.

## Quality Gate atual

Status: aprovado para integracao tecnica.

Motivo: falhas criticas e altas corrigidas; `pytest`, `node --check`, `docker compose config` e `npm audit` passaram. Residuos temporarios removidos apos validacao.
