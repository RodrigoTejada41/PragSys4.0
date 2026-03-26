# Modulo de Contratos

## Objetivo

Adicionar gestao de contratos vinculados a clientes sem quebrar o fluxo operacional existente de cadastro, dashboard, financeiro e configuracoes.

## Escopo entregue

- entidade `contratos` relacionada em `1 cliente -> N contratos`;
- cadastro, edicao, exclusao e consulta de contratos;
- upload, substituicao, visualizacao e download de arquivo do contrato;
- classificacao automatica de status:
  - `ativo`
  - `a_vencer`
  - `vencido`
- dashboard com alertas de contratos e leitura de cobrancas em atraso;
- configuracoes persistidas para:
  - dias de antecedencia do alerta;
  - habilitacao de e-mail automatico;
  - diretorio de armazenamento dos arquivos;
- cobranca recorrente integrada ao modulo financeiro;
- relatorios sinteticos e analiticos de contratos com filtros;
- exportacao de relatorios em `.xlsx` e `.pdf`;
- rotina automatica diaria para:
  - recalcular status;
  - gerar cobrancas recorrentes sem duplicidade;
  - disparar notificacoes por e-mail quando aplicavel.

## Arquitetura aplicada

### Persistencia

- modelo SQLAlchemy em `app/infrastructure/models.py`;
- migracoes incrementais em `app/infrastructure/migrations.py`;
- arquivos armazenados em disco no diretorio configurado por `contract_storage_dir`, com nome interno unico por `UUID`;
- cobrancas recorrentes persistidas na tabela `financeiro`, usando `contrato_id` para navegacao cruzada entre contrato e contas a receber.

### Servicos

- regras de negocio centralizadas em `app/application/contracts_service.py`;
- scheduler leve em `app/application/contract_scheduler.py`;
- configuracoes centralizadas em `system_settings` via `app/application/settings_service.py`;
- exportacao `.xlsx` gerada de forma nativa em `app/application/xlsx_export.py`.

### API

Rotas principais:

- `GET /api/v1/contratos`
- `GET /api/v1/contratos/dashboard`
- `GET /api/v1/contratos/relatorios`
- `GET /api/v1/contratos/relatorios.xlsx`
- `GET /api/v1/contratos/relatorios.pdf`
- `GET /api/v1/contratos/{contract_id}`
- `PUT /api/v1/contratos/{contract_id}`
- `DELETE /api/v1/contratos/{contract_id}`
- `GET /api/v1/contratos/{contract_id}/arquivo`
- `POST /api/v1/contratos/rotina/sincronizar`
- `GET /api/v1/clientes/{customer_id}/contratos`
- `POST /api/v1/clientes/{customer_id}/contratos`

## Regras de negocio

- `data_vencimento` nao pode ser anterior a `data_inicio`;
- contratos com cobranca automatica exigem `valor_mensal > 0`;
- `tipo_cobranca` suportado:
  - `mensal`
  - `anual`
  - `personalizado`
- `dia_vencimento` usa o valor informado no contrato ou, na ausencia dele, o dia da data de vencimento contratual;
- status nao depende de acao manual do usuario;
- contrato vencido: `hoje > data_vencimento`;
- contrato a vencer: `data_vencimento - hoje <= contract_alert_days`;
- contrato ativo: fora da janela de alerta e ainda valido;
- arquivo aceito:
  - `.pdf`
  - `.doc`
  - `.docx`
  - `.png`
  - `.jpg`
  - `.jpeg`
  - `.txt`
- tamanho maximo do arquivo: `10 MB`;
- notificacao por e-mail so dispara quando:
  - `notifications_enabled = true`;
  - `contract_email_enabled = true`;
  - o cliente possui e-mail cadastrado;
  - o contrato entrou em estado `a_vencer` ou `vencido`;
  - a notificacao daquele estado ainda nao foi enviada;
- cobranca automatica so gera titulo para contratos `ativos` ou `a_vencer`;
- a referencia financeira do contrato usa chave deterministica por competencia para impedir duplicidade;
- contratos com cobrancas financeiras vinculadas nao podem ser excluidos, preservando rastreabilidade.

## Financeiro recorrente

- novos campos do contrato:
  - `valor_mensal`
  - `tipo_cobranca`
  - `dia_vencimento`
  - `gerar_cobranca_automatica`
- cada cobranca automatica gera um registro em `financeiro` com:
  - `tipo = receita`
  - `origem = contrato`
  - `contrato_id` preenchido
  - `cliente_id` herdado do contrato
  - `referencia` unica por periodo
- a tela do contrato passou a exibir resumo de cobrancas geradas, pendentes e vencidas;
- o relatorio analitico mostra a ultima cobranca e a situacao financeira consolidada do contrato.

## Integracao com clientes

O cadastro de clientes suporta `email` opcional. Isso continua sendo a base para notificacao contratual sem introduzir um cadastro paralelo de contatos.

Compatibilidade preservada:

- clientes antigos continuam validos sem e-mail;
- o envio de e-mail apenas nao ocorre para clientes sem endereco cadastrado;
- o CRUD atual de clientes continua operando normalmente.

## Integracao com frontend

Na tela de clientes:

- foi adicionada uma area de contratos vinculada ao cliente selecionado;
- o formulario de contratos depende da selecao explicita de um cliente na tabela;
- a tabela permite:
  - editar;
  - excluir;
  - visualizar arquivo;
  - baixar arquivo;
- o resumo agora mostra cobranca automatica e volume financeiro por contrato.

No dashboard:

- foram adicionados indicadores de contratos a vencer e vencidos;
- foi adicionada uma lista lateral com contratos em alerta;
- o dashboard contratual tambem expone contagem de cobrancas vencidas e a vencer.

No financeiro:

- a tela `Relatorios financeiros` ganhou a secao `Relatorios de contratos`;
- filtros e exportacoes ficam centralizados na area de relatarios, sem criar um modulo paralelo.

Em configuracoes:

- permanecem disponiveis os campos de antecedencia, e-mail automatico e diretorio de armazenamento.

## Scheduler

- inicializado no `lifespan` da aplicacao;
- roda em thread daemon;
- executa no maximo uma vez por dia;
- usa `contract_scheduler_poll_seconds` apenas para verificar o momento de executar;
- nao introduz dependencias externas.

## SMTP

Configuracoes suportadas por ambiente:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`
- `SMTP_USE_SSL`
- `SMTP_SENDER_EMAIL`
- `SMTP_SENDER_NAME`

Observacao:

- o modulo nao cria dependencias obrigatorias novas;
- se SMTP nao estiver configurado, o sistema continua funcionando e apenas registra falha de notificacao no contrato.

## Validacao executada

- testes de criacao de contrato com arquivo;
- testes de listagem por cliente;
- testes de status `ativo`, `a_vencer` e `vencido`;
- testes de rotina de notificacao com envio unico por status;
- testes de geracao automatica de cobranca sem duplicidade;
- testes de relatorio com filtros;
- testes de exportacao `.xlsx` e `.pdf`;
- testes de configuracoes do modulo;
- testes de UI para presenca das novas opcoes na SPA.

Resultado da validacao:

- `86 passed in 48.82s`
