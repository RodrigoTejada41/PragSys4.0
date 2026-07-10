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

## Atualizacao operacional 2026-07-10

Ambientes publicados na VPS Movis Tecnologia:

- Producao: `https://www.movisystecnologia.com.br/PragSys/app`
- Dev/teste: `https://www.movisystecnologia.com.br/dev/app`

Documento operacional:

- `docs/operacao-vps-movisys.md`

Estado validado:

- DNS publico aponta para `172.233.177.135`.
- Nginx com HTTPS ativo via Let's Encrypt.
- Containers `syspragas-prod`, `syspragas-dev`, `syspragas-whatsapp-bridge-prod` e `syspragas-whatsapp-bridge-dev` saudaveis.
- Google OAuth configurado em producao e dev.
- WhatsApp QR via bridge Baileys configurado em producao e dev.
- Teste focado: `pytest tests/test_whatsapp_integration.py -q` -> `15 passed`.

Segredos e senhas nao foram registrados em documentacao versionada.
