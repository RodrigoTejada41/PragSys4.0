# Base Demonstracao Integrada

## Objetivo

Este pacote cria uma base demonstracao consistente para o SysPragas, cobrindo os fluxos principais de:

- empresa prestadora e filial vinculada
- usuarios com RBAC
- dados tecnicos institucionais
- produtos e estoque
- importacoes CSV e XML
- clientes PF e PJ
- contratos com cenarios ativo, a vencer e vencido
- ordens de servico e agendamentos
- financeiro e recibos
- documentos PDF para demonstracao

## Como gerar

Pelo script dedicado:

```powershell
.venv\Scripts\python.exe scripts\generate_demo_dataset.py --output-dir output\demo_seed
```

Ou pelo utilitario de banco:

```powershell
.venv\Scripts\python.exe scripts\manage_db.py seed-demo --output-dir output\demo_seed
```

## O que e criado

### Empresas

- `Dedetiza Prime Servicos Ambientais Ltda`
- `Dedetiza Prime Filial Centro Ltda`

### Usuarios

Senha padrao para todos os usuarios demonstracao:

- `Demo@123`

Usuarios criados:

- `master.demo`
- `admin.demo`
- `operador.demo`
- `admin.filial.demo`

### Estoque

Fluxos cobertos:

- cadastro tecnico de produtos
- saldo inicial
- entrada manual
- transferencia entre matriz e filial
- balanco
- inventario com ajuste
- baixa automatica por uso em OS
- importacao CSV
- importacao XML de NF

### Clientes e contratos

Cenarios incluidos:

- cliente PF
- cliente PJ com contrato ativo
- cliente PJ com contrato a vencer
- cliente PJ com contrato vencido

### Operacao

Ordens de servico geradas com:

- status `aberta`
- status `em_execucao`
- status `concluida`
- OS `avulsa`
- OS `contrato`

### Financeiro

Fluxos incluidos:

- contas a receber
- contas a pagar
- cobranca mock com referencia tipo Asaas
- recibo
- baixa de pagamento

## Arquivos gerados

No diretorio informado sao gerados:

- `dataset_blueprint.json`
- `dataset_manifest.json`
- `demo_seed_dump.sql`
- `assets/` com assinatura e licencas mock
- `documents/` com PDFs de OS, relatorio tecnico, certificados e recibo

## Observacoes de compatibilidade

- A exportacao SQL usa `iterdump` do SQLite, alinhada ao banco atual do projeto.
- O seed respeita o modelo existente do sistema e nao cria campos fora da arquitetura atual.
- O cadastro de produtos hoje nao possui campo nativo de status ativo/inativo; por isso a base demonstracao preserva o schema atual sem inventar comportamento paralelo.
