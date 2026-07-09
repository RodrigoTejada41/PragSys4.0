# Estado Atual Do Projeto

Data: 2026-07-09
Projeto: SysPragas 4.1.0
Raiz: `E:\Projetos\Controle_de_Pragas4.0`
Branch: `main`
HEAD: `8adeea1 docs: add dev demo seed handoff summary`

## Estado operacional

Projeto com arquitetura documentada como monolito modular em camadas:

- `app/core`
- `app/domain`
- `app/application`
- `app/infrastructure`
- `app/interfaces`
- `app/modules`

## Mudanca registrada nesta etapa

Foi adicionada governanca Spec-Driven Development na raiz do projeto.

Entrada principal:

- `specs/README.md`

Fluxo obrigatorio:

`SPEC -> PLAN -> TASKS -> IMPLEMENTATION`

## Modulos SDD iniciais

- `core-domain`
- `application-services`
- `infrastructure-db`
- `interfaces-web-api`
- `auth-security`
- `multitenancy`
- `customers-contracts`
- `work-orders`
- `finance-nfe`
- `documents-reports`
- `whatsapp`
- `deployment-quality`

## Decisao arquitetural registrada

- `docs/decisions/2026-07-09-spec-driven-development.md`

## Regras vigentes

- Nao iniciar codigo sem spec, plan e tasks aprovados.
- Mudanca multi-modulo exige aprovacao de todos os modulos afetados.
- Seguranca, fiscal, multempresa e dados sensiveis exigem aprovacao explicita.
- Preservar arquitetura em camadas descrita em `docs/architecture.md`.

## Pendencias

- Aprovar ou ajustar os artefatos SDD criados.
- Atualizar `specs/approval-log.md` quando houver aprovacao real.
- Revisar alteracoes preexistentes no worktree antes de qualquer commit.
- Decidir se `movisys_motor_fiscal_completo/` deve permanecer no mesmo repositorio ou ser separado.

## Validacao

Foi feita validacao documental por listagem dos arquivos criados.

Nao foram executados testes automatizados nesta etapa.
Motivo: mudanca restrita a documentacao/processo.

## Retomada

Para continuar, abrir primeiro:

- `RETOMADA_EXATA.md`
- `specs/README.md`
- `specs/module-map.md`

