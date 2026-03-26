# PR 4.1.0

## Resumo

Esta PR consolida a release `4.1.0`, registra o backup versionado em `release/SysPragas-4.1/` e aplica otimizações seguras de performance sem alterar comportamento funcional do sistema.

## O que entra

- versionamento do projeto para `4.1.0`;
- snapshot de release em `release/SysPragas-4.1/`;
- infraestrutura de testes otimizada com banco-template por processo e assets temporarios por sessao;
- custo de hash configuravel para ambiente de teste;
- indices e migracao de performance para consultas frequentes;
- ajuste de carregamento ORM de Ordem de Servico com `selectinload`;
- marcadores de teste `unit`, `integration`, `documents` e `external`;
- pequena otimização no fluxo de PDF de garantia, reduzindo custo repetitivo de resolucao/consulta.
- remocao do `bkp` do controle de versao, com estrategia de backup migrada para artefato `.zip`.

## Impacto esperado

- suite automatizada reduzida de cerca de `14m30s` para a faixa de `42s-45s`;
- menor custo em consultas de OS, financeiro e importacoes;
- execucao seletiva de testes para desenvolvimento e CI;
- preservacao das regras de negocio existentes.

## Validacao

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Resultado validado localmente:

- `76 passed in 45.47s`

## Riscos observados

- migracao nova adiciona indices; o bootstrap atual deve aplica-la sem ajuste manual;
- o snapshot `release/SysPragas-4.1/bkp` aumenta o volume versionado por ser um backup deliberado;
- nao houve mudanca intencional em contratos de API ou fluxos operacionais.
