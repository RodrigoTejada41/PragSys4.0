from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AppointmentSource,
    AppointmentStatus,
    CashFlowType,
    FinanceStatus,
    FinanceType,
    GoogleSyncStatus,
    LicenseStatus,
    UserRole,
    WorkOrderStatus,
)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    username: str
    role: UserRole
    is_active: bool
    empresa_prestadora_id: Optional[int] = None
    empresa_prestadora_nome: Optional[str] = None


class ProviderCompanyBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, min_length=2, max_length=2)


class ProviderCompanyCreate(ProviderCompanyBase):
    usuarios_vinculados_ids: List[int] = Field(default_factory=list)


class ProviderCompanyUpdate(ProviderCompanyBase):
    usuarios_vinculados_ids: List[int] = Field(default_factory=list)


class ProviderCompanyRead(ProviderCompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuarios_vinculados_ids: List[int] = Field(default_factory=list)
    usuarios_vinculados_nomes: List[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    nome: str
    username: str
    password: str = Field(min_length=6)
    role: UserRole
    is_active: bool = True
    empresa_prestadora_id: Optional[int] = None
    nova_empresa_prestadora: Optional[ProviderCompanyCreate] = None
    licenca_inicial: Optional["LicenseCreate"] = None


class UserUpdate(BaseModel):
    nome: str
    username: str
    role: UserRole
    is_active: bool = True
    password: Optional[str] = Field(default=None, min_length=6)
    empresa_prestadora_id: Optional[int] = None


class LicenseBase(BaseModel):
    descricao: str
    start_date: date
    end_date: date
    max_users: int = Field(ge=1)
    status: LicenseStatus = LicenseStatus.ATIVA
    notes: Optional[str] = None
    empresa_prestadora_id: Optional[int] = None


class LicenseCreate(LicenseBase):
    pass


class LicenseUpdate(LicenseBase):
    pass


class LicenseRead(LicenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_prestadora_nome: Optional[str] = None


class CustomerBase(BaseModel):
    razao_social: str
    cpf_cnpj: str
    cep: Optional[str] = None
    endereco: str
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: str
    estado: str = Field(min_length=2, max_length=2)
    telefone: str
    contato: str


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CustomerCnpjLookupRead(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None


class AddressLookupRead(BaseModel):
    cep: str
    endereco: str
    bairro: Optional[str] = None
    cidade: str
    estado: str


class ProductBase(BaseModel):
    nome: str
    principio_ativo: str
    grupo_quimico: str
    toxicidade: str
    concentracao: str
    registro_ms: str
    estoque_atual: Decimal = Field(default=Decimal("0.00"), ge=0)
    estoque_minimo: Decimal = Field(default=Decimal("0.00"), ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductXmlImportItemRead(BaseModel):
    nome: str
    codigo: str
    quantidade: Decimal
    produto_id: int
    acao: str


class ProductXmlImportResult(BaseModel):
    nota_numero: str
    chave_acesso: Optional[str] = None
    fornecedor_nome: str
    fornecedor_documento: Optional[str] = None
    data_emissao: date
    valor_total: Decimal
    produtos_processados: int
    produtos_criados: int
    produtos_atualizados: int
    financeiro_criado: bool
    finance_entry_id: Optional[int] = None
    itens: List[ProductXmlImportItemRead]


class ProductCsvImportItemRead(BaseModel):
    nome: str
    registro_ms: str
    quantidade_entrada: Decimal
    custo_total: Decimal
    produto_id: int
    finance_entry_id: Optional[int] = None
    acao: str


class ProductCsvImportResult(BaseModel):
    referencia_lote: str
    fornecedor_padrao: Optional[str] = None
    data_importacao: date
    produtos_processados: int
    produtos_criados: int
    produtos_atualizados: int
    lancamentos_financeiros: int
    valor_financeiro_total: Decimal
    itens: List[ProductCsvImportItemRead]


class PestBase(BaseModel):
    nome_comum: str
    nome_cientifico: str
    descricao: str


class PestCreate(PestBase):
    pass


class PestUpdate(PestBase):
    pass


class PestRead(PestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TechnicianBase(BaseModel):
    nome: str
    registro: str
    telefone: str
    ativo: bool = True


class TechnicianCreate(TechnicianBase):
    pass


class TechnicianUpdate(TechnicianBase):
    pass


class TechnicianRead(TechnicianBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class FinanceEntryBase(BaseModel):
    tipo: FinanceType
    descricao: str
    valor: Decimal = Field(gt=0)
    vencimento: date
    status: FinanceStatus = FinanceStatus.PENDENTE
    categoria: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    origem: str = "manual"
    referencia: Optional[str] = None
    parcela_atual: int = Field(default=1, ge=1)
    total_parcelas: int = Field(default=1, ge=1)
    observacoes: Optional[str] = None
    cliente_id: Optional[int] = None
    os_id: Optional[int] = None


class FinanceEntryCreate(FinanceEntryBase):
    pass


class FinanceEntryUpdate(FinanceEntryBase):
    pass


class FinanceEntryRead(FinanceEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    valor_pago: Decimal
    saldo_aberto: Decimal
    data_pagamento: Optional[date] = None


class FinancePaymentRequest(BaseModel):
    valor: Optional[Decimal] = Field(default=None, gt=0)
    data_pagamento: Optional[date] = None


class CashLedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    finance_entry_id: int
    tipo: CashFlowType
    origem: str
    valor: Decimal
    data_movimento: date
    referencia: Optional[str] = None


class FinanceDashboardRead(BaseModel):
    total_a_receber: Decimal
    total_a_pagar: Decimal
    saldo_atual: Decimal
    inadimplencia_quantidade: int
    inadimplencia_valor: Decimal


class WorkOrderProductCreate(BaseModel):
    produto_id: int
    quantidade: Decimal = Field(gt=0)
    diluicao: str


class WorkOrderProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    quantidade: Decimal
    diluicao: str
    produto: ProductRead


class WorkOrderPestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    praga: PestRead


class WorkOrderPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    created_at: datetime
    url: str


class WorkOrderCreate(BaseModel):
    numero: str
    cliente_id: int
    tecnico_id: int
    data_execucao: date
    hora_inicio: time
    hora_fim: Optional[time] = None
    local_execucao: str
    observacoes: Optional[str] = None
    garantia_ate: date
    status: WorkOrderStatus = WorkOrderStatus.ABERTA
    valor_servico: Decimal = Field(default=Decimal("0.00"), ge=0)
    produtos: List[WorkOrderProductCreate] = Field(default_factory=list)
    pragas_ids: List[int] = Field(default_factory=list)
    gerar_financeiro: bool = True
    gerar_agendamento: bool = True
    tipo_servico_agendamento: Optional[str] = None
    duracao_prevista_minutos: int = Field(default=60, ge=15, le=480)
    observacoes_internas_agendamento: Optional[str] = None
    instrucoes_tecnicas_agendamento: Optional[str] = None
    retorno_revisita_agendamento: Optional[str] = None
    sincronizar_google_agenda: bool = False


class WorkOrderUpdate(WorkOrderCreate):
    pass


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    cliente_id: int
    tecnico_id: int
    data_execucao: date
    hora_inicio: time
    hora_fim: Optional[time] = None
    local_execucao: str
    observacoes: Optional[str] = None
    garantia_ate: date
    status: WorkOrderStatus
    valor_servico: Decimal
    cliente: CustomerRead
    tecnico: TechnicianRead
    produtos: List[WorkOrderProductRead]
    pragas: List[WorkOrderPestRead]
    fotos: List[WorkOrderPhotoRead] = Field(default_factory=list)


class AppointmentHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int] = None
    usuario_nome: Optional[str] = None
    acao: str
    status_anterior: Optional[AppointmentStatus] = None
    status_novo: Optional[AppointmentStatus] = None
    detalhes: Optional[str] = None
    created_at: datetime


class AppointmentBase(BaseModel):
    cliente_id: int
    os_id: Optional[int] = None
    tecnico_id: Optional[int] = None
    tipo_servico: str
    data_agendamento: date
    hora_agendamento: time
    duracao_prevista_minutos: int = Field(default=60, ge=15, le=480)
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None
    instrucoes_tecnicas: Optional[str] = None
    retorno_revisita: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.PENDENTE
    sincronizar_google: bool = False
    agendamento_pai_id: Optional[int] = None


class AppointmentCreate(AppointmentBase):
    origem: AppointmentSource = AppointmentSource.MANUAL


class AppointmentUpdate(AppointmentBase):
    pass


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    detalhes: Optional[str] = None


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    cliente_nome: str
    telefone: str
    endereco_completo: str
    os_id: Optional[int] = None
    os_numero: Optional[str] = None
    tecnico_id: Optional[int] = None
    tecnico_nome: Optional[str] = None
    usuario_responsavel_id: Optional[int] = None
    usuario_responsavel_nome: Optional[str] = None
    usuario_ultima_atualizacao_id: Optional[int] = None
    usuario_ultima_atualizacao_nome: Optional[str] = None
    tipo_servico: str
    data_agendamento: date
    hora_agendamento: time
    duracao_prevista_minutos: int
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None
    instrucoes_tecnicas: Optional[str] = None
    retorno_revisita: Optional[str] = None
    status: AppointmentStatus
    origem: AppointmentSource
    sincronizar_google: bool
    google_calendar_event_id: Optional[str] = None
    google_calendar_id: Optional[str] = None
    google_sync_status: GoogleSyncStatus
    google_sync_message: Optional[str] = None
    agendamento_pai_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    historico: List[AppointmentHistoryRead] = Field(default_factory=list)


class AppointmentDashboardRead(BaseModel):
    total: int
    pendente: int
    confirmado: int
    em_deslocamento: int
    em_atendimento: int
    concluido: int
    reagendado: int
    cancelado: int
    nao_realizado: int


UserCreate.model_rebuild()
