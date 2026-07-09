# Multitenancy Spec

Status: Draft inicial
Approver: TBD
Approval date: TBD
Approval reference: TBD

## Objetivo

Definir isolamento logico por empresa prestadora.

## Escopo

- `empresa_prestadora_id`
- filtros por empresa
- dados compartilhados ou isolados

## Criterios de aceite

- Consultas devem respeitar escopo da empresa.
- Operacoes criticas devem impedir vazamento entre empresas.
- Testes devem cobrir isolamento minimo.

