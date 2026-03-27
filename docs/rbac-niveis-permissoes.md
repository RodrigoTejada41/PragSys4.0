# RBAC E Permissoes Granulares

## Resumo

Foi implementado um controle de acesso com:

- nivel principal do usuario: `master`, `admin`, `operador`
- permissoes granulares por modulo e funcionalidade
- enforcement no backend por rota
- ajuste fino no frontend por checkboxes no cadastro de usuario

## Niveis

### MASTER

- acesso total
- sem restricoes
- pode gerenciar empresas prestadoras e licencas

### ADMIN

- acesso amplo ao sistema
- restrito ao escopo da propria empresa
- nao pode gerenciar empresas prestadoras
- nao pode gerenciar licencas

### OPERADOR

- acesso operacional
- sem acesso a configuracoes criticas por padrao
- pode receber permissoes extras de forma granular

## Modelo tecnico

- `users.role`: nivel principal
- `users.permissions_json`: permissoes granulares persistidas
- `app/core/permissions.py`: catalogo, defaults por nivel e funcoes de normalizacao
- `app/interfaces/api/deps.py`: dependencia `require_access(...)` para validar nivel + permissao

## Permissoes implementadas

- `customers.view`
- `customers.edit`
- `contracts.view`
- `contracts.manage`
- `stock.view`
- `stock.manage`
- `stock.move`
- `finance.view`
- `finance.manage`
- `work_orders.view`
- `work_orders.manage`
- `appointments.view`
- `appointments.manage`
- `settings.view`
- `settings.manage`
- `users.manage`
- `records.delete`
- `provider_companies.manage`
- `licenses.manage`
- `fiscal.view`
- `fiscal.manage`
- `integrations.manage`

## Rotas protegidas

Principais grupos ajustados:

- usuarios
- empresas prestadoras
- licencas
- clientes
- contratos
- estoque / produtos
- financeiro
- recibos
- fiscal / NF-e
- agenda
- ordens de servico
- integracoes Google e WhatsApp
- configuracoes

## Frontend

Tela de usuario atualizada com:

- seletor de nivel
- aplicacao automatica do preset de permissoes do nivel
- checkboxes por categoria
- possibilidade de ajuste fino antes de salvar

## Validacao executada

```powershell
.venv\Scripts\python.exe -m flake8 app tests
.venv\Scripts\python.exe -m pytest tests\test_access_control.py tests\test_multitenancy.py tests\test_auth.py tests\test_settings.py -q
docker compose up --build -d
```

## Cenarios cobertos

- `master` com acesso global
- `admin` bloqueado para empresas prestadoras e licencas
- `admin` com permissao financeira removida
- `operador` com permissao granular adicional
- isolamento multiempresa preservado

## Observacoes

- o backend continua sendo a fonte de verdade; o frontend apenas reflete as permissoes
- `master` continua com acesso irrestrito mesmo que o payload de permissoes seja alterado
