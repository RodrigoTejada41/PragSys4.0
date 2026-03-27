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
- centro de informacao toxicologica
- CIT

## Regras de seguranca

- leitura e edicao restritas a `admin` e `master`
- dados resolvidos sempre no escopo da `empresa_prestadora_id` do usuario logado
- ativos tecnicos nao sao expostos por caminho publico
- preview e download usam rotas autenticadas
- validacao de tipo e tamanho no upload
- CIT padronizado em todos os documentos

## UX implementada

Em `Configuracoes` foi criada uma secao institucional com:

- campos regulatorios da empresa
- upload de licenca sanitaria
- upload de licenca ambiental
- upload de assinatura
- canvas para assinatura desenhada
- preview de arquivos enviados
- tentativa de extracao automatica dos dados regulatorios quando a licenca em PDF possui texto selecionavel
- orientacao visual explicita informando que CIT nao e upload e pode exigir preenchimento manual

## Integracao documental

OS, relatorio tecnico e certificados agora consultam o cadastro institucional da empresa vinculada a ordem.

Se faltar qualquer item obrigatorio, a emissao do documento e bloqueada antes da geracao do PDF.

Campos bloqueantes:

- responsavel tecnico
- conselho/registro profissional
- licenca sanitaria
- licenca ambiental
- endereco da empresa
- centro de informacao toxicologica
- CIT

## Padrao visual aplicado nos documentos

- mesma referencia de CIT no rodape dos certificados
- mesma logica de assinatura do responsavel tecnico
- assinatura com area fixa, redimensionamento proporcional e contencao dentro da margem
- botoes de acao das telas de configuracao alinhados no mesmo padrao visual

## Extracao automatica por PDF

Quando a licenca sanitaria ou ambiental e enviada em PDF com camada de texto, o sistema tenta preencher automaticamente:

- responsavel tecnico
- registro profissional
- endereco da empresa
- centro de informacao toxicologica
- telefone CIT
- numero da licenca correspondente
- com tolerancia a acentos e variacoes comuns de rotulo no PDF
- com suporte ao formato comum `Numero da Licenca` e `Registro: CRBio ...`

Observacao:

- PDFs apenas escaneados, sem texto selecionavel, ainda podem exigir preenchimento manual
- se o PDF nao trouxer CIT/telefone CIT no proprio conteudo, esse campo continua exigindo preenchimento manual

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

- `36 passed`
- build local em Docker concluido
- `health` validado em `http://127.0.0.1:8000/health`
