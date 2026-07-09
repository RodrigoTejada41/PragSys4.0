# Central API Orchestrator

Status: MVP implementado
Data: 2026-07-09

## Objetivo

Centralizar cadastro, descoberta, health check, dependencias e auditoria de comandos operacionais dos servicos do ecossistema SysPragas.

## Escopo do MVP

- Cadastro de servicos gerenciados.
- Registro de dependencias entre servicos.
- Listagem de dependencias.
- Health check por `health_url`.
- Historico de health check.
- Auditoria de comando `reload`.
- Permissoes RBAC dedicadas.

## Endpoints

- `GET /api/v1/orchestrator/services`
- `POST /api/v1/orchestrator/services`
- `GET /api/v1/orchestrator/services/{service_id}`
- `GET /api/v1/orchestrator/services/{service_id}/health`
- `GET /api/v1/orchestrator/services/{service_id}/history`
- `POST /api/v1/orchestrator/services/{service_id}/start`
- `POST /api/v1/orchestrator/services/{service_id}/stop`
- `POST /api/v1/orchestrator/services/{service_id}/restart`
- `POST /api/v1/orchestrator/services/{service_id}/reload`
- `GET /api/v1/orchestrator/dependencies`
- `POST /api/v1/orchestrator/diagnostics`
- `POST /api/v1/orchestrator/recovery/run`

## Permissoes

- `orchestrator.view`: consultar servicos, dependencias e health.
- `orchestrator.manage`: cadastrar servicos.
- `orchestrator.command`: executar comandos administrativos.
- `orchestrator.logs`: reservado para logs.
- `orchestrator.audit`: reservado para auditoria detalhada.

## Tabelas

- `managed_services`
- `service_dependencies`
- `service_health_checks`
- `service_command_audit`

## Limites atuais

- Comandos de servicos externos registram auditoria como aceitos.
- Executor `local_windows` so executa comandos cadastrados na allowlist interna.
- Execucao local usa `subprocess.run` com `shell=False`.
- Docker fica para fase seguinte.
- Nao remover comunicacao legada entre modulos sem nova aprovacao SDD.

## Diagnostico operacional

O endpoint `POST /api/v1/orchestrator/diagnostics` valida:

- Portas duplicadas.
- Servicos sem `health_url`.
- Dependencias nao resolvidas.

Status possiveis:

- `ok`: sem problemas.
- `warning`: um ou mais problemas encontrados.

## Historico operacional

O endpoint `GET /api/v1/orchestrator/services/{service_id}/history` retorna:

- Ultimos health checks persistidos.
- Ultimos comandos administrativos auditados.

Limite atual:

- Ate 50 health checks.
- Ate 50 comandos auditados.

## Recuperacao automatica segura

O endpoint `POST /api/v1/orchestrator/recovery/run` avalia servicos com:

- `recovery_policy = restart_on_failure`.
- `status` igual a `unhealthy` ou `degraded`.

Comportamento:

- Audita `restart` quando ainda ha tentativas disponiveis.
- Bloqueia quando `max_restart_attempts` foi atingido.
- Nao executa processo real para executor externo.
- Executa executor local Windows somente se houver allowlist interna configurada.

## Painel administrativo

O painel fica em Configuracoes do sistema.

Recursos:

- Listagem de servicos.
- Status, tipo e porta.
- Diagnostico operacional.
- Recuperacao manual.
- Comandos `restart` e `reload`.

## Validacao

Comandos executados:

```powershell
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_lifecycle_full
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_lifecycle_regression
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_diag_full
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_diag_regression
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_history_full
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_history_regression
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_executor_full
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_central_api_orchestrator.py tests\test_web_ui.py -q --basetemp=.pytest_tmp_orchestrator_panel_full
.\.venv_rebuilt\Scripts\python.exe -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py tests\test_web_ui.py -q --basetemp=.pytest_tmp_orchestrator_final_all
.\.venv_rebuilt\Scripts\python.exe -c "from app.main import app; print('app import ok')"
```

Resultados:

- `4 passed in 33.94s`
- `5 passed in 26.31s`
- `12 passed in 31.44s`
- `6 passed in 28.23s`
- `13 passed in 30.05s`
- `7 passed in 29.59s`
- `14 passed in 30.49s`
- `9 passed in 45.97s`
- `13 passed in 30.18s`
- `20 passed in 31.21s`
- `app import ok`
