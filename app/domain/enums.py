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
