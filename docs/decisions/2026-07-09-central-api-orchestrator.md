# Decisao - Central API Orchestrator

Data: 2026-07-09
Status: Aprovado para MVP

## Contexto

Foi solicitado um nucleo operacional central para gerenciar servicos, APIs e processos do ecossistema SysPragas/ERP/PDV.

O objetivo e reduzir comunicacoes diretas entre modulos e centralizar descoberta, health check, logs, configuracao, autenticacao, comandos operacionais e recuperacao automatica.

## Decisao proposta

Criar o modulo SDD `central-api-orchestrator`.

Implementacao inicial proposta:

- Modulo interno do monolito modular.
- Rotas sob `/api/v1/orchestrator`.
- Persistencia dedicada para servicos, dependencias, health checks, eventos, auditoria e versoes de configuracao.
- Execucao protegida por permissoes especificas.
- Adaptadores de processo por ambiente.
- Painel administrativo apos contratos backend.

## Justificativa

- Evita acoplamento direto entre CRM, PDV, Comanda, Cozinha, Fiscal, Agente Local e demais modulos.
- Permite monitoramento centralizado.
- Cria base para recuperacao automatica e service discovery.
- Mantem migracao gradual, sem quebrar fluxos existentes.

## Restricoes

- Nao implementar comandos administrativos sem autenticacao e auditoria.
- Nao remover comunicacao legada antes de migracao aprovada.
- Nao expor controle de processo local sem allowlist.
- Nao ativar recuperacao automatica em producao sem homologacao.

## Modulos afetados

- `central-api-orchestrator`
- `application-services`
- `infrastructure-db`
- `interfaces-web-api`
- `auth-security`
- `deployment-quality`
- `whatsapp` quando incluir bridge.
- `finance-nfe` quando incluir Fiscal, NF-e, NFC-e, DANFE ou certificado.

## Status de aprovacao

Aprovado por Rodrigo Tejada em 2026-07-09 via `chat:2026-07-09:pode-continuar-central-api-orchestrator`.

Escopo inicial liberado: MVP interno com cadastro de servicos, dependencias, health check HTTP, historico, auditoria e endpoints administrativos protegidos.
