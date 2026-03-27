# SysPragas 4.0

Versao 4.0 do sistema SysPragas para operacao, financeiro, documentos tecnicos e integracoes empresariais.

## Documentacao de engenharia

- [Base de documentacao](docs/README.md)
- [Especificacao funcional](docs/functional-specification.md)
- [Arquitetura](docs/architecture.md)
- [Referencia de API](docs/api-reference.md)
- [Padroes de codigo](docs/code-standards.md)
- [Processo de entrega](docs/delivery-process.md)
- [Guia de contribuicao](CONTRIBUTING.md)
- [Relatorio tecnico da versao 4.0](docs/reports/qa-report-v4.0.md)

## Principais capacidades

- API FastAPI em `/api/v1`
- Autenticacao JWT com RBAC para perfis MASTER, ADMIN e OPERADOR
- Cadastros de clientes, produtos, pragas, tecnicos, usuarios e empresas prestadoras
- Ordens de servico com regras de negocio, baixa de estoque e vinculo financeiro
- Recibos, fluxo financeiro, resumo de caixa e apoio fiscal/NF-e
- Agendamentos com sincronizacao Google Agenda
- Notificacoes e monitoramento de conexao WhatsApp
- Emissao de ordem de servico, relatorio tecnico e certificados sanitarios em PDF
- Certificado moldura baseado em `modelos/` com assinatura tecnica em `assinaturas_tecnicas/`
- Suite automatizada de testes com Pytest

## Estrutura principal

- `app/domain`: enums e conceitos centrais
- `app/application`: casos de uso, schemas e servicos de aplicacao
- `app/infrastructure`: banco, modelos e integracoes externas
- `app/interfaces`: rotas HTTP, templates e assets web
- `app/modules`: slices funcionais como WhatsApp e SEFAZ/NF-e
- `docs/`: documentacao e relatorios
- `tests/`: testes automatizados

## Como executar

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Interface web:

- `http://127.0.0.1:8000/app`
- `http://127.0.0.1:8000/docs`

## Credenciais iniciais

- Usuario: `admin`
- Senha: `syspragas123`

As credenciais podem ser alteradas via `DEFAULT_ADMIN_USERNAME` e `DEFAULT_ADMIN_PASSWORD`.

## Configuracao

Use `.env.example` e `.env.sefaz-homologacao.example` como base.

Pontos relevantes desta versao:

- `TECHNICAL_SIGNATURES_DIR=assinaturas_tecnicas`
- `CERTIFICATE_MODELS_DIR=modelos`
- `WHATSAPP_STATUS_API_URL=`
- `GOOGLE_CALENDAR_ENABLED=`
- configuracoes fiscais e SEFAZ conforme a documentacao em `docs/`

## Deploy local com Docker

```powershell
docker compose up --build
```

## Testes

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Observacao regulatoria

Os documentos operacionais e certificados seguem requisitos informacionais compativeis com a RDC 622/2022. O sistema fornece layout profissional e campos obrigatorios, sem alegar homologacao visual oficial da Anvisa.
