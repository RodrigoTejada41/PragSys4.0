# NF-e Direta SEFAZ

## Visao geral

O projeto agora suporta dois providers de NF-e:

- `focus_nfe`
- `sefaz_direct`

Quando `NFE_PROVIDER=sefaz_direct`, a emissao passa pelo fluxo interno:

1. montagem do XML NF-e 4.00
2. assinatura digital com certificado A1
3. validacao XSD
4. envio SOAP para SEFAZ
5. consulta de recibo
6. persistencia de XML, protocolo e status

## Estrutura

- `app/modules/sefaz_nfe/xml_generator.py`
- `app/modules/sefaz_nfe/signer.py`
- `app/modules/sefaz_nfe/sefaz_client.py`
- `app/modules/sefaz_nfe/services.py`
- `app/modules/sefaz_nfe/routes.py`

## Configuracao obrigatoria

O certificado A1 deve ser cadastrado preferencialmente em:

```text
Configuracoes -> Certificado Digital
```

Com o certificado central cadastrado, `SEFAZ_NFE_CERTIFICATE_PATH` e `SEFAZ_NFE_CERTIFICATE_PASSWORD` deixam de ser obrigatorios para o assinador interno. Eles continuam aceitos como fallback para ambientes legados.

- `NFE_PROVIDER=sefaz_direct`
- `SEFAZ_NFE_UF`
- certificado central cadastrado ou `SEFAZ_NFE_CERTIFICATE_PATH`
- certificado central cadastrado ou `SEFAZ_NFE_CERTIFICATE_PASSWORD`
- `SEFAZ_NFE_XSD_DIR`
- `COMPANY_CNPJ`
- `COMPANY_IE`
- `COMPANY_CRT`
- `COMPANY_STREET`
- `COMPANY_NUMBER`
- `COMPANY_DISTRICT`
- `COMPANY_CITY`
- `COMPANY_CITY_CODE`
- `COMPANY_STATE`
- `COMPANY_STATE_CODE`
- `COMPANY_ZIP_CODE`

## Persistencia

A tabela `notas_fiscais` passou a armazenar:

- `xml_enviado`
- `xml_autorizado`
- `protocolo_autorizacao`
- `recibo_lote`
- `lote_id`

## Observacoes operacionais

- a validacao XSD depende dos schemas oficiais da NF-e no diretorio configurado
- a assinatura depende de `signxml`, `lxml`, `cryptography` e certificado A1 valido
- o certificado central de `Configuracoes -> Certificado Digital` tem prioridade sobre o arquivo configurado no `.env`
- as URLs SOAP por UF/ambiente podem ser configuradas via `SEFAZ_NFE_WS_URLS_JSON`
- o codigo atual foi estruturado para homologacao e integracao direta, mas a operacao real depende de certificado, schemas e endpoints oficiais por UF

## Regra especial para homologacao

- em `homologacao`, o sistema pode operar sem `SEFAZ_NFE_XSD_DIR`
- nesse modo, a validacao XSD local e ignorada apenas para testes
- em `producao`, `SEFAZ_NFE_XSD_DIR` continua obrigatorio
