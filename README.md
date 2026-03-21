# SysPragas

MVP funcional inspirado nos dois documentos fornecidos para gestao de empresas de controle de pragas.

## O que foi implementado

- API FastAPI em `/api/v1`
- Autenticacao JWT com usuario administrador inicial
- Controle de acesso RBAC com perfis MASTER, ADMIN e OPERADOR
- Cadastros de clientes, produtos, pragas e tecnicos
- Ordens de servico com regras de negocio
- Baixa automatica de estoque por produto utilizado
- Lancamento financeiro automatico ao gerar OS com valor
- Emissao de ordem de servico em PDF
- Emissao de relatorio tecnico em PDF
- Emissao de certificado sanitario em PDF
- Emissao de certificado sanitario para moldura com logo configuravel
- Testes automatizados com Pytest

## Arquitetura

Estrutura baseada em:

- `app/domain`: enums e regras centrais
- `app/application`: schemas e casos de uso
- `app/infrastructure`: banco e modelos SQLAlchemy
- `app/interfaces`: rotas HTTP

## Como executar

```powershell
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Interface web:

- `http://127.0.0.1:8000/app`
- `http://127.0.0.1:8000/docs`

## O que a interface web faz

- login e sessao
- dashboard com busca e filtros
- gestao de usuarios e licencas para perfil MASTER
- cadastro, edicao e exclusao de clientes
- cadastro, edicao e exclusao de produtos
- cadastro, edicao e exclusao de pragas
- cadastro, edicao e exclusao de tecnicos
- criacao, edicao e exclusao de ordens de servico
- criacao, edicao e exclusao de lancamentos financeiros manuais
- emissao de ordem de servico PDF
- emissao de relatorio tecnico
- emissao de certificado sanitario
- emissao de certificado moldura

## Credenciais iniciais

- Usuario: `admin`
- Senha: `syspragas123`

Perfil inicial criado automaticamente: `MASTER`

Voce pode alterar isso com as variaveis `DEFAULT_ADMIN_USERNAME` e `DEFAULT_ADMIN_PASSWORD`.

## Endpoints principais

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET/POST /api/v1/clientes`
- `GET/POST /api/v1/produtos`
- `GET/POST /api/v1/pragas`
- `GET/POST /api/v1/tecnicos`
- `GET/POST /api/v1/financeiro`
- `GET/POST /api/v1/os`
- `GET/POST /api/v1/usuarios`
- `GET/POST /api/v1/licencas`
- `GET /api/v1/os/{id}/pdf`
- `GET /api/v1/os/{id}/relatorio-tecnico.pdf`
- `GET /api/v1/os/{id}/certificado-sanitario.pdf`
- `GET /api/v1/os/{id}/certificado-moldura.pdf`

## Variaveis opcionais

```env
DATABASE_URL=sqlite:///./syspragas.db
JWT_SECRET=<SECRET>
ACCESS_TOKEN_EXPIRE_MINUTES=480
COMPANY_NAME=Minha Empresa
COMPANY_LOGO_PATH=C:/caminho/logo.png
COMPANY_LEGAL_NAME=Minha Empresa Controle de Pragas Ltda
COMPANY_TRADE_NAME=Minha Marca
COMPANY_ADDRESS=Rua Exemplo, 100 - Sao Paulo/SP
COMPANY_PHONE=(11) 0000-0000
SANITARY_LICENSE_NUMBER=12345
SANITARY_LICENSE_EXPIRY=31/12/2026
ENVIRONMENTAL_LICENSE_NUMBER=67890
ENVIRONMENTAL_LICENSE_EXPIRY=31/12/2026
TOXICOLOGY_CENTER_PHONE=0800-722-6001
TECHNICAL_RESPONSIBLE_NAME=Nome do RT
TECHNICAL_RESPONSIBLE_REGISTRY=CRQ/CRBio/Outro 12345
```

## Observacao regulatoria

Os modelos de comprovante, relatorio e certificados foram ajustados com base na [RDC 622/2022](https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-622-de-9-de-marco-de-2022-386107395), que entrou em vigor em **1 de abril de 2022** e revogou a RDC 52/2009.

Ponto importante:

- a Anvisa define informacoes minimas obrigatorias para o comprovante de execucao do servico
- ela nao fornece um layout oficial unico de "certificado bonito"
- por isso o sistema gera documentos em formato compativel, mas sem usar frases proibidas como "aprovado pela Anvisa"

## Deploy local com Docker

```powershell
docker compose up --build
```

Depois acesse:

- `http://127.0.0.1:8000/app`
- `http://127.0.0.1:8000/docs`

## Deploy online

O projeto agora inclui:

- [Dockerfile](E:/Projetos/Controle_de_pragas1.1/Dockerfile) para qualquer plataforma que aceite container
- [docker-compose.yml](E:/Projetos/Controle_de_pragas1.1/docker-compose.yml) para subir localmente
- [render.yaml](E:/Projetos/Controle_de_pragas1.1/render.yaml) para deploy rapido no Render

Se quiser publicar online, basta usar uma plataforma com suporte a Docker e apontar para este projeto.

## Testes

```powershell
.venv\Scripts\python -m pytest
```
