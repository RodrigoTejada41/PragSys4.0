# Modulo de Agendamento

## Objetivo

O modulo de agendamento organiza visitas tecnicas, servicos programados, revisitas e retornos operacionais vinculados a clientes e, quando aplicavel, a ordens de servico. A implementacao foi desenhada para manter separacao clara entre agenda, OS e integracao externa com Google Agenda.

## Estrutura implementada

- Backend:
  - `app/application/scheduling_services.py`
  - `app/interfaces/api/routes/appointments.py`
  - integracao com `app/application/services.py`
- Persistencia:
  - `Appointment`
  - `AppointmentHistory`
- Frontend:
  - nova view `Agenda` em `app/interfaces/web/templates/pages/app.html`
  - fluxo visual em `app/interfaces/web/static/app.js`
  - estilos em `app/interfaces/web/static/styles.css`

## Modelagem de dados

### Tabela `agendamentos`

Campos principais:

- `id`
- `cliente_id` -> FK para `clientes`
- `os_id` -> FK opcional para `ordens_servico`
- `tecnico_id` -> FK opcional para `tecnicos`
- `usuario_responsavel_id` -> FK para `usuarios`
- `usuario_ultima_atualizacao_id` -> FK para `usuarios`
- `agendamento_pai_id` -> FK autorreferente para revisitas e retornos
- `tipo_servico`
- `telefone`
- `endereco_completo`
- `data_agendamento`
- `hora_agendamento`
- `duracao_prevista_minutos`
- `observacoes`
- `observacoes_internas`
- `instrucoes_tecnicas`
- `retorno_revisita`
- `status`
- `origem`
- `sincronizar_google`
- `google_calendar_event_id`
- `google_calendar_id`
- `google_sync_status`
- `google_sync_message`
- `created_at`
- `updated_at`

### Tabela `historico_agendamentos`

Campos principais:

- `id`
- `agendamento_id` -> FK para `agendamentos`
- `usuario_id` -> FK para `usuarios`
- `acao`
- `status_anterior`
- `status_novo`
- `detalhes`
- `created_at`

## Regras de negocio

- Todo agendamento precisa de cliente, tipo de servico, data, hora e duracao.
- O telefone e o endereco sao herdados do cadastro do cliente para evitar divergencia operacional.
- A mesma OS so gera um agendamento principal automatico por vez.
- O tecnico nao pode ter conflito de horario em agendamentos ativos no mesmo periodo.
- Alteracao de data e hora da OS atualiza o agendamento vinculado.
- Conclusao do agendamento pode concluir a OS vinculada.
- Conclusao da OS pode concluir o agendamento automatico vinculado.
- Cancelamento da geracao automatica na OS cancela o agendamento automatico associado.
- Toda alteracao relevante gera historico.

## Status operacionais

- `pendente`
- `confirmado`
- `em_deslocamento`
- `em_atendimento`
- `concluido`
- `reagendado`
- `cancelado`
- `nao_realizado`

## Fluxo com Ordem de Servico

### Criacao de OS

Ao salvar a OS, o formulario permite:

- definir se deve gerar agendamento
- informar tipo de servico
- definir duracao prevista
- registrar observacoes internas
- registrar instrucoes tecnicas
- registrar retorno ou revisita
- marcar sincronizacao com Google Agenda

Se a opcao estiver ativa, o backend cria ou atualiza automaticamente um agendamento vinculado a:

- cliente da OS
- tecnico da OS
- data e hora da OS
- observacoes da OS

### Atualizacao de OS

Quando a OS muda:

- data e hora refletem no agendamento
- tecnico reflete no agendamento
- observacoes complementares do agendamento sao atualizadas
- reagendamentos marcam o compromisso como `reagendado`

### Conclusao

- concluir a OS conclui o agendamento automatico vinculado
- concluir o agendamento conclui a OS vinculada

## Fluxo com Google Agenda

O modulo esta preparado para integracao via API REST do Google Calendar.

Configuracoes previstas:

- `GOOGLE_CALENDAR_ENABLED`
- `GOOGLE_CALENDAR_ID`
- `GOOGLE_CALENDAR_ACCESS_TOKEN`
- `COMPANY_TIMEZONE`

Operacoes suportadas:

- criar evento
- atualizar evento
- remover evento em cancelamento ou nao realizacao
- registrar estado de sincronizacao
- gravar mensagem de erro para diagnostico

Payload enviado ao Google:

- titulo com cliente e tipo de servico
- endereco
- observacoes
- janela de inicio e fim
- propriedades privadas com IDs internos

## Telas implementadas

### View `Agenda`

- formulario lateral para criar e editar agendamentos
- resumo rapido por status
- filtros por cliente, tecnico, status, busca livre e data
- visualizacao diaria, semanal e mensal
- lista do dia
- lista de compromissos em foco
- lista de compromissos atrasados
- acoes rapidas:
  - editar / reagendar
  - confirmar
  - em deslocamento
  - em atendimento
  - concluir
  - cancelar
  - abrir OS vinculada
  - sincronizar Google

### View `Ordens de servico`

O formulario da OS ganhou um bloco proprio de agendamento para controlar a criacao automatica da agenda sem misturar a listagem operacional com o cadastro.

## Endpoints principais

- `GET /api/v1/agendamentos`
- `GET /api/v1/agendamentos/dashboard`
- `GET /api/v1/agendamentos/{id}`
- `POST /api/v1/agendamentos`
- `PUT /api/v1/agendamentos/{id}`
- `POST /api/v1/agendamentos/{id}/status`
- `POST /api/v1/agendamentos/{id}/sync-google`

## Observabilidade e manutencao

- historico por acao e por transicao de status
- mensagens de erro de sincronizacao armazenadas no proprio agendamento
- servicos concentrados em `scheduling_services.py`
- frontend isolado na view `Agenda`
- integracao com OS encapsulada em funcoes de sincronizacao

## Melhorias futuras recomendadas

- refresh automatico em tempo real para operacao multiusuario
- notificacoes por WhatsApp, e-mail ou push
- bloqueio visual de agenda por tecnico
- drag and drop de reagendamento no calendario
- fila assicrona para sincronizacao com Google Agenda
- tokens OAuth renovaveis em vez de token fixo
- SLA por tipo de servico
- relatarios de produtividade por tecnico e periodo
