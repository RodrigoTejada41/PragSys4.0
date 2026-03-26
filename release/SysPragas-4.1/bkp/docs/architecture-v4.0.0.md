# Arquitetura Alvo 4.0.0

## Diagnostico resumido da base anterior

Antes da fase 4.0.0 o sistema funcionava como monolito modular util, mas ainda com sinais claros de maturidade de MVP:

- bootstrap de banco, seed e migracoes misturados no startup;
- modelo principal ainda centrado em empresa unica;
- Docker ocupando papel operacional maior do que o necessario;
- pouca separacao entre runtime local e runtime em rede;
- ausencia de trilha formal de schema migrations;
- isolamento de dados por empresa ainda incompleto nas entidades transacionais.

## Direcao arquitetural

A release 4.0.0 consolida o sistema como um **monolito modular profissional**, com divisao explicita entre camadas e preparacao para multitenancy por empresa.

### Camadas

- `interfaces`: HTTP API, UI web, templates e assets.
- `application`: orquestracao de casos de uso, schemas, servicos e validacoes.
- `domain`: enums e regras sem dependencia de transporte.
- `infrastructure`: persistencia, modelos, integracoes externas e migracoes.
- `core`: configuracao, seguranca, logging e excecoes transversais.

### Principios adotados

- baixo acoplamento entre web, regra e persistencia;
- alta coesao por modulo funcional;
- evolucao segura por migracoes rastreadas;
- operacao local-first com suporte a rede interna;
- multempresa com isolamento logico por `empresa_prestadora_id`;
- Docker opcional e nao mandatatorio.

## Topologia de execucao recomendada

### Modo local

- FastAPI rodando diretamente na maquina;
- SQLite como opcao padrao inicial;
- arquivos e certificados no filesystem local;
- uso indicado para escritorio unico, homologacao e instalacoes simples.

### Modo rede interna

- FastAPI rodando em um servidor Windows/Linux da empresa;
- host `0.0.0.0` e porta configuravel;
- banco local centralizado ou banco externo configurado via `DATABASE_URL`;
- clientes acessando pelo navegador na rede.

## Banco e migracoes

A partir da 4.0.0 o projeto passa a ter:

- tabela `schema_migrations`;
- migracoes aplicadas por versao;
- fundacao de tenant nas tabelas operacionais principais;
- script dedicado para inicializacao e verificacao do banco.

## Multempresa

O eixo de multempresa da 4.0.0 e `empresa_prestadora_id`.

### Entidades com fundacao de tenant

- `users`
- `clientes`
- `produtos`
- `pragas`
- `tecnicos`
- `ordens_servico`
- `agendamentos`
- `financeiro`
- `recibos`
- `notas_fiscais`

### Regra de evolucao

- usuario master pode operar de forma transversal;
- usuarios vinculados a empresa devem operar somente dentro do proprio tenant;
- novas evolucoes devem propagar filtro de tenant na camada de aplicacao, nunca apenas na UI.

## Riscos conhecidos

- a base ainda precisa de fechamento completo do isolamento em todos os casos de uso;
- SQLite atende bem a modo local, mas para rede com concorrencia moderada a alta o recomendado e migrar para Postgres;
- integracoes fiscais e externas exigem revisao tenant-aware antes de operacao multempresa em producao.
