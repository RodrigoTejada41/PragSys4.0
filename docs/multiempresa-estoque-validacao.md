# Multiempresa E Estoque

## Visao geral

Esta entrega consolida a base de multiempresa com:

- vinculo obrigatorio de usuario com empresa prestadora
- relacao matriz / filial por `empresa_pai_id`
- visao de estoque entre empresas vinculadas apenas por configuracao explicita
- historico de movimentacao de estoque por empresa
- isolamento operacional mantido por `empresa_prestadora_id`

## Estrutura afetada

### Tabelas afetadas

- `empresas_prestadoras`
- `users`
- `produtos`
- `estoque_movimentacoes`
- tabelas operacionais ja existentes com `empresa_prestadora_id` continuam no escopo multiempresa:
  - `clientes`
  - `contratos`
  - `pragas`
  - `tecnicos`
  - `ordens_servico`
  - `agendamentos`
  - `financeiro`
  - `recibos`
  - `notas_fiscais`

### Campos novos ou reforcados

- `empresas_prestadoras.is_active`
- `empresas_prestadoras.is_provider`
- `empresas_prestadoras.empresa_pai_id`
- `empresas_prestadoras.compartilha_visualizacao_estoque`
- `users.empresa_prestadora_id` obrigatorio no modelo atual
- `estoque_movimentacoes.*`

## APIs afetadas

### Ajustadas

- `GET /api/v1/usuarios`
- `POST /api/v1/usuarios`
- `PUT /api/v1/usuarios/{user_id}`
- `DELETE /api/v1/usuarios/{user_id}`
- `GET /api/v1/produtos`
- `POST /api/v1/produtos`
- `PUT /api/v1/produtos/{product_id}`

### Novas

- `GET /api/v1/produtos/estoque`
- `GET /api/v1/produtos/estoque/movimentacoes`
- `POST /api/v1/produtos/estoque/movimentacoes`

## Permissoes implementadas

- `master`:
  - administra empresas, licencas e usuarios globais
  - ve qualquer empresa
- `admin`:
  - gerencia usuarios da propria empresa
  - nao cria empresa nova pelo fluxo de usuario
  - nao atua fora da propria empresa
- `operador`:
  - opera no escopo da empresa vinculada
- `gestor_estoque`:
  - foco no modulo de produtos e estoque
  - pode registrar movimentacoes de estoque

## Regras de isolamento

- usuarios sem empresa nao podem ser criados nem atualizados
- empresa inativa ou nao prestadora nao pode ser vinculada a novo usuario
- catalogo de produtos continua isolado por empresa
- visao cruzada foi habilitada apenas para endpoints de estoque
- visao cruzada depende de `compartilha_visualizacao_estoque` e da hierarquia matriz/filial
- os saldos continuam separados por empresa; nao ha consolidacao automatica

## Checklist tecnico de validacao

- [x] migracoes executam em banco limpo de teste
- [x] cadastro de usuario sem empresa retorna erro
- [x] login de usuarios vinculados continua funcional
- [x] produtos gravam empresa de origem
- [x] saldo inicial gera historico de estoque
- [x] movimentacao manual de estoque registra saldo anterior e posterior
- [x] filial com permissao enxerga estoque vinculado sem somar saldos
- [x] empresa independente nao enxerga estoque de outra
- [x] lint local passou
- [x] testes automatizados locais passaram

## Validacao local executada

Comandos executados:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_multitenancy.py -q
.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_settings.py -q
.venv\Scripts\python.exe -m flake8 app tests
```

## Passos para VPS DEV

1. Fazer backup do banco DEV.
2. Publicar a branch homologada.
3. Rodar o deploy DEV para aplicar o novo build e as migracoes.
4. Validar no DEV:
   - login com `master`
   - cadastro de empresa matriz e filial
   - cadastro de usuario vinculado
   - cadastro e movimentacao de produto
   - visao de estoque entre matriz e filial
   - regressao dos modulos de clientes, OS e financeiro
5. Confirmar integridade antes de promover para producao.

## Riscos e mitigacoes

- Risco: base legada com usuarios sem empresa.
  - Mitigacao: migracao faz backfill para a primeira empresa existente.
- Risco: ajuste manual de estoque sem trilha.
  - Mitigacao: todo ajuste relevante agora gera registro em `estoque_movimentacoes`.
- Risco: vazamento entre empresas por leitura cruzada.
  - Mitigacao: somente endpoints de estoque usam lista expandida de empresas acessiveis; os demais continuam filtrados pela empresa do usuario.
- Risco: admins de empresa criarem usuarios fora do escopo.
  - Mitigacao: backend restringe criacao, edicao e exclusao ao `empresa_prestadora_id` do proprio admin.
