# Configuracao Institucional de Documentos

## Objetivo

Esta entrega cria um cadastro institucional por empresa prestadora para abastecer automaticamente:

- Ordem de Servico
- Relatorio Tecnico
- Certificado Sanitario
- Certificado com moldura

## Estrutura tecnica

- nova tabela: `dados_tecnicos_empresa`
- relacionamento unico por `empresa_prestadora_id`
- persistencia binaria no banco para:
  - licenca sanitaria digitalizada
  - licenca ambiental digitalizada
  - assinatura do responsavel tecnico

## Dados controlados por empresa

- razao social documental
- nome fantasia documental
- CNPJ
- endereco da empresa
- telefone
- nome do responsavel tecnico
- conselho profissional
- numero do registro
- UF do registro
- numero e validade da licenca sanitaria
- numero e validade da licenca ambiental
- CIT

## Regras de seguranca

- leitura e edicao restritas a `admin` e `master`
- dados resolvidos sempre no escopo da `empresa_prestadora_id` do usuario logado
- ativos tecnicos nao sao expostos por caminho publico
- preview e download usam rotas autenticadas
- validacao de tipo e tamanho no upload

## UX implementada

Em `Configuracoes` foi criada uma secao institucional com:

- campos regulatorios da empresa
- upload de licenca sanitaria
- upload de licenca ambiental
- upload de assinatura
- canvas para assinatura desenhada
- preview de arquivos enviados

## Integracao documental

OS, relatorio tecnico e certificados agora consultam o cadastro institucional da empresa vinculada a ordem.

Se faltar qualquer item obrigatorio, a emissao do documento e bloqueada antes da geracao do PDF.

Campos bloqueantes:

- responsavel tecnico
- conselho/registro profissional
- licenca sanitaria
- licenca ambiental
- endereco da empresa
- CIT

## Estrategia de migracao

- a migracao cria `dados_tecnicos_empresa`
- os valores legados de `system_settings` sao copiados para cada empresa existente como base inicial
- depois disso, os documentos passam a ler o cadastro por empresa

## Validacao executada

Comandos executados:

```powershell
.venv\Scripts\python.exe -m flake8 app tests
.venv\Scripts\python.exe -m pytest tests\test_settings.py tests\test_documents.py tests\test_auth.py tests\test_multitenancy.py tests\test_work_orders.py -q
docker compose up --build -d
```

Resultado:

- `33 passed`
- build local em Docker concluido
- `health` validado em `http://127.0.0.1:8000/health`
