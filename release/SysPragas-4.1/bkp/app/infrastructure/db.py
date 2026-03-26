from datetime import date, timedelta
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.infrastructure.migrations import run_migrations


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
    from app.application.settings_service import ensure_system_settings_seed
    from app.infrastructure.models import License, NcmTaxProfile, ProviderCompany, SimplesNationalConfig, User

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)

    settings = get_settings()
    session = get_session_local()()
    try:
        existing = (
            session.query(User)
            .filter(User.username == settings.default_admin_username)
            .first()
        )
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

        if not existing:
            admin = User(
                nome=settings.default_admin_name,
                username=settings.default_admin_username,
                password_hash=get_password_hash(settings.default_admin_password),
                role="master",
                is_active=True,
                empresa_prestadora_id=default_company.id,
            )
            session.add(admin)
        elif not session.query(User).filter(User.role == "master").first():
            existing.role = "master"
            existing.is_active = True

        existing_license = session.query(License).order_by(License.id.desc()).first()
        if not existing_license:
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

        if session.query(NcmTaxProfile).count() == 0:
            session.add_all(
                [
                    NcmTaxProfile(
                        codigo="38089199",
                        descricao="Inseticidas e produtos similares para controle de pragas urbanas",
                        aliquota_icms=18,
                        aliquota_ipi=0,
                        aliquota_pis=1.65,
                        aliquota_cofins=7.60,
                        fonte_dados="seed_local",
                    ),
                    NcmTaxProfile(
                        codigo="38089299",
                        descricao="Fungicidas e desinfetantes de uso profissional",
                        aliquota_icms=18,
                        aliquota_ipi=0,
                        aliquota_pis=1.65,
                        aliquota_cofins=7.60,
                        fonte_dados="seed_local",
                    ),
                    NcmTaxProfile(
                        codigo="38089329",
                        descricao="Herbicidas e reguladores em formulacoes especiais",
                        aliquota_icms=18,
                        aliquota_ipi=0,
                        aliquota_pis=1.65,
                        aliquota_cofins=7.60,
                        fonte_dados="seed_local",
                    ),
                    NcmTaxProfile(
                        codigo="34029039",
                        descricao="Detergentes e produtos auxiliares de higienizacao profissional",
                        aliquota_icms=18,
                        aliquota_ipi=5,
                        aliquota_pis=1.65,
                        aliquota_cofins=7.60,
                        fonte_dados="seed_local",
                    ),
                    NcmTaxProfile(
                        codigo="39269090",
                        descricao="Acessorios, armadilhas e componentes tecnicos diversos",
                        aliquota_icms=18,
                        aliquota_ipi=0,
                        aliquota_pis=1.65,
                        aliquota_cofins=7.60,
                        fonte_dados="seed_local",
                    ),
                ]
            )

        if not session.query(SimplesNationalConfig).filter(SimplesNationalConfig.vigente.is_(True)).first():
            session.add(
                SimplesNationalConfig(
                    faixa_faturamento_inicio=0,
                    faixa_faturamento_fim=None,
                    aliquota=settings.simples_nacional_default_aliquota,
                    anexo=settings.simples_nacional_default_anexo,
                    vigente=True,
                    observacoes="Configuracao inicial criada automaticamente pelo sistema.",
                )
            )

        session.commit()
        ensure_system_settings_seed(session)
    finally:
        session.close()
