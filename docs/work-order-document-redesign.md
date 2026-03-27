# Redesign da Ordem de Servico

## Objetivo

Elevar o comprovante de execucao / ordem de servico para um padrao mais profissional, com estrutura documental clara, validacoes obrigatorias de conformidade e separacao do template em modulo reutilizavel.

## Arquivos principais

- `E:\Projetos\Controle_de_pragas1.1\app\application\work_order_documents.py`
- `E:\Projetos\Controle_de_pragas1.1\app\application\services.py`
- `E:\Projetos\Controle_de_pragas1.1\tests\test_documents.py`
- `E:\Projetos\Controle_de_pragas1.1\tests\conftest.py`

## O que mudou

### 1. Template separado da regra de servico

A montagem visual da OS saiu do fluxo principal de `services.py` e passou para `work_order_documents.py`.

Isso trouxe:

- separacao entre orquestracao e apresentacao
- base mais facil para evoluir outros documentos
- menor risco de quebrar o CRUD da OS ao mexer apenas no PDF

### 2. Nova estrutura documental

O PDF passou a seguir secoes fixas:

- cabecalho com dados da empresa
- identificacao da OS
- cliente
- servico executado
- produtos aplicados em tabela
- orientacoes
- observacoes
- dados legais da empresa
- assinaturas

### 3. Validacoes obrigatorias

A geracao agora bloqueia se faltarem dados essenciais de conformidade:

- responsavel tecnico
- registro profissional
- licenca sanitaria
- licenca ambiental
- endereco da empresa
- CIT

O bloqueio retorna erro de negocio antes da emissao do PDF, evitando documento com informacao regulatoria incompleta ou placeholder.

### 4. Padronizacao de dados

Foram ajustados:

- data em `dd/mm/yyyy`
- horario de inicio e termino em campos separados
- status formatado para leitura humana
- ausencia de texto `nao configurado` no documento final
- observacoes com fallback profissional

### 5. Produtos aplicados

Os produtos deixaram de ser uma lista corrida e passaram para tabela com:

- produto
- principio ativo
- registro MS
- diluicao
- quantidade

## Validacao executada

### Qualidade estatica

- `flake8 app tests`

### Testes automatizados

- `pytest tests\test_documents.py tests\test_multitenancy.py tests\test_work_orders.py tests\test_auth.py tests\test_settings.py -q`
- resultado: `30 passed`

### Cobertura funcional adicionada

- geracao de documentos continua funcional
- bloqueio da OS quando faltam dados regulatorios obrigatorios
- isolamento multiempresa continua preservado

## Riscos mitigados

- documento emitido com dados tecnicos incompletos
- layout da OS misturado com logica de negocio
- produtos aplicados com leitura confusa
- uso de placeholders regulatorios em PDF final

## Proximo passo recomendado

- validar visualmente a OS no container local
- depois homologar em VPS DEV
