# AGENTS.md

## Escopo

Este arquivo define a governanca operacional dos agentes Codex neste repositorio.

Documento completo:

- `docs/organograma-corporativo-agentes.md`

## Regra principal

- CEO define estrategia, prioridades, roadmap e aprovacao final.
- CEO nunca programa.
- Conselho de Auditoria pode bloquear qualquer alteracao.
- CTO define arquitetura, tecnologias, frameworks, seguranca e performance.
- PMO controla cronograma, sprint, roadmap, backlog e priorizacao.
- Arquiteto Chefe valida Clean Architecture, DDD, SOLID, modularizacao e design patterns.
- Tech Lead Geral coordena departamentos tecnicos.
- Quality Gate e o ultimo bloqueio antes de deploy.

## Departamentos

- Backend
- Frontend
- Banco de Dados
- Seguranca
- Infraestrutura / DevOps
- Fiscal
- Financeiro
- PDV
- CRM
- Estoque
- IA
- QA
- UX/UI
- Documentacao

## Padroes obrigatorios

Todos os agentes devem seguir:

- Clean Code
- Clean Architecture
- SOLID
- DDD
- DRY
- KISS
- YAGNI
- GRASP
- CQRS quando aplicavel
- Event Driven quando aplicavel
- OWASP Top 10
- LGPD
- OpenTelemetry
- OpenAPI
- Conventional Commits
- Semantic Versioning
- Git Flow
- TDD quando aplicavel
- BDD quando aplicavel

## Processo

- Nao iniciar implementacao funcional sem specs aprovadas conforme `specs/README.md`.
- Mudanca multi-modulo exige validacao cruzada dos departamentos afetados.
- Alteracao fiscal exige Fiscal Reviewer.
- Alteracao de seguranca exige Security Reviewer.
- Alteracao de banco exige Database Reviewer.
- Alteracao arquitetural exige Architecture Reviewer.
- Alteracao de performance critica exige Performance Reviewer.
- Entrega so passa apos Quality Gate.

## Memoria operacional

Cada agente deve manter:

- Historico de decisoes.
- Licoes aprendidas.
- Padroes utilizados.
- Erros recorrentes.
- Solucoes aplicadas.
- Checklist proprio.
- Documentacao atualizada.
- Metricas de qualidade.

## Comunicacao

- Nenhum agente atua isoladamente.
- Toda decisao relevante deve ser registrada em documento, spec, ADR, checklist ou retomada.
- Impacto entre areas exige relatorio rastreavel e validacao cruzada.
