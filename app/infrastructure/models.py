from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="operador")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_users: Mapped[int] = mapped_column(nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ativa")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(String(2), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    contato: Mapped[str] = mapped_column(String(120), nullable=False)

    ordens_servico: Mapped[List["WorkOrder"]] = relationship(back_populates="cliente")
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="cliente")


class Product(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    principio_ativo: Mapped[str] = mapped_column(String(120), nullable=False)
    grupo_quimico: Mapped[str] = mapped_column(String(120), nullable=False)
    toxicidade: Mapped[str] = mapped_column(String(80), nullable=False)
    concentracao: Mapped[str] = mapped_column(String(60), nullable=False)
    registro_ms: Mapped[str] = mapped_column(String(60), nullable=False)
    estoque_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

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
    financeiros: Mapped[List["FinanceEntry"]] = relationship(back_populates="ordem_servico")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True)

    cliente: Mapped[Optional["Customer"]] = relationship(back_populates="financeiros")
    ordem_servico: Mapped[Optional["WorkOrder"]] = relationship(back_populates="financeiros")
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    financeiro: Mapped["FinanceEntry"] = relationship(back_populates="movimentos_caixa")
