# Release SysPragas 4.1

Versao 4.1 da linha SysPragas com foco em estabilidade, rastreabilidade de release e aceleracao segura da suite automatizada.

## Escopo desta release

- consolidacao da base 4.x para manutencao continua;
- versionamento principal elevado para `4.1.0`;
- estrategia de backup por artefato `.zip`, evitando duplicacao versionada dentro do repositorio;
- otimizacao segura da infraestrutura de testes, sem alterar regras de negocio.

## Destaques tecnicos

- banco-template de testes para eliminar recriacao completa de schema a cada caso;
- assets temporarios de teste compartilhados por sessao;
- token de autenticacao de teste emitido diretamente no fixture;
- custo de hash configuravel por ambiente;
- suite automatizada reduzida de cerca de 14m30s para cerca de 44s.
- resolucao de templates e assinaturas passou a refletir mudancas no filesystem sem reinicio do processo.

## Referencias

- `CHANGELOG.md`
- `README.md`
- `docs/performance-test-suite-report-2026-03-26.md`
- `scripts/create_release_backup.ps1`
