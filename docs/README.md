# Base de Documentacao Tecnica

Este diretorio concentra a documentacao estruturada do projeto para apoiar manutencao, onboarding e evolucao arquitetural.

## Mapa dos documentos

- `architecture-v4.0.0.md`: arquitetura alvo da remodelacao 4.0.0, com foco em operacao local/rede e multempresa.
- `functional-specification.md`: escopo funcional, modulos e regras de negocio.
- `architecture.md`: arquitetura atual, limites entre camadas, decisoes e principios SOLID.
- `ESTADO_ATUAL_PROJETO.md`: checkpoint atual para retomada do projeto.
- `organograma-estado-atual-projeto.md`: organograma tecnico e estado operacional atual do projeto.
- `manual-instalacao-completo.md`: instalacao local, Docker, VPS, comandos, backup e troubleshooting para operadores iniciantes.
- `decisions/2026-07-09-spec-driven-development.md`: decisao de Spec-Driven Development na raiz do projeto.
- `organograma-corporativo-agentes.md`: governanca corporativa dos agentes Codex, departamentos, revisores e Quality Gate.
- `decisions/2026-07-09-central-api-orchestrator.md`: decisao proposta para API Central Orchestrator / Service Manager.
- `central-api-orchestrator.md`: endpoints, permissoes, tabelas e limites do MVP da API Central.
- `certificado-digital.md`: modulo central de certificado A1, API, seguranca, auditoria e integracao fiscal.
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
- `operacao-vps-movisys.md`: estado operacional da VPS Movis Tecnologia, DNS, Nginx, HTTPS, containers, Google OAuth e WhatsApp QR sem segredos.
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
- consulte `ESTADO_ATUAL_PROJETO.md` e `../RETOMADA_EXATA.md` antes de retomar trabalho pausado;
- consulte `organograma-estado-atual-projeto.md` para entender modulos, ambientes e estado operacional atual;
- consulte `manual-instalacao-completo.md` para instalar, atualizar, testar, fazer backup ou diagnosticar erros comuns;
- consulte `../specs/README.md` antes de iniciar nova implementacao;
- consulte `organograma-corporativo-agentes.md` e `../AGENTS.md` para regras de atuacao dos agentes;
- consulte `../specs/central-api-orchestrator/` antes de implementar API Central, service discovery, health check ou gerenciamento de servicos;
- consulte `central-api-orchestrator.md` antes de operar ou evoluir o MVP da API Central;
- consulte `certificado-digital.md` antes de alterar certificado A1, assinatura XML, SEFAZ ou emissao fiscal;
- consulte `api-reference.md` antes de mudar contratos HTTP;
- consulte `installation-local.md` e `installation-network.md` antes de subir ambientes;
- consulte `multitenancy-architecture.md` antes de tocar em isolamento por empresa;
- consulte `contracts-module.md` antes de alterar vencimento, arquivos ou notificacoes contratuais;
- consulte `database-admin.md` antes de alterar backup, restauracao ou limpeza operacional do banco;
- consulte `design-system.md` antes de alterar formularios, campos e padroes visuais compartilhados;
- consulte `cicd-linode.md` antes de alterar pipeline, deploy remoto ou estrutura de release operacional;
- consulte `operacao-vps-movisys.md` antes de acessar a VPS, validar ambiente publicado ou alterar DNS/Nginx/containers;
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
