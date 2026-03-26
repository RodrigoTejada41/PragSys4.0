# Arquitetura Multempresa

## Estrategia escolhida

Foi adotada a abordagem de **multitenancy por coluna de tenant**, usando `empresa_prestadora_id` como identificador de isolamento.

## Motivos

- menor custo de migracao a partir da base atual;
- compatibilidade com operacao local e em rede;
- viabiliza escalada gradual sem quebrar toda a arquitetura;
- permite segmentacao por usuario e por empresa no mesmo banco.

## Regras de isolamento

- cada usuario comum pertence a uma empresa;
- cada registro operacional deve carregar `empresa_prestadora_id`;
- filtros de tenant devem ser aplicados na camada `application`;
- UI nunca deve ser a unica barreira de isolamento;
- usuario `master` pode operar com visao global.

## Entidades priorizadas na fundacao 4.0.0

- clientes
- produtos
- pragas
- tecnicos
- ordens de servico
- agendamentos
- financeiro
- recibos
- notas fiscais

## Proximo fechamento tecnico recomendado

- propagar filtros tenant-aware em todas as consultas CRUD;
- impedir escrita de entidade cruzada entre empresas;
- adicionar auditoria de `criado_por` e `atualizado_por`;
- revisar relatorios e PDFs para respeitarem contexto da empresa ativa.
