# Checklist de Deploy e Validacao 4.1.0

## Antes do deploy

- confirmar branch e commit de release corretos;
- validar que `.env` de destino esta completo e sem segredos faltando;
- verificar paths de `TECHNICAL_SIGNATURES_DIR` e `CERTIFICATE_MODELS_DIR`;
- verificar configuracoes fiscais e de integracao Google/WhatsApp;
- garantir backup do banco antes da atualizacao.

## Atualizacao

- atualizar codigo da release desejada;
- instalar dependencias com:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

- iniciar a aplicacao e permitir o bootstrap/migracoes:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app
```

## Verificacoes tecnicas

- abrir `/health` e confirmar `status=ok`;
- abrir `/app` e confirmar carregamento do frontend;
- autenticar com usuario administrativo;
- verificar acesso a clientes, produtos, financeiro e OS;
- emitir uma OS de teste;
- abrir PDF da OS, relatorio tecnico e certificados;
- verificar configuracoes em `/api/v1/settings`;
- validar status das integracoes Google e WhatsApp;
- se houver NF-e direta, validar readiness da SEFAZ.

## Verificacoes de banco

- confirmar que a tabela `schema_migrations` recebeu `20260326_001_performance_indexes`;
- validar que o banco abre normalmente apos restart;
- se possivel, inspecionar a existencia dos indices novos em ambiente homologado.

## Validacao automatizada

Executar no minimo:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Execucoes seletivas uteis:

```powershell
.venv\Scripts\python.exe -m pytest -q -m unit
.venv\Scripts\python.exe -m pytest -q -m documents
.venv\Scripts\python.exe -m pytest -q -m integration
```

## Pos-deploy

- monitorar logs de startup e erros de documento/PDF;
- validar uso basico com um usuario operador;
- registrar horario, commit e responsavel pela publicacao;
- manter rollback preparado com backup de banco e release anterior.
