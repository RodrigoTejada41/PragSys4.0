# SysPragas 4.1.0

Sistema operacional para empresas de controle de pragas, remodelado para operar como aplicacao web local ou em rede interna, com base arquitetural para multempresa e sem dependencia obrigatoria de container.

## Estado atual da release

- Versao formal: `4.1.0`
- Stack principal: FastAPI, SQLAlchemy, Pydantic, Jinja2 e frontend web proprio
- Execucao principal recomendada: instalacao local direta na maquina ou servidor interno
- Docker: mantido como opcao de suporte, nao como requisito principal

## Objetivos da fase 4.1.0

- profissionalizar a arquitetura para manutencao de longo prazo;
- padronizar bootstrap, logs, configuracao e versionamento;
- preparar a fundacao de multempresa por `empresa_prestadora_id`;
- separar melhor runtime local, runtime em rede e gerenciamento de banco;
- consolidar documentacao tecnica, operacional e de release.
- reduzir drasticamente o tempo da suite automatizada com infraestrutura de teste mais leve e previsivel.

## Estrutura principal

- `app/core`: configuracao, seguranca, excecoes e logging
- `app/domain`: enums e regras centrais
- `app/application`: schemas, servicos e casos de uso
- `app/infrastructure`: banco, modelos e migracoes rastreaveis
- `app/interfaces`: rotas HTTP, templates e assets web
- `app/modules`: modulos especializados como SEFAZ NF-e e WhatsApp
- `docs`: documentacao tecnica, operacional e arquitetural
- `scripts`: automacao de execucao local, rede, banco e empacotamento
- `release`: registros de release sem sobrescrever versoes anteriores

## Como executar localmente

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\scripts\run_local.ps1
```

Acesse:

- `http://127.0.0.1:8000/app`
- `http://127.0.0.1:8000/docs`

## Como executar em rede interna

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\scripts\run_network.ps1 -HostAddress 0.0.0.0 -Port 8000
```

Acesse de outra maquina da rede:

- `http://IP_DO_SERVIDOR:8000/app`

## Como inicializar ou atualizar o banco

```powershell
.venv\Scripts\python.exe scripts\manage_db.py init
.venv\Scripts\python.exe scripts\manage_db.py status
```

## Credenciais iniciais

- Usuario: `admin`
- Senha: `syspragas123`

## Documentacao obrigatoria da release

- [Mapa da documentacao](docs/README.md)
- [Organograma do estado atual](docs/organograma-estado-atual-projeto.md)
- [Manual completo de instalacao](docs/manual-instalacao-completo.md)
- [Arquitetura alvo 4.0.0](docs/architecture-v4.0.0.md)
- [Relatorio de performance da suite](docs/performance-test-suite-report-2026-03-26.md)
- [Instalacao local](docs/installation-local.md)
- [Execucao em rede](docs/installation-network.md)
- [Arquitetura multempresa](docs/multitenancy-architecture.md)
- [Bridge QR do WhatsApp](docs/whatsapp-qr-bridge.md)
- [Publicacao no GitHub](docs/github-publishing.md)
- [Relatorio tecnico da release](docs/technical-report-4.0.0.md)

## Docker

O projeto continua com `Dockerfile` e `docker-compose.yml`, mas a release 4.1.0 mantem que o modo principal de operacao e instalacao direta. Container passa a ser opcional para homologacao, empacotamento ou infraestrutura futura.

## WhatsApp com QR Code

O projeto agora inclui um bridge opcional com `Baileys` para autenticacao via QR Code e envio de mensagens sem dependencia obrigatoria de API paga.

Execucao local:

```powershell
.\scripts\run_whatsapp_bridge.ps1
```

Execucao via Docker:

```powershell
docker compose --profile whatsapp-bridge up --build -d
```

## Testes

```powershell
.venv\Scripts\python.exe -m pytest -q
```
