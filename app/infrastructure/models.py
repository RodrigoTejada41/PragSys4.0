from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, LargeBinary, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProviderCompany(Base):
    __tablename__ = "empresas_prestadoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    cep: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_provider: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    empresa_pai_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )
    compartilha_visualizacao_estoque: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_account_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    google_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    empresa_pai: Mapped[Optional["ProviderCompany"]] = relationship(
        remote_side=[id],
        back_populates="filiais",
        foreign_keys=[empresa_pai_id],
    )
    filiais: Mapped[List["ProviderCompany"]] = relationship(
        back_populates="empresa_pai",
        foreign_keys=[empresa_pai_id],
    )
    usuarios: Mapped[List["User"]] = relationship(back_populates="empresa_prestadora")
    licencas: Mapped[List["License"]] = relationship(back_populates="empresa_prestadora")
    estoque_movimentacoes: Mapped[List["StockMovement"]] = relationship(
        back_populates="empresa_prestadora",
        foreign_keys="StockMovement.empresa_prestadora_id",
    )
    dados_tecnicos: Mapped[Optional["CompanyTechnicalData"]] = relationship(
        back_populates="empresa_prestadora",
        uselist=False,
        cascade="all, delete-orphan",
    )
    certificado_digital: Mapped[Optional["DigitalCertificate"]] = relationship(
        back_populates="empresa_prestadora",
        uselist=False,
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="operador")
    permissions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
    )

    empresa_prestadora: Mapped["ProviderCompany"] = relationship(back_populates="usuarios")
    agendamentos_criados: Mapped[List["Appointment"]] = relationship(
        back_populates="usuario_responsavel",
        foreign_keys="Appointment.usuario_responsavel_id",
    )
    agendamentos_atualizados: Mapped[List["Appointment"]] = relationship(
        back_populates="usuario_ultima_atualizacao",
        foreign_keys="Appointment.usuario_ultima_atualizacao_id",
    )
    historico_agendamentos: Mapped[List["AppointmentHistory"]] = relationship(back_populates="usuario")
    historico_whatsapp_agendamentos: Mapped[List["AppointmentWhatsAppLog"]] = relationship(back_populates="usuario")
    historico_recibos: Mapped[List["ReceiptHistory"]] = relationship(back_populates="usuario")
    estoque_movimentacoes: Mapped[List["StockMovement"]] = relationship(back_populates="usuario")


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_users: Mapped[int] = mapped_column(nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ativa")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
    )

    empresa_prestadora: Mapped[Optional["ProviderCompany"]] = relationship(back_populates="licencas")


class Customer(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)
    cep: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complemento: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    contato: Mapped[str] = mapped_column(String(120), nullable=False)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    ordens_servico: Mapped[List["WorkOrder"]] = relationship(back_populates="cliente")
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="cliente")
    agendamentos: Mapped[List["Appointment"]] = relationship(back_populates="cliente")
    notas_fiscais: Mapped[List["NfeInvoice"]] = relationship(back_populates="cliente")
    recibos: Mapped[List["Receipt"]] = relationship(back_populates="cliente")
    contratos: Mapped[List["Contract"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        order_by="Contract.data_vencimento.asc()",
    )


class Contract(Base):
    __tablename__ = "contratos"
    __table_args__ = (
        Index("ix_contratos_cliente_status", "cliente_id", "status"),
        Index("ix_contratos_status_vencimento", "status", "data_vencimento"),
        Index("ix_contratos_cobranca_automatica_status", "gerar_cobranca_automatica", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ativo", index=True)
    valor_mensal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tipo_cobranca: Mapped[str] = mapped_column(String(20), nullable=False, default="mensal", index=True)
    dia_vencimento: Mapped[Optional[int]] = mapped_column(nullable=True)
    gerar_cobranca_automatica: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    arquivo_nome_original: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    arquivo_nome_armazenado: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    arquivo_content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    arquivo_tamanho: Mapped[Optional[int]] = mapped_column(nullable=True)
    arquivo_caminho: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_notification_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    last_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_notification_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Customer"] = relationship(back_populates="contratos")
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="contrato")


class NcmTaxProfile(Base):
    __tablename__ = "ncm"

    codigo: Mapped[str] = mapped_column(String(8), primary_key=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliquota_icms: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_ipi: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_pis: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_cofins: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    fonte_dados: Mapped[str] = mapped_column(String(60), nullable=False, default="cache_local")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    produtos: Mapped[List["Product"]] = relationship(back_populates="perfil_ncm")


class Product(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    categoria: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False, default="UN")
    codigo_barras: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    qr_code_value: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    principio_ativo: Mapped[str] = mapped_column(String(120), nullable=False)
    grupo_quimico: Mapped[str] = mapped_column(String(120), nullable=False)
    toxicidade: Mapped[str] = mapped_column(String(80), nullable=False)
    concentracao: Mapped[str] = mapped_column(String(60), nullable=False)
    registro_ms: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    ncm: Mapped[Optional[str]] = mapped_column(ForeignKey("ncm.codigo"), nullable=True, index=True)
    ncm_descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    aliquota_icms: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_ipi: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_pis: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_cofins: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    override_tributacao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estoque_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    perfil_ncm: Mapped[Optional["NcmTaxProfile"]] = relationship(back_populates="produtos")
    empresa_prestadora: Mapped[Optional["ProviderCompany"]] = relationship()
    itens_ordem_servico: Mapped[List["WorkOrderProduct"]] = relationship(back_populates="produto")
    estoque_movimentacoes: Mapped[List["StockMovement"]] = relationship(
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="StockMovement.created_at.desc()",
    )
    estoque_saldos: Mapped[List["StockLocationBalance"]] = relationship(
        back_populates="produto",
        cascade="all, delete-orphan",
    )
    inventario_itens: Mapped[List["StockInventoryItem"]] = relationship(back_populates="produto")


class StockMovement(Base):
    __tablename__ = "estoque_movimentacoes"
    __table_args__ = (
        Index("ix_estoque_movimentacoes_empresa_data", "empresa_prestadora_id", "created_at"),
        Index("ix_estoque_movimentacoes_produto_data", "produto_id", "created_at"),
        Index("ix_estoque_movimentacoes_tipo_empresa", "tipo_movimento", "empresa_prestadora_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
        index=True,
    )
    empresa_relacionada_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )
    armazem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("estoque_armazens.id"), nullable=True, index=True)
    local_id: Mapped[Optional[int]] = mapped_column(ForeignKey("estoque_locais.id"), nullable=True, index=True)
    armazem_relacionado_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("estoque_armazens.id"),
        nullable=True,
        index=True,
    )
    local_relacionado_id: Mapped[Optional[int]] = mapped_column(ForeignKey("estoque_locais.id"), nullable=True, index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    tipo_movimento: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    origem: Mapped[str] = mapped_column(String(50), nullable=False, default="manual", index=True)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False, default="UN")
    saldo_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    saldo_posterior: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    referencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    codigo_lido: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    produto: Mapped["Product"] = relationship(back_populates="estoque_movimentacoes")
    empresa_prestadora: Mapped["ProviderCompany"] = relationship(
        back_populates="estoque_movimentacoes",
        foreign_keys=[empresa_prestadora_id],
    )
    empresa_relacionada: Mapped[Optional["ProviderCompany"]] = relationship(foreign_keys=[empresa_relacionada_id])
    armazem: Mapped[Optional["StockWarehouse"]] = relationship(foreign_keys=[armazem_id])
    local: Mapped[Optional["StockLocation"]] = relationship(foreign_keys=[local_id])
    armazem_relacionado: Mapped[Optional["StockWarehouse"]] = relationship(foreign_keys=[armazem_relacionado_id])
    local_relacionado: Mapped[Optional["StockLocation"]] = relationship(foreign_keys=[local_relacionado_id])
    usuario: Mapped[Optional["User"]] = relationship(back_populates="estoque_movimentacoes")


class StockImportLog(Base):
    __tablename__ = "estoque_importacoes"
    __table_args__ = (
        Index("ix_estoque_importacoes_empresa_data", "empresa_prestadora_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(ForeignKey("empresas_prestadoras.id"), nullable=False, index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    tipo_arquivo: Mapped[str] = mapped_column(String(20), nullable=False)
    origem: Mapped[str] = mapped_column(String(30), nullable=False)
    referencia: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    nome_arquivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    produtos_processados: Mapped[int] = mapped_column(nullable=False, default=0)
    produtos_criados: Mapped[int] = mapped_column(nullable=False, default=0)
    produtos_atualizados: Mapped[int] = mapped_column(nullable=False, default=0)
    total_movimentado: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    errors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    empresa_prestadora: Mapped["ProviderCompany"] = relationship()
    usuario: Mapped[Optional["User"]] = relationship()


class StockWarehouse(Base):
    __tablename__ = "estoque_armazens"
    __table_args__ = (
        UniqueConstraint("empresa_prestadora_id", "codigo", name="uq_estoque_armazens_empresa_codigo"),
        Index("ix_estoque_armazens_empresa_nome", "empresa_prestadora_id", "nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="armazem")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    padrao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    empresa_prestadora: Mapped["ProviderCompany"] = relationship()
    locais: Mapped[List["StockLocation"]] = relationship(
        back_populates="armazem",
        cascade="all, delete-orphan",
        order_by="StockLocation.nome.asc()",
    )
    saldos: Mapped[List["StockLocationBalance"]] = relationship(back_populates="armazem")


class StockLocation(Base):
    __tablename__ = "estoque_locais"
    __table_args__ = (
        UniqueConstraint("armazem_id", "codigo", name="uq_estoque_locais_armazem_codigo"),
        Index("ix_estoque_locais_empresa_nome", "empresa_prestadora_id", "nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
        index=True,
    )
    armazem_id: Mapped[int] = mapped_column(ForeignKey("estoque_armazens.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    padrao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    empresa_prestadora: Mapped["ProviderCompany"] = relationship()
    armazem: Mapped["StockWarehouse"] = relationship(back_populates="locais")
    saldos: Mapped[List["StockLocationBalance"]] = relationship(back_populates="local")
    inventarios: Mapped[List["StockInventorySession"]] = relationship(back_populates="local")


class StockLocationBalance(Base):
    __tablename__ = "estoque_saldos"
    __table_args__ = (
        UniqueConstraint("produto_id", "armazem_id", "local_id", name="uq_estoque_saldos_produto_local"),
        Index("ix_estoque_saldos_empresa_produto", "empresa_prestadora_id", "produto_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
        index=True,
    )
    armazem_id: Mapped[int] = mapped_column(ForeignKey("estoque_armazens.id"), nullable=False, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("estoque_locais.id"), nullable=False, index=True)
    quantidade_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    produto: Mapped["Product"] = relationship(back_populates="estoque_saldos")
    armazem: Mapped["StockWarehouse"] = relationship(back_populates="saldos")
    local: Mapped["StockLocation"] = relationship(back_populates="saldos")


class StockInventorySession(Base):
    __tablename__ = "estoque_inventarios"
    __table_args__ = (
        Index("ix_estoque_inventarios_empresa_status", "empresa_prestadora_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
        index=True,
    )
    armazem_id: Mapped[int] = mapped_column(ForeignKey("estoque_armazens.id"), nullable=False, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("estoque_locais.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="aberto", index=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    finished_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    armazem: Mapped["StockWarehouse"] = relationship()
    local: Mapped["StockLocation"] = relationship(back_populates="inventarios")
    itens: Mapped[List["StockInventoryItem"]] = relationship(
        back_populates="inventario",
        cascade="all, delete-orphan",
        order_by="StockInventoryItem.id.asc()",
    )


class StockInventoryItem(Base):
    __tablename__ = "estoque_inventario_itens"
    __table_args__ = (
        UniqueConstraint("inventario_id", "produto_id", name="uq_estoque_inventario_item_produto"),
        Index("ix_estoque_inventario_itens_produto", "produto_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inventario_id: Mapped[int] = mapped_column(ForeignKey("estoque_inventarios.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade_sistema: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    quantidade_contada: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    divergencia: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    ultimo_codigo_lido: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    inventario: Mapped["StockInventorySession"] = relationship(back_populates="itens")
    produto: Mapped["Product"] = relationship(back_populates="inventario_itens")


class Pest(Base):
    __tablename__ = "pragas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_comum: Mapped[str] = mapped_column(String(120), nullable=False)
    nome_cientifico: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    ordens_servico: Mapped[List["WorkOrderPest"]] = relationship(back_populates="praga")


class Technician(Base):
    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    registro: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    ordens_servico: Mapped[List["WorkOrder"]] = relationship(back_populates="tecnico")
    agendamentos: Mapped[List["Appointment"]] = relationship(back_populates="tecnico")


class WorkOrder(Base):
    __tablename__ = "ordens_servico"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey("tecnicos.id"), nullable=False)
    data_execucao: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    local_execucao: Mapped[str] = mapped_column(String(255), nullable=False)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    garantia_ate: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="aberta")
    tipo_os: Mapped[str] = mapped_column(String(20), nullable=False, default="avulsa", index=True)
    valor_servico: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Customer"] = relationship(back_populates="ordens_servico")
    tecnico: Mapped["Technician"] = relationship(back_populates="ordens_servico")
    produtos: Mapped[List["WorkOrderProduct"]] = relationship(
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
    )
    pragas: Mapped[List["WorkOrderPest"]] = relationship(
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
    )
    fotos: Mapped[List["WorkOrderPhoto"]] = relationship(
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
    )
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="ordem_servico")
    agendamentos: Mapped[List["Appointment"]] = relationship(back_populates="ordem_servico")
    recibos: Mapped[List["Receipt"]] = relationship(back_populates="ordem_servico")


class Appointment(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True, index=True)
    tecnico_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tecnicos.id"), nullable=True, index=True)
    usuario_responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    usuario_ultima_atualizacao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    agendamento_pai_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agendamentos.id"), nullable=True, index=True)
    tipo_servico: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    endereco_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    data_agendamento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora_agendamento: Mapped[time] = mapped_column(Time, nullable=False)
    duracao_prevista_minutos: Mapped[int] = mapped_column(nullable=False, default=60)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacoes_internas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instrucoes_tecnicas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retorno_revisita: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendente", index=True)
    origem: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    sincronizar_google: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    google_calendar_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sync_status: Mapped[str] = mapped_column(String(30), nullable=False, default="desconectado")
    google_sync_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Customer"] = relationship(back_populates="agendamentos")
    ordem_servico: Mapped[Optional["WorkOrder"]] = relationship(back_populates="agendamentos")
    tecnico: Mapped[Optional["Technician"]] = relationship(back_populates="agendamentos")
    usuario_responsavel: Mapped[Optional["User"]] = relationship(
        back_populates="agendamentos_criados",
        foreign_keys=[usuario_responsavel_id],
    )
    usuario_ultima_atualizacao: Mapped[Optional["User"]] = relationship(
        back_populates="agendamentos_atualizados",
        foreign_keys=[usuario_ultima_atualizacao_id],
    )
    agendamento_pai: Mapped[Optional["Appointment"]] = relationship(remote_side=[id], back_populates="revisitas")
    revisitas: Mapped[List["Appointment"]] = relationship(back_populates="agendamento_pai")
    historico: Mapped[List["AppointmentHistory"]] = relationship(
        back_populates="agendamento",
        cascade="all, delete-orphan",
        order_by="AppointmentHistory.created_at.desc()",
    )
    whatsapp_logs: Mapped[List["AppointmentWhatsAppLog"]] = relationship(
        back_populates="agendamento",
        cascade="all, delete-orphan",
        order_by="AppointmentWhatsAppLog.created_at.desc()",
    )

    @property
    def whatsapp_status(self) -> Optional[str]:
        return self.whatsapp_logs[0].status if self.whatsapp_logs else None

    @property
    def whatsapp_ultimo_erro(self) -> Optional[str]:
        return self.whatsapp_logs[0].erro if self.whatsapp_logs else None

    @property
    def whatsapp_ultimo_envio_em(self) -> Optional[datetime]:
        return self.whatsapp_logs[0].created_at if self.whatsapp_logs else None


class AppointmentHistory(Base):
    __tablename__ = "agendamento_historico"

    id: Mapped[int] = mapped_column(primary_key=True)
    agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), nullable=False, index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    acao: Mapped[str] = mapped_column(String(60), nullable=False)
    status_anterior: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status_novo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    agendamento: Mapped["Appointment"] = relationship(back_populates="historico")
    usuario: Mapped[Optional["User"]] = relationship(back_populates="historico_agendamentos")


class AppointmentWhatsAppLog(Base):
    __tablename__ = "agendamento_whatsapp_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    agendamento_id: Mapped[int] = mapped_column(ForeignKey("agendamentos.id"), nullable=False, index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="custom")
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    destino_telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    automatico: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    erro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    resposta_externa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    agendamento: Mapped["Appointment"] = relationship(back_populates="whatsapp_logs")
    usuario: Mapped[Optional["User"]] = relationship(back_populates="historico_whatsapp_agendamentos")


class WorkOrderPhoto(Base):
    __tablename__ = "os_fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    ordem_servico: Mapped["WorkOrder"] = relationship(back_populates="fotos")

    @property
    def url(self) -> str:
        return f"/api/v1/os/fotos/{self.id}"


class WorkOrderProduct(Base):
    __tablename__ = "os_produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    diluicao: Mapped[str] = mapped_column(String(60), nullable=False)

    ordem_servico: Mapped["WorkOrder"] = relationship(back_populates="produtos")
    produto: Mapped["Product"] = relationship(back_populates="itens_ordem_servico")


class WorkOrderPest(Base):
    __tablename__ = "os_pragas"

    id: Mapped[int] = mapped_column(primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False, index=True)
    praga_id: Mapped[int] = mapped_column(ForeignKey("pragas.id"), nullable=False, index=True)

    ordem_servico: Mapped["WorkOrder"] = relationship(back_populates="pragas")
    praga: Mapped["Pest"] = relationship(back_populates="ordens_servico")


class FinanceEntry(Base):
    __tablename__ = "financeiro"
    __table_args__ = (
        Index("ix_financeiro_origem_referencia", "origem", "referencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendente")
    categoria: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    fornecedor_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    origem: Mapped[str] = mapped_column(String(50), nullable=False, default="manual", index=True)
    referencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    parcela_atual: Mapped[int] = mapped_column(nullable=False, default=1)
    total_parcelas: Mapped[int] = mapped_column(nullable=False, default=1)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True, index=True)
    contrato_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contratos.id"), nullable=True, index=True)
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True, index=True)
    nfe_id: Mapped[Optional[int]] = mapped_column(ForeignKey("notas_fiscais.id"), nullable=True, index=True)
    recibo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("recibos.id"), nullable=True, index=True)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped[Optional["Customer"]] = relationship(back_populates="financeiros")
    contrato: Mapped[Optional["Contract"]] = relationship(back_populates="financeiros")
    ordem_servico: Mapped[Optional["WorkOrder"]] = relationship(back_populates="financeiros")
    nota_fiscal: Mapped[Optional["NfeInvoice"]] = relationship(back_populates="financeiro")
    recibo: Mapped[Optional["Receipt"]] = relationship(back_populates="financeiro")
    movimentos_caixa: Mapped[List["CashLedgerEntry"]] = relationship(
        back_populates="financeiro",
        cascade="all, delete-orphan",
    )

    @property
    def saldo_aberto(self) -> Decimal:
        return Decimal(self.valor) - Decimal(self.valor_pago)


class CashLedgerEntry(Base):
    __tablename__ = "fluxo_caixa"

    id: Mapped[int] = mapped_column(primary_key=True)
    finance_entry_id: Mapped[int] = mapped_column(ForeignKey("financeiro.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    origem: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_movimento: Mapped[date] = mapped_column(Date, nullable=False)
    referencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    financeiro: Mapped["FinanceEntry"] = relationship(back_populates="movimentos_caixa")


class Receipt(Base):
    __tablename__ = "recibos"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    data_recebimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valor_por_extenso: Mapped[str] = mapped_column(Text, nullable=False)
    texto_formal: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Customer"] = relationship(back_populates="recibos")
    ordem_servico: Mapped[Optional["WorkOrder"]] = relationship(back_populates="recibos")
    financeiro: Mapped[Optional["FinanceEntry"]] = relationship(back_populates="recibo", uselist=False)
    historico: Mapped[List["ReceiptHistory"]] = relationship(
        back_populates="recibo",
        cascade="all, delete-orphan",
        order_by="ReceiptHistory.created_at.desc()",
    )

    @property
    def finance_entry_id(self) -> Optional[int]:
        return self.financeiro.id if self.financeiro else None

    @property
    def os_numero(self) -> Optional[str]:
        return self.ordem_servico.numero if self.ordem_servico else None


class ReceiptHistory(Base):
    __tablename__ = "recibo_historico"

    id: Mapped[int] = mapped_column(primary_key=True)
    recibo_id: Mapped[int] = mapped_column(ForeignKey("recibos.id"), nullable=False, index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    acao: Mapped[str] = mapped_column(String(60), nullable=False)
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    recibo: Mapped["Receipt"] = relationship(back_populates="historico")
    usuario: Mapped[Optional["User"]] = relationship(back_populates="historico_recibos")


class NfeInvoice(Base):
    __tablename__ = "notas_fiscais"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_nfe: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_emissao: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="emitida", index=True)
    referencia_externa: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True, index=True)
    ambiente: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    provedor: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    status_processamento: Mapped[str] = mapped_column(String(40), nullable=False, default="pendente_envio", index=True)
    status_externo: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    mensagem_retorno: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chave_nfe: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)
    xml_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    payload_enviado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resposta_externa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    xml_enviado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    xml_autorizado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    danfe_pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    danfe_pdf_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    protocolo_autorizacao: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    recibo_lote: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    lote_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Customer"] = relationship(back_populates="notas_fiscais")
    financeiro: Mapped[Optional["FinanceEntry"]] = relationship(back_populates="nota_fiscal", uselist=False)

    @property
    def finance_entry_id(self) -> Optional[int]:
        return self.financeiro.id if self.financeiro else None


class ManagedService(Base):
    __tablename__ = "managed_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    service_type: Mapped[str] = mapped_column(String(40), nullable=False, default="api", index=True)
    executor_type: Mapped[str] = mapped_column(String(40), nullable=False, default="external")
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    health_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)
    startup_order: Mapped[int] = mapped_column(nullable=False, default=100)
    shutdown_order: Mapped[int] = mapped_column(nullable=False, default=100)
    startup_timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=30)
    response_timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=5)
    max_restart_attempts: Mapped[int] = mapped_column(nullable=False, default=3)
    recovery_policy: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="registered", index=True)
    last_health_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    dependencies: Mapped[List["ServiceDependency"]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
        foreign_keys="ServiceDependency.service_id",
    )
    health_checks: Mapped[List["ServiceHealthCheck"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    command_audits: Mapped[List["ServiceCommandAudit"]] = relationship(back_populates="service", cascade="all, delete-orphan")


class ServiceDependency(Base):
    __tablename__ = "service_dependencies"
    __table_args__ = (UniqueConstraint("service_id", "dependency_id", name="uq_service_dependency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("managed_services.id"), nullable=False, index=True)
    dependency_id: Mapped[int] = mapped_column(ForeignKey("managed_services.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    service: Mapped["ManagedService"] = relationship(
        back_populates="dependencies",
        foreign_keys=[service_id],
    )
    dependency: Mapped["ManagedService"] = relationship(foreign_keys=[dependency_id])


class ServiceHealthCheck(Base):
    __tablename__ = "service_health_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("managed_services.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    cpu_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    memory_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    disk_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    active_connections: Mapped[Optional[int]] = mapped_column(nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, index=True)

    service: Mapped["ManagedService"] = relationship(back_populates="health_checks")


class ServiceCommandAudit(Base):
    __tablename__ = "service_command_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("managed_services.id"), nullable=False, index=True)
    command: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, index=True)

    service: Mapped["ManagedService"] = relationship(back_populates="command_audits")
    requested_by: Mapped[Optional["User"]] = relationship()


class SimplesNationalConfig(Base):
    __tablename__ = "simples_nacional_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    faixa_faturamento_inicio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    faixa_faturamento_fim: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    aliquota: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    anexo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)


class CompanyTechnicalData(Base):
    __tablename__ = "dados_tecnicos_empresa"
    __table_args__ = (
        UniqueConstraint("empresa_prestadora_id", name="uq_dados_tecnicos_empresa_empresa"),
        Index("ix_dados_tecnicos_empresa_empresa_prestadora_id", "empresa_prestadora_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=False,
    )
    legal_name: Mapped[str] = mapped_column(String(160), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    technical_responsible_name: Mapped[str] = mapped_column(String(160), nullable=False)
    technical_registry_type: Mapped[str] = mapped_column(String(40), nullable=False)
    technical_registry_number: Mapped[str] = mapped_column(String(60), nullable=False)
    technical_registry_state: Mapped[str] = mapped_column(String(2), nullable=False)
    sanitary_license_number: Mapped[str] = mapped_column(String(80), nullable=False)
    sanitary_license_expiry: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    environmental_license_number: Mapped[str] = mapped_column(String(80), nullable=False)
    environmental_license_expiry: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    toxicology_center_name: Mapped[str] = mapped_column(String(160), nullable=False, default="Centro de Informacao Toxicologica")
    toxicology_center_phone: Mapped[str] = mapped_column(String(40), nullable=False)
    sanitary_license_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sanitary_license_content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sanitary_license_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    sanitary_license_uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    environmental_license_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    environmental_license_content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    environmental_license_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    environmental_license_uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signature_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    signature_content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    signature_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    signature_uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signature_source: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    empresa_prestadora: Mapped["ProviderCompany"] = relationship(back_populates="dados_tecnicos")


class DigitalCertificate(Base):
    __tablename__ = "certificados_digitais"
    __table_args__ = (
        UniqueConstraint("empresa_prestadora_id", name="uq_certificados_digitais_empresa"),
        Index("ix_certificados_digitais_empresa_prestadora_id", "empresa_prestadora_id"),
        Index("ix_certificados_digitais_valid_to", "valid_to"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_prestadora_id: Mapped[int] = mapped_column(ForeignKey("empresas_prestadoras.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False, default="application/x-pkcs12")
    encrypted_file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    certificate_type: Mapped[str] = mapped_column(String(20), nullable=False, default="A1")
    serial_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    thumbprint: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issuer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    signature_algorithm: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    company_info_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_info_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chain_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="valid", index=True)
    last_validation_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    last_validation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    empresa_prestadora: Mapped["ProviderCompany"] = relationship(back_populates="certificado_digital")
    updated_by: Mapped[Optional["User"]] = relationship()


class DigitalCertificateAudit(Base):
    __tablename__ = "certificado_digital_auditoria"
    __table_args__ = (
        Index("ix_certificado_digital_auditoria_empresa_data", "empresa_prestadora_id", "created_at"),
        Index("ix_certificado_digital_auditoria_certificate_id", "certificate_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    certificate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("certificados_digitais.id"), nullable=True)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(ForeignKey("empresas_prestadoras.id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, index=True)

    certificate: Mapped[Optional["DigitalCertificate"]] = relationship()
    empresa_prestadora: Mapped[Optional["ProviderCompany"]] = relationship()
    user: Mapped[Optional["User"]] = relationship()


class BackgroundJobRun(Base):
    __tablename__ = "background_job_runs"
    __table_args__ = (
        UniqueConstraint("task_name", "run_date", name="uq_background_job_runs_task_date"),
        Index("ix_background_job_runs_task_name", "task_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_name: Mapped[str] = mapped_column(String(80), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
