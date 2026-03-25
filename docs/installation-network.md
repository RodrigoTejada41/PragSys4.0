# Execucao Em Rede

## Objetivo

Disponibilizar o SysPragas para outras maquinas da rede interna, sem dependencia obrigatoria de container.

## Topologia recomendada

- um servidor interno com o projeto instalado;
- banco local do servidor ou banco externo dedicado;
- acesso via navegador dos clientes da rede.

## Subida do servico

```powershell
Copy-Item .env.example .env
.venv\Scripts\python.exe scripts\manage_db.py init
.\scripts\run_network.ps1 -HostAddress 0.0.0.0 -Port 8000
```

## Acesso

- `http://IP_DO_SERVIDOR:8000/app`

## Cuidados operacionais

- liberar a porta configurada no firewall;
- proteger a maquina servidora com usuario administrativo restrito;
- usar senha forte e `JWT_SECRET` exclusivo;
- considerar Postgres para rede com mais usuarios ou mais volume.
