from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AppointmentSource,
    AppointmentStatus,
    CashFlowType,
    FinanceStatus,
    FinanceType,
    GoogleSyncStatus,
    NfeEnvironment,
    NfeProcessingStatus,
    LicenseStatus,
    NfeStatus,
    ReceiptPaymentMethod,
    UserRole,
    WhatsAppDeliveryStatus,
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
    google_calendar_id: Optional[str] = None
    google_account_email: Optional[str] = None
    google_connected: bool = False


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
    ncm: Optional[str] = None
    ncm_descricao: Optional[str] = None
    aliquota_icms: Decimal = Field(default=Decimal("0.0000"), ge=0)
    aliquota_ipi: Decimal = Field(default=Decimal("0.0000"), ge=0)
    aliquota_pis: Decimal = Field(default=Decimal("0.0000"), ge=0)
    aliquota_cofins: Decimal = Field(default=Decimal("0.0000"), ge=0)
    override_tributacao: bool = False
    estoque_atual: Decimal = Field(default=Decimal("0.00"), ge=0)
    estoque_minimo: Decimal = Field(default=Decimal("0.00"), ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class NcmTaxProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descricao: str
    aliquota_icms: Decimal
    aliquota_ipi: Decimal
    aliquota_pis: Decimal
    aliquota_cofins: Decimal
    fonte_dados: str
    updated_at: datetime


class NcmAutocompleteRead(BaseModel):
    codigo: str
    descricao: str


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
    nfe_id: Optional[int] = None


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
    recibo_id: Optional[int] = None


class ReceiptHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int] = None
    usuario_nome: Optional[str] = None
    acao: str
    detalhes: Optional[str] = None
    created_at: datetime


class ReceiptBase(BaseModel):
    cliente_id: int
    os_id: Optional[int] = None
    valor: Decimal = Field(gt=0)
    forma_pagamento: ReceiptPaymentMethod
    descricao: str = Field(min_length=5, max_length=2000)
    data_recebimento: date


class ReceiptCreate(ReceiptBase):
    pass


class ReceiptUpdate(ReceiptBase):
    pass


class ReceiptPreviewRead(BaseModel):
    cliente_id: int
    cliente_nome: str
    cliente_documento: str
    os_id: Optional[int] = None
    os_numero: Optional[str] = None
    valor: Decimal
    valor_formatado: str
    valor_por_extenso: str
    forma_pagamento: ReceiptPaymentMethod
    forma_pagamento_label: str
    descricao: str
    data_recebimento: date
    data_recebimento_formatada: str
    texto_formal: str


class ReceiptRead(ReceiptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    valor_por_extenso: str
    texto_formal: str
    cliente: CustomerRead
    os_numero: Optional[str] = None
    finance_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    historico: List[ReceiptHistoryRead] = Field(default_factory=list)


class FinanceCashFlowSummaryRead(BaseModel):
    periodo: str
    recebido: Decimal
    pendente: Decimal
    vencido: Decimal
    quantidade_recebida: int
    quantidade_pendente: int
    quantidade_vencida: int


class SimplesNationalConfigBase(BaseModel):
    faixa_faturamento_inicio: Decimal = Field(default=Decimal("0.00"), ge=0)
    faixa_faturamento_fim: Optional[Decimal] = Field(default=None, ge=0)
    aliquota: Decimal = Field(gt=0)
    anexo: Optional[str] = None
    vigente: bool = True
    observacoes: Optional[str] = None


class SimplesNationalConfigCreate(SimplesNationalConfigBase):
    pass


class SimplesNationalConfigUpdate(SimplesNationalConfigBase):
    pass


class SimplesNationalConfigRead(SimplesNationalConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SimplesNationalMonthlySummaryRead(BaseModel):
    referencia: str
    faturamento_bruto: Decimal
    aliquota_aplicada: Decimal
    anexo: Optional[str] = None
    imposto_estimado: Decimal
    notas_emitidas: int


class NfeInvoiceBase(BaseModel):
    numero_nfe: str
    cliente_id: int
    valor_total: Decimal = Field(gt=0)
    data_emissao: date
    data_vencimento: date
    status: NfeStatus = NfeStatus.EMITIDA
    observacoes: Optional[str] = None


class NfeItemPayload(BaseModel):
    descricao: str
    ncm: str
    quantidade: Decimal = Field(gt=0)
    valor_unitario: Decimal = Field(gt=0)
    produto_id: Optional[int] = None
    cfop: Optional[str] = None
    unidade_comercial: Optional[str] = None
    aliquota_icms: Optional[Decimal] = Field(default=None, ge=0)
    aliquota_ipi: Optional[Decimal] = Field(default=None, ge=0)
    aliquota_pis: Optional[Decimal] = Field(default=None, ge=0)
    aliquota_cofins: Optional[Decimal] = Field(default=None, ge=0)


class NfeInvoiceCreate(NfeInvoiceBase):
    gerar_financeiro: bool = True
    natureza_operacao: str = "Venda"
    ambiente: NfeEnvironment = NfeEnvironment.HOMOLOGACAO
    referencia_externa: Optional[str] = None
    webhook_url: Optional[str] = None
    nome_emitente: Optional[str] = None
    cnpj_emitente: Optional[str] = None
    nome_destinatario: Optional[str] = None
    cpf_destinatario: Optional[str] = None
    cnpj_destinatario: Optional[str] = None
    itens: List[NfeItemPayload] = Field(default_factory=list)
    payload_externo: Optional[dict[str, Any]] = None


class NfeInvoiceUpdate(NfeInvoiceBase):
    webhook_url: Optional[str] = None
    referencia_externa: Optional[str] = None
    ambiente: NfeEnvironment = NfeEnvironment.HOMOLOGACAO


class NfeCancelRequest(BaseModel):
    justificativa: Optional[str] = None


class NfeWebhookEvent(BaseModel):
    referencia: str
    status: Optional[str] = None
    chave_nfe: Optional[str] = None
    caminho_xml_nota_fiscal: Optional[str] = None
    caminho_danfe: Optional[str] = None
    mensagem_sefaz: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class NfeInvoiceRead(NfeInvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente: CustomerRead
    finance_entry_id: Optional[int] = None
    referencia_externa: Optional[str] = None
    ambiente: Optional[NfeEnvironment] = None
    provedor: Optional[str] = None
    status_processamento: NfeProcessingStatus
    status_externo: Optional[str] = None
    mensagem_retorno: Optional[str] = None
    chave_nfe: Optional[str] = None
    protocolo_autorizacao: Optional[str] = None
    recibo_lote: Optional[str] = None
    lote_id: Optional[str] = None
    xml_url: Optional[str] = None
    pdf_url: Optional[str] = None
    payload_enviado: Optional[str] = None
    xml_enviado: Optional[str] = None
    xml_autorizado: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SefazDirectReadinessRead(BaseModel):
    ready: bool
    provider: str
    environment: str
    uf: Optional[str] = None
    certificate_path: Optional[str] = None
    xsd_dir: Optional[str] = None
    required_items: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


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


class AppointmentWhatsAppLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int] = None
    usuario_nome: Optional[str] = None
    provider: str
    status: WhatsAppDeliveryStatus
    destino_telefone: str
    mensagem: str
    automatico: bool
    erro: Optional[str] = None
    external_message_id: Optional[str] = None
    resposta_externa: Optional[str] = None
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
    whatsapp_status: Optional[WhatsAppDeliveryStatus] = None
    whatsapp_ultimo_erro: Optional[str] = None
    whatsapp_ultimo_envio_em: Optional[datetime] = None
    agendamento_pai_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    historico: List[AppointmentHistoryRead] = Field(default_factory=list)
    whatsapp_logs: List[AppointmentWhatsAppLogRead] = Field(default_factory=list)


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


class WhatsAppConfigStatusRead(BaseModel):
    enabled: bool
    provider: str
    configured: bool
    api_base_url: Optional[str] = None
    sender_id_configured: bool
    auth_configured: bool


class GoogleCalendarOAuthStartRead(BaseModel):
    authorization_url: str
    message: str


class GoogleCalendarAppointmentSyncRead(BaseModel):
    mode: str
    message: str
    authorization_url: Optional[str] = None
    appointment: Optional[AppointmentRead] = None


UserCreate.model_rebuild()
