# Relatorio Tecnico Da Release 4.0.0

## Responsabilidade

- criado_por: Rodrigo Alves Tejada
- atualizado_por: Rodrigo Alves Tejada

## O que foi alterado

- versao formal elevada para `4.0.0`;
- runtime organizado para operacao local e em rede sem dependencia obrigatoria de container;
- configuracao central ampliada com host, porta, logging e modo de acesso remoto;
- sistema de migracoes rastreadas criado em `schema_migrations`;
- fundacao de multempresa adicionada no schema com `empresa_prestadora_id`;
- camada de configuracoes dinamicas criada com persistencia em `system_settings`;
- menu centralizado de configuracoes incorporado ao frontend administrativo;
- controle operacional de Google Agenda, WhatsApp, multiempresa e modo local/rede unificado em uma unica area;
- scripts dedicados de execucao e banco adicionados;
- documentacao tecnica e operacional reestruturada.

## O que foi corrigido

- acoplamento entre bootstrap de schema e startup sem trilha de versao;
- dependencia excessiva de container como narrativa principal de operacao;
- falta de documentacao objetiva para modo local e modo rede.
- ausencia de governanca central para integracoes e parametros do sistema;
- dependencia de ajustes espalhados em frontend para refletir estado operacional de Google Agenda e WhatsApp.
- persistencia inconsistente da sessao Google quando a conta conectava, mas a flag global de integracao permanecia desabilitada;
- falha de sincronizacao por comparacao entre `datetime` com e sem timezone no ciclo de expiracao do token Google;
- pouca clareza operacional no retorno visual dos cards de agendamento para sincronizacao manual com Google Agenda.

## O que foi modernizado

- metadados de runtime;
- organizacao da release;
- estrategia de banco e migracao;
- documentacao de arquitetura;
- experiencia administrativa do frontend com uma area de configuracoes limpa e segmentada;
- padrao de renderizacao da Ordem de Servico, preservando numero automatico sem edicao manual.
- payload operacional enviado ao Google Agenda, agora com endereco, telefone, tecnico, horario detalhado e duracao prevista;
- rotulo da acao de sincronizacao no card do agendamento, agora focado em sincronizar ou reenviar ao Google em vez de termos ambiguos.

## Processo executado nesta fase

- criacao da camada persistente `system_settings` com seed automatica, endpoint administrativo e painel web centralizado de configuracoes;
- adaptacao das integracoes Google Agenda e WhatsApp para respeitar configuracoes persistidas sem perder fallback de ambiente;
- reforma do frontend administrativo com area `Config. do sistema`, resumo de integracoes, atalhos de governanca e layout mais limpo;
- endurecimento do fluxo da Ordem de Servico com numero sequencial automatico e remocao do input manual da interface;
- revisao do fluxo de agenda para detectar conflito de tecnico antes do submit e exibir a janela horaria ocupada;
- diagnostico em container do erro `500` na agenda Google, com identificacao de comparacao `offset-naive` vs `offset-aware` e correcao no backend;
- diagnostico em container da falsa percepcao de conta Google "nao persistida", com identificacao da flag `google_calendar_enabled` desabilitada e religamento automatico no callback OAuth;
- ampliacao do evento enviado ao Google Agenda para refletir dados operacionais do atendimento no titulo e na descricao;
- diagnostico por logs Docker do erro `403` vindo do Google, confirmando dependencia de habilitacao da Google Calendar API no projeto cloud do cliente;
- refinamento do card de agendamento para expor botao claro de sincronizacao ou nova tentativa com Google.

## O que foi preparado para expansao futura

- fechamento de multempresa fim a fim;
- adocao de Postgres para cenarios maiores;
- auditoria de usuario criador/alterador;
- isolamento mais forte em servicos, relatorios e integracoes.
- extensao da camada `system_settings` para notificacoes, templates e parametros por empresa;
- evolucao da area de configuracoes para cadastro guiado de perfis e politicas por tenant.

## Riscos identificados

- ainda existem casos de uso legados que precisam receber filtro de tenant explicitamente;
- multempresa em producao exige concluir enforcement em toda a camada de aplicacao;
- SQLite deve ser tratado como opcao inicial, nao como banco definitivo para rede mais intensa.
- a interface web ainda esta concentrada em `app.js`, o que recomenda modularizacao futura por dominio visual;
- configuracoes globais ja operam de forma persistente, mas o proximo passo e permitir override por empresa onde fizer sentido.
- a sincronizacao com Google Agenda continua dependente da correta habilitacao da Google Calendar API no projeto Google Cloud associado ao OAuth.

## Pendencias

- concluir tenant enforcement nas rotas e servicos de todos os modulos;
- revisar RBAC com escopo por empresa;
- cobrir multempresa com testes automatizados dedicados.
- modularizar o frontend administrativo em arquivos menores por area funcional;
- adicionar auditoria explicita de `criado_por` e `atualizado_por` nas entidades operacionais.

## Recomendacoes

- seguir a proxima fase focando em isolamento transacional real;
- migrar rede corporativa para Postgres;
- adicionar observabilidade e trilha de auditoria por usuario.
- transformar `system_settings` em servico com escopo global e por empresa;
- separar a camada web em modulos de configuracoes, agenda, financeiro e OS para reduzir acoplamento do frontend.
