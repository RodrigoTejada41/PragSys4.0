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


def _migration_20260326_003_contract_billing_reporting(engine: Engine) -> None:
    _add_column_if_missing(engine, "contratos", "valor_mensal", "valor_mensal NUMERIC NOT NULL DEFAULT 0")
    _add_column_if_missing(
        engine,
        "contratos",
        "tipo_cobranca",
        "tipo_cobranca VARCHAR(20) NOT NULL DEFAULT 'mensal'",
    )
    _add_column_if_missing(engine, "contratos", "dia_vencimento", "dia_vencimento INTEGER")
    _add_column_if_missing(
        engine,
        "contratos",
        "gerar_cobranca_automatica",
        "gerar_cobranca_automatica BOOLEAN NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(engine, "financeiro", "contrato_id", "contrato_id INTEGER")

    _create_index_if_missing(engine, "contratos", "ix_contratos_tipo_cobranca", ["tipo_cobranca"])
    _create_index_if_missing(
        engine,
        "contratos",
        "ix_contratos_gerar_cobranca_automatica",
        ["gerar_cobranca_automatica"],
    )
    _create_index_if_missing(
        engine,
        "contratos",
        "ix_contratos_cobranca_automatica_status",
        ["gerar_cobranca_automatica", "status"],
    )
    _create_index_if_missing(engine, "financeiro", "ix_financeiro_contrato_id", ["contrato_id"])


def _migration_20260326_004_work_order_contract_type(engine: Engine) -> None:
    _add_column_if_missing(
        engine,
        "ordens_servico",
        "tipo_os",
        "tipo_os VARCHAR(20) NOT NULL DEFAULT 'avulsa'",
    )
    _create_index_if_missing(engine, "ordens_servico", "ix_ordens_servico_tipo_os", ["tipo_os"])
    with engine.begin() as connection:
        connection.execute(text("UPDATE ordens_servico SET tipo_os = 'avulsa' WHERE tipo_os IS NULL OR tipo_os = ''"))


def _migration_20260327_001_backend_hardening(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS background_job_runs (
                    id INTEGER PRIMARY KEY,
                    task_name VARCHAR(80) NOT NULL,
                    run_date DATE NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_background_job_runs_task_date UNIQUE (task_name, run_date)
                )
                """
            )
        )
    _create_index_if_missing(engine, "background_job_runs", "ix_background_job_runs_task_name", ["task_name"])


def _migration_20260327_002_multiempresa_estoque(engine: Engine) -> None:
    _add_column_if_missing(
        engine,
        "empresas_prestadoras",
        "is_active",
        "is_active BOOLEAN NOT NULL DEFAULT 1",
    )
    _add_column_if_missing(
        engine,
        "empresas_prestadoras",
        "is_provider",
        "is_provider BOOLEAN NOT NULL DEFAULT 1",
    )
    _add_column_if_missing(
        engine,
        "empresas_prestadoras",
        "empresa_pai_id",
        "empresa_pai_id INTEGER",
    )
    _add_column_if_missing(
        engine,
        "empresas_prestadoras",
        "compartilha_visualizacao_estoque",
        "compartilha_visualizacao_estoque BOOLEAN NOT NULL DEFAULT 0",
    )
    _create_index_if_missing(engine, "empresas_prestadoras", "ix_empresas_prestadoras_is_active", ["is_active"])
    _create_index_if_missing(engine, "empresas_prestadoras", "ix_empresas_prestadoras_is_provider", ["is_provider"])
    _create_index_if_missing(engine, "empresas_prestadoras", "ix_empresas_prestadoras_empresa_pai_id", ["empresa_pai_id"])

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE users
                SET empresa_prestadora_id = (
                    SELECT id FROM empresas_prestadoras ORDER BY id LIMIT 1
                )
                WHERE empresa_prestadora_id IS NULL
                """
            )
        )
        connection.execute(text("UPDATE empresas_prestadoras SET is_active = 1 WHERE is_active IS NULL"))
        connection.execute(text("UPDATE empresas_prestadoras SET is_provider = 1 WHERE is_provider IS NULL"))
        connection.execute(
            text(
                "UPDATE empresas_prestadoras SET compartilha_visualizacao_estoque = 0 "
                "WHERE compartilha_visualizacao_estoque IS NULL"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
                    id INTEGER PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    empresa_prestadora_id INTEGER NOT NULL,
                    empresa_relacionada_id INTEGER,
                    usuario_id INTEGER,
                    tipo_movimento VARCHAR(30) NOT NULL,
                    origem VARCHAR(50) NOT NULL DEFAULT 'manual',
                    motivo VARCHAR(255) NOT NULL,
                    quantidade NUMERIC NOT NULL,
                    saldo_anterior NUMERIC NOT NULL DEFAULT 0,
                    saldo_posterior NUMERIC NOT NULL DEFAULT 0,
                    referencia VARCHAR(120),
                    observacoes TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    _create_index_if_missing(
        engine,
        "estoque_movimentacoes",
        "ix_estoque_movimentacoes_empresa_data",
        ["empresa_prestadora_id", "created_at"],
    )
    _create_index_if_missing(
        engine,
        "estoque_movimentacoes",
        "ix_estoque_movimentacoes_produto_data",
        ["produto_id", "created_at"],
    )
    _create_index_if_missing(
        engine,
        "estoque_movimentacoes",
        "ix_estoque_movimentacoes_tipo_empresa",
        ["tipo_movimento", "empresa_prestadora_id"],
    )
    _create_index_if_missing(engine, "estoque_movimentacoes", "ix_estoque_movimentacoes_referencia", ["referencia"])
    _create_index_if_missing(engine, "estoque_movimentacoes", "ix_estoque_movimentacoes_usuario_id", ["usuario_id"])


def _migration_20260327_003_user_permissions(engine: Engine) -> None:
    _add_column_if_missing(engine, "users", "permissions_json", "permissions_json TEXT")


def _migration_20260327_004_company_technical_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS dados_tecnicos_empresa (
                    id INTEGER PRIMARY KEY,
                    empresa_prestadora_id INTEGER NOT NULL,
                    legal_name VARCHAR(160) NOT NULL,
                    trade_name VARCHAR(160),
                    cnpj VARCHAR(20),
                    address VARCHAR(255) NOT NULL,
                    phone VARCHAR(30),
                    technical_responsible_name VARCHAR(160) NOT NULL,
                    technical_registry_type VARCHAR(40) NOT NULL DEFAULT 'CRBio',
                    technical_registry_number VARCHAR(60) NOT NULL DEFAULT '',
                    technical_registry_state VARCHAR(2) NOT NULL DEFAULT 'SP',
                    sanitary_license_number VARCHAR(80) NOT NULL,
                    sanitary_license_expiry VARCHAR(20),
                    environmental_license_number VARCHAR(80) NOT NULL,
                    environmental_license_expiry VARCHAR(20),
                    toxicology_center_name VARCHAR(160) NOT NULL DEFAULT 'Centro de Informacao Toxicologica',
                    toxicology_center_phone VARCHAR(40) NOT NULL,
                    sanitary_license_filename VARCHAR(255),
                    sanitary_license_content_type VARCHAR(120),
                    sanitary_license_data BLOB,
                    sanitary_license_uploaded_at DATETIME,
                    environmental_license_filename VARCHAR(255),
                    environmental_license_content_type VARCHAR(120),
                    environmental_license_data BLOB,
                    environmental_license_uploaded_at DATETIME,
                    signature_filename VARCHAR(255),
                    signature_content_type VARCHAR(120),
                    signature_data BLOB,
                    signature_uploaded_at DATETIME,
                    signature_source VARCHAR(20),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_dados_tecnicos_empresa_empresa UNIQUE (empresa_prestadora_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO dados_tecnicos_empresa (
                    empresa_prestadora_id,
                    legal_name,
                    trade_name,
                    cnpj,
                    address,
                    phone,
                    technical_responsible_name,
                    technical_registry_type,
                    technical_registry_number,
                    technical_registry_state,
                    sanitary_license_number,
                    sanitary_license_expiry,
                    environmental_license_number,
                    environmental_license_expiry,
                    toxicology_center_name,
                    toxicology_center_phone,
                    created_at,
                    updated_at
                )
                SELECT
                    company.id,
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'company_legal_name'),
                        json_quote(COALESCE(company.razao_social, 'Empresa nao configurada'))
                    ),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'company_trade_name'),
                        json_quote(COALESCE(company.nome_fantasia, company.razao_social, 'Empresa nao configurada'))
                    ),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'company_cnpj'),
                        json_quote(company.cnpj)
                    ),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'company_address'),
                        json_quote(COALESCE(company.endereco, 'Endereco nao configurado'))
                    ),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'company_phone'),
                        json_quote(company.telefone)
                    ),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'technical_responsible_name'),
                        json_quote('Responsavel tecnico nao configurado')
                    ),
                    CASE
                        WHEN COALESCE((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '""') LIKE '\"% %\"'
                            THEN substr(
                                trim(json_extract((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '$')),
                                1,
                                instr(trim(json_extract((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '$')), ' ') - 1
                            )
                        ELSE 'CRBio'
                    END,
                    CASE
                        WHEN COALESCE((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '""') LIKE '\"% %\"'
                            THEN substr(
                                trim(json_extract((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '$')),
                                instr(trim(json_extract((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '$')), ' ') + 1
                            )
                        ELSE COALESCE(
                            json_extract((SELECT value FROM system_settings WHERE key = 'technical_responsible_registry'), '$'),
                            ''
                        )
                    END,
                    'SP',
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'sanitary_license_number'),
                        json_quote('Licenca sanitaria nao configurada')
                    ),
                    COALESCE((SELECT value FROM system_settings WHERE key = 'sanitary_license_expiry'), json_quote(NULL)),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'environmental_license_number'),
                        json_quote('Licenca ambiental nao configurada')
                    ),
                    COALESCE((SELECT value FROM system_settings WHERE key = 'environmental_license_expiry'), json_quote(NULL)),
                    json_quote('Centro de Informacao Toxicologica'),
                    COALESCE(
                        (SELECT value FROM system_settings WHERE key = 'toxicology_center_phone'),
                        json_quote('0800 nao configurado')
                    ),
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                FROM empresas_prestadoras company
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dados_tecnicos_empresa existing
                    WHERE existing.empresa_prestadora_id = company.id
                )
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE dados_tecnicos_empresa
                SET
                    legal_name = json_extract(legal_name, '$'),
                    trade_name = json_extract(trade_name, '$'),
                    cnpj = json_extract(cnpj, '$'),
                    address = json_extract(address, '$'),
                    phone = json_extract(phone, '$'),
                    technical_responsible_name = json_extract(technical_responsible_name, '$'),
                    sanitary_license_number = json_extract(sanitary_license_number, '$'),
                    sanitary_license_expiry = json_extract(sanitary_license_expiry, '$'),
                    environmental_license_number = json_extract(environmental_license_number, '$'),
                    environmental_license_expiry = json_extract(environmental_license_expiry, '$'),
                    toxicology_center_name = json_extract(toxicology_center_name, '$'),
                    toxicology_center_phone = json_extract(toxicology_center_phone, '$')
                """
            )
        )
    _create_index_if_missing(
        engine,
        "dados_tecnicos_empresa",
        "ix_dados_tecnicos_empresa_empresa_prestadora_id",
        ["empresa_prestadora_id"],
    )


def _migration_20260327_005_cit_name(engine: Engine) -> None:
    _add_column_if_missing(
        engine,
        "dados_tecnicos_empresa",
        "toxicology_center_name",
        "toxicology_center_name VARCHAR(160) NOT NULL DEFAULT 'Centro de Informacao Toxicologica'",
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE dados_tecnicos_empresa
                SET toxicology_center_name = 'Centro de Informacao Toxicologica'
                WHERE toxicology_center_name IS NULL OR trim(toxicology_center_name) = ''
                """
            )
        )


def _migration_20260327_006_stock_module_expansion(engine: Engine) -> None:
    _add_column_if_missing(engine, "produtos", "categoria", "categoria VARCHAR(80)")
    _add_column_if_missing(engine, "produtos", "unidade_medida", "unidade_medida VARCHAR(10) NOT NULL DEFAULT 'UN'")
    _add_column_if_missing(engine, "estoque_movimentacoes", "unidade_medida", "unidade_medida VARCHAR(10) NOT NULL DEFAULT 'UN'")
    _create_index_if_missing(engine, "produtos", "ix_produtos_categoria", ["categoria"])

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE produtos
                SET unidade_medida = 'UN'
                WHERE unidade_medida IS NULL OR trim(unidade_medida) = ''
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE estoque_movimentacoes
                SET unidade_medida = 'UN'
                WHERE unidade_medida IS NULL OR trim(unidade_medida) = ''
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_importacoes (
                    id INTEGER PRIMARY KEY,
                    empresa_prestadora_id INTEGER NOT NULL,
                    usuario_id INTEGER,
                    tipo_arquivo VARCHAR(20) NOT NULL,
                    origem VARCHAR(30) NOT NULL,
                    referencia VARCHAR(120) NOT NULL,
                    nome_arquivo VARCHAR(255),
                    produtos_processados INTEGER NOT NULL DEFAULT 0,
                    produtos_criados INTEGER NOT NULL DEFAULT 0,
                    produtos_atualizados INTEGER NOT NULL DEFAULT 0,
                    total_movimentado NUMERIC NOT NULL DEFAULT 0,
                    errors_json TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    _create_index_if_missing(engine, "estoque_importacoes", "ix_estoque_importacoes_empresa_data", ["empresa_prestadora_id", "created_at"])


def _migration_20260327_007_stock_traceability(engine: Engine) -> None:
    _add_column_if_missing(engine, "produtos", "codigo_barras", "codigo_barras VARCHAR(80)")
    _add_column_if_missing(engine, "produtos", "qr_code_value", "qr_code_value VARCHAR(120)")
    _create_index_if_missing(engine, "produtos", "ix_produtos_codigo_barras", ["codigo_barras"])
    _create_index_if_missing(engine, "produtos", "ix_produtos_qr_code_value", ["qr_code_value"])

    _add_column_if_missing(engine, "estoque_movimentacoes", "armazem_id", "armazem_id INTEGER")
    _add_column_if_missing(engine, "estoque_movimentacoes", "local_id", "local_id INTEGER")
    _add_column_if_missing(engine, "estoque_movimentacoes", "armazem_relacionado_id", "armazem_relacionado_id INTEGER")
    _add_column_if_missing(engine, "estoque_movimentacoes", "local_relacionado_id", "local_relacionado_id INTEGER")
    _add_column_if_missing(engine, "estoque_movimentacoes", "codigo_lido", "codigo_lido VARCHAR(120)")
    _create_index_if_missing(engine, "estoque_movimentacoes", "ix_estoque_movimentacoes_armazem_id", ["armazem_id"])
    _create_index_if_missing(engine, "estoque_movimentacoes", "ix_estoque_movimentacoes_local_id", ["local_id"])
    _create_index_if_missing(engine, "estoque_movimentacoes", "ix_estoque_movimentacoes_codigo_lido", ["codigo_lido"])

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_armazens (
                    id INTEGER PRIMARY KEY,
                    empresa_prestadora_id INTEGER NOT NULL,
                    nome VARCHAR(120) NOT NULL,
                    codigo VARCHAR(40) NOT NULL,
                    descricao TEXT,
                    tipo VARCHAR(30) NOT NULL DEFAULT 'armazem',
                    ativo BOOLEAN NOT NULL DEFAULT 1,
                    padrao BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_estoque_armazens_empresa_codigo UNIQUE (empresa_prestadora_id, codigo)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_locais (
                    id INTEGER PRIMARY KEY,
                    empresa_prestadora_id INTEGER NOT NULL,
                    armazem_id INTEGER NOT NULL,
                    nome VARCHAR(120) NOT NULL,
                    codigo VARCHAR(40) NOT NULL,
                    descricao TEXT,
                    ativo BOOLEAN NOT NULL DEFAULT 1,
                    padrao BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_estoque_locais_armazem_codigo UNIQUE (armazem_id, codigo)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_saldos (
                    id INTEGER PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    empresa_prestadora_id INTEGER NOT NULL,
                    armazem_id INTEGER NOT NULL,
                    local_id INTEGER NOT NULL,
                    quantidade_atual NUMERIC NOT NULL DEFAULT 0,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_estoque_saldos_produto_local UNIQUE (produto_id, armazem_id, local_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_inventarios (
                    id INTEGER PRIMARY KEY,
                    empresa_prestadora_id INTEGER NOT NULL,
                    armazem_id INTEGER NOT NULL,
                    local_id INTEGER NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'aberto',
                    observacoes TEXT,
                    created_by_user_id INTEGER,
                    finished_by_user_id INTEGER,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS estoque_inventario_itens (
                    id INTEGER PRIMARY KEY,
                    inventario_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade_sistema NUMERIC NOT NULL DEFAULT 0,
                    quantidade_contada NUMERIC NOT NULL DEFAULT 0,
                    divergencia NUMERIC NOT NULL DEFAULT 0,
                    ultimo_codigo_lido VARCHAR(120),
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_estoque_inventario_item_produto UNIQUE (inventario_id, produto_id)
                )
                """
            )
        )

        connection.execute(
            text(
                """
                INSERT INTO estoque_armazens (empresa_prestadora_id, nome, codigo, descricao, tipo, ativo, padrao, created_at)
                SELECT company.id, 'Armazem principal', 'MAIN', 'Estrutura padrao criada automaticamente.', 'armazem', 1, 1, CURRENT_TIMESTAMP
                FROM empresas_prestadoras company
                WHERE NOT EXISTS (
                    SELECT 1 FROM estoque_armazens warehouse WHERE warehouse.empresa_prestadora_id = company.id
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO estoque_locais (empresa_prestadora_id, armazem_id, nome, codigo, descricao, ativo, padrao, created_at)
                SELECT warehouse.empresa_prestadora_id, warehouse.id, 'Geral', 'GERAL', 'Local padrao criado automaticamente.', 1, 1, CURRENT_TIMESTAMP
                FROM estoque_armazens warehouse
                WHERE warehouse.padrao = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM estoque_locais location WHERE location.armazem_id = warehouse.id
                  )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO estoque_saldos (produto_id, empresa_prestadora_id, armazem_id, local_id, quantidade_atual, updated_at)
                SELECT
                    product.id,
                    product.empresa_prestadora_id,
                    warehouse.id,
                    location.id,
                    COALESCE(product.estoque_atual, 0),
                    CURRENT_TIMESTAMP
                FROM produtos product
                JOIN estoque_armazens warehouse
                  ON warehouse.empresa_prestadora_id = product.empresa_prestadora_id
                 AND warehouse.padrao = 1
                JOIN estoque_locais location
                  ON location.armazem_id = warehouse.id
                 AND location.padrao = 1
                WHERE product.empresa_prestadora_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM estoque_saldos balance
                      WHERE balance.produto_id = product.id
                  )
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE produtos
                SET qr_code_value = 'PRD-' || COALESCE(empresa_prestadora_id, 0) || '-' || id
                WHERE qr_code_value IS NULL OR trim(qr_code_value) = ''
                """
            )
        )

    _create_index_if_missing(engine, "estoque_armazens", "ix_estoque_armazens_empresa_nome", ["empresa_prestadora_id", "nome"])
    _create_index_if_missing(engine, "estoque_locais", "ix_estoque_locais_empresa_nome", ["empresa_prestadora_id", "nome"])
    _create_index_if_missing(engine, "estoque_saldos", "ix_estoque_saldos_empresa_produto", ["empresa_prestadora_id", "produto_id"])
    _create_index_if_missing(engine, "estoque_inventarios", "ix_estoque_inventarios_empresa_status", ["empresa_prestadora_id", "status"])
    _create_index_if_missing(engine, "estoque_inventario_itens", "ix_estoque_inventario_itens_produto", ["produto_id"])


MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("20260321_001_legacy_backfill", _migration_20260321_001_legacy_backfill),
    ("20260325_001_multitenancy_foundation", _migration_20260325_001_multitenancy_foundation),
    ("20260325_002_system_settings", _migration_20260325_002_system_settings),
    ("20260325_003_whatsapp_template_refresh", _migration_20260325_003_whatsapp_template_refresh),
    ("20260326_001_performance_indexes", _migration_20260326_001_performance_indexes),
    ("20260326_002_contracts_module", _migration_20260326_002_contracts_module),
    ("20260326_003_contract_billing_reporting", _migration_20260326_003_contract_billing_reporting),
    ("20260326_004_work_order_contract_type", _migration_20260326_004_work_order_contract_type),
    ("20260327_001_backend_hardening", _migration_20260327_001_backend_hardening),
    ("20260327_002_multiempresa_estoque", _migration_20260327_002_multiempresa_estoque),
    ("20260327_003_user_permissions", _migration_20260327_003_user_permissions),
    ("20260327_004_company_technical_data", _migration_20260327_004_company_technical_data),
    ("20260327_005_cit_name", _migration_20260327_005_cit_name),
    ("20260327_006_stock_module_expansion", _migration_20260327_006_stock_module_expansion),
    ("20260327_007_stock_traceability", _migration_20260327_007_stock_traceability),
]


def run_migrations(engine: Engine) -> None:
    _ensure_migration_table(engine)
    applied_versions = _get_applied_versions(engine)
    for version, migration in MIGRATIONS:
        if version in applied_versions:
            continue
        migration(engine)
        _mark_migration_applied(engine, version)
