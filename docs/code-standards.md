# Padroes de Codigo

## Objetivo

Estabelecer um baseline de clean code e manutencao para o monolito atual, reduzindo acoplamento e custo de onboarding.

## Principios obrigatorios

- nomes devem refletir intencao de negocio;
- uma funcao deve ter uma responsabilidade principal;
- validacao de borda deve acontecer cedo;
- regras de negocio devem ficar fora de templates e rotas;
- duplicacao funcional deve ser removida antes de crescer;
- comentarios devem explicar motivo, nao o obvio.

## Organizacao por camada

- `interfaces`: parsing HTTP, response codes, auth, renderizacao;
- `application`: orquestracao, validacao semantica, regras de negocio, geracao de documentos;
- `infrastructure`: banco, ORM e detalhes de persistencia;
- `domain`: enums e conceitos centrais.

## Convencoes de implementacao

- prefira helpers pequenos e deterministas para normalizacao;
- prefira schemas distintos para create, read e update;
- evite funcoes gigantes com multiplos niveis de decisao;
- normalize CPF/CNPJ, CEP, valores monetarios e estados em um unico ponto;
- mantenha side effects explicitos no nome da funcao.

## Tratamento de erros

- regras violadas devem lançar `BusinessRuleViolation`;
- excecoes de infraestrutura externa devem ser traduzidas para mensagens previsiveis;
- nao exponha stack traces ou detalhes internos em contratos HTTP.

## Testes

- cubra fluxos felizes e regras impeditivas;
- adicione teste de regressao para cada bug corrigido;
- preserve isolamento entre casos de teste;
- valide efeitos colaterais importantes: estoque, financeiro, documentos e autorizacao.

## Refatoracao recomendada

Ordem sugerida para evolucao:

1. extrair `services.py` por agregado;
2. criar modulo dedicado para documentos PDF;
3. introduzir repositorios ou gateways quando a camada `application` ficar fortemente acoplada a SQLAlchemy;
4. padronizar datas para UTC aware.

## Revisao de codigo

Toda revisao deve responder:

- a responsabilidade ficou na camada certa?
- o contrato externo mudou sem necessidade?
- existe nome melhor para clarificar a regra?
- a mudanca aumenta ou reduz acoplamento?
- ha cobertura automatizada suficiente para o risco introduzido?
