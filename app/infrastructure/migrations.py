from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Engine, inspect, text

LEGACY_WHATSAPP_TEMPLATE = '"Seu agendamento foi confirmado com sucesso."'
UPDATED_WHATSAPP_TEMPLATE = (
    '"Ola {nome_cliente}, tudo bem?\\n\\nSeu agendamento foi confirmado com sucesso!\\n\\n'
    'Data: {data}\\nHora: {hora}\\nTecnico: {tecnico}\\nServico: {servico}\\n\\n'
    'Qualquer duvida estamos a disposicao."'
)


MigrationFn = Callable[[Engine], None]


def _ensure_migration_table(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(40) PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def _get_applied_versions(engine: Engine) -> set[str]:
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def _mark_migration_applied(engine: Engine, version: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO schema_migrations (version) VALUES (:version)"),
            {"version": version},
        )


def _add_column_if_missing(engine: Engine, table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if table_name not in tables:
        return
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def _create_index_if_missing(engine: Engine, table_name: str, index_name: str, columns: list[str]) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if table_name not in tables:
        return
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name in existing_indexes:
        return
    column_list = ", ".join(columns)
    with engine.begin() as connection:
        connection.execute(text(f"CREATE INDEX {index_name} ON {table_name} ({column_list})"))


def _migration_20260321_001_legacy_backfill(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as connection:
            if "created_at" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                connection.execute(text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
            if "empresa_prestadora_id" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN empresa_prestadora_id INTEGER"))

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "empresas_prestadoras" in tables:
        company_columns = {column["name"] for column in inspector.get_columns("empresas_prestadoras")}
        statements = []
        if "created_at" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN created_at DATETIME")
        if "google_calendar_id" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_calendar_id VARCHAR(255)")
        if "google_account_email" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_account_email VARCHAR(255)")
        if "google_access_token" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_access_token TEXT")
        if "google_refresh_token" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_refresh_token TEXT")
        if "google_token_expires_at" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_token_expires_at DATETIME")
        if "google_connected_at" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN google_connected_at DATETIME")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            if "created_at" not in company_columns:
                connection.execute(text("UPDATE empresas_prestadoras SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))

    if "licenses" in tables:
        license_columns = {column["name"] for column in inspector.get_columns("licenses")}
        with engine.begin() as connection:
            if "empresa_prestadora_id" not in license_columns:
                connection.execute(text("ALTER TABLE licenses ADD COLUMN empresa_prestadora_id INTEGER"))

    if "clientes" in tables:
        customer_columns = {column["name"] for column in inspector.get_columns("clientes")}
        statements = []
        if "cep" not in customer_columns:
            statements.append("ALTER TABLE clientes ADD COLUMN cep VARCHAR(9)")
        if "numero" not in customer_columns:
            statements.append("ALTER TABLE clientes ADD COLUMN numero VARCHAR(20)")
        if "complemento" not in customer_columns:
            statements.append("ALTER TABLE clientes ADD COLUMN complemento VARCHAR(120)")
        if "bairro" not in customer_columns:
            statements.append("ALTER TABLE clientes ADD COLUMN bairro VARCHAR(120)")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    if "financeiro" in tables:
        finance_columns = {column["name"] for column in inspector.get_columns("financeiro")}
        statements = []
        if "valor_pago" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN valor_pago NUMERIC NOT NULL DEFAULT 0")
        if "data_pagamento" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN data_pagamento DATE")
        if "categoria" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN categoria VARCHAR(80)")
        if "fornecedor_nome" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN fornecedor_nome VARCHAR(150)")
        if "origem" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN origem VARCHAR(50) NOT NULL DEFAULT 'manual'")
        if "referencia" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN referencia VARCHAR(120)")
        if "parcela_atual" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN parcela_atual INTEGER NOT NULL DEFAULT 1")
        if "total_parcelas" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN total_parcelas INTEGER NOT NULL DEFAULT 1")
        if "observacoes" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN observacoes TEXT")
        if "created_at" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN created_at DATETIME")
        if "nfe_id" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN nfe_id INTEGER")
        if "recibo_id" not in finance_columns:
            statements.append("ALTER TABLE financeiro ADD COLUMN recibo_id INTEGER")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(text("UPDATE financeiro SET valor_pago = 0 WHERE valor_pago IS NULL"))
            connection.execute(text("UPDATE financeiro SET origem = CASE WHEN os_id IS NULL THEN 'manual' ELSE 'ordem_servico' END WHERE origem IS NULL"))
            connection.execute(text("UPDATE financeiro SET parcela_atual = 1 WHERE parcela_atual IS NULL"))
            connection.execute(text("UPDATE financeiro SET total_parcelas = 1 WHERE total_parcelas IS NULL"))
            connection.execute(text("UPDATE financeiro SET referencia = 'FIN-' || id WHERE referencia IS NULL"))
            connection.execute(text("UPDATE financeiro SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))

    if "produtos" in tables:
        product_columns = {column["name"] for column in inspector.get_columns("produtos")}
        statements = []
        if "ncm" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN ncm VARCHAR(8)")
        if "ncm_descricao" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN ncm_descricao VARCHAR(255)")
        if "aliquota_icms" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN aliquota_icms NUMERIC NOT NULL DEFAULT 0")
        if "aliquota_ipi" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN aliquota_ipi NUMERIC NOT NULL DEFAULT 0")
        if "aliquota_pis" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN aliquota_pis NUMERIC NOT NULL DEFAULT 0")
        if "aliquota_cofins" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN aliquota_cofins NUMERIC NOT NULL DEFAULT 0")
        if "override_tributacao" not in product_columns:
            statements.append("ALTER TABLE produtos ADD COLUMN override_tributacao BOOLEAN NOT NULL DEFAULT 0")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    if "notas_fiscais" in tables:
        nfe_columns = {column["name"] for column in inspector.get_columns("notas_fiscais")}
        statements = []
        if "referencia_externa" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN referencia_externa VARCHAR(80)")
        if "ambiente" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN ambiente VARCHAR(20)")
        if "provedor" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN provedor VARCHAR(40)")
        if "status_processamento" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN status_processamento VARCHAR(40) NOT NULL DEFAULT 'pendente_envio'")
        if "status_externo" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN status_externo VARCHAR(60)")
        if "mensagem_retorno" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN mensagem_retorno TEXT")
        if "chave_nfe" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN chave_nfe VARCHAR(60)")
        if "xml_url" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN xml_url VARCHAR(500)")
        if "pdf_url" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN pdf_url VARCHAR(500)")
        if "webhook_url" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN webhook_url VARCHAR(500)")
        if "payload_enviado" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN payload_enviado TEXT")
        if "resposta_externa" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN resposta_externa TEXT")
        if "xml_enviado" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN xml_enviado TEXT")
        if "xml_autorizado" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN xml_autorizado TEXT")
        if "protocolo_autorizacao" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN protocolo_autorizacao VARCHAR(40)")
        if "recibo_lote" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN recibo_lote VARCHAR(40)")
        if "lote_id" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN lote_id VARCHAR(20)")
        if "updated_at" not in nfe_columns:
            statements.append("ALTER TABLE notas_fiscais ADD COLUMN updated_at DATETIME")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(text("UPDATE notas_fiscais SET status_processamento = 'pendente_envio' WHERE status_processamento IS NULL"))
            connection.execute(text("UPDATE notas_fiscais SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))


def _migration_20260325_001_multitenancy_foundation(engine: Engine) -> None:
    tenant_targets = {
        "clientes": "empresa_prestadora_id INTEGER",
        "produtos": "empresa_prestadora_id INTEGER",
        "pragas": "empresa_prestadora_id INTEGER",
        "tecnicos": "empresa_prestadora_id INTEGER",
        "ordens_servico": "empresa_prestadora_id INTEGER",
        "agendamentos": "empresa_prestadora_id INTEGER",
        "financeiro": "empresa_prestadora_id INTEGER",
        "recibos": "empresa_prestadora_id INTEGER",
        "notas_fiscais": "empresa_prestadora_id INTEGER",
    }
    for table_name, ddl in tenant_targets.items():
        _add_column_if_missing(engine, table_name, "empresa_prestadora_id", ddl)

    with engine.begin() as connection:
        connection.execute(text("UPDATE clientes SET empresa_prestadora_id = (SELECT id FROM empresas_prestadoras ORDER BY id LIMIT 1) WHERE empresa_prestadora_id IS NULL"))
        connection.execute(text("UPDATE produtos SET empresa_prestadora_id = (SELECT id FROM empresas_prestadoras ORDER BY id LIMIT 1) WHERE empresa_prestadora_id IS NULL"))
        connection.execute(text("UPDATE pragas SET empresa_prestadora_id = (SELECT id FROM empresas_prestadoras ORDER BY id LIMIT 1) WHERE empresa_prestadora_id IS NULL"))
        connection.execute(text("UPDATE tecnicos SET empresa_prestadora_id = (SELECT id FROM empresas_prestadoras ORDER BY id LIMIT 1) WHERE empresa_prestadora_id IS NULL"))
        connection.execute(
            text(
                """
                UPDATE ordens_servico
                SET empresa_prestadora_id = (
                    SELECT clientes.empresa_prestadora_id
                    FROM clientes
                    WHERE clientes.id = ordens_servico.cliente_id
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE agendamentos
                SET empresa_prestadora_id = COALESCE(
                    (
                        SELECT ordens_servico.empresa_prestadora_id
                        FROM ordens_servico
                        WHERE ordens_servico.id = agendamentos.os_id
                    ),
                    (
                        SELECT clientes.empresa_prestadora_id
                        FROM clientes
                        WHERE clientes.id = agendamentos.cliente_id
                    )
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE recibos
                SET empresa_prestadora_id = COALESCE(
                    (
                        SELECT ordens_servico.empresa_prestadora_id
                        FROM ordens_servico
                        WHERE ordens_servico.id = recibos.os_id
                    ),
                    (
                        SELECT clientes.empresa_prestadora_id
                        FROM clientes
                        WHERE clientes.id = recibos.cliente_id
                    )
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE notas_fiscais
                SET empresa_prestadora_id = (
                    SELECT clientes.empresa_prestadora_id
                    FROM clientes
                    WHERE clientes.id = notas_fiscais.cliente_id
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE financeiro
                SET empresa_prestadora_id = COALESCE(
                    (
                        SELECT ordens_servico.empresa_prestadora_id
                        FROM ordens_servico
                        WHERE ordens_servico.id = financeiro.os_id
                    ),
                    (
                        SELECT clientes.empresa_prestadora_id
                        FROM clientes
                        WHERE clientes.id = financeiro.cliente_id
                    ),
                    (
                        SELECT notas_fiscais.empresa_prestadora_id
                        FROM notas_fiscais
                        WHERE notas_fiscais.id = financeiro.nfe_id
                    ),
                    (
                        SELECT recibos.empresa_prestadora_id
                        FROM recibos
                        WHERE recibos.id = financeiro.recibo_id
                    )
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )


def _migration_20260325_002_system_settings(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY,
                    key VARCHAR(80) NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by_user_id INTEGER
                )
                """
            )
        )


def _migration_20260325_003_whatsapp_template_refresh(engine: Engine) -> None:
    inspector = inspect(engine)
    if "system_settings" not in set(inspector.get_table_names()):
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE system_settings
                SET value = :new_value
                WHERE key = 'whatsapp_default_message'
                  AND value = :legacy_value
                """
            ),
            {"new_value": UPDATED_WHATSAPP_TEMPLATE, "legacy_value": LEGACY_WHATSAPP_TEMPLATE},
        )


def _migration_20260326_001_performance_indexes(engine: Engine) -> None:
    _create_index_if_missing(engine, "produtos", "ix_produtos_registro_ms", ["registro_ms"])
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_cliente_id", ["cliente_id"])
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_os_id", ["os_id"])
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_origem", ["origem"])
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_referencia", ["referencia"])
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_origem_referencia", ["origem", "referencia"])
    _create_index_if_missing(engine, "os_produtos", "ix_os_produtos_os_id", ["os_id"])
    _create_index_if_missing(engine, "os_produtos", "ix_os_produtos_produto_id", ["produto_id"])
    _create_index_if_missing(engine, "os_pragas", "ix_os_pragas_os_id", ["os_id"])
    _create_index_if_missing(engine, "os_pragas", "ix_os_pragas_praga_id", ["praga_id"])


def _migration_20260326_002_contracts_module(engine: Engine) -> None:
    _add_column_if_missing(engine, "clientes", "email", "email VARCHAR(150)")
    _create_index_if_missing(engine, "clientes", "ix_clientes_email", ["email"])

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS contratos (
                    id INTEGER PRIMARY KEY,
                    cliente_id INTEGER NOT NULL,
                    nome VARCHAR(180) NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_vencimento DATE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'ativo',
                    observacoes TEXT,
                    arquivo_nome_original VARCHAR(255),
                    arquivo_nome_armazenado VARCHAR(255) UNIQUE,
                    arquivo_content_type VARCHAR(120),
                    arquivo_tamanho INTEGER,
                    arquivo_caminho VARCHAR(500),
                    last_notification_status VARCHAR(20),
                    last_notification_sent_at DATETIME,
                    last_notification_error TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    empresa_prestadora_id INTEGER
                )
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE contratos
                SET empresa_prestadora_id = (
                    SELECT clientes.empresa_prestadora_id
                    FROM clientes
                    WHERE clientes.id = contratos.cliente_id
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )

    _create_index_if_missing(engine, "contratos", "ix_contratos_cliente_id", ["cliente_id"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_status", ["status"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_data_vencimento", ["data_vencimento"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_empresa_prestadora_id", ["empresa_prestadora_id"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_last_notification_status", ["last_notification_status"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_cliente_status", ["cliente_id", "status"])
    _create_index_if_missing(engine, "contratos", "ix_contratos_status_vencimento", ["status", "data_vencimento"])


MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("20260321_001_legacy_backfill", _migration_20260321_001_legacy_backfill),
    ("20260325_001_multitenancy_foundation", _migration_20260325_001_multitenancy_foundation),
    ("20260325_002_system_settings", _migration_20260325_002_system_settings),
    ("20260325_003_whatsapp_template_refresh", _migration_20260325_003_whatsapp_template_refresh),
    ("20260326_001_performance_indexes", _migration_20260326_001_performance_indexes),
    ("20260326_002_contracts_module", _migration_20260326_002_contracts_module),
]


def run_migrations(engine: Engine) -> None:
    _ensure_migration_table(engine)
    applied_versions = _get_applied_versions(engine)
    for version, migration in MIGRATIONS:
        if version in applied_versions:
            continue
        migration(engine)
        _mark_migration_applied(engine, version)
