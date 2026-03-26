# Modulo de Contratos

## Objetivo

Adicionar gestao de contratos vinculados a clientes sem quebrar o fluxo operacional existente de cadastro, dashboard e configuracoes.

## Escopo entregue

- entidade `contratos` relacionada em `1 cliente -> N contratos`;
- cadastro, edicao, exclusao e consulta de contratos;
- upload, substituicao, visualizacao e download de arquivo do contrato;
- classificacao automatica de status:
  - `ativo`
  - `a_vencer`
  - `vencido`
- dashboard com alertas de contratos a vencer e vencidos;
- configuracoes persistidas para:
  - dias de antecedencia do alerta;
  - habilitacao de e-mail automatico;
  - diretorio de armazenamento dos arquivos;
- rotina automatica diaria para:
  - recalcular status;
  - disparar notificacoes por e-mail quando aplicavel.

## Arquitetura aplicada

### Persistencia

- modelo SQLAlchemy em `app/infrastructure/models.py`;
- migracao incremental em `app/infrastructure/migrations.py`;
- arquivos armazenados em disco no diretorio configurado por `contract_storage_dir`, com nome interno unico por `UUID`.

### Servicos

- regras de negocio centralizadas em `app/application/contracts_service.py`;
- scheduler leve em `app/application/contract_scheduler.py`;
- configuracoes centralizadas em `system_settings` via `app/application/settings_service.py`.

### API

Rotas principais:

- `GET /api/v1/contratos`
- `GET /api/v1/contratos/dashboard`
- `GET /api/v1/contratos/{contract_id}`
- `PUT /api/v1/contratos/{contract_id}`
- `DELETE /api/v1/contratos/{contract_id}`
- `GET /api/v1/contratos/{contract_id}/arquivo`
- `POST /api/v1/contratos/rotina/sincronizar`
- `GET /api/v1/clientes/{customer_id}/contratos`
- `POST /api/v1/clientes/{customer_id}/contratos`

## Regras de negocio

- `data_vencimento` nao pode ser anterior a `data_inicio`;
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
  - a notificacao daquele estado ainda nao foi enviada.

## Integracao com clientes

O cadastro de clientes passou a aceitar `email` opcional. Isso foi necessario para suportar notificacao contratual sem introduzir um cadastro paralelo de contatos.

Compatibilidade preservada:

- clientes antigos continuam validos sem e-mail;
- o envio de e-mail apenas nao ocorre para clientes sem endereco cadastrado;
- CRUD atual de clientes continua operando normalmente.

## Integracao com frontend

Na tela de clientes:

- foi adicionada uma area de contratos vinculada ao cliente selecionado;
- o formulario de contratos depende da selecao explicita de um cliente na tabela;
- a tabela permite:
  - editar;
  - excluir;
  - visualizar arquivo;
  - baixar arquivo.

No dashboard:

- foram adicionados indicadores de contratos a vencer e vencidos;
- foi adicionada uma lista lateral com contratos em alerta.

Em configuracoes:

- foram adicionados os campos de contratos no painel administrativo.

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
- testes de configuracoes do modulo;
- testes de UI para presenca das novas opcoes na SPA.

Resultado da validacao:

- `84 passed in 46.98s`
