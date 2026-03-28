# Modulo de Estoque com Rastreabilidade

## Entregue
- separacao do workspace de estoque do cadastro de produtos
- estrutura por armazem e local fisico
- saldo por produto/local
- lookup por codigo interno, codigo de barras e QR Code
- QR Code automatico por produto
- codigo de barras manual com validacao de duplicidade
- movimentacao manual com armazem/local
- transferencia entre unidades com origem e destino
- inventario por leitura com consolidacao de divergencias
- geracao de etiquetas em PDF com QR Code e Code128

## Regras preservadas
- multiempresa por empresa_prestadora_id
- visao cruzada apenas dentro das regras ja existentes
- permissoes atuais de stock.view, stock.manage e stock.move
- historico e auditoria centralizados em estoque_movimentacoes
- reaproveitamento do cadastro de produtos existente

## Novas estruturas
- estoque_armazens
- estoque_locais
- estoque_saldos
- estoque_inventarios
- estoque_inventario_itens
- produtos.codigo_barras
- produtos.qr_code_value
- estoque_movimentacoes.armazem_id
- estoque_movimentacoes.local_id
- estoque_movimentacoes.armazem_relacionado_id
- estoque_movimentacoes.local_relacionado_id
- estoque_movimentacoes.codigo_lido

## APIs novas
- GET /api/v1/produtos/estoque/armazens
- POST /api/v1/produtos/estoque/armazens
- PUT /api/v1/produtos/estoque/armazens/{warehouse_id}
- GET /api/v1/produtos/estoque/locais
- POST /api/v1/produtos/estoque/locais
- PUT /api/v1/produtos/estoque/locais/{location_id}
- GET /api/v1/produtos/estoque/buscar-por-codigo/{codigo}
- GET /api/v1/produtos/estoque/inventarios
- POST /api/v1/produtos/estoque/inventarios
- POST /api/v1/produtos/estoque/inventarios/{inventory_id}/contagens
- POST /api/v1/produtos/estoque/inventarios/{inventory_id}/finalizar
- POST /api/v1/produtos/estoque/etiquetas/pdf

## Fluxos principais
### Movimentacao
- o operador pode selecionar produto ou ler codigo
- o sistema resolve produto, armazem e local padrao quando necessario
- a movimentacao atualiza saldo total do produto e saldo do local fisico

### Inventario
- abre um inventario por armazem/local
- cada leitura acumula quantidade contada por produto
- a finalizacao pode aplicar ajuste automatico com trilha de auditoria

### Etiquetas
- gera PDF em lote a partir dos produtos filtrados
- cada etiqueta inclui nome, registro, unidade, Code128 e QR Code

## Validacao executada
- flake8 app tests
- pytest tests/test_stock_module.py -q
- pytest -q
- node --check app/interfaces/web/static/app.js
- docker compose up --build -d
- health check em /health

## Navegacao por paginas
- Estoque: operacao geral e estrutura fisica
- Importacoes: XML, CSV, planilhas e auditoria das cargas
- Armazens e locais: cadastro da estrutura fisica por deposito, veiculo, equipe e prateleira
- Balanco: saldo contado e ajuste manual imediato
- Inventario: abertura de sessao, leitura continua e fechamento com divergencias
- Etiquetas: geracao de PDF e revisao dos identificadores dos produtos
- Transferencias: movimentacoes entre unidades vinculadas
- cada tela mostra apenas o contexto operacional correspondente
