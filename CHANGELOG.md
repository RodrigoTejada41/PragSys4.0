# Changelog

## [4.0.0] - 2026-03-25

- Inicio formal da remodelacao arquitetural do produto como release maior.
- Versionamento elevado para 4.0.0 em `pyproject.toml` e metadados da aplicacao.
- Runtime local e runtime em rede documentados e suportados por scripts dedicados.
- Docker rebaixado para opcao complementar, nao mais como requisito principal de operacao.
- Mecanismo de migracao de schema reorganizado com rastreio em `schema_migrations`.
- Fundacao de multempresa introduzida no schema com `empresa_prestadora_id` nas entidades operacionais centrais.
- Logging basico centralizado e payload de autenticacao preparado para transportar contexto de empresa.
- Base documental expandida para arquitetura alvo, operacao local/rede, publicacao no GitHub e relatorio tecnico da release.
- Nova pasta de release criada sem sobrescrever a base anterior: `release/SysPragas-4.0.0`.

## [3.1.0] - 2026-03-21

- Reestruturacao da interface administrativa da Ordem de Servico, com separacao entre cadastro e ordens registradas.
- Validacao reforcada do salvamento da OS, fluxo de impressao e emissao de certificado sanitario.
- Melhorias visuais no modulo de OS, produtos aplicados, botoes de acao e responsividade.
- Suporte a fotos anexadas na Ordem de Servico.
- Docker configurado e validado para execucao da aplicacao.
- Base de documentacao tecnica adicionada em `docs/`, com arquitetura, API, padroes de codigo e processo de entrega.
- Novo modulo de agendamento integrado a clientes, tecnicos, Ordem de Servico e historico operacional.
- Preparacao da integracao com Google Agenda e testes automatizados do fluxo de agenda.

## [3.2.6] - 2026-03-25

- Compatibilidade de anotacoes de tipo ajustada para preservar suporte ao Python 3.9 nos modulos fiscal, agendamento, recibos, Google Calendar, NF-e e WhatsApp.
- Ambiente virtual principal `.venv` reparado e realinhado com as dependencias declaradas do projeto.
- Suite automatizada validada com sucesso no fluxo padrao de desenvolvimento: `53 passed`.
