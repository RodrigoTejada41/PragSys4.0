# Checklist De Homologacao RBAC

## Massa de teste sugerida

### Empresa 1

- Razao social: `Empresa Homologacao Alpha Ltda`
- Nome fantasia: `Alpha Controle`
- CNPJ: `11111111000111`
- Cidade: `Sao Paulo`
- Estado: `SP`

### Empresa 2

- Razao social: `Empresa Homologacao Beta Ltda`
- Nome fantasia: `Beta Controle`
- CNPJ: `22222222000122`
- Cidade: `Campinas`
- Estado: `SP`

### Usuarios

- `admin` / `syspragas123` - `MASTER`
- `admin.alpha` / `Senha@123` - `ADMIN`
- `operador.alpha` / `Senha@123` - `OPERADOR`
- `estoque.alpha` / `Senha@123` - `OPERADOR` com foco em estoque
- `admin.beta` / `Senha@123` - `ADMIN`

## Checklist

| ID | Cenario | Usuario | Acao | Resultado esperado | Status | Observacao |
|---|---|---|---|---|---|---|
| 1 | Login MASTER | `admin` | Entrar no sistema | Login com sucesso |  |  |
| 2 | Menu MASTER | `admin` | Ver menu lateral | Ve `Empresas`, `Licencas`, `Usuarios`, `Financeiro`, `Configuracoes` |  |  |
| 3 | Criar empresa Alpha | `admin` | Cadastrar empresa | Empresa criada com sucesso |  |  |
| 4 | Criar empresa Beta | `admin` | Cadastrar empresa | Empresa criada com sucesso |  |  |
| 5 | Criar ADMIN Alpha | `admin` | Cadastrar usuario `admin.alpha` | Usuario criado com empresa vinculada |  |  |
| 6 | Criar OPERADOR Alpha | `admin` | Cadastrar usuario `operador.alpha` | Usuario criado com permissoes customizadas |  |  |
| 7 | Criar ESTOQUE Alpha | `admin` | Cadastrar usuario `estoque.alpha` | Usuario criado com foco em estoque |  |  |
| 8 | Criar ADMIN Beta | `admin` | Cadastrar usuario `admin.beta` | Usuario criado com empresa vinculada |  |  |
| 9 | Login ADMIN Alpha | `admin.alpha` | Entrar no sistema | Login com sucesso |  |  |
| 10 | Menu ADMIN Alpha | `admin.alpha` | Ver menu lateral | Nao ve `Empresas` nem `Licencas` |  |  |
| 11 | Financeiro ADMIN | `admin.alpha` | Abrir financeiro | Acesso permitido |  |  |
| 12 | Usuarios ADMIN | `admin.alpha` | Abrir usuarios | Acesso permitido |  |  |
| 13 | Criar usuario pela empresa | `admin.alpha` | Criar usuario da Alpha | Permitido |  |  |
| 14 | Empresas via UI | `admin.alpha` | Tentar acessar empresas | Bloqueado ou oculto |  |  |
| 15 | Licencas via UI | `admin.alpha` | Tentar acessar licencas | Bloqueado ou oculto |  |  |
| 16 | Empresas via API | `admin.alpha` | `POST /empresas-prestadoras` | `403` |  |  |
| 17 | Licencas via API | `admin.alpha` | `POST /licencas` | `403` |  |  |
| 18 | Login OPERADOR Alpha | `operador.alpha` | Entrar no sistema | Login com sucesso |  |  |
| 19 | Menu OPERADOR | `operador.alpha` | Ver menu | So modulos liberados |  |  |
| 20 | Clientes OPERADOR | `operador.alpha` | Abrir clientes | Permitido se `customers.view` marcado |  |  |
| 21 | Editar cliente | `operador.alpha` | Criar ou editar cliente | Permitido se `customers.edit` marcado |  |  |
| 22 | Financeiro OPERADOR | `operador.alpha` | Abrir financeiro | Bloqueado se `finance.view` desmarcado |  |  |
| 23 | Configuracoes OPERADOR | `operador.alpha` | Abrir configuracoes | Bloqueado |  |  |
| 24 | Usuarios OPERADOR | `operador.alpha` | Abrir usuarios | Bloqueado |  |  |
| 25 | Login ESTOQUE Alpha | `estoque.alpha` | Entrar no sistema | Login com sucesso |  |  |
| 26 | Ver estoque | `estoque.alpha` | Abrir produtos ou estoque | Permitido |  |  |
| 27 | Movimentar estoque | `estoque.alpha` | Registrar entrada ou saida | Permitido se `stock.move` marcado |  |  |
| 28 | Criar produto | `estoque.alpha` | Tentar cadastrar produto | Bloqueado se `stock.manage` desmarcado |  |  |
| 29 | Login ADMIN Beta | `admin.beta` | Entrar no sistema | Login com sucesso |  |  |
| 30 | Isolamento Beta x Alpha | `admin.beta` | Ver clientes, produtos e OS | Nao enxerga dados da Alpha |  |  |
| 31 | Isolamento Alpha x Beta | `admin.alpha` | Ver clientes, produtos e OS | Nao enxerga dados da Beta |  |  |
| 32 | Visao global MASTER | `admin` | Ver dados gerais | MASTER mante acesso global |  |  |
| 33 | Usuario sem empresa | `admin` | Tentar criar usuario sem empresa | Sistema bloqueia |  |  |
| 34 | Permissao granular removida | `admin` | Tirar `finance.view` de um ADMIN | Usuario perde acesso ao financeiro |  |  |
| 35 | Permissao granular adicionada | `admin` | Dar `customers.edit` a OPERADOR | Usuario passa a editar clientes |  |  |

## Legenda de status

- `Passou`
- `Falhou`
- `Parcial`
- `Nao testado`

## Evidencias recomendadas

- print da tela
- nome do usuario testado
- endpoint testado, se for API
- mensagem exibida
- horario do teste

## Resumo final da homologacao

- Total testado:
- Passou:
- Falhou:
- Parcial:
- Principais observacoes:
- Apto para DEV: `Sim / Nao`
