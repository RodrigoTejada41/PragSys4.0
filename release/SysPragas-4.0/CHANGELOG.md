# Changelog

## [4.0.0] - 2026-03-24

- consolidacao da release 4.0 em pasta dedicada e isolada da versao anterior
- atualizacao do versionamento da aplicacao, metadados do pacote e endpoint de health
- padronizacao dos assets de certificado com `modelos/` e `assinaturas_tecnicas/`
- suporte a status operacional de WhatsApp e gestao de conexao do Google Agenda
- alinhamento do README com capacidades reais da plataforma e links relativos da documentacao
- geracao do relatorio tecnico de QA da release em `docs/reports/qa-report-v4.0.md`

## [3.2.5] - Em desenvolvimento

- linha de desenvolvimento imediatamente anterior a consolidacao da release 4.0

## [3.1.0] - 2026-03-21

- reestruturacao da interface administrativa da Ordem de Servico, com separacao entre cadastro e ordens registradas
- validacao reforcada do salvamento da OS, fluxo de impressao e emissao de certificado sanitario
- melhorias visuais no modulo de OS, produtos aplicados, botoes de acao e responsividade
- suporte a fotos anexadas na Ordem de Servico
- Docker configurado e validado para execucao da aplicacao
- base de documentacao tecnica adicionada em `docs/`, com arquitetura, API, padroes de codigo e processo de entrega
- novo modulo de agendamento integrado a clientes, tecnicos, Ordem de Servico e historico operacional
- preparacao da integracao com Google Agenda e testes automatizados do fluxo de agenda
