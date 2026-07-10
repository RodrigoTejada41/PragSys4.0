# RETOMADA EXATA - SysPragas

Data: 2026-07-09
Projeto: `E:\Projetos\Controle_de_Pragas4.0`
Branch: `main`
HEAD: `8adeea1 docs: add dev demo seed handoff summary`

## Abrir primeiro

1. `RETOMADA_EXATA.md`
2. `docs/ESTADO_ATUAL_PROJETO.md`
3. `specs/README.md`
4. `specs/module-map.md`

## Estado desta retomada

Foi criada a estrutura de Spec-Driven Development na raiz do projeto.

Fluxo oficial:

`SPEC -> PLAN -> TASKS -> IMPLEMENTATION`

Regra atual: codigo novo so deve iniciar depois de `spec.md`, `plan.md` e `tasks.md` aprovados no modulo afetado.

## Arquivos criados nesta etapa

- `specs/README.md`
- `specs/module-map.md`
- `specs/approval-log.md`
- `specs/_templates/spec.md`
- `specs/_templates/plan.md`
- `specs/_templates/tasks.md`
- `docs/decisions/2026-07-09-spec-driven-development.md`
- `specs/core-domain/{spec.md,plan.md,tasks.md}`
- `specs/application-services/{spec.md,plan.md,tasks.md}`
- `specs/infrastructure-db/{spec.md,plan.md,tasks.md}`
- `specs/interfaces-web-api/{spec.md,plan.md,tasks.md}`
- `specs/auth-security/{spec.md,plan.md,tasks.md}`
- `specs/multitenancy/{spec.md,plan.md,tasks.md}`
- `specs/customers-contracts/{spec.md,plan.md,tasks.md}`
- `specs/work-orders/{spec.md,plan.md,tasks.md}`
- `specs/finance-nfe/{spec.md,plan.md,tasks.md}`
- `specs/documents-reports/{spec.md,plan.md,tasks.md}`
- `specs/whatsapp/{spec.md,plan.md,tasks.md}`
- `specs/deployment-quality/{spec.md,plan.md,tasks.md}`

## Status de aprovacao

Todos os artefatos SDD estao como `Draft inicial`.

Nao ha aprovacao registrada.
Nao iniciar implementacao funcional baseada nesses specs antes de aprovar os modulos afetados.

## Worktree no momento do registro

Comando executado:

```powershell
git status --short --branch
```

Resultado:

```text
## main...origin/main
 M .dockerignore
 M .env.example
 M .gitignore
 M Dockerfile
 M app/application/schemas.py
 M app/core/config.py
 M app/infrastructure/migrations.py
 M app/infrastructure/models.py
 M app/interfaces/api/routes/nfe.py
 M app/interfaces/web/static/app.js
 M docker-compose.yml
 M tests/test_nfe_direct_module.py
?? app/application/nfe_danfe_service.py
?? docs/auditoria-homologacao-2026-07-09.md
?? docs/decisions/
?? movisys_motor_fiscal_completo/
?? specs/
?? syspragas-homologacao-dashboard.png
?? syspragas-homologacao-mobile.png
```

Observacao: havia alteracoes anteriores no worktree antes da criacao do SDD. Nao foram revertidas nem normalizadas.

## Ultimo commit conhecido

Comando executado:

```powershell
git log -1 --oneline
```

Resultado:

```text
8adeea1 docs: add dev demo seed handoff summary
```

## Validacao feita

- Verificada ausencia previa de `specs/` na raiz.
- Criada estrutura SDD na raiz.
- Listados arquivos criados em `specs` e `docs/decisions`.
- Nenhum teste de aplicacao foi executado, pois a mudanca foi documental/processual.

## Validacao adicional em 2026-07-09

- Restaurado `pip` em `.venv_rebuilt` com `python -m ensurepip --upgrade`.
- Instalado projeto no venv com `python -m pip install -e ".[dev]"`.
- Validado import da aplicacao: `from app.main import app`.
- Validado modulo NF-e/DANFE: `python -m pytest tests\test_nfe_direct_module.py -q --basetemp=.pytest_tmp_nfe`.
- Resultado: `12 passed in 46.83s`.
- Primeiro teste sem `--basetemp` executou os testes, mas falhou no cleanup do temp global do Windows com `PermissionError` em `pytest-current`; reexecucao com temp local passou.
- `.gitignore` atualizado para ignorar `.venv_rebuilt/` e `.pytest_tmp*/`.
- Criado `AGENTS.md` raiz com governanca operacional dos agentes Codex.
- Criado `docs/organograma-corporativo-agentes.md` com organograma, departamentos, revisores, Quality Gate e padroes obrigatorios.
- Atualizado `docs/README.md` para apontar a nova governanca.
- Registrado prompt da API Central como modulo SDD `central-api-orchestrator`.
- Criados `specs/central-api-orchestrator/spec.md`, `plan.md` e `tasks.md`.
- Criada decisao `docs/decisions/2026-07-09-central-api-orchestrator.md`.
- Atualizados `specs/README.md`, `specs/module-map.md` e `specs/approval-log.md`.
- Implementacao funcional da API Central permanece bloqueada ate aprovacao explicita dos artefatos SDD.

## MVP Central API Orchestrator em 2026-07-09

- Branch criada: `codex/central-api-orchestrator`.
- Aprovado `central-api-orchestrator` por Rodrigo Tejada via `chat:2026-07-09:pode-continuar-central-api-orchestrator`.
- Implementado MVP com cadastro de servicos, dependencias, health check, historico e auditoria de comando `reload`.
- Criados modelos `ManagedService`, `ServiceDependency`, `ServiceHealthCheck` e `ServiceCommandAudit`.
- Criado servico `app/application/central_orchestrator_service.py`.
- Criada rota `app/interfaces/api/routes/orchestrator.py` sob `/api/v1/orchestrator`.
- Adicionadas permissoes `orchestrator.view`, `orchestrator.manage`, `orchestrator.command`, `orchestrator.logs` e `orchestrator.audit`.
- Criada migracao `20260709_002_central_orchestrator`.
- Criado `docs/central-api-orchestrator.md`.
- Testes: `tests/test_central_api_orchestrator.py` -> `4 passed in 33.94s`.
- Regressao: `tests/test_access_control.py tests/test_auth.py tests/test_central_api_orchestrator.py` -> `11 passed in 39.61s`.
- Import: `from app.main import app` -> `app import ok`.
- Limite atual: MVP ainda nao inicia, para ou reinicia processos reais; comando `reload` apenas audita aceite.
- Adicionados comandos administrativos `start`, `stop` e `restart` sob `/api/v1/orchestrator/services/{service_id}/...`.
- Esses comandos registram auditoria como `accepted` e nao executam processo real.
- Teste novo RED/GREEN: `test_orchestrator_lifecycle_commands_are_audited_without_process_execution`.
- Testes finais: `tests/test_central_api_orchestrator.py` -> `5 passed in 26.31s`.
- Regressao final: `tests/test_access_control.py tests/test_auth.py tests/test_central_api_orchestrator.py` -> `12 passed in 31.44s`.
- Adicionado diagnostico operacional em `POST /api/v1/orchestrator/diagnostics`.
- Diagnostico valida portas duplicadas, servicos sem `health_url` e dependencias nao resolvidas.
- Teste novo RED/GREEN: `test_orchestrator_diagnostics_reports_port_conflicts_and_missing_health_url`.
- Testes finais apos diagnostico: `tests/test_central_api_orchestrator.py` -> `6 passed in 28.23s`.
- Regressao final apos diagnostico: `tests/test_access_control.py tests/test_auth.py tests/test_central_api_orchestrator.py` -> `13 passed in 30.05s`.
- Adicionados detalhes e historico operacional:
  - `GET /api/v1/orchestrator/services/{service_id}`
  - `GET /api/v1/orchestrator/services/{service_id}/history`
- Historico retorna ultimos health checks e comandos auditados.
- Teste novo RED/GREEN: `test_orchestrator_service_detail_and_history_expose_health_and_commands`.
- Testes finais apos historico: `tests/test_central_api_orchestrator.py` -> `7 passed in 29.59s`.
- Regressao final apos historico: `tests/test_access_control.py tests/test_auth.py tests/test_central_api_orchestrator.py` -> `14 passed in 30.49s`.
- Implementada recuperacao automatica segura em `POST /api/v1/orchestrator/recovery/run`.
- Recuperacao audita `restart` para servicos `unhealthy/degraded` com `restart_on_failure`, respeitando `max_restart_attempts`.
- Implementado executor `local_windows` com allowlist interna, `subprocess.run(shell=False)` e bloqueio quando allowlist nao existe.
- Implementado painel administrativo minimo em Configuracoes do sistema:
  - listagem de servicos;
  - diagnostico operacional;
  - recuperacao manual;
  - comandos `restart` e `reload`.
- Testes executor/recuperacao/painel:
  - `test_orchestrator_recovery_restarts_unhealthy_service_until_attempt_limit` -> `1 passed in 36.01s`;
  - `test_orchestrator_local_windows_executor_runs_only_allowlisted_command` -> `1 passed in 45.27s`;
  - `tests/test_central_api_orchestrator.py` -> `9 passed in 45.97s`;
  - `tests/test_central_api_orchestrator.py tests/test_web_ui.py` -> `13 passed in 30.18s`;
  - `tests/test_access_control.py tests/test_auth.py tests/test_central_api_orchestrator.py tests/test_web_ui.py` -> `20 passed in 31.21s`;
  - `node --check app/interfaces/web/static/app.js` -> sem erros.

## Proximo passo recomendado

1. Revisar `docs/central-api-orchestrator.md`.
2. Decidir proxima fase: painel administrativo, executor local Windows ou recuperacao automatica.
3. Aprovar fase escolhida em `specs/central-api-orchestrator/tasks.md`.
4. Implementar com testes antes do codigo.

## Deploy VPS Movis em 2026-07-10

Documento operacional principal:

- `docs/operacao-vps-movisys.md`

Ambientes publicados:

- Producao: `https://www.movisystecnologia.com.br/PragSys/app`
- Dev/teste: `https://www.movisystecnologia.com.br/dev/app`

VPS:

- IP: `172.233.177.135`
- Usuario SSH atual: `root`
- Diretorio producao: `/opt/syspragas/prod`
- Diretorio dev: `/opt/syspragas/dev`

Containers validados:

- `syspragas-prod`: `8011 -> 8000`
- `syspragas-dev`: `8012 -> 8000`
- `syspragas-whatsapp-bridge-prod`: `127.0.0.1:3111 -> 3100`
- `syspragas-whatsapp-bridge-dev`: `127.0.0.1:3112 -> 3100`

Integracoes:

- Google OAuth configurado em producao e dev.
- WhatsApp QR configurado via `services/whatsapp-bridge`.
- QR Code gerado com sucesso em prod e dev; status esperado antes da leitura: `aguardando_conexao`.

Validacoes:

- HTTPS publico com `www`: HTTP 200 em `/PragSys/app` e `/dev/app`.
- `pytest tests/test_whatsapp_integration.py -q` -> `15 passed`.
- `node --check app/interfaces/web/static/app.js` -> sem erros.
- `node --check services/whatsapp-bridge/src/server.js` -> sem erros.
- `docker compose --env-file deploy\env\.env.prod.example --profile whatsapp-bridge config --quiet` -> sem erros.

Seguranca:

- Senhas, tokens, OAuth secret e chaves nao foram registrados em docs versionados.
- Arquivo local ignorado criado: `tools/local/ACESSOS_CRITICOS.local.md`.
- Pendencia: trocar senha root enviada em chat e migrar SSH para usuario/chave de deploy.
