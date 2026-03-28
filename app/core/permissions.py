from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from app.domain.enums import UserRole

PERMISSION_CATALOG: dict[str, list[tuple[str, str]]] = {
    "clientes": [
        ("customers.view", "Ver clientes"),
        ("customers.edit", "Criar e editar clientes"),
    ],
    "contratos": [
        ("contracts.view", "Ver contratos"),
        ("contracts.manage", "Criar e editar contratos"),
    ],
    "estoque": [
        ("stock.view", "Ver estoque"),
        ("stock.manage", "Cadastrar produtos"),
        ("stock.move", "Movimentar estoque"),
    ],
    "financeiro": [
        ("finance.view", "Ver financeiro"),
        ("finance.manage", "Lancar e editar financeiro"),
    ],
    "operacao": [
        ("work_orders.view", "Ver ordens de servico"),
        ("work_orders.manage", "Gerenciar ordens de servico"),
        ("appointments.view", "Ver agenda"),
        ("appointments.manage", "Gerenciar agenda"),
    ],
    "sistema": [
        ("settings.view", "Ver configuracoes"),
        ("settings.manage", "Alterar configuracoes"),
        ("users.manage", "Gerenciar usuarios"),
        ("records.delete", "Excluir registros"),
        ("provider_companies.manage", "Gerenciar empresas prestadoras"),
        ("licenses.manage", "Gerenciar licencas"),
        ("fiscal.view", "Ver fiscal e NF-e"),
        ("fiscal.manage", "Emitir e gerenciar NF-e"),
        ("integrations.manage", "Gerenciar integracoes"),
    ],
}


def _build_defaults(*granted_permissions: str) -> dict[str, bool]:
    defaults = {permission_key: False for groups in PERMISSION_CATALOG.values() for permission_key, _ in groups}
    for permission_key in granted_permissions:
        defaults[permission_key] = True
    return defaults


ROLE_DEFAULT_PERMISSIONS: dict[str, dict[str, bool]] = {
    UserRole.MASTER.value: {permission_key: True for groups in PERMISSION_CATALOG.values() for permission_key, _ in groups},
    UserRole.ADMIN.value: _build_defaults(
        "customers.view",
        "customers.edit",
        "contracts.view",
        "contracts.manage",
        "stock.view",
        "stock.manage",
        "stock.move",
        "finance.view",
        "finance.manage",
        "work_orders.view",
        "work_orders.manage",
        "appointments.view",
        "appointments.manage",
        "settings.view",
        "settings.manage",
        "users.manage",
        "records.delete",
        "fiscal.view",
        "fiscal.manage",
        "integrations.manage",
    ),
    UserRole.OPERADOR.value: _build_defaults(
        "customers.view",
        "customers.edit",
        "contracts.view",
        "stock.view",
        "work_orders.view",
        "work_orders.manage",
        "appointments.view",
        "appointments.manage",
        "fiscal.view",
    ),
}


def get_default_permissions_for_role(role: str) -> dict[str, bool]:
    return deepcopy(ROLE_DEFAULT_PERMISSIONS.get(role, ROLE_DEFAULT_PERMISSIONS[UserRole.OPERADOR.value]))


def normalize_permissions(role: str, raw_permissions: dict[str, Any] | None) -> dict[str, bool]:
    base_permissions = get_default_permissions_for_role(role)
    if role == UserRole.MASTER.value:
        return {permission_key: True for permission_key in base_permissions}
    if not raw_permissions:
        return base_permissions
    for permission_key in base_permissions:
        if permission_key in raw_permissions:
            base_permissions[permission_key] = bool(raw_permissions[permission_key])
    return base_permissions


def dump_permissions_json(role: str, raw_permissions: dict[str, Any] | None) -> str:
    return json.dumps(normalize_permissions(role, raw_permissions), sort_keys=True)


def load_permissions_json(role: str, payload: str | None) -> dict[str, bool]:
    if not payload:
        return get_default_permissions_for_role(role)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return get_default_permissions_for_role(role)
    if not isinstance(parsed, dict):
        return get_default_permissions_for_role(role)
    return normalize_permissions(role, parsed)


def has_permission(role: str, permissions: dict[str, bool] | None, permission_key: str) -> bool:
    if role == UserRole.MASTER.value:
        return True
    effective_permissions = normalize_permissions(role, permissions or {})
    return bool(effective_permissions.get(permission_key, False))
