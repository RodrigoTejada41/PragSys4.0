# Relatorio de Performance da Suite e Oportunidades de Otimizacao

Data da analise: 2026-03-26

## Resumo executivo

- Suite antes da otimizacao: `76 passed in 870.63s (0:14:30)`
- Suite depois da otimizacao: `76 passed in 42.03s`
- Reducao absoluta: `828.60s`
- Reducao percentual aproximada: `95.0%`

O principal gargalo nao estava no corpo dos testes, mas na infraestrutura de teste:

- recriacao completa do banco SQLite em disco a cada teste;
- execucao de bootstrap completo (`init_db`, seeds e migracoes) para cada caso;
- `drop_all` e remocao de arquivos ao final de cada teste;
- recriacao de assets temporarios em disco a cada teste;
- custo criptografico desnecessariamente alto no ambiente de teste para hash e verificacao de senha.

## Mudancas aplicadas

### Infraestrutura de teste

- criado banco-template de testes pre-semeado por processo;
- cada teste agora recebe uma copia limpa desse template, preservando isolamento sem recriar schema inteiro;
- removido `drop_all` por teste, trocado por descarte do arquivo copiado;
- assets temporarios passaram a ser preparados uma vez por sessao, e nao por teste;
- nomes de arquivos temporarios ficaram isolados por PID, evitando lock entre execucoes concorrentes.
- `auth_headers` deixou de depender de login HTTP em todos os testes e passou a emitir token diretamente a partir do usuario seeded.

### Banco e acesso a dados

- adicionados indices dedicados para consultas frequentes em `produtos`, `financeiro`, `os_produtos` e `os_pragas`;
- migracao `20260326_001_performance_indexes` criada para aplicar os indices sem quebrar bases existentes;
- carregamento das colecoes de Ordem de Servico passou de `joinedload` para `selectinload`, reduzindo explosao de linhas em consultas com muitos relacionamentos.

### Organizacao da suite

- marcadores `unit`, `integration`, `documents` e `external` adicionados ao `pytest`;
- marcacao automatica centralizada em `tests/conftest.py`, sem precisar espalhar anotacoes por todos os arquivos.

### Configuracao de seguranca

- `password_hash_iterations` passou a ser configuravel via settings;
- ambiente de teste usa `PASSWORD_HASH_ITERATIONS=1000`;
- ambiente normal continua com padrao `100_000`, sem mudanca de comportamento em producao.

## Arquivos alterados

- `tests/conftest.py`
- `app/core/config.py`
- `app/core/security.py`
- `app/application/services.py`
- `app/infrastructure/models.py`
- `app/infrastructure/migrations.py`
- `pyproject.toml`

## Top 10 testes mais lentos apos a otimizacao

Tempos de `call`, que agora representam melhor o custo funcional real:

1. `tests/test_documents.py::test_all_work_order_documents_are_generated` - `1.55s`
2. `tests/test_documents.py::test_guarantee_certificate_is_generated_from_visual_template` - `1.53s`
3. `tests/test_crud_operations.py::test_update_and_delete_core_records` - `1.51s`
4. `tests/test_rbac.py::test_operador_can_use_os_but_cannot_access_finance_or_license_management` - `1.08s`
5. `tests/test_multitenancy.py::test_company_data_isolated_across_core_modules` - `1.03s`
6. `tests/test_work_orders.py::test_reopen_work_order_reopens_linked_appointment` - `0.91s`
7. `tests/test_work_orders.py::test_work_order_allows_photo_upload_and_removal` - `0.87s`
8. `tests/test_work_orders.py::test_quick_actions_complete_and_settle_work_order_and_finance` - `0.84s`
9. `tests/test_crud_operations.py::test_update_and_delete_work_order_reconcile_stock_and_finance` - `0.80s`
10. `tests/test_appointments.py::test_completing_appointment_updates_linked_work_order` - `0.74s`

## Gargalos encontrados

### Gargalo 1: bootstrap do banco por teste

Era o maior problema. No baseline, praticamente todos os testes exibiam:

- `setup` entre `8s` e `9.5s`
- `teardown` entre `2s` e `2.7s`

Isso mascarava a medicao real do tempo do teste e dominava quase toda a suite.

### Gargalo 2: I/O em disco repetitivo

- criacao e exclusao do SQLite para cada caso;
- escrita repetida dos arquivos de assinatura e modelo;
- limpeza total de schema ao final de cada teste.

### Gargalo 3: custo de hash de senha no ambiente de teste

O sistema usa PBKDF2 com `100_000` iteracoes, o que faz sentido para runtime real, mas penaliza o ambiente de teste sem agregar cobertura funcional.

### Gargalo 4: testes de documentos

Mesmo apos a otimizacao estrutural, os testes de documentos continuam entre os mais lentos porque exercitam geracao de PDF/imagem e composicao de documentos.

## Classificacao dos testes

### Unitarios ou quase unitarios

- `tests/test_nfe_direct_module.py`
- `tests/test_web_ui.py::test_static_app_js_includes_appointment_availability_feedback`
- `tests/test_crud_operations.py::test_import_templates_are_available`

### Integracao

A maior parte da suite cai aqui, pois usa `TestClient`, banco SQLite e servicos reais:

- `tests/test_appointments.py`
- `tests/test_auth.py`
- `tests/test_crud_operations.py`
- `tests/test_documents.py`
- `tests/test_financial_module.py`
- `tests/test_multitenancy.py`
- `tests/test_nfe_external_integration.py`
- `tests/test_rbac.py`
- `tests/test_receipts.py`
- `tests/test_settings.py`
- `tests/test_whatsapp_integration.py`
- `tests/test_work_orders.py`

### End-to-end

Nao ha testes E2E completos de navegador ou de integracoes externas reais na suite atual. O repositorio trabalha principalmente com integracao HTTP local e mocks/stubs.

## Redundancia e sobreposicao

Nao foram encontrados duplicados exatos claros. Ha, no entanto, grupos com sobreposicao funcional moderada:

- rotas legadas e novas de sincronizacao Google;
- multiplos cenarios do endpoint de status do WhatsApp;
- varias validacoes de fluxo de OS que compartilham muito setup.

Esses grupos ainda parecem defensaveis porque cobrem contratos ou ramos diferentes. Se o objetivo for reduzir ainda mais o tempo, o passo seguinte seria consolidar setup comum nesses arquivos, nao remover cenarios.

## Oportunidades seguras para deixar o software mais leve

Sem alterar comportamento:

1. Criar indexes adicionais para campos de consulta frequente, com migracao dedicada.
   Parcialmente implementado: `produtos.registro_ms`, `financeiro.cliente_id`, `financeiro.os_id`, `financeiro.origem`, `financeiro.referencia`, `financeiro(origem, referencia)`, `os_produtos.os_id`, `os_produtos.produto_id`, `os_pragas.os_id`, `os_pragas.praga_id`.

2. Evitar bootstrap completo quando o banco ja estiver inicializado e consistente.
   Hoje `init_db()` ainda roda em todo startup do app e do `TestClient`, mesmo quando nada mudou.

3. Separar geracao de documentos em servicos mais finos e testar partes puras sem sempre gerar artefato completo.
   Isso reduz custo de CPU e I/O na suite sem perder cobertura de regra.

4. Introduzir marcadores de teste.
   Ja implementado: `unit`, `integration`, `documents`, `external`, permitindo pipelines mais rapidos no dia a dia.

5. Adicionar `pytest-xdist` futuramente.
   Com os arquivos por PID, a infraestrutura ja ficou muito mais preparada para execucoes paralelas entre processos.

6. Revisar caminhos de consulta mais usados nas rotas de OS, agendamento e financeiro.
   Ha indicios de que boa parte do custo funcional restante vem de fluxos encadeados com varias operacoes de persistencia.

## Validacao

- A suite completa continuou verde apos as mudancas.
- Nenhuma funcionalidade foi removida.
- O comportamento esperado da aplicacao foi preservado.

## Comandos usados

```powershell
.venv\Scripts\python.exe -m pytest -q --durations=0
.venv\Scripts\python.exe -m pytest -q --durations=20
```
