# Instalacao Local

## Objetivo

Executar o SysPragas diretamente na maquina, sem depender de Docker.

## Requisitos

- Python 3.9 ou superior
- ambiente virtual `.venv`
- acesso ao diretorio do projeto

## Passos

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.venv\Scripts\python.exe scripts\manage_db.py init
.\scripts\run_local.ps1
```

## Enderecos

- Aplicacao: `http://127.0.0.1:8000/app`
- API docs: `http://127.0.0.1:8000/docs`

## Observacoes

- para ambiente offline, mantenha banco e assets locais;
- para instalacao de escritorio unico, SQLite e suficiente;
- certificados e segredos devem ficar fora do Git e configurados por `.env`.
