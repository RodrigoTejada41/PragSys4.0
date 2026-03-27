from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AppointmentSource,
    AppointmentStatus,
    CashFlowType,
    ContractBillingType,
    ContractStatus,
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
    WorkOrderType,
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
    permissions: dict[str, bool] = Field(default_factory=dict)


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
    is_active: bool = True
    is_provider: bool = True
    empresa_pai_id: Optional[int] = None
    compartilha_visualizacao_estoque: bool = False


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
    empresa_pai_nome: Optional[str] = None
    filiais_ids: List[int] = Field(default_factory=list)
    filiais_nomes: List[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    nome: str
    username: str
    password: str = Field(min_length=6)
    role: UserRole
    is_active: bool = True
    empresa_prestadora_id: Optional[int] = None
    permissions: dict[str, bool] = Field(default_factory=dict)
    nova_empresa_prestadora: Optional[ProviderCompanyCreate] = None
    licenca_inicial: Optional["LicenseCreate"] = None


class UserUpdate(BaseModel):
    nome: str
    username: str
    role: UserRole
    is_active: bool = True
    password: Optional[str] = Field(default=None, min_length=6)
    empresa_prestadora_id: Optional[int] = None
    permissions: dict[str, bool] = Field(default_factory=dict)


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
    email: Optional[str] = None
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
    empresa_prestadora_id: Optional[int] = None
    empresa_prestadora_nome: Optional[str] = None


class StockMovementCreate(BaseModel):
    produto_id: int
    tipo_movimento: str = Field(min_length=1, max_length=30)
    quantidade: Decimal = Field(gt=0)
    motivo: str = Field(min_length=3, max_length=255)
    observacoes: Optional[str] = None
    referencia: Optional[str] = Field(default=None, max_length=120)
    empresa_prestadora_id: Optional[int] = None
    empresa_relacionada_id: Optional[int] = None


class StockMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    produto_nome: str
    empresa_prestadora_id: int
    empresa_prestadora_nome: Optional[str] = None
    empresa_relacionada_id: Optional[int] = None
    empresa_relacionada_nome: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_nome: Optional[str] = None
    tipo_movimento: str
    origem: str
    motivo: str
    quantidade: Decimal
    saldo_anterior: Decimal
    saldo_posterior: Decimal
    referencia: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: datetime


class StockPositionRead(BaseModel):
    produto_id: int
    produto_nome: str
    empresa_prestadora_id: int
    empresa_prestadora_nome: str
    estoque_atual: Decimal
    estoque_minimo: Decimal
    registro_ms: str


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
    contrato_id: Optional[int] = None
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
    numero: Optional[str] = None
    cliente_id: int
    tecnico_id: int
    data_execucao: date
    hora_inicio: time
    hora_fim: Optional[time] = None
    local_execucao: str
    observacoes: Optional[str] = None
    garantia_ate: date
    status: WorkOrderStatus = WorkOrderStatus.ABERTA
    tipo_os: WorkOrderType = WorkOrderType.AVULSA
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
    tipo_os: WorkOrderType
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
    enviar_whatsapp: bool = True
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
    supports_qr: bool = False


class WhatsAppConnectionStatusRead(BaseModel):
    status: str
    provider: str
    instance_name: Optional[str] = None
    connected_phone: Optional[str] = None
    error_message: Optional[str] = None
    configured: bool
    supports_qr: bool = False
    session_persistent: bool = False


class WhatsAppQrSessionRead(BaseModel):
    status: str
    provider: str
    instance_name: Optional[str] = None
    qr_code: Optional[str] = None
    qr_image_data_url: Optional[str] = None
    pairing_code: Optional[str] = None
    expires_at: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None


class GoogleCalendarOAuthStartRead(BaseModel):
    authorization_url: str
    message: str


class GoogleCalendarConnectionStatusRead(BaseModel):
    status: str
    message: str
    company_id: int
    company_name: str
    account_email: Optional[str] = None
    calendar_id: Optional[str] = None


class GoogleCalendarAppointmentSyncRead(BaseModel):
    mode: str
    message: str
    authorization_url: Optional[str] = None
    appointment: Optional[AppointmentRead] = None


class SettingsIntegrationsRead(BaseModel):
    google_calendar_enabled: bool
    whatsapp_enabled: bool
    whatsapp_auto_send: bool
    whatsapp_default_message: str


class SettingsContractsRead(BaseModel):
    alert_days: int
    email_enabled: bool
    storage_dir: str


class SettingsSystemRead(BaseModel):
    multiempresa_enabled: bool
    operation_mode: str
    notifications_enabled: bool
    appointment_default_google_sync: bool


class SettingsEmailRead(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_sender_email: Optional[str] = None
    smtp_sender_name: Optional[str] = None
    smtp_password_configured: bool


class SettingsDatabaseRead(BaseModel):
    backup_dir: str
    engine: str
    database_file_name: Optional[str] = None


class SettingsEnvironmentRead(BaseModel):
    database_url_masked: str
    app_host: str
    app_port: int
    allow_remote_access: bool


class SettingsAssetRead(BaseModel):
    has_file: bool
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_at: Optional[str] = None


class SettingsCompanyRead(BaseModel):
    legal_name: str
    trade_name: str
    cnpj: Optional[str] = None
    address: str
    phone: Optional[str] = None
    technical_responsible_name: str
    technical_registry_type: str
    technical_registry_number: str
    technical_registry_state: str
    technical_responsible_registry: str
    sanitary_license_number: str
    sanitary_license_expiry: Optional[str] = None
    environmental_license_number: str
    environmental_license_expiry: Optional[str] = None
    toxicology_center_name: str
    toxicology_center_phone: str
    sanitary_license_file: SettingsAssetRead
    environmental_license_file: SettingsAssetRead
    technical_signature: SettingsAssetRead


class SystemSettingsRead(BaseModel):
    integrations: SettingsIntegrationsRead
    contracts: SettingsContractsRead
    system: SettingsSystemRead
    email: SettingsEmailRead
    database: SettingsDatabaseRead
    environment: SettingsEnvironmentRead
    company: SettingsCompanyRead


class SettingsIntegrationsUpdate(BaseModel):
    google_calendar_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    whatsapp_auto_send: Optional[bool] = None
    whatsapp_default_message: Optional[str] = None


class SettingsContractsUpdate(BaseModel):
    alert_days: Optional[int] = Field(default=None, ge=1, le=365)
    email_enabled: Optional[bool] = None
    storage_dir: Optional[str] = None


class SettingsSystemUpdate(BaseModel):
    multiempresa_enabled: Optional[bool] = None
    operation_mode: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    appointment_default_google_sync: Optional[bool] = None


class SettingsEmailUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(default=None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    smtp_sender_email: Optional[str] = None
    smtp_sender_name: Optional[str] = None


class SettingsDatabaseUpdate(BaseModel):
    backup_dir: Optional[str] = None


class SettingsCompanyUpdate(BaseModel):
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    technical_responsible_name: Optional[str] = None
    technical_registry_type: Optional[str] = None
    technical_registry_number: Optional[str] = None
    technical_registry_state: Optional[str] = None
    technical_responsible_registry: Optional[str] = None
    sanitary_license_number: Optional[str] = None
    sanitary_license_expiry: Optional[str] = None
    environmental_license_number: Optional[str] = None
    environmental_license_expiry: Optional[str] = None
    toxicology_center_name: Optional[str] = None
    toxicology_center_phone: Optional[str] = None


class SystemSettingsUpdate(BaseModel):
    integrations: Optional[SettingsIntegrationsUpdate] = None
    contracts: Optional[SettingsContractsUpdate] = None
    system: Optional[SettingsSystemUpdate] = None
    email: Optional[SettingsEmailUpdate] = None
    database: Optional[SettingsDatabaseUpdate] = None
    company: Optional[SettingsCompanyUpdate] = None


class DatabaseMaintenanceRead(BaseModel):
    message: str
    file_name: Optional[str] = None
    backup_dir: Optional[str] = None
    safety_backup_file: Optional[str] = None
    details: dict[str, int] = Field(default_factory=dict)


class DatabaseCleanupRequest(BaseModel):
    confirmation: str = Field(min_length=1)
    include_finance: bool = False


class ContractBase(BaseModel):
    nome: str = Field(min_length=3, max_length=180)
    data_inicio: date
    data_vencimento: date
    valor_mensal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tipo_cobranca: ContractBillingType = ContractBillingType.MENSAL
    dia_vencimento: Optional[int] = Field(default=None, ge=1, le=31)
    gerar_cobranca_automatica: bool = False
    observacoes: Optional[str] = Field(default=None, max_length=4000)

    def model_post_init(self, __context) -> None:
        if self.data_vencimento < self.data_inicio:
            raise ValueError("A data de vencimento nao pode ser anterior a data de inicio.")


class ContractCreate(ContractBase):
    pass


class ContractUpdate(ContractBase):
    pass


class ContractRead(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    cliente_email: Optional[str] = None
    nome: str
    data_inicio: date
    data_vencimento: date
    status: ContractStatus
    valor_mensal: Decimal
    tipo_cobranca: ContractBillingType
    dia_vencimento: Optional[int] = None
    gerar_cobranca_automatica: bool = False
    observacoes: Optional[str] = None
    arquivo_nome_original: Optional[str] = None
    arquivo_content_type: Optional[str] = None
    arquivo_tamanho: Optional[int] = None
    arquivo_disponivel: bool = False
    dias_para_vencimento: int
    created_at: datetime
    updated_at: datetime
    ultima_cobranca_gerada_em: Optional[date] = None
    ultima_cobranca_status: Optional[FinanceStatus] = None
    ultima_cobranca_valor: Optional[Decimal] = None
    quantidade_cobrancas: int = 0
    quantidade_cobrancas_pendentes: int = 0
    quantidade_cobrancas_vencidas: int = 0


class ContractAlertRead(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    nome: str
    data_vencimento: date
    status: ContractStatus
    dias_para_vencimento: int


class ContractDashboardRead(BaseModel):
    total: int
    ativos: int
    vencidos: int
    a_vencer: int
    alert_days: int
    vencidos_alertas: List[ContractAlertRead] = Field(default_factory=list)
    a_vencer_alertas: List[ContractAlertRead] = Field(default_factory=list)
    cobrancas_vencidas: int = 0
    cobrancas_a_vencer: int = 0
    valor_mensal_previsto: Decimal = Field(default=Decimal("0.00"))


class ContractMaintenanceRead(BaseModel):
    processed: int
    updated_statuses: int
    email_sent: int
    email_failed: int
    charges_generated: int = 0


class ContractReportFiltersRead(BaseModel):
    cliente_id: Optional[int] = None
    status: Optional[ContractStatus] = None
    data_inicio_de: Optional[date] = None
    data_inicio_ate: Optional[date] = None
    data_vencimento_de: Optional[date] = None
    data_vencimento_ate: Optional[date] = None
    cobranca_ativa: Optional[bool] = None


class ContractReportSummaryRead(BaseModel):
    total_contratos: int
    ativos: int
    vencidos: int
    a_vencer: int
    com_cobranca_ativa: int
    valor_total_mensal_previsto: Decimal


class ContractReportItemRead(BaseModel):
    contrato_id: int
    cliente_id: int
    cliente_nome: str
    nome: str
    data_inicio: date
    data_vencimento: date
    status: ContractStatus
    valor_mensal: Decimal
    tipo_cobranca: ContractBillingType
    gerar_cobranca_automatica: bool
    ultima_cobranca_gerada_em: Optional[date] = None
    situacao_financeira: str
    ultimo_lancamento_id: Optional[int] = None
    ultimo_lancamento_status: Optional[FinanceStatus] = None
    ultimo_lancamento_valor: Optional[Decimal] = None
    total_cobrancas: int = 0


class ContractReportRead(BaseModel):
    filtros: ContractReportFiltersRead
    resumo: ContractReportSummaryRead
    itens: List[ContractReportItemRead] = Field(default_factory=list)


UserCreate.model_rebuild()
