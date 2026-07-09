# Central API Orchestrator Plan

Status: Aprovado
Approver: Rodrigo Tejada
Approval date: 2026-07-09
Approval reference: chat:2026-07-09:pode-continuar-central-api-orchestrator

## Estrategia

- Implementar primeiro como modulo interno do monolito modular.
- Isolar regras em camada de aplicacao.
- Manter persistencia em tabelas dedicadas.
- Expor API administrativa protegida.
- Integrar UI administrativa depois dos contratos backend.
- Suportar adaptadores de processo por ambiente: local Windows, processo Python, Docker e endpoint externo.
- Migrar comunicacao direta entre modulos somente em fases aprovadas.

## Impacto tecnico

- Camadas afetadas:
  - `app/application`
  - `app/infrastructure`
  - `app/interfaces/api`
  - `app/interfaces/web`
  - `app/core`
  - `app/modules`
- Tabelas afetadas:
  - Novas tabelas de servicos, dependencias, health checks, eventos, auditoria e versoes de configuracao.
- Endpoints afetados:
  - Novo grupo `/api/v1/orchestrator/*`.
  - Nova tela administrativa no frontend.
- Permissoes afetadas:
  - `orchestrator.view`
  - `orchestrator.manage`
  - `orchestrator.command`
  - `orchestrator.logs`
  - `orchestrator.audit`

## Fases

### Fase 1 - Contratos e modelo

1. Definir enums de status, tipo de servico, politica de recuperacao e tipo de executor.
2. Criar schemas de entrada e saida.
3. Criar modelos e migracoes.
4. Criar repository/DAO para servicos e historico.
5. Criar testes unitarios de validacao de dependencia.

### Fase 2 - Health check e descoberta

1. Implementar cliente HTTP de health check com timeout.
2. Implementar avaliacao de estado.
3. Persistir historico.
4. Expor endpoints de listagem, status e dependencias.
5. Criar testes de integracao da API.

### Fase 3 - Comandos operacionais

1. Criar interface de executor de processo.
2. Implementar executor seguro para servico externo por URL.
3. Implementar executor local Windows somente com allowlist de comandos.
4. Implementar start, stop, restart e reload.
5. Auditar todos os comandos.

### Fase 4 - Recuperacao automatica

1. Implementar politica de tentativas.
2. Implementar job periodico.
3. Evitar loop por janela temporal.
4. Registrar eventos de falha, recuperacao e esgotamento.
5. Criar testes de recuperacao.

### Fase 5 - Painel administrativo

1. Criar tela de servicos.
2. Exibir status, uptime, versao, recursos, ultimo erro e dependencias.
3. Adicionar comandos administrativos com confirmacao.
4. Adicionar logs e historico.
5. Validar responsividade e permissao.

### Fase 6 - Integracao Agente Local

1. Definir contrato entre API Central e Agente Local Windows.
2. Adicionar heartbeat do agente.
3. Adicionar diagnostico do ambiente local.
4. Adicionar recuperacao apos falha do sistema operacional.
5. Documentar instalacao e operacao.

## Ordem de execucao

1. Aprovar spec.
2. Aprovar plan.
3. Aprovar tasks.
4. Criar contratos backend.
5. Criar persistencia.
6. Implementar servico de orquestracao.
7. Expor endpoints.
8. Implementar testes.
9. Implementar painel.
10. Validar seguranca.
11. Validar arquitetura.
12. Passar pelo Quality Gate.

## Testes obrigatorios

- Unitarios para grafo de dependencias.
- Unitarios para politica de recuperacao.
- Unitarios para avaliacao de health check.
- Integracao para CRUD de servicos.
- Integracao para comandos administrativos.
- Teste de permissao/RBAC.
- Teste de auditoria.
- Teste de falha simulada e recuperacao.
- Teste de UI administrativa quando painel for implementado.

## Plano de rollback

- Manter modulo desativado por flag ate homologacao.
- Migracoes devem ser aditivas.
- Rotas novas nao devem alterar contratos existentes.
- Painel deve ser ocultado se permissao ou flag estiver indisponivel.
- Comunicacao direta legada permanece ate migracao explicita aprovada.

## Validacoes obrigatorias antes de deploy

- Code Reviewer.
- Security Reviewer.
- Architecture Reviewer.
- Database Reviewer.
- Performance Reviewer.
- Fiscal Reviewer se incluir servicos fiscais.
- Quality Gate.
