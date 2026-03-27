# Referencia de API

## Convencoes gerais

- Base path: `/api/v1`
- Autenticacao: `Authorization: Bearer <token>`
- Formato predominante: JSON
- Documentacao interativa: `/docs`

## Status codes esperados

- `200`: leitura ou alteracao com retorno de payload
- `201`: recurso criado
- `204`: exclusao sem corpo de resposta
- `400`: violacao de regra de negocio
- `401`: token ausente, invalido ou credencial incorreta
- `403`: usuario sem permissao
- `404`: recurso nao encontrado quando aplicavel

## Recursos da API

### Auth

- `POST /auth/login`
- `GET /auth/me`

Responsabilidade:

- emitir token JWT;
- retornar contexto do usuario autenticado.

### Clientes

- `GET /clientes`
- `GET /clientes/consultar-cnpj/{cnpj}`
- `GET /clientes/consultar-cep/{cep}`
- `POST /clientes`
- `PUT /clientes/{id}`
- `DELETE /clientes/{id}`

Observacoes:

- payload do cliente agora aceita `email` opcional.

### Contratos

- `GET /contratos`
- `GET /contratos/dashboard`
- `GET /contratos/relatorios`
- `GET /contratos/relatorios.xlsx`
- `GET /contratos/relatorios.pdf`
- `GET /contratos/{id}`
- `PUT /contratos/{id}`
- `DELETE /contratos/{id}`
- `GET /contratos/{id}/arquivo`
- `POST /contratos/rotina/sincronizar`
- `GET /clientes/{customer_id}/contratos`
- `POST /clientes/{customer_id}/contratos`

Observacoes:

- criacao e edicao de contratos usam `multipart/form-data`;
- o arquivo do contrato e opcional;
- o payload de contrato tambem aceita:
  - `valor_mensal`
  - `tipo_cobranca`
  - `dia_vencimento`
  - `gerar_cobranca_automatica`
- os endpoints de relatorio aceitam filtros por cliente, status, periodos e cobranca ativa;
- downloads e visualizacao retornam binario com `Content-Disposition` apropriado.

### Configuracoes

- `GET /settings`
- `PUT /settings`
- `GET /settings/database/backup`
- `POST /settings/database/restore`
- `POST /settings/database/cleanup`

Observacoes:

- o payload administrativo passou a incluir o bloco `email`;
- `email` aceita `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_use_tls`, `smtp_use_ssl`, `smtp_sender_email` e `smtp_sender_name`;
- o bloco `database` aceita `backup_dir`;
- a resposta devolve `smtp_password_configured` no lugar da senha em claro;
- notificacoes automáticas de contratos usam primeiro o SMTP salvo em configuracoes e mantem fallback para `.env` quando ainda nao houve sobrescrita administrativa.
- `GET /settings/database/backup` exporta o banco SQLite atual em formato `.db`;
- `POST /settings/database/restore` recebe `multipart/form-data` com `file` e `confirmation = RESTAURAR`;
- `POST /settings/database/cleanup` recebe JSON com `confirmation = CONFIRMAR` e `include_finance`.

### Empresas prestadoras

- `GET /empresas-prestadoras`
- `GET /empresas-prestadoras/consultar-cnpj/{cnpj}`
- `POST /empresas-prestadoras`
- `PUT /empresas-prestadoras/{id}`
- `DELETE /empresas-prestadoras/{id}`

### Produtos

- `GET /produtos`
- `POST /produtos`
- `PUT /produtos/{id}`
- `DELETE /produtos/{id}`
- `POST /produtos/importar-xml`
- `POST /produtos/importar-csv`

Observacoes:

- importacoes podem gerar atualizacao de estoque;
- importacoes podem gerar lancamentos financeiros derivados.

### Pragas

- `GET /pragas`
- `POST /pragas`
- `PUT /pragas/{id}`
- `DELETE /pragas/{id}`

### Tecnicos

- `GET /tecnicos`
- `POST /tecnicos`
- `PUT /tecnicos/{id}`
- `DELETE /tecnicos/{id}`

### Financeiro

- `GET /financeiro`
- `GET /financeiro/caixa`
- `GET /financeiro/dashboard`
- `POST /financeiro`
- `PUT /financeiro/{id}`
- `POST /financeiro/{id}/pagar`
- `DELETE /financeiro/{id}`

Observacoes:

- lancamentos financeiros agora podem carregar `contrato_id`;
- registros com `origem = contrato` sao gerados automaticamente pela rotina contratual;
- `POST /financeiro` rejeita vinculo direto com `os_id` quando a OS for do tipo `contrato`;
- cobrancas recorrentes entram no mesmo fluxo de contas a receber e baixa ja existente.

### Ordens de servico

- `GET /os`
- `POST /os`
- `PUT /os/{id}`
- `POST /os/{id}/efetuar`
- `POST /os/{id}/baixar`
- `POST /os/{id}/reabrir`
- `DELETE /os/{id}`
- `GET /os/{id}/pdf`
- `GET /os/{id}/relatorio-tecnico.pdf`
- `GET /os/{id}/certificado-sanitario.pdf`
- `GET /os/{id}/certificado-moldura.pdf`

Observacoes:

- payload de OS agora aceita `tipo_os` com valores `avulsa` e `contrato`;
- OS `avulsa` pode continuar gerando financeiro automatico quando `gerar_financeiro = true`;
- OS `contrato` continua gerando agendamento normalmente, mas nunca gera financeiro automatico;
- OS `contrato` tambem bloqueia recibos e lancamentos financeiros vinculados por chamada direta, para evitar cobranca duplicada.

### Usuarios

- `GET /usuarios`
- `POST /usuarios`
- `PUT /usuarios/{id}`
- `DELETE /usuarios/{id}`

### Licencas

- `GET /licencas`
- `POST /licencas`
- `PUT /licencas/{id}`
- `DELETE /licencas/{id}`

## Regras de contrato

- contratos de request e response devem permanecer nos schemas Pydantic;
- validacoes sintaticas pertencem aos schemas;
- validacoes semanticas e regras de negocio pertencem aos servicos;
- erros funcionais devem usar `BusinessRuleViolation` para manter resposta consistente.

## Politica de evolucao

- mudanças breaking devem criar nova versao de API;
- campos novos devem ser adicionados de forma retrocompativel sempre que possivel;
- endpoints devem permanecer focados em um agregado e uma intencao.
