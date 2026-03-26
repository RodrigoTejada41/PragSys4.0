# Changelog

## [4.1.1] - 2026-03-26

- Modulo de contratos integrado ao cadastro de clientes com entidade propria, relacionamento `1:N`, status automatico e dashboard de alertas.
- Cadastro de clientes passou a suportar `email` opcional para habilitar notificacoes contratuais sem quebrar compatibilidade com registros existentes.
- Upload, visualizacao, download e substituicao de arquivos contratuais adicionados com armazenamento local configuravel e validacao de tipo/tamanho.
- Configuracoes dinamicas passaram a incluir antecedencia do alerta contratual, chave de envio automatico por e-mail e diretorio de armazenamento.
- Rotina automatica diaria de contratos adicionada no `lifespan` da aplicacao para recalculo de status e disparo de notificacoes SMTP.
- API expandida com endpoints de contratos globais, contratos por cliente, dashboard contratual, arquivo e rotina administrativa de sincronizacao.
- Interface web de clientes ganhou area dedicada para contratos, com selecao por cliente, resumo operacional e acoes de arquivo.
- Dashboard passou a destacar contratos a vencer e vencidos no radar operacional.
- Documentacao tecnica adicionada para o modulo em `docs/contracts-module.md` e referencias funcionais/API atualizadas.
- Suite validada apos a entrega com `84 passed in 46.98s`.

## [4.1.0] - 2026-03-26

- Versionamento elevado para `4.1.0` em `pyproject.toml`, configuracao da aplicacao e `.env.example`.
- Registro de release `release/SysPragas-4.1` criado para backup versionado no repositrio.
- Infraestrutura de testes otimizada com banco-template por processo, reducao de I/O repetitivo e assets temporarios compartilhados por sessao.
- Custo de hash de senha tornou-se configuravel, preservando padrao forte em runtime real e permitindo execucao de testes mais leve.
- Fixture de autenticacao passou a emitir token direto sobre o usuario seeded, evitando login HTTP repetitivo na suite.
- Consultas frequentes receberam indices dedicados e migracao de performance segura para `produtos`, `financeiro`, `os_produtos` e `os_pragas`.
- Carregamento ORM das colecoes de Ordem de Servico foi ajustado para `selectinload`, reduzindo custo de consultas com relacionamentos.
- Suite passou a expor marcadores `unit`, `integration`, `documents` e `external` para execucao seletiva em desenvolvimento e CI.
- Suite completa revalidada apos as mudancas com reducao de tempo de aproximadamente 14m30s para cerca de 42s.

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
- Modulo de WhatsApp evoluido para suportar sessao por QR Code, status persistente da conexao e botao dedicado de conexao na agenda e nas configuracoes.
- Bridge opcional de WhatsApp via `Baileys` adicionada ao repositorio para execucao local, em rede interna ou via Docker profile.

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
