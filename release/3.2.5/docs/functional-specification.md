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
- uso como entidade central para OS e financeiro.

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
- geracao automatica de financeiro quando aplicavel;
- emissao de documentos PDF.

### Financeiro

- CRUD de lancamentos manuais;
- conciliacao com ordens de servico;
- pagamentos parciais;
- fluxo de caixa derivado dos pagamentos;
- status pendente, pago e atrasado.

### Documentos

- ordem de servico em PDF;
- relatorio tecnico em PDF;
- certificado sanitario em PDF;
- certificado moldura com logo configuravel.

## Regras de negocio criticas

- um usuario precisa estar ativo para autenticar;
- o papel do usuario define os recursos acessiveis;
- uma OS nao pode consumir estoque inexistente;
- uma OS com valor pode gerar lancamento financeiro automaticamente;
- exclusao de OS deve reconciliar estoque e financeiro vinculados;
- lancamentos vinculados a OS nao devem ser alterados como se fossem manuais;
- pagamentos parciais devem atualizar saldo e registrar movimento de caixa;
- importacoes de XML devem rejeitar nota duplicada;
- dados de CNPJ e CEP devem ser normalizados antes de persistir.

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
