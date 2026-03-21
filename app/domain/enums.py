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


class CashFlowType(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class WorkOrderStatus(str, Enum):
    ABERTA = "aberta"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class LicenseStatus(str, Enum):
    ATIVA = "ativa"
    EXPIRADA = "expirada"
    SUSPENSA = "suspensa"


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
