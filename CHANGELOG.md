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
- Menu centralizado de `Configuracoes` introduzido na interface web para governanca de integracoes, parametros operacionais, multiempresa e ambiente.
- Persistencia de configuracoes dinamicas adicionada com tabela `system_settings`, seed automatica e endpoint administrativo `/api/v1/settings`.
- Frontend reorganizado com area administrativa mais limpa, agrupamento por contexto operacional e painel dedicado para Google Agenda, WhatsApp, usuarios e ambiente.
- Integracoes Google Agenda e WhatsApp passaram a respeitar configuracoes persistidas sem quebrar o comportamento legado por ambiente.
- Formularios de agendamento e Ordem de Servico passaram a obedecer o padrao configuravel de sincronizacao Google.
- Suite de regressao expandida para cobrir acesso ao menu de configuracoes, atualizacao de settings e alternancia do modo multiempresa.
- Fluxo OAuth do Google Agenda ajustado para reativar automaticamente a integracao ao conectar uma conta.
- Persistencia da sessao Google estabilizada para contexto de empresa prestadora e expiracao de token com timezone legado.
- Eventos enviados ao Google Agenda passaram a incluir endereco, telefone, tecnico, horario detalhado e duracao prevista.
- Titulo do evento do Google Agenda passou a usar o padrao `Cliente | Tecnico | Hora`.
- Cards de agendamento passaram a expor botao explicito de sincronizacao/reenvio com Google e mensagens operacionais mais claras em caso de falha.

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
