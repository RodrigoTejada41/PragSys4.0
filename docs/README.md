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
- `contracts-module.md`: modulo de contratos com arquivos, vencimento, notificacoes e rotina automatica.
- `database-admin.md`: backup, restauracao e limpeza operacional do banco SQLite com foco em uso local e offline.
- `design-system.md`: tokens visuais, padronizacao de formularios e arquitetura de componentes de interface.
- `cicd-linode.md`: pipeline GitHub Actions com deploy automatizado para `dev` e `production`, incluindo bootstrap da VPS, script remoto e operacao de rollback na Linode.
- `backend-hardening-2026-03-27.md`: melhorias de seguranca e robustez aplicadas no backend em runtime, settings e scheduler.
- `github-actions-secrets.md`: checklist de segredos e variaveis necessarios para o CI/CD remoto.
- `whatsapp-qr-bridge.md`: execucao e configuracao do bridge local de WhatsApp com QR Code baseado em Baileys.
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
- consulte `contracts-module.md` antes de alterar vencimento, arquivos ou notificacoes contratuais;
- consulte `database-admin.md` antes de alterar backup, restauracao ou limpeza operacional do banco;
- consulte `design-system.md` antes de alterar formularios, campos e padroes visuais compartilhados;
- consulte `cicd-linode.md` antes de alterar pipeline, deploy remoto ou estrutura de release operacional;
- consulte `backend-hardening-2026-03-27.md` antes de alterar bootstrap seguro, scheduler diario ou persistencia de secrets em settings;
- consulte `github-actions-secrets.md` ao configurar GitHub Actions, SSH e variaveis por ambiente;
- consulte `whatsapp-qr-bridge.md` antes de ativar ou manter a integracao de WhatsApp por QR Code;
- consulte `github-publishing.md` antes de preparar entrega para GitHub;
- consulte `technical-report-4.0.0.md` para entender o escopo tecnico da release maior;
- consulte `financial-nfe-module.md` antes de evoluir cobranca, emissao de NF-e ou regras fiscais;
- consulte `sefaz-direct-nfe-module.md` antes de ativar ou ajustar a emissao direta pela SEFAZ;
- consulte `validation-review-2026-03-25.md` para entender o diagnostico recente do ambiente e a validacao executada no repositorio;
- consulte `code-standards.md` antes de abrir PR de refactor ou feature;
- consulte `delivery-process.md` para planejar e acompanhar trabalho em sprint.
