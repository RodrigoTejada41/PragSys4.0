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
- downloads e visualizacao retornam binario com `Content-Disposition` apropriado.

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
- `GET /financeiro/resumo`
- `GET /financeiro/caixa`
- `POST /financeiro`
- `PUT /financeiro/{id}`
- `POST /financeiro/{id}/pagar`
- `DELETE /financeiro/{id}`

### Ordens de servico

- `GET /os`
- `POST /os`
- `PUT /os/{id}`
- `POST /os/{id}/concluir`
- `POST /os/{id}/quitar`
- `DELETE /os/{id}`
- `GET /os/{id}/pdf`
- `GET /os/{id}/relatorio-tecnico.pdf`
- `GET /os/{id}/certificado-sanitario.pdf`
- `GET /os/{id}/certificado-moldura.pdf`

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
