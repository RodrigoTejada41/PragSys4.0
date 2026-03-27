# Modulo de Banco de Dados

## Objetivo

O painel de banco de dados entrega tres operacoes administrativas seguras para ambientes locais e offline:

- backup manual do banco SQLite;
- restauracao assistida com backup de seguranca;
- limpeza de movimentacoes operacionais sem apagar cadastros mestres.

## Escopo atual

- engine suportado: `sqlite`;
- formato de exportacao e restauracao: `.db`, `.sqlite` ou `.sqlite3`;
- acesso restrito a perfis `master` e `admin`.

## Fluxos disponiveis

### Backup

- endpoint: `GET /api/v1/settings/database/backup`;
- nome automatico: `backup_YYYYMMDD_HHMMSS.db`;
- a API gera um arquivo consistente via `sqlite3.backup`;
- no frontend, navegadores compativeis com File System Access API podem salvar direto na pasta escolhida;
- quando esse recurso nao estiver disponivel, o arquivo e baixado pelo navegador normalmente.

### Restauracao

- endpoint: `POST /api/v1/settings/database/restore`;
- payload: `multipart/form-data` com `file` e `confirmation = RESTAURAR`;
- o arquivo e validado antes da troca;
- antes da restauracao, o sistema cria um backup de seguranca em `database.backup_dir`;
- a substituicao do banco so acontece depois que o arquivo restaurado passa em validacao local.

### Limpeza operacional

- endpoint: `POST /api/v1/settings/database/cleanup`;
- payload: `confirmation = CONFIRMAR` e `include_finance`;
- sempre remove:
  - agendamentos;
  - historico de agendamentos;
  - logs de WhatsApp dos agendamentos;
  - ordens de servico;
  - itens, pragas e fotos vinculadas a OS;
  - estado de notificacao dos contratos.
- quando `include_finance = true`, remove tambem:
  - financeiro;
  - fluxo de caixa;
  - recibos e historico;
  - NF-e.
- quando `include_finance = false`, o financeiro e preservado e os vinculos com OS sao destacados para evitar referencia quebrada.

## Seguranca e integridade

- nenhuma restauracao ocorre sem confirmacao explicita;
- nenhum dado atual e sobrescrito sem gerar backup de seguranca antes;
- arquivos enviados sao restritos a backups SQLite validos;
- falhas durante a restauracao nao substituem o banco atual;
- operacoes relevantes sao registradas em log de aplicacao.

## Validacao executada

- exportacao de backup com retorno SQLite valido;
- restauracao com retorno ao estado anterior e criacao de backup de seguranca;
- limpeza operacional preservando clientes e destacando financeiro quando a opcao financeira estiver desabilitada.
