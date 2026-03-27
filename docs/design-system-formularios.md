# Design System de Formularios e Inputs

## Objetivo

Centralizar a base visual da interface para que inputs, formularios e blocos de trabalho sigam o mesmo padrao visual, sem quebrar os fluxos atuais gerados pelo frontend dinamico.

## Arquivos principais

- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\design-system.css`
- `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\components\head_assets.html`

## Estrutura criada

### 1. Tokens de design

O arquivo `design-system.css` agora concentra:

- paleta principal e estados de feedback
- tipografia base e de titulos
- escala de espacamento
- raios de borda
- sombras
- altura e padding padrao dos controles
- anel de foco e estados de sucesso/erro

Os tokens foram espelhados para as variaveis `--sys-*` existentes, o que permite evoluir a interface sem reescrever o CSS legado inteiro.

### 2. Padronizacao de campos

Foram unificados:

- `input`
- `select`
- `textarea`
- filtros operacionais
- estados `focus`, `error`, `success` e `disabled`
- labels acima do campo
- mensagens de validacao abaixo do campo

### 3. Padronizacao de formularios

Foram ajustados:

- espacamento interno de paineis
- hierarquia visual de titulos e textos de apoio
- grids responsivos de campos
- alinhamento de acoes
- grupos de permissao do cadastro de usuarios

### 4. Componentes de workspace

Nesta etapa o Design System tambem passou a cobrir:

- botoes primarios, secundarios e destrutivos
- badges e pills de status
- tabelas e paginacao do DataTables
- toast de feedback
- navegacao superior e menu lateral
- estilo base para modais Bootstrap futuros

### 5. Dashboard e paineis operacionais

Foi adicionada uma camada visual para:

- cards de KPI e widgets do dashboard
- estados vazios e mensagens de ausencia de dados
- cards de resumo de contratos, configuracoes e recibos
- paineis de agenda operacional
- cards de ordens de servico e seus blocos de resumo
- blocos de alerta e radar operacional

### 6. Acabamento final

Esta etapa final padronizou:

- tela de login
- cards de preview de recibo
- janelas auxiliares de preview documental
- visual de impressao resumida de agendamento
- ajustes finos de responsividade para mobile

## Decisao tecnica

Em vez de substituir `styles.css`, a entrega adiciona um arquivo central novo, carregado depois do legado. Isso reduz risco de regressao e permite migracao progressiva para o Design System.

## Impacto esperado

- formularios mais consistentes e legiveis
- melhor leitura dos estados de validacao
- menos variacao visual entre modulos
- melhor leitura do workspace operacional e da navegacao
- dashboards e paineis mais coerentes entre si
- experiencia de entrada e visual documental mais profissionais
- base mais segura para evoluir novos modulos SaaS

## Validacao recomendada

- login
- cadastro de clientes
- cadastro de produtos
- cadastro de usuarios
- painel de permissoes
- filtros de financeiro
- agenda operacional
- formularios de empresas e licencas
- menu lateral e estados ativos
- tabelas com filtro e paginacao
- badges de status em financeiro, licencas e usuarios
- toast de feedback apos salvar ou excluir registros
- dashboard inicial e cards de KPI
- ordens em foco e cards da agenda operacional
- estados vazios em contratos, estoque, agenda e empresas
- tela de login em desktop e mobile
- preview de recibo e abertura de PDF em nova janela
