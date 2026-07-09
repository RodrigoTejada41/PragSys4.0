# Module Map

Status: Draft inicial
Approver: TBD
Approval date: TBD
Approval reference: TBD

## Mapa

| Modulo SDD | Diretorios principais | Responsabilidade |
|---|---|---|
| `core-domain` | `app/core`, `app/domain` | Configuracao, seguranca base, enums e conceitos centrais. |
| `application-services` | `app/application` | Schemas, casos de uso e regras de negocio. |
| `infrastructure-db` | `app/infrastructure`, `runtime`, `uploads` | Banco, modelos, migracoes, persistencia e arquivos runtime. |
| `interfaces-web-api` | `app/interfaces` | Rotas HTTP, templates, assets e contratos externos da UI/API. |
| `auth-security` | `app/core/security*`, rotas de auth, docs de RBAC | Autenticacao, autorizacao, permissoes e protecao de dados. |
| `multitenancy` | modelos com `empresa_prestadora_id`, docs multempresa | Isolamento logico por empresa prestadora. |
| `customers-contracts` | clientes, contratos, prestadoras | Cadastro comercial e relacao contratual. |
| `work-orders` | ordens de servico, agenda, assinaturas | Fluxo operacional de atendimento tecnico. |
| `finance-nfe` | financeiro, NF-e, SEFAZ, DANFE | Faturamento, documentos fiscais e integracoes fiscais. |
| `documents-reports` | documentos, PDFs, relatorios | Geracao documental e consultas gerenciais. |
| `whatsapp` | `app/modules/whatsapp`, `services`, scripts bridge | QR bridge, envio de mensagens e integracoes WhatsApp. |
| `deployment-quality` | `scripts`, `deploy`, `.github`, `tests`, configs | Execucao, CI, release, testes e qualidade. |
| `central-api-orchestrator` | `app/modules/central_orchestrator`, `app/application`, `app/infrastructure`, `app/interfaces/api`, `app/interfaces/web` | Orquestracao, service discovery, health check, comandos operacionais, recuperacao automatica e painel central de servicos. |

## Regra de manutencao

Ao criar novo modulo funcional, registrar aqui antes de iniciar implementacao.
