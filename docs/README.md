# Base de Documentacao Tecnica

Este diretorio concentra a documentacao estruturada do projeto para apoiar manutencao, onboarding e evolucao arquitetural.

## Mapa dos documentos

- `functional-specification.md`: escopo funcional, modulos e regras de negocio.
- `architecture.md`: arquitetura atual, limites entre camadas, decisoes e principios SOLID.
- `api-reference.md`: contratos principais da API REST, autenticacao e convencoes.
- `code-standards.md`: padroes de clean code, organizacao de codigo, testes e refatoracao.
- `delivery-process.md`: versionamento, fluxo de PR e operacao em Agile/Scrum.
- `adr/ADR-0001-layered-modular-monolith.md`: decisao arquitetural base do sistema.

## Como usar esta base

- consulte `functional-specification.md` antes de alterar regras de negocio;
- consulte `architecture.md` antes de mover responsabilidades entre modulos;
- consulte `api-reference.md` antes de mudar contratos HTTP;
- consulte `code-standards.md` antes de abrir PR de refactor ou feature;
- consulte `delivery-process.md` para planejar e acompanhar trabalho em sprint.
