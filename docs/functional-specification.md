# Especificacao Funcional

## Visao do produto

O SysPragas e um sistema operacional para empresas de controle de pragas com foco em cadastro, execucao de ordens de servico, controle de estoque, financeiro e emissao documental.

## Objetivos de negocio

- centralizar dados operacionais e administrativos;
- reduzir retrabalho manual na emissao de documentos;
- garantir rastreabilidade de estoque e financeiro vinculados a servicos;
- suportar operacao com perfis de acesso diferentes;
- permitir crescimento incremental sem reescrever o nucleo do sistema.

## Perfis de usuario

- `MASTER`: gestao global do sistema, usuarios e licencas.
- `ADMIN`: operacao administrativa com acesso ampliado.
- `OPERADOR`: execucao operacional com acesso restrito.

## Modulos funcionais

### Autenticacao e sessao

- login via JWT;
- identificacao do usuario autenticado;
- restricao de acesso por papel de usuario.

### Empresas prestadoras e licencas

- cadastro de empresas prestadoras;
- vinculo de usuarios e licencas a empresa prestadora;
- criacao de licenca inicial automatica no bootstrap do sistema.

### Clientes

- CRUD completo;
- consulta auxiliar de CNPJ e CEP por servico externo;
- suporte a e-mail opcional para comunicacoes automatizadas;
- uso como entidade central para OS e financeiro.

### Contratos

- multiplos contratos por cliente;
- cadastro de periodo, descricao e observacoes;
- configuracao de cobranca por contrato:
  - valor mensal;
  - tipo de cobranca;
  - dia de vencimento;
  - geracao automatica;
- upload e substituicao de arquivo contratual;
- status automatico por vencimento;
- alertas visuais de contratos a vencer e vencidos;
- notificacao por e-mail com base em configuracao do sistema;
- configuracao administrativa de SMTP no painel com host, porta, credenciais, TLS/SSL e remetente;
- rotina automatica para recalculo diario do status;
- relatorios sinteticos e analiticos com exportacao em `.xlsx` e `.pdf`.

### Produtos

- CRUD completo;
- controle de estoque atual e minimo;
- importacao por XML de NFe;
- importacao por CSV para carga e reposicao de estoque.

### Pragas

- CRUD completo para catalogo de pragas atendidas.

### Tecnicos

- CRUD completo;
- vinculo com ordens de servico.

### Ordens de servico

- abertura, edicao, exclusao e conclusao;
- associacao com cliente, tecnico, pragas e produtos;
- baixa automatica de estoque;
- classificacao explicita entre OS `avulsa` e OS `contrato`;
- geracao automatica de financeiro apenas para OS `avulsa`, quando aplicavel;
- manutencao do agendamento operacional para OS `avulsa` e `contrato`;
- emissao de documentos PDF.

### Financeiro

- CRUD de lancamentos manuais;
- conciliacao com ordens de servico;
- conciliacao com contratos recorrentes;
- pagamentos parciais;
- fluxo de caixa derivado dos pagamentos;
- status pendente, pago e atrasado.

### Banco de dados

- backup manual do banco SQLite com nome automatico e exportacao estruturada em `.db`;
- restauracao a partir de backup validado, com criacao obrigatoria de backup de seguranca antes da substituicao;
- limpeza operacional com dupla confirmacao para remover OS, agendamentos, logs e historicos;
- opcao de incluir financeiro, recibos, fluxo de caixa e NF-e na limpeza operacional;
- persistencia do diretorio padrao de backup no painel de configuracoes.

### Documentos

- ordem de servico em PDF;
- relatorio tecnico em PDF;
- certificado sanitario em PDF;
- certificado moldura com logo configuravel.

## Regras de negocio criticas

- um usuario precisa estar ativo para autenticar;
- o papel do usuario define os recursos acessiveis;
- uma OS nao pode consumir estoque inexistente;
- uma OS `avulsa` com valor pode gerar lancamento financeiro automaticamente;
- uma OS `contrato` nao pode gerar cobranca, conta a receber ou recibo vinculado;
- exclusao de OS deve reconciliar estoque e financeiro vinculados;
- lancamentos vinculados a OS nao devem ser alterados como se fossem manuais;
- pagamentos parciais devem atualizar saldo e registrar movimento de caixa;
- importacoes de XML devem rejeitar nota duplicada;
- dados de CNPJ e CEP devem ser normalizados antes de persistir.
- contratos nao podem ter vencimento anterior ao inicio.
- contratos com cobranca automatica exigem valor maior que zero.
- contratos devem refletir status automaticamente sem edicao manual.
- notificacoes contratuais nao devem duplicar envio para o mesmo status.
- cobrancas de contrato nao podem ser duplicadas para a mesma competencia.
- contratos com cobranca vinculada nao devem ser excluidos para preservar o historico financeiro.

## Requisitos de qualidade

- rastreabilidade entre regra, endpoint e teste;
- manutencao simples para novos modulos operacionais;
- consistencia entre UI web, API e regras de negocio;
- comportamento coberto por testes para fluxos criticos.

## Fora do escopo atual

- multi-tenant isolado por schema ou banco;
- filas assicronas;
- observabilidade distribuida;
- integracao nativa com gateway de pagamento;
- automacao completa de deploy continuo.
