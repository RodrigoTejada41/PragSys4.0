# Contributing Guide

## Objetivo

Este projeto segue uma abordagem de monolito modular com FastAPI. As contribuicoes devem priorizar previsibilidade, legibilidade e baixo acoplamento entre camadas.

## Setup rapido

Instalacao editavel com dependencias de desenvolvimento:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Executar a aplicacao:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Executar testes:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Fluxo de trabalho

1. Crie uma branch curta e objetiva.
2. Mantenha cada commit com uma intencao unica.
3. Atualize testes e documentacao no mesmo change set da feature.
4. Abra PR com contexto funcional, impacto tecnico e estrategia de validacao.

Padrao sugerido de branch:

- `feat/<escopo-curto>`
- `fix/<escopo-curto>`
- `refactor/<escopo-curto>`
- `docs/<escopo-curto>`
- `test/<escopo-curto>`

## Padrao de commit

Use mensagens claras e orientadas a resultado:

- `feat: adiciona cadastro de empresas prestadoras`
- `fix: corrige conciliacao de estoque na exclusao da OS`
- `docs: adiciona guia de arquitetura e API`

## Checklist de pull request

- a mudanca tem objetivo funcional claro;
- a camada afetada esta correta para a responsabilidade adicionada;
- regras de negocio ficaram na camada `application`;
- detalhes de persistencia ficaram em `infrastructure`;
- interfaces HTTP nao passaram a concentrar regras de negocio;
- nomes, funcoes e schemas continuam coerentes com o dominio;
- testes automatizados foram atualizados ou justificados;
- documentacao relevante foi revisada.

## Definition of Done

Uma entrega so e considerada pronta quando:

- requisitos funcionais e regras de negocio foram implementados;
- testes passam localmente;
- nao ha regressao conhecida nos fluxos principais;
- documentacao de uso, arquitetura ou API foi atualizada quando necessario;
- riscos, pendencias e trade-offs foram explicitados no PR.

## Documentacao principal

- `docs/README.md`
- `docs/functional-specification.md`
- `docs/architecture.md`
- `docs/api-reference.md`
- `docs/code-standards.md`
- `docs/delivery-process.md`
