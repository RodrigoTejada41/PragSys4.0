# Design System

## Objetivo

O frontend passou a usar uma base visual centralizada para formularios, filtros e componentes de entrada, com foco em:

- consistencia visual;
- reutilizacao;
- manutencao segura sem reescrever a SPA;
- preparacao para crescimento futuro do produto.

## Estrutura

- tokens globais em [`app/interfaces/web/static/styles.css`](/E:/Projetos/Controle_de_pragas1.1/app/interfaces/web/static/styles.css);
- enriquecimento comportamental e validacao visual em [`app/interfaces/web/static/ui.js`](/E:/Projetos/Controle_de_pragas1.1/app/interfaces/web/static/ui.js);
- integracao da SPA em [`app/interfaces/web/static/app.js`](/E:/Projetos/Controle_de_pragas1.1/app/interfaces/web/static/app.js).

## Tokens

### Cores

- `--sys-color-primary`
- `--sys-color-secondary`
- `--sys-color-success`
- `--sys-color-danger`
- `--sys-color-warning`
- `--sys-color-background`
- `--sys-color-surface`
- `--sys-color-text`
- `--sys-color-text-secondary`

### Tipografia

- `--sys-font-family-base`
- `--sys-font-family-heading`
- `--sys-font-size-sm`
- `--sys-font-size-md`
- `--sys-font-size-lg`
- `--sys-font-weight-regular`
- `--sys-font-weight-bold`

### Espacamento e forma

- `--sys-space-1` ate `--sys-space-6`
- `--sys-radius`
- `--sys-radius-sm`
- `--sys-radius-xs`
- `--sys-border-width`
- `--sys-control-height`

## Componentes padrao

### Campos

O design system padroniza:

- `input`
- `select`
- `textarea`
- estados de `focus`, `disabled`, `error` e `success`
- labels sempre acima do campo
- mensagens visuais abaixo do campo via `.ui-field-message`

### Formularios

Todos os formularios gerados pela SPA passam por `SysPragasUI.enhanceAllForms()` para receber:

- classes estruturais reutilizaveis;
- campos com altura e padding consistentes;
- acoes com alinhamento uniforme;
- validacao visual sem alterar a regra de negocio existente.

## Validacao

- validacoes nativas usam `SysPragasUI.validateForm(form)`;
- formularios com regra customizada, como O.S. e agendamento, usam `SysPragasUI.markInvalid(...)` para destacar campo e mensagem de forma consistente;
- o erro geral do formulario continua existindo para regras de negocio compostas.

## Limites atuais

- a arquitetura atual ainda usa HTML montado em `app.js`, entao a padronizacao foi feita por composicao e enriquecimento de DOM para evitar regressao;
- dark mode e temas adicionais ainda nao foram ativados;
- mascaras de documento e telefone continuam no comportamento legado.
