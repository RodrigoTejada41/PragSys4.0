# Modulo Financeiro Integrado a NF-e

## Objetivo

Organizar contas a receber e a pagar, manter vinculo cruzado com NF-e e reduzir erro manual no cadastro fiscal de produtos via NCM e aliquotas base.

## Escopo entregue

- cadastro e listagem de NF-e em `notas_fiscais`;
- geracao automatica de contas a receber em `financeiro` ao salvar NF-e;
- bloqueio de edicao/exclusao direta de lancamentos originados por NF-e;
- busca textual em financeiro por descricao, referencia e fornecedor;
- resumo de fluxo de caixa com recebido, pendente e vencido;
- configuracao de Simples Nacional com faixa, aliquota, anexo e vigencia;
- resumo mensal do Simples com base em NF-e emitidas;
- base local de NCM com cache em `ncm`;
- aplicacao automatica de aliquotas fiscais no cadastro de produto;
- override manual de tributacao por produto quando necessario;
- interface administrativa para financeiro, NF-e, Simples e apoio fiscal no cadastro de produtos.

## Modelagem

### `notas_fiscais`

- `id`
- `numero_nfe`
- `cliente_id`
- `valor_total`
- `data_emissao`
- `data_vencimento`
- `status`
- `observacoes`
- `created_at`

### `financeiro`

Adicao do campo:

- `nfe_id`

Relacionamentos:

- `cliente_id -> clientes.id`
- `os_id -> ordens_servico.id`
- `nfe_id -> notas_fiscais.id`

### `ncm`

- `codigo`
- `descricao`
- `aliquota_icms`
- `aliquota_ipi`
- `aliquota_pis`
- `aliquota_cofins`
- `fonte_dados`
- `updated_at`
- `created_at`

### `simples_nacional_config`

- `id`
- `faixa_faturamento_inicio`
- `faixa_faturamento_fim`
- `aliquota`
- `anexo`
- `vigente`
- `observacoes`
- `created_at`
- `updated_at`

## Regras principais

- NF-e emitida pode gerar automaticamente um unico titulo financeiro vinculado.
- Lancamento gerado por NF-e nao pode ser editado ou excluido diretamente no financeiro.
- Alteracao da NF-e atualiza o titulo financeiro vinculado, desde que ainda nao tenha baixa.
- Busca de NCM consulta primeiro a base local; fonte externa fica opcional por configuracao.
- Quando `override_tributacao=false`, o produto herda descricao e aliquotas da base NCM.
- Quando `override_tributacao=true`, o produto preserva aliquotas manuais.
- Resumo do Simples usa apenas NF-e com `status=emitida`.

## Endpoints

### NF-e

- `GET /api/v1/nfe`
- `POST /api/v1/nfe`
- `PUT /api/v1/nfe/{nfe_id}`
- `DELETE /api/v1/nfe/{nfe_id}`

### Fiscal

- `GET /api/v1/fiscal/ncm`
- `GET /api/v1/fiscal/ncm/{codigo}`
- `GET /api/v1/fiscal/simples`
- `POST /api/v1/fiscal/simples`
- `PUT /api/v1/fiscal/simples/{config_id}`
- `GET /api/v1/fiscal/simples/resumo/{year}/{month}`
- `GET /api/v1/fiscal/fluxo-caixa/resumo`

## Fluxo operacional

1. Usuario emite ou registra a NF-e.
2. O sistema salva a nota fiscal.
3. Se `gerar_financeiro=true`, cria conta a receber vinculada a `nfe_id`.
4. O financeiro passa a exibir origem, cliente, vencimento e status do titulo.
5. O modulo fiscal consolida as NF-e emitidas no resumo mensal do Simples.
6. No cadastro de produto, o operador informa o NCM e recebe aliquotas automaticamente.

## Preparacao para fonte externa de NCM

Configuracoes suportadas:

- `NCM_EXTERNAL_SOURCE_URL`
- `NCM_EXTERNAL_SOURCE_TOKEN`

Estrategia:

- consulta local primeiro;
- consulta externa apenas quando o NCM nao existir no cache local;
- persistencia local do retorno para reduzir latencia e repeticao de chamadas.

## Melhorias futuras recomendadas

- importacao periodica de tabela NCM oficial para refresh do cache local;
- trilha de auditoria dedicada para mudancas em NF-e e configuracoes fiscais;
- conciliacao bancaria e contas a pagar recorrentes;
- emissao real de NF-e via integrador externo;
- dashboard gerencial com DRE simplificada e comparativos mensais.
