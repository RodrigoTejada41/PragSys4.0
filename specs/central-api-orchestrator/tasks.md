# Central API Orchestrator Tasks

Status: Aprovado
Approver: Rodrigo Tejada
Approval date: 2026-07-09
Approval reference: chat:2026-07-09:pode-continuar-central-api-orchestrator

## Tarefas

- [x] Confirmar spec aprovada.
- [x] Confirmar plan aprovado.
- [x] Confirmar tasks aprovadas.
- [x] Registrar aprovacao em `specs/approval-log.md`.
- [x] Definir permissoes RBAC.
- [x] Criar enums e schemas.
- [x] Criar modelos e migracoes.
- [ ] Criar repository/DAO.
- [x] Criar servico de validacao de dependencias.
- [x] Criar servico de health check.
- [x] Criar servico de eventos e historico.
- [x] Criar servico de comando operacional.
- [x] Criar politica de recuperacao automatica.
- [x] Criar endpoints administrativos.
- [x] Criar painel administrativo.
- [ ] Integrar com Agente Local Windows.
- [x] Criar testes unitarios.
- [x] Criar testes de integracao.
- [x] Criar testes de permissao.
- [ ] Criar testes de UI quando aplicavel.
- [x] Atualizar documentacao operacional.
- [x] Executar validacao local.
- [x] Registrar evidencias.
- [ ] Submeter para revisores.
- [ ] Submeter para Quality Gate.

## Evidencias

- `python -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator` -> `4 passed in 33.94s`.
- `python -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_final` -> `11 passed in 39.61s`.
- `python -m pytest tests\test_central_api_orchestrator.py::test_orchestrator_lifecycle_commands_are_audited_without_process_execution -q --basetemp=.pytest_tmp_orchestrator_lifecycle_green` -> `1 passed in 29.84s`.
- `python -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_lifecycle_full` -> `5 passed in 26.31s`.
- `python -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_lifecycle_regression` -> `12 passed in 31.44s`.
- `python -m pytest tests\test_central_api_orchestrator.py::test_orchestrator_diagnostics_reports_port_conflicts_and_missing_health_url -q --basetemp=.pytest_tmp_orchestrator_diag_green` -> `1 passed in 23.66s`.
- `python -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_diag_full` -> `6 passed in 28.23s`.
- `python -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_diag_regression` -> `13 passed in 30.05s`.
- `python -m pytest tests\test_central_api_orchestrator.py::test_orchestrator_service_detail_and_history_expose_health_and_commands -q --basetemp=.pytest_tmp_orchestrator_history_green` -> `1 passed in 27.27s`.
- `python -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_history_full` -> `7 passed in 29.59s`.
- `python -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_history_regression` -> `14 passed in 30.49s`.
- `python -m pytest tests\test_central_api_orchestrator.py::test_orchestrator_recovery_restarts_unhealthy_service_until_attempt_limit -q --basetemp=.pytest_tmp_orchestrator_recovery_green` -> `1 passed in 36.01s`.
- `python -m pytest tests\test_central_api_orchestrator.py::test_orchestrator_local_windows_executor_runs_only_allowlisted_command -q --basetemp=.pytest_tmp_orchestrator_executor_green` -> `1 passed in 45.27s`.
- `python -m pytest tests\test_central_api_orchestrator.py -q --basetemp=.pytest_tmp_orchestrator_executor_full` -> `9 passed in 45.97s`.
- `python -m pytest tests\test_web_ui.py::test_static_app_js_includes_appointment_availability_feedback -q --basetemp=.pytest_tmp_orchestrator_panel_green` -> `1 passed in 24.16s`.
- `node --check app\interfaces\web\static\app.js` -> sem erros.
- `python -m pytest tests\test_central_api_orchestrator.py tests\test_web_ui.py -q --basetemp=.pytest_tmp_orchestrator_panel_full` -> `13 passed in 30.18s`.
- `python -m pytest tests\test_access_control.py tests\test_auth.py tests\test_central_api_orchestrator.py tests\test_web_ui.py -q --basetemp=.pytest_tmp_orchestrator_final_all` -> `20 passed in 31.21s`.
- `python -c "from app.main import app; print('app import ok')"` -> `app import ok`.

## Bloqueios conhecidos

- Fases seguintes seguem bloqueadas ate nova aprovacao ou priorizacao explicita.
- Escopo exige validacao cruzada de Backend, Banco, Seguranca, Infraestrutura, QA, UX/UI, Documentacao e Fiscal quando envolver Motor Fiscal, NF-e, NFC-e ou certificado.
