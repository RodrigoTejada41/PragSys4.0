# Changelog Tecnico - 2026-03-27

## Escopo da entrega

Consolidacao de tres frentes principais no SysPragas:

- estrutura multiempresa com isolamento por empresa
- RBAC com niveis e permissoes granulares
- Design System com padronizacao progressiva da interface

## 1. Multiempresa e estoque

### Implementado

- vinculo obrigatorio de usuario com empresa prestadora
- base para relacao matriz e filial
- isolamento de dados por `empresa_id`
- estrutura de visualizacao controlada de estoque entre unidades relacionadas
- historico de movimentacao de estoque por empresa

### Arquivos centrais

- `E:\Projetos\Controle_de_pragas1.1\app\infrastructure\models.py`
- `E:\Projetos\Controle_de_pragas1.1\app\infrastructure\migrations.py`
- `E:\Projetos\Controle_de_pragas1.1\app\application\services.py`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\api\routes\products.py`
- `E:\Projetos\Controle_de_pragas1.1\tests\test_multitenancy.py`

## 2. Controle de acesso

### Implementado

- niveis `master`, `admin` e `operador`
- permissoes granulares por usuario
- validacao central de acesso no backend
- protecao de rotas sensiveis por permissao
- interface de usuario com selecao de nivel e checkboxes de permissao

### Arquivos centrais

- `E:\Projetos\Controle_de_pragas1.1\app\core\permissions.py`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\api\deps.py`
- `E:\Projetos\Controle_de_pragas1.1\app\application\schemas.py`
- `E:\Projetos\Controle_de_pragas1.1\app\application\services.py`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\app.js`
- `E:\Projetos\Controle_de_pragas1.1\tests\test_access_control.py`

## 3. Design System

### Implementado

- arquivo central de tokens e componentes visuais
- padronizacao de inputs, selects, textareas e mensagens de validacao
- padronizacao de botoes, badges, tabelas, toast e navegacao
- padronizacao de dashboard, cards operacionais e estados vazios
- refinamento final da tela de login, previews documentais e responsividade

### Arquivos centrais

- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\design-system.css`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\components\head_assets.html`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\components\login_screen.html`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\components\navbar.html`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\components\sidebar.html`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\partials\dashboard_view.html`
- `E:\Projetos\Controle_de_pragas1.1\docs\design-system-formularios.md`

## 4. Documentacao adicionada

- `E:\Projetos\Controle_de_pragas1.1\docs\multiempresa-estoque-validacao.md`
- `E:\Projetos\Controle_de_pragas1.1\docs\rbac-niveis-permissoes.md`
- `E:\Projetos\Controle_de_pragas1.1\docs\checklist-homologacao-rbac.md`
- `E:\Projetos\Controle_de_pragas1.1\docs\design-system-formularios.md`

## 5. Validacao executada

## 5A. Complemento visual - botoes e navegacao

### Implementado

- consolidacao de uma base visual unica para botoes do sistema
- reforco do alinhamento de acoes de formulario sem empurrar botoes auxiliares para posicoes erradas
- helper central em `app.js` para gerar botoes dinamicos com variantes padronizadas
- correcao da navegacao para que apenas a view ativa fique visivel
- correcao especifica para o Dashboard nao permanecer renderizado ao trocar de tela
- refinamento final dos `toolbar-link` e atalhos documentais para reduzir a diferenca visual entre links de acao e botoes

### Arquivos centrais

- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\design-system.css`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\styles.css`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\app.js`

### Testes automatizados

- `pytest tests\\test_auth.py tests\\test_settings.py tests\\test_access_control.py tests\\test_multitenancy.py -q`
- resultado: `12 passed`

### Qualidade estatica

- `flake8 app tests`

### Validacao local containerizada

- `docker compose up --build -d`
- `GET /health` respondendo `{"status":"ok"}`

## 6. Observacoes operacionais

- os arquivos nao rastreados em `uploads/contratos` ficaram fora do commit
- a pasta `.playwright-cli/` tambem ficou fora do commit
- a entrega esta pronta para homologacao local e, apos aprovacao, para subida em VPS DEV
