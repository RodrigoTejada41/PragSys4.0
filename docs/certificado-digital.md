# Modulo De Certificado Digital

Data: 2026-07-10
Escopo: Configuracoes -> Certificado Digital

## Objetivo

Centralizar o certificado digital A1 da empresa para emissao fiscal, assinatura XML, comunicacao SEFAZ e identificacao automatica do emissor.

## Interface

Menu:

```text
Configuracoes -> Certificado Digital
```

A tela permite:

- selecionar arquivo `.pfx` ou `.p12`;
- informar senha sem exibir o valor;
- validar arquivo antes de salvar;
- salvar/substituir certificado;
- testar o certificado salvo;
- remover certificado;
- aplicar dados extraidos no cadastro da empresa;
- visualizar status, validade, emissor, serie, thumbprint e alertas.

## API

Base:

```text
/api/v1/settings/digital-certificate
```

Endpoints:

| Metodo | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/v1/settings/digital-certificate` | Consulta status e metadados |
| `POST` | `/api/v1/settings/digital-certificate/validate` | Valida upload sem salvar |
| `POST` | `/api/v1/settings/digital-certificate` | Salva ou substitui certificado |
| `POST` | `/api/v1/settings/digital-certificate/test` | Testa certificado salvo |
| `POST` | `/api/v1/settings/digital-certificate/apply-company` | Aplica dados extraidos ao cadastro da empresa |
| `DELETE` | `/api/v1/settings/digital-certificate` | Remove certificado central |

Permissoes:

- leitura: `settings.view`;
- alteracao/teste/remocao: `settings.manage`;
- roles aceitas: `master`, `admin`.

## Persistencia

Tabelas:

- `certificados_digitais`;
- `certificado_digital_auditoria`.

Campos sensiveis:

- `encrypted_file_data`;
- `encrypted_password`.

Criptografia:

- usa `SETTINGS_ENCRYPTION_KEY` quando configurado;
- fallback para `JWT_SECRET`;
- nunca retorna senha pela API;
- nunca grava senha em log ou documentacao.

## Extracao automatica

O sistema extrai quando o certificado contem os campos:

- razao social;
- nome fantasia/unidade organizacional;
- CNPJ;
- inscricao estadual quando presente em OID ICP-Brasil conhecido;
- logradouro;
- cidade;
- UF;
- CEP;
- numero de serie;
- emissor;
- autoridade certificadora;
- validade;
- thumbprint;
- algoritmo de assinatura.

Observacao: certificados A1 normalmente nao carregam todos os dados de endereco, inscricao municipal ou codigo IBGE. Quando o campo nao existir no certificado, a API retorna `null` e nao inventa dados.

## Alertas

Alertas automaticos:

- certificado vencido;
- vencimento em ate 60 dias;
- vencimento em ate 30 dias;
- vencimento em ate 15 dias;
- vencimento em ate 7 dias;
- cadeia intermediaria nao embutida no PFX/P12.

Os alertas aparecem no painel do certificado. O payload tambem fica disponivel em `GET /api/v1/settings`.

## Integracao fiscal

O assinador SEFAZ (`app/modules/sefaz_nfe/signer.py`) agora tenta carregar primeiro o certificado central salvo no banco.

Fallback mantido:

- `SEFAZ_NFE_CERTIFICATE_PATH`;
- `SEFAZ_NFE_CERTIFICATE_PASSWORD`.

Esse fallback preserva compatibilidade com ambientes antigos, mas o caminho recomendado passa a ser o cadastro central em Configuracoes.

## Auditoria

Eventos registrados:

- `created`;
- `replaced`;
- `tested`;
- `company_applied`;
- `removed`.

Cada evento salva:

- empresa;
- usuario;
- acao;
- status;
- data/hora;
- detalhe sem senha.

## Validacao

Testes automatizados adicionados em:

- `tests/test_settings.py`

Cobertura:

- consulta inicial sem certificado;
- validacao de PFX valido;
- rejeicao por senha incorreta;
- armazenamento criptografado;
- teste do certificado salvo;
- aplicacao de dados no cadastro da empresa;
- auditoria dos eventos.
