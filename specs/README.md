# SysPragas Specs

Status: Draft inicial.

Implementacao bloqueada por modulo ate aprovacao de `spec.md`, `plan.md` e `tasks.md`.

## Regra obrigatoria

Fluxo unico:

`SPEC -> PLAN -> TASKS -> IMPLEMENTATION`

Arquivos de controle:

- `module-map.md`: mapa entre diretorios do projeto e modulos SDD.
- `approval-log.md`: registro auditavel de aprovacoes.
- `_templates/`: modelos oficiais para novos modulos.

## Modulos iniciais

- `core-domain/`
- `application-services/`
- `infrastructure-db/`
- `interfaces-web-api/`
- `auth-security/`
- `multitenancy/`
- `customers-contracts/`
- `work-orders/`
- `finance-nfe/`
- `documents-reports/`
- `whatsapp/`
- `deployment-quality/`
- `central-api-orchestrator/`

## Regra de aprovacao

Cada arquivo deve registrar:

- Status.
- Approver.
- Approval date.
- Approval reference.

Valores validos de `Status`:

- `Draft inicial`: documento criado, nao aprovado.
- `Em revisao`: aguardando revisao tecnica.
- `Aprovado`: liberado para implementacao.
- `Reprovado`: bloqueado ate correcao.
- `Obsoleto`: substituido por outro documento.

Quem pode aprovar:

- Responsavel tecnico do modulo.
- Product owner ou responsavel operacional do fluxo.
- Responsavel fiscal para NF-e.
- Responsavel de seguranca para autenticacao, permissao, segredo, certificado ou dados sensiveis.

Formato de `Approval reference`:

- `chat:<data>:<resumo>`.
- `issue:<id>`.
- `pr:<id>`.
- `decision:<arquivo-em-docs-decisions>`.

## Regra para multiplos modulos

Uma alteracao que afeta mais de um modulo deve aprovar todos os `spec.md`, `plan.md` e `tasks.md` dos modulos afetados.

Sem aprovacao explicita, nao iniciar codigo.
