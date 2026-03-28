# Assistente virtual do sistema

## Objetivo

Foi adicionado um assistente virtual contextual para funcionar como "treinador do software" dentro da interface web. Ele orienta o usuario com base nas funcionalidades que ja existem no sistema, sem inventar fluxos paralelos.

## O que foi implementado

- botao flutuante fixo no canto inferior direito
- painel retangular centralizado, com visual de central de ajuda
- grade de cards clicaveis por modulo
- modo de ensino guiado dentro do proprio painel
- chat textual como apoio secundario
- resposta contextual baseada na tela atual
- respostas alinhadas ao perfil do usuario:
  - `master`
  - `admin`
  - `operador`
  - `gestor_estoque`
- rota autenticada para chat:
  - `POST /api/v1/assistente/chat`

## Regras de funcionamento

- o assistente so aparece apos login
- o assistente usa a tela atual como contexto
- as respostas seguem a estrutura real do sistema:
  - estoque
  - ordens de servico
  - financeiro
  - clientes
  - configuracoes
  - usuarios
  - empresas prestadoras
  - licencas
- se o usuario perguntar sobre um modulo sem permissao, o assistente responde com orientacao segura e avisa a restricao

## Experiencia de uso

- o primeiro clique abre a central de ajuda no centro da interface
- o usuario pode aprender sem digitar, apenas clicando nos cards de modulo
- cada modulo abre um conteudo didatico com:
  - o que e
  - para que serve
  - onde fica
  - passo a passo
  - exemplo real
  - dica pratica
  - proxima acao sugerida
- o chat textual continua disponivel como suporte complementar
- o painel pode ser minimizado ou fechado sem perder o historico da conversa

## Arquitetura

- backend:
  - `E:\Projetos\Controle_de_pragas1.1\app\application\assistant_service.py`
  - `E:\Projetos\Controle_de_pragas1.1\app\interfaces\api\routes\assistant.py`
- frontend:
  - `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\templates\base.html`
  - `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\app.js`
  - `E:\Projetos\Controle_de_pragas1.1\app\interfaces\web\static\design-system.css`

## Validacao recomendada

1. entrar no sistema
2. abrir o assistente no dashboard
3. validar os cards de modulo no painel central
4. clicar em `Estoque` e depois em `Saida (baixa)`
5. clicar em `Ordem de Servico` e depois em `Como criar uma OS`
6. abrir o chat textual e pedir: `Como dar baixa no estoque?`
7. testar com perfil restrito e confirmar que modulos bloqueados nao aparecem ou recebem resposta compativel com a permissao
