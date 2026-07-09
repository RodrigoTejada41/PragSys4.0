# Central API Orchestrator Spec

Status: Aprovado
Approver: Rodrigo Tejada
Approval date: 2026-07-09
Approval reference: chat:2026-07-09:pode-continuar-central-api-orchestrator

## Objetivo

Definir a API Central responsavel por orquestrar, monitorar e administrar servicos do ecossistema SysPragas/ERP/PDV.

A API Central deve ser o ponto unico de comunicacao operacional entre CRM, PDV, Comanda, Cozinha, Agente Local, Motor Fiscal e demais modulos, reduzindo acoplamento direto entre aplicacoes.

## Escopo

### Inclui

- Cadastro dinamico de servicos gerenciados.
- Metadados de configuracao por servico.
- Descoberta de servicos.
- Health check periodico.
- Historico de saude.
- Controle de ciclo de vida: iniciar, parar, reiniciar e recarregar configuracoes.
- Politica configuravel de recuperacao automatica.
- Validacao de dependencias e portas.
- Logs operacionais centralizados.
- Endpoints administrativos.
- Painel administrativo.
- Integracao com Agente Local Windows.
- Governanca de autenticacao entre servicos.
- Metricas, eventos e trilha de auditoria.

### Nao inclui

- Substituir regras internas dos modulos existentes.
- Remover imediatamente comunicacoes legadas entre modulos.
- Implementar Kubernetes obrigatorio na primeira fase.
- Executar atualizacoes automaticas sem aprovacao operacional.
- Gerenciar certificados fiscais sem validacao do Departamento Fiscal.
- Expor comandos administrativos sem autenticacao forte.

## Servicos gerenciados iniciais

- Motor Fiscal.
- API Fiscal.
- API CRM.
- API PDV.
- API Comanda.
- API Cozinha.
- API Financeiro.
- API Estoque.
- API Relatorios.
- API Integracoes.
- API PIX.
- API TEF.
- API Impressao.
- API Balanca.
- API Scanner.
- API Backup.
- API Atualizacao.
- API Monitoramento.
- Agente Local Windows.
- Servico de Sincronizacao Offline.
- Banco de Dados Local.
- Banco de Dados Central.
- Servico de Filas.
- Cache Redis quando utilizado.

## Requisitos funcionais

- Permitir cadastrar servico com nome, tipo, porta, URL, health endpoint, dependencias e politica de recuperacao.
- Validar integridade das configuracoes antes da inicializacao.
- Validar dependencias antes de iniciar servicos dependentes.
- Validar portas em uso antes de iniciar processo local.
- Validar certificados digitais quando o servico declarar dependencia fiscal.
- Validar conexao com banco quando o servico declarar dependencia de persistencia.
- Inicializar servicos em ordem topologica baseada em dependencias.
- Encerrar servicos em ordem reversa segura.
- Consultar health check periodicamente.
- Registrar ultimo erro, ultima inicializacao, uptime, versao e tempo de resposta.
- Registrar historico de indisponibilidade e recuperacao.
- Reiniciar automaticamente servicos conforme politica configurada.
- Bloquear reinicio infinito por limite de tentativas e janela temporal.
- Notificar administradores quando a recuperacao falhar.
- Expor API administrativa para listar, consultar, iniciar, parar, reiniciar, diagnosticar e exportar logs.
- Expor painel administrativo com status, recursos, versoes, logs, falhas, uptime e dependencias.
- Integrar com Agente Local Windows para execucao em segundo plano e inicializacao com Windows.
- Permitir recarregar configuracoes sem reinstalacao.

## Requisitos nao funcionais

- Validacao de entrada em todos os endpoints.
- Controle de permissao por funcao.
- JWT obrigatorio para comunicacao entre servicos.
- OAuth2 quando aplicavel a integracoes externas.
- HTTPS/TLS em comunicacao remota.
- Assinatura de requisicoes sensiveis.
- Auditoria para comandos administrativos.
- Logs estruturados para acoes criticas.
- Compatibilidade com execucao local e rede interna.
- Baixo acoplamento entre orquestrador e modulos.
- Design modular e testavel.
- Observabilidade por logs, metricas e tracing quando disponivel.
- Operacao tolerante a falhas.

## Regras de negocio

- Nenhum servico dependente deve iniciar antes de seus pre-requisitos estarem saudaveis.
- Servico sem health check valido deve entrar em estado `degradado` ou `indisponivel`.
- Comando de parada deve tentar encerramento gracioso antes de finalizar processo de forma forcada.
- Reinicio automatico deve respeitar politica por servico.
- Servico fiscal exige validacao fiscal antes de deploy.
- Comandos sensiveis exigem permissao administrativa e auditoria.
- Nenhum modulo deve depender de acesso direto a outro modulo quando houver rota via orquestrador aprovada.
- Falha persistente deve gerar evento administrativo.

## Contratos

- APIs:
  - `GET /api/v1/orchestrator/services`
  - `POST /api/v1/orchestrator/services`
  - `GET /api/v1/orchestrator/services/{service_id}`
  - `GET /api/v1/orchestrator/services/{service_id}/health`
  - `POST /api/v1/orchestrator/services/{service_id}/start`
  - `POST /api/v1/orchestrator/services/{service_id}/stop`
  - `POST /api/v1/orchestrator/services/{service_id}/restart`
  - `POST /api/v1/orchestrator/services/{service_id}/reload`
  - `GET /api/v1/orchestrator/services/{service_id}/logs`
  - `GET /api/v1/orchestrator/services/{service_id}/history`
  - `POST /api/v1/orchestrator/diagnostics`
  - `GET /api/v1/orchestrator/dependencies`
  - `GET /api/v1/orchestrator/export/logs`
- Schemas:
  - `ManagedServiceCreate`
  - `ManagedServiceUpdate`
  - `ManagedServiceRead`
  - `ServiceHealthRead`
  - `ServiceDependencyRead`
  - `ServiceRecoveryPolicy`
  - `ServiceEventRead`
  - `ServiceCommandResult`
- Banco:
  - `managed_services`
  - `service_dependencies`
  - `service_health_checks`
  - `service_events`
  - `service_command_audit`
  - `service_config_versions`
- Eventos/jobs:
  - Job periodico de health check.
  - Job de recuperacao automatica.
  - Evento `service.started`.
  - Evento `service.stopped`.
  - Evento `service.failed`.
  - Evento `service.recovered`.
  - Evento `service.recovery_exhausted`.

## Riscos

- Controle de processos pode variar entre Windows, Docker e Linux.
- Comandos administrativos mal protegidos podem causar indisponibilidade.
- Health check agressivo pode gerar carga desnecessaria.
- Reinicio automatico mal configurado pode gerar loop.
- Centralizacao excessiva pode criar ponto unico de falha.
- Migracao abrupta pode quebrar comunicacoes legadas.
- Integracao fiscal exige cuidado com certificado, SEFAZ e conformidade.

## Criterios de aceite

- Servicos podem ser cadastrados com dependencias e politica de recuperacao.
- Inicializacao respeita dependencias.
- Health check registra historico.
- Falha simulada gera evento e tentativa de recuperacao.
- Limite de tentativas bloqueia loop de reinicio.
- API administrativa exige autenticacao e permissao.
- Acoes administrativas ficam auditadas.
- Painel mostra status e historico dos servicos.
- Testes cobrem regras de dependencia, recuperacao e permissao.
- Documentacao operacional descreve instalacao, configuracao e rollback.
