# Arquitetura

## Estilo arquitetural

O projeto adota um monolito modular em camadas. A estrategia privilegia simplicidade de deploy e clareza de fluxo, mantendo separacao de responsabilidades entre dominio, aplicacao, infraestrutura e interfaces.

## Camadas e responsabilidades

### `app/domain`

- enums e conceitos centrais do dominio;
- tipos estaveis e sem dependencia de framework.

### `app/application`

- schemas de entrada e saida;
- casos de uso e regras de negocio;
- coordenacao entre validacao, persistencia e geracao de documentos.

### `app/infrastructure`

- engine, sessao e bootstrap do banco;
- modelos SQLAlchemy;
- migracoes leves e detalhes de persistencia.

### `app/interfaces`

- rotas REST;
- dependencias de autenticacao e autorizacao;
- rotas e assets da interface web.

## Regra de dependencia

As dependencias devem apontar para dentro:

- `interfaces` pode depender de `application`, `domain` e `infrastructure`;
- `application` pode depender de `domain` e `infrastructure`;
- `domain` nao deve depender de framework, banco ou HTTP.

## Fluxo principal de requisicao

1. A rota HTTP recebe request e valida permissao.
2. O schema Pydantic normaliza o payload.
3. A camada `application` executa o caso de uso.
4. A camada `infrastructure` persiste ou consulta dados.
5. A resposta e serializada de volta para a API ou UI.

## Aplicacao de principios SOLID

### Single Responsibility Principle

- rotas cuidam de transporte HTTP;
- `db.py` cuida do ciclo de engine/sessao;
- modelos representam persistencia;
- schemas representam contrato.

Diretriz futura:

- o arquivo `app/application/services.py` deve ser gradualmente fatiado por contexto (`customers`, `finance`, `work_orders`, `documents`) para reduzir concentracao de responsabilidades.

### Open/Closed Principle

- novos recursos devem entrar por novos casos de uso ou modulos, evitando alterar fluxos estaveis sem necessidade;
- enums e schemas ajudam a expandir comportamentos com baixo impacto colateral.

### Liskov Substitution Principle

- schemas derivados e enums devem preservar contratos e semantica dos tipos usados pelas rotas e servicos.

### Interface Segregation Principle

- endpoints e schemas devem expor apenas o necessario para cada operacao;
- modelos de criacao, leitura e atualizacao devem continuar separados.

### Dependency Inversion Principle

- regras de negocio devem depender de abstracoes do dominio e contratos de dados, nao de detalhes HTTP;
- se o volume crescer, repositorios por agregado podem ser introduzidos para desacoplar ainda mais `application` de SQLAlchemy.

## Decisoes arquiteturais relevantes

- SQLite e usado como banco padrao para simplificar o bootstrap local;
- migracoes sao leves e executadas no bootstrap em `init_db()`;
- autenticacao usa JWT stateless;
- documentos PDF sao gerados no backend sincronamente.

## Riscos tecnicos atuais

- `app/application/services.py` concentra muitos casos de uso e tende a crescer demais;
- as migracoes em tempo de bootstrap sao praticas para MVP, mas devem migrar para ferramenta dedicada se o schema continuar evoluindo;
- uso recorrente de `datetime.utcnow()` gera warnings e deve ser padronizado para UTC aware.

## Diretrizes de evolucao

- introduzir modulos de servico por agregado antes de adicionar novas features grandes;
- isolar geracao de PDF em modulo proprio de documentos;
- manter contratos HTTP estaveis e versionados sob `/api/v1`;
- adicionar observabilidade basica antes de ampliar integracoes externas.
