# ADR-0001: Layered Modular Monolith

## Status

Accepted

## Contexto

O sistema precisa entregar rapidamente funcionalidades operacionais para controle de pragas sem introduzir custo prematuro de microservicos, mensageria ou infraestrutura distribuida.

## Decisao

Adotar um monolito modular em camadas com:

- `domain` para conceitos centrais;
- `application` para casos de uso;
- `infrastructure` para persistencia;
- `interfaces` para API e web.

## Consequencias

Positivas:

- deploy simples;
- baixo custo operacional;
- facil rastrear regra de negocio ponta a ponta;
- onboarding mais rapido.

Negativas:

- risco de concentracao excessiva em modulos centrais;
- necessidade de disciplina para manter fronteiras de camada;
- crescimento do arquivo `services.py` se nao houver refatoracao incremental.

## Revisao futura

Reavaliar esta ADR quando houver:

- necessidade clara de multi-tenant forte;
- integracoes assincronas relevantes;
- escalabilidade independente por contexto;
- time suficiente para suportar maior complexidade operacional.
