from datetime import date, timedelta
from typing import Generator, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.security import get_password_hash


class Base(DeclarativeBase):
    pass


_engine = None
_session_local: Optional[sessionmaker] = None
_engine_url: Optional[str] = None


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def get_engine():
    global _engine, _session_local, _engine_url
    settings = get_settings()
    if _engine is None or _engine_url != settings.database_url:
        _engine = create_engine(
            settings.database_url,
            connect_args=_connect_args(settings.database_url),
            future=True,
        )
        _session_local = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
        _engine_url = settings.database_url
    return _engine


def get_session_local() -> sessionmaker:
    get_engine()
    assert _session_local is not None
    return _session_local


def reset_engine() -> None:
    global _engine, _session_local, _engine_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_local = None
    _engine_url = None


def get_db() -> Generator[Session, None, None]:
    session = get_session_local()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app.infrastructure.models import License, ProviderCompany, User

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations(engine)

    settings = get_settings()
    session = get_session_local()()
    try:
        existing = (
            session.query(User)
            .filter(User.username == settings.default_admin_username)
            .first()
        )
        if not existing:
            admin = User(
                nome=settings.default_admin_name,
                username=settings.default_admin_username,
                password_hash=get_password_hash(settings.default_admin_password),
                role="master",
                is_active=True,
            )
            session.add(admin)
        elif not session.query(User).filter(User.role == "master").first():
            existing.role = "master"
            existing.is_active = True

        existing_license = session.query(License).order_by(License.id.desc()).first()
        if not existing_license:
            default_company = session.query(ProviderCompany).filter(ProviderCompany.cnpj == "00000000000000").first()
            if not default_company:
                default_company = ProviderCompany(
                    razao_social="Prestadora padrao SysPragas",
                    nome_fantasia="SysPragas",
                    cnpj="00000000000000",
                    email="contato@syspragas.local",
                    telefone="0000000000",
                    cidade="Sao Paulo",
                    estado="SP",
                )
                session.add(default_company)
                session.flush()
            license_entry = License(
                descricao="Licenca inicial SysPragas",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                max_users=10,
                status="ativa",
                notes="Licenca inicial criada automaticamente pelo sistema.",
                empresa_prestadora_id=default_company.id,
            )
            session.add(license_entry)

        session.commit()
    finally:
        session.close()


def _apply_lightweight_migrations(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as connection:
            if "created_at" not in user_columns:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN created_at DATETIME")
                )
                connection.execute(
                    text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                )
            if "empresa_prestadora_id" not in user_columns:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN empresa_prestadora_id INTEGER")
                )

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "empresas_prestadoras" in tables:
        company_columns = {column["name"] for column in inspector.get_columns("empresas_prestadoras")}
        statements = []
        if "created_at" not in company_columns:
            statements.append("ALTER TABLE empresas_prestadoras ADD COLUMN created_at DATETIME")
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            if "created_at" not in company_columns:
                connection.execute(text("UPDATE empresas_prestadoras SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "licenses" in tables:
        license_columns = {column["name"] for column in inspector.get_columns("licenses")}
        with engine.begin() as connection:
            if "empresa_prestadora_id" not in license_columns:
                connection.execute(
                    text("ALTER TABLE licenses ADD COLUMN empresa_prestadora_id INTEGER")
                )

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

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

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

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

        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(text("UPDATE financeiro SET valor_pago = 0 WHERE valor_pago IS NULL"))
            connection.execute(text("UPDATE financeiro SET origem = CASE WHEN os_id IS NULL THEN 'manual' ELSE 'ordem_servico' END WHERE origem IS NULL"))
            connection.execute(text("UPDATE financeiro SET parcela_atual = 1 WHERE parcela_atual IS NULL"))
            connection.execute(text("UPDATE financeiro SET total_parcelas = 1 WHERE total_parcelas IS NULL"))
            connection.execute(text("UPDATE financeiro SET referencia = 'FIN-' || id WHERE referencia IS NULL"))
            connection.execute(text("UPDATE financeiro SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
