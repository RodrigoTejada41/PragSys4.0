from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, LargeBinary, Numeric, String, Text, Time
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
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_account_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    google_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

    usuarios: Mapped[List["User"]] = relationship(back_populates="empresa_prestadora")
    licencas: Mapped[List["License"]] = relationship(back_populates="empresa_prestadora")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="operador")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    empresa_prestadora_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresas_prestadoras.id"),
        nullable=True,
    )

    empresa_prestadora: Mapped[Optional["ProviderCompany"]] = relationship(back_populates="usuarios")
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
    cep: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complemento: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    contato: Mapped[str] = mapped_column(String(120), nullable=False)

    ordens_servico: Mapped[List["WorkOrder"]] = relationship(back_populates="cliente")
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="cliente")
    agendamentos: Mapped[List["Appointment"]] = relationship(back_populates="cliente")
    notas_fiscais: Mapped[List["NfeInvoice"]] = relationship(back_populates="cliente")
    recibos: Mapped[List["Receipt"]] = relationship(back_populates="cliente")


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
    principio_ativo: Mapped[str] = mapped_column(String(120), nullable=False)
    grupo_quimico: Mapped[str] = mapped_column(String(120), nullable=False)
    toxicidade: Mapped[str] = mapped_column(String(80), nullable=False)
    concentracao: Mapped[str] = mapped_column(String(60), nullable=False)
    registro_ms: Mapped[str] = mapped_column(String(60), nullable=False)
    ncm: Mapped[Optional[str]] = mapped_column(ForeignKey("ncm.codigo"), nullable=True, index=True)
    ncm_descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    aliquota_icms: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_ipi: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_pis: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    aliquota_cofins: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    override_tributacao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estoque_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    perfil_ncm: Mapped[Optional["NcmTaxProfile"]] = relationship(back_populates="produtos")
    itens_ordem_servico: Mapped[List["WorkOrderProduct"]] = relationship(back_populates="produto")


class Pest(Base):
    __tablename__ = "pragas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_comum: Mapped[str] = mapped_column(String(120), nullable=False)
    nome_cientifico: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)

    ordens_servico: Mapped[List["WorkOrderPest"]] = relationship(back_populates="praga")


class Technician(Base):
    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    registro: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
    valor_servico: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)

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
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    diluicao: Mapped[str] = mapped_column(String(60), nullable=False)

    ordem_servico: Mapped["WorkOrder"] = relationship(back_populates="produtos")
    produto: Mapped["Product"] = relationship(back_populates="itens_ordem_servico")


class WorkOrderPest(Base):
    __tablename__ = "os_pragas"

    id: Mapped[int] = mapped_column(primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    praga_id: Mapped[int] = mapped_column(ForeignKey("pragas.id"), nullable=False)

    ordem_servico: Mapped["WorkOrder"] = relationship(back_populates="pragas")
    praga: Mapped["Pest"] = relationship(back_populates="ordens_servico")


class FinanceEntry(Base):
    __tablename__ = "financeiro"

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
    origem: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    referencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    parcela_atual: Mapped[int] = mapped_column(nullable=False, default=1)
    total_parcelas: Mapped[int] = mapped_column(nullable=False, default=1)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True)
    nfe_id: Mapped[Optional[int]] = mapped_column(ForeignKey("notas_fiscais.id"), nullable=True, index=True)
    recibo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("recibos.id"), nullable=True, index=True)

    cliente: Mapped[Optional["Customer"]] = relationship(back_populates="financeiros")
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
    protocolo_autorizacao: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    recibo_lote: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    lote_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    cliente: Mapped["Customer"] = relationship(back_populates="notas_fiscais")
    financeiro: Mapped[Optional["FinanceEntry"]] = relationship(back_populates="nota_fiscal", uselist=False)

    @property
    def finance_entry_id(self) -> Optional[int]:
        return self.financeiro.id if self.financeiro else None


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
