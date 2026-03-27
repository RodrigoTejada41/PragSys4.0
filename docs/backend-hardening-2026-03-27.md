# Endurecimento do Backend - 2026-03-27

Esta entrega reforca o backend em quatro frentes prioritarias: configuracao segura em producao, protecao de segredos persistidos, coordenacao do scheduler diario e tratamento mais preciso de autenticacao.

## O que mudou

- `app/core/config.py`
  - adicionou `APP_ENV`;
  - adicionou `SETTINGS_ENCRYPTION_KEY`;
  - passou a falhar em producao se `JWT_SECRET` ou `DEFAULT_ADMIN_PASSWORD` continuarem nos valores inseguros de fabrica.

- `app/application/settings_service.py`
  - configuracoes sensiveis como `smtp_password` passaram a ser gravadas criptografadas;
  - leitura continua compativel com valores antigos em texto puro, permitindo migracao gradual sem quebrar ambientes existentes.

- `app/infrastructure/models.py`
  - nova tabela `background_job_runs` para coordenar execucoes diarias unicas por tarefa.

- `app/infrastructure/migrations.py`
  - nova migracao `20260327_001_backend_hardening` para criar a estrutura de coordenacao do scheduler.

- `app/application/contract_scheduler.py`
  - cada ciclo diario agora faz claim unico no banco antes de executar;
  - se a rotina falhar, o claim e liberado para nova tentativa no mesmo dia.

- `app/interfaces/api/deps.py`
  - autenticacao deixou de mascarar qualquer excecao interna como `401`;
  - agora apenas falhas de token/negocio retornam `401`, preservando `500` real para erros internos inesperados.

## Motivacao tecnica

- reduzir risco operacional em producao com defaults inseguros;
- evitar vazamento trivial de credenciais SMTP no banco;
- impedir execucao duplicada de manutencao contratual em cenarios com mais de um processo;
- melhorar observabilidade de falhas reais no backend.

## Impacto esperado

- producao fica mais segura por padrao;
- settings sensiveis passam a exigir consistencia de `SETTINGS_ENCRYPTION_KEY` ou `JWT_SECRET`;
- scheduler contratual fica mais previsivel em multiplas instancias/processos;
- autenticacao fica mais diagnostica e menos opaca em caso de bug interno.

## Validacao

- nova cobertura em `tests/test_backend_hardening.py`;
- suite completa revalidada apos a implementacao.
