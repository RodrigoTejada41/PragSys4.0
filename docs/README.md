# Base de Documentacao Tecnica

Este diretorio concentra a documentacao estruturada do projeto para apoiar manutencao, onboarding e evolucao arquitetural.

## Mapa dos documentos

- `architecture-v4.0.0.md`: arquitetura alvo da remodelacao 4.0.0, com foco em operacao local/rede e multempresa.
- `functional-specification.md`: escopo funcional, modulos e regras de negocio.
- `architecture.md`: arquitetura atual, limites entre camadas, decisoes e principios SOLID.
- `api-reference.md`: contratos principais da API REST, autenticacao e convencoes.
- `code-standards.md`: padroes de clean code, organizacao de codigo, testes e refatoracao.
- `delivery-process.md`: versionamento, fluxo de PR e operacao em Agile/Scrum.
- `installation-local.md`: como instalar e executar o sistema localmente sem Docker.
- `installation-network.md`: como executar o sistema em rede interna.
- `multitenancy-architecture.md`: estrategia tecnica de multempresa por `empresa_prestadora_id`.
- `github-publishing.md`: padrao de organizacao e publicacao do repositorio.
- `technical-report-4.0.0.md`: relatorio tecnico consolidado da fase 4.0.0.
- `financial-nfe-module.md`: integracao entre financeiro, NF-e, Simples Nacional e apoio fiscal por NCM.
- `sefaz-direct-nfe-module.md`: arquitetura e configuracao da emissao direta de NF-e com SEFAZ.
- `validation-review-2026-03-25.md`: registro da revisao tecnica do worktree, diagnostico do ambiente Python e validacao da suite.
- `adr/ADR-0001-layered-modular-monolith.md`: decisao arquitetural base do sistema.

## Como usar esta base

- consulte `functional-specification.md` antes de alterar regras de negocio;
- consulte `architecture-v4.0.0.md` ao planejar refactor estrutural, operacao em rede ou multempresa;
- consulte `architecture.md` antes de mover responsabilidades entre modulos;
- consulte `api-reference.md` antes de mudar contratos HTTP;
- consulte `installation-local.md` e `installation-network.md` antes de subir ambientes;
- consulte `multitenancy-architecture.md` antes de tocar em isolamento por empresa;
- consulte `github-publishing.md` antes de preparar entrega para GitHub;
- consulte `technical-report-4.0.0.md` para entender o escopo tecnico da release maior;
- consulte `financial-nfe-module.md` antes de evoluir cobranca, emissao de NF-e ou regras fiscais;
- consulte `sefaz-direct-nfe-module.md` antes de ativar ou ajustar a emissao direta pela SEFAZ;
- consulte `validation-review-2026-03-25.md` para entender o diagnostico recente do ambiente e a validacao executada no repositorio;
- consulte `code-standards.md` antes de abrir PR de refactor ou feature;
- consulte `delivery-process.md` para planejar e acompanhar trabalho em sprint.
