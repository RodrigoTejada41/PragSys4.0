# PR 4.1.0

## Resumo

Esta PR consolida a release `4.1.0`, registra a estrategia de backup da release em `release/SysPragas-4.1/` e aplica otimizacoes seguras de performance sem alterar comportamento funcional do sistema.

## O que entra

- versionamento do projeto para `4.1.0`;
- registro da release em `release/SysPragas-4.1/`;
- infraestrutura de testes otimizada com banco-template por processo e assets temporarios por sessao;
- custo de hash configuravel para ambiente de teste;
- indices e migracao de performance para consultas frequentes;
- ajuste de carregamento ORM de Ordem de Servico com `selectinload`;
- marcadores de teste `unit`, `integration`, `documents` e `external`;
- pequena otimizacao no fluxo de PDF de garantia, reduzindo custo repetitivo de resolucao e consulta;
- remocao do `bkp` do controle de versao, com estrategia de backup migrada para artefato `.zip`;
- exclusao padrao de `assinaturas`, `assinaturas_tecnicas`, `certificado` e `XSD` do backup automatizado, com inclusao opcional via `-IncludeSensitiveAssets`;
- correcao do cache de filesystem para templates, certificados e assinaturas, refletindo alteracoes em disco sem reinicio.

## Impacto esperado

- suite automatizada reduzida de cerca de `14m30s` para a faixa de `42s-45s`;
- menor custo em consultas de OS, financeiro e importacoes;
- execucao seletiva de testes para desenvolvimento e CI;
- preservacao das regras de negocio existentes.

## Validacao

```powershell
.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts\create_release_backup.ps1 -Version 4.1
powershell -ExecutionPolicy Bypass -File scripts\create_release_backup.ps1 -Version 4.1 -IncludeSensitiveAssets
```

Resultado validado localmente:

- `78 passed in 44.93s`
- backup padrao sem entradas sob `assinaturas/`, `assinaturas_tecnicas/`, `certificado/` e `XSD/`
- backup com `-IncludeSensitiveAssets` incluindo ativos sensiveis presentes no ambiente local

## Riscos observados

- migracao nova adiciona indices; o bootstrap atual deve aplica-la sem ajuste manual;
- o backup com ativos sensiveis agora exige chamada explicita via `-IncludeSensitiveAssets`;
- nao houve mudanca intencional em contratos de API ou fluxos operacionais.
