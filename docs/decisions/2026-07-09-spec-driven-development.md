# Decision: Spec-Driven Development No SysPragas

Date: 2026-07-09

## Context

O projeto possui modulos fiscais, financeiros, operacionais, autenticacao, multempresa, documentos, WhatsApp e deploy local/rede. Implementacao direta sem especificacao aumenta risco de regressao e acoplamento.

## Decision

Criar `specs/` na raiz do projeto com um fluxo obrigatorio:

`SPEC -> PLAN -> TASKS -> IMPLEMENTATION`

Cada modulo deve manter:

- `spec.md`
- `plan.md`
- `tasks.md`

Codigo so deve iniciar quando os tres arquivos do modulo estiverem aprovados.

## Quality Gates

- Respeitar arquitetura em camadas definida em `docs/architecture.md`.
- Validar entrada, permissao e isolamento multempresa.
- Usar queries parametrizadas ou ORM de forma segura.
- Manter logs e auditoria para acoes criticas.
- Atualizar testes e documentacao afetada.
- Registrar riscos fiscais, seguranca e rollback quando aplicavel.

## Consequences

- Novas features iniciam por documentacao.
- Mudancas multi-modulo exigem aprovacao de todos os modulos afetados.
- Implementacoes ficam rastreaveis por modulo, criterio de aceite e evidencia.

