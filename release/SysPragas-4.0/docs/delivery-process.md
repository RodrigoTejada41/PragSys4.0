# Processo de Entrega

## Modelo de trabalho

O projeto deve operar com backlog priorizado e entregas incrementais. A referencia de processo e Scrum adaptado para time pequeno.

## Cerimonias recomendadas

### Sprint Planning

- revisar backlog priorizado;
- alinhar objetivo da sprint;
- quebrar historias em tarefas tecnicas pequenas;
- explicitar dependencias, riscos e criterios de aceite.

### Daily Scrum

Cada membro responde:

- o que concluiu desde a ultima daily;
- o que vai executar ate a proxima;
- quais impedimentos existem.

### Sprint Review

- demonstrar incremento funcional;
- validar criterios de aceite;
- coletar feedback de negocio e operacao.

### Retrospective

- registrar o que funcionou;
- registrar desperdicios e gargalos;
- definir no maximo tres acoes objetivas para a sprint seguinte.

## Estrutura minima do backlog

Cada item deve conter:

- contexto de negocio;
- resultado esperado;
- criterios de aceite;
- impacto tecnico;
- definicao de testes necessarios;
- atualizacao documental esperada.

## Politica de versionamento

- seguir Semantic Versioning para releases publicas;
- `MAJOR` para breaking changes;
- `MINOR` para novas features retrocompativeis;
- `PATCH` para correcoes e ajustes internos.

## Estrategia de controle de versao

- `main` deve permanecer estavel;
- features entram por PR;
- commits pequenos facilitam rollback e auditoria;
- rebase ou squash devem preservar historico legivel.

## Criterios de aceite tecnico

- testes relevantes executados;
- contratos documentados;
- impactos em dados ou migracao avaliados;
- rollback ou mitigacao conhecidos quando houver risco;
- documentacao atualizada no mesmo ciclo.
