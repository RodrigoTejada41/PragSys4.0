# Modulo de Estoque Profissional

## Escopo entregue

Esta evolucao amplia o estoque existente sem recriar regras ja implantadas. O modulo continua usando a base atual de produtos, movimentacoes, empresas, usuarios, permissoes e auditoria, com extensoes para operacao profissional.

## Principais entregas

- cadastro de produtos com `categoria` e `unidade_medida`
- unidades suportadas: `UN`, `ML`, `L`, `G`, `KG`
- conversao segura entre unidades compativeis em movimentacoes, balanco e transferencia
- listagem visual de posicoes de estoque por empresa/unidade sem consolidacao indevida
- alerta de estoque baixo por produto
- historico detalhado de estoque com origem, referencia, usuario e empresa relacionada
- balanco de estoque com justificativa obrigatoria
- transferencia entre matriz e filial/unidades vinculadas, mantendo saldos separados
- importacao por `XML`, `CSV` e `XLSX`
- log de importacao com arquivo, referencia, totais processados e rastreabilidade por empresa
- endpoint de empresas acessiveis no contexto de estoque para suportar a UI

## Regras preservadas

- isolamento multiempresa por `empresa_prestadora_id`
- respeita permissao granular existente:
  - `stock.view`
  - `stock.manage`
  - `stock.move`
- `master` continua com visao global
- `admin` e `gestor_estoque` operam dentro do escopo permitido
- visualizacao cruzada segue relacionamento matriz/filial ja existente
- estoque nao e somado entre empresas diferentes
- reutiliza a mesma tabela de produtos e a mesma trilha de movimentacoes ja existente

## Novos endpoints

- `GET /api/v1/produtos/estoque/empresas`
- `POST /api/v1/produtos/importar-xlsx`
- `POST /api/v1/produtos/estoque/balanco`
- `POST /api/v1/produtos/estoque/transferencias`
- `GET /api/v1/produtos/estoque/importacoes`

## Banco de dados

### Tabelas/colunas afetadas

- `produtos`
  - `categoria`
  - `unidade_medida`
- `estoque_movimentacoes`
  - `unidade_medida`
- nova tabela `estoque_importacoes`

## Validacoes aplicadas

- unidade invalida e rejeitada no backend
- transferencia permitida apenas para empresas acessiveis no contexto de estoque
- balanco exige justificativa
- importacoes validam campos obrigatorios antes de gravar
- exclusao de produto preserva historico operacional e bloqueia casos com uso em OS ou rastreabilidade critica

## Validacao local executada

- `flake8 app tests`
- `pytest -q`
- `docker compose up --build -d`
- `GET /health`

## Arquivos principais alterados

- `E:\Projetos\Controle_de_pragas1.1pppplication\schemas.py`
- `E:\Projetos\Controle_de_pragas1.1pppplication\services.py`
- `E:\Projetos\Controle_de_pragas1.1pp\infrastructure\models.py`
- `E:\Projetos\Controle_de_pragas1.1pp\infrastructure\migrations.py`
- `E:\Projetos\Controle_de_pragas1.1pp\interfacespi
outes\products.py`
- `E:\Projetos\Controle_de_pragas1.1pp\interfaces\web\staticpp.js`
- `E:\Projetos\Controle_de_pragas1.1	ests	est_stock_module.py`


## Evolucao de UX e navegacao

- menu lateral com entrada propria `Estoque`
- separacao clara entre:
  - `Produtos`: cadastro e base tecnica/fiscal
  - `Estoque`: saldo, movimentacao, balanco, transferencia, importacao e historico
- a tela de produtos deixou de concentrar operacoes de estoque
- o modulo de estoque ganhou filtros proprios por empresa, categoria, produto e status
- a lista de estoque agora expoe acoes rapidas para entrada, saida e balanco sem misturar com o CRUD de produto
