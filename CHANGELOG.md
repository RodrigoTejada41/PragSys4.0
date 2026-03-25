# Changelog

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
