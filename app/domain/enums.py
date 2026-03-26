from enum import Enum


class UserRole(str, Enum):
    MASTER = "master"
    ADMIN = "admin"
    OPERADOR = "operador"


class FinanceType(str, Enum):
    RECEITA = "receita"
    DESPESA = "despesa"


class FinanceStatus(str, Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    ATRASADO = "atrasado"


class ReceiptPaymentMethod(str, Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    TRANSFERENCIA = "transferencia"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    BOLETO = "boleto"
    CHEQUE = "cheque"
    OUTROS = "outros"


class CashFlowType(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class WorkOrderStatus(str, Enum):
    ABERTA = "aberta"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class WorkOrderType(str, Enum):
    AVULSA = "avulsa"
    CONTRATO = "contrato"


class LicenseStatus(str, Enum):
    ATIVA = "ativa"
    EXPIRADA = "expirada"
    SUSPENSA = "suspensa"


class ContractStatus(str, Enum):
    ATIVO = "ativo"
    VENCIDO = "vencido"
    A_VENCER = "a_vencer"


class ContractBillingType(str, Enum):
    MENSAL = "mensal"
    ANUAL = "anual"
    PERSONALIZADO = "personalizado"


class AppointmentStatus(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    EM_DESLOCAMENTO = "em_deslocamento"
    EM_ATENDIMENTO = "em_atendimento"
    CONCLUIDO = "concluido"
    REAGENDADO = "reagendado"
    CANCELADO = "cancelado"
    NAO_REALIZADO = "nao_realizado"


class AppointmentSource(str, Enum):
    MANUAL = "manual"
    ORDEM_SERVICO = "ordem_servico"


class GoogleSyncStatus(str, Enum):
    PENDENTE = "pendente"
    SINCRONIZADO = "sincronizado"
    FALHA = "falha"
    DESCONECTADO = "desconectado"


class WhatsAppDeliveryStatus(str, Enum):
    ENVIADO = "enviado"
    FALHA = "falha"


class NfeStatus(str, Enum):
    EMITIDA = "emitida"
    CANCELADA = "cancelada"


class NfeEnvironment(str, Enum):
    HOMOLOGACAO = "homologacao"
    PRODUCAO = "producao"


class NfeProcessingStatus(str, Enum):
    PENDENTE_ENVIO = "pendente_envio"
    PROCESSANDO = "processando"
    AUTORIZADO = "autorizado"
    REJEITADO = "rejeitado"
    CANCELADO = "cancelado"
    ERRO_INTEGRACAO = "erro_integracao"
