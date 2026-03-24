import csv
import json
from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from io import StringIO
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.application.schemas import (
    AddressLookupRead,
    CustomerCnpjLookupRead,
    FinancePaymentRequest,
    CustomerCreate,
    CustomerUpdate,
    FinanceEntryCreate,
    FinanceEntryUpdate,
    LicenseCreate,
    LicenseUpdate,
    PestCreate,
    PestUpdate,
    ProviderCompanyCreate,
    ProviderCompanyUpdate,
    ProductCreate,
    ProductCsvImportResult,
    ProductXmlImportResult,
    ProductUpdate,
    TechnicianCreate,
    TechnicianUpdate,
    UserCreate,
    UserUpdate,
    WorkOrderCreate,
    WorkOrderUpdate,
)
from app.core.exceptions import BusinessRuleViolation
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.enums import FinanceStatus
from app.infrastructure.models import (
    CashLedgerEntry,
    Customer,
    FinanceEntry,
    License,
    Pest,
    ProviderCompany,
    Product,
    Technician,
    User,
    WorkOrder,
    WorkOrderPhoto,
    WorkOrderPest,
    WorkOrderProduct,
)

MONEY_QUANTIZER = Decimal("0.01")
MAX_WORK_ORDER_PHOTO_BYTES = 5 * 1024 * 1024
MAX_WORK_ORDER_PHOTO_ITEMS = 8
ALLOWED_WORK_ORDER_PHOTO_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _money(value: Decimal) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(value).quantize(MONEY_QUANTIZER)


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _digits_only(value: Optional[str]) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _normalize_cnpj(value: Optional[str]) -> str:
    return _digits_only(value)


def _normalize_cep(value: Optional[str]) -> Optional[str]:
    digits = _digits_only(value)
    return digits or None


def _normalize_company_payload(payload: ProviderCompanyCreate) -> dict:
    data = payload.model_dump()
    data["cnpj"] = _normalize_cnpj(data.get("cnpj"))
    data["cep"] = _normalize_cep(data.get("cep"))
    data["estado"] = data.get("estado").upper() if data.get("estado") else None
    return data


def _normalize_customer_payload(payload) -> dict:
    data = payload.model_dump()
    data["cpf_cnpj"] = _normalize_cnpj(data.get("cpf_cnpj"))
    data["cep"] = _normalize_cep(data.get("cep"))
    data["estado"] = data.get("estado", "").upper()
    return data


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "SysPragas/3.1"})
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise BusinessRuleViolation("Consulta nao encontrou dados para o identificador informado.") from exc
        raise BusinessRuleViolation("Falha ao consultar o servico externo no momento.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BusinessRuleViolation("Falha ao consultar o servico externo no momento.") from exc


def _get_provider_company_or_fail(db: Session, provider_company_id: int) -> ProviderCompany:
    provider_company = db.query(ProviderCompany).filter(ProviderCompany.id == provider_company_id).first()
    if not provider_company:
        raise BusinessRuleViolation("Empresa prestadora nao encontrada.")
    return provider_company


def _serialize_user(user: User) -> User:
    if user.empresa_prestadora:
        user.empresa_prestadora_nome = user.empresa_prestadora.nome_fantasia or user.empresa_prestadora.razao_social
    else:
        user.empresa_prestadora_nome = None
    return user


def _serialize_license(license_entry: License) -> License:
    if license_entry.empresa_prestadora:
        license_entry.empresa_prestadora_nome = (
            license_entry.empresa_prestadora.nome_fantasia or license_entry.empresa_prestadora.razao_social
        )
    else:
        license_entry.empresa_prestadora_nome = None
    return license_entry


def _serialize_provider_company(provider_company: ProviderCompany) -> ProviderCompany:
    provider_company.usuarios_vinculados_ids = [user.id for user in provider_company.usuarios]
    provider_company.usuarios_vinculados_nomes = [user.nome for user in provider_company.usuarios]
    provider_company.google_connected = bool(
        provider_company.google_refresh_token or provider_company.google_access_token
    )
    return provider_company


def _get_current_license_for_company(db: Session, provider_company_id: Optional[int]) -> Optional[License]:
    query = db.query(License)
    if provider_company_id is None:
        query = query.filter(License.empresa_prestadora_id.is_(None))
    else:
        query = query.filter(License.empresa_prestadora_id == provider_company_id)
    return query.order_by(License.end_date.desc(), License.id.desc()).first()


def _add_months(base_date: date, months_to_add: int) -> date:
    month_index = (base_date.month - 1) + months_to_add
    year = base_date.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _split_installments(total: Decimal, installments: int) -> List[Decimal]:
    total_value = _money(total)
    base = (total_value / installments).quantize(MONEY_QUANTIZER)
    amounts = [base for _ in range(installments)]
    diff = total_value - sum(amounts)
    amounts[-1] = _money(amounts[-1] + diff)
    return amounts


def _finance_direction(entry: FinanceEntry) -> str:
    return "entrada" if entry.tipo == "receita" else "saida"


def _sync_finance_status(entry: FinanceEntry, today: Optional[date] = None) -> bool:
    today = today or date.today()
    original_status = entry.status
    saldo = _money(Decimal(entry.valor) - Decimal(entry.valor_pago))

    if saldo <= Decimal("0.00"):
        entry.valor_pago = _money(entry.valor)
        entry.status = FinanceStatus.PAGO.value
        if entry.data_pagamento is None:
            entry.data_pagamento = today
    elif entry.vencimento < today:
        entry.status = FinanceStatus.ATRASADO.value
    else:
        entry.status = FinanceStatus.PENDENTE.value

    return entry.status != original_status


def _sync_finance_statuses(db: Session, entries: Iterable[FinanceEntry]) -> None:
    changed = False
    for entry in entries:
        changed = _sync_finance_status(entry) or changed
    if changed:
        db.commit()


def _create_cash_ledger_entry(
    db: Session,
    entry: FinanceEntry,
    amount: Decimal,
    movement_date: date,
) -> CashLedgerEntry:
    ledger_entry = CashLedgerEntry(
        finance_entry_id=entry.id,
        tipo=_finance_direction(entry),
        origem=entry.origem,
        valor=_money(amount),
        data_movimento=movement_date,
        referencia=entry.referencia or entry.descricao,
    )
    db.add(ledger_entry)
    return ledger_entry


def _apply_finance_payment(
    db: Session,
    entry: FinanceEntry,
    amount: Optional[Decimal] = None,
    payment_date: Optional[date] = None,
) -> FinanceEntry:
    _sync_finance_status(entry)
    open_balance = _money(Decimal(entry.valor) - Decimal(entry.valor_pago))
    if open_balance <= Decimal("0.00"):
        raise BusinessRuleViolation("Este lancamento ja esta totalmente pago.")

    paid_amount = _money(amount if amount is not None else open_balance)
    if paid_amount <= Decimal("0.00"):
        raise BusinessRuleViolation("O valor informado para pagamento deve ser maior que zero.")
    if paid_amount > open_balance:
        raise BusinessRuleViolation("O valor informado excede o saldo em aberto.")

    entry.valor_pago = _money(Decimal(entry.valor_pago) + paid_amount)
    entry.data_pagamento = payment_date or date.today()
    _sync_finance_status(entry, today=entry.data_pagamento)
    _create_cash_ledger_entry(db, entry, paid_amount, entry.data_pagamento)
    return entry


def _validate_finance_payload(
    db: Session,
    payload: FinanceEntryCreate,
    current_entry: Optional[FinanceEntry] = None,
) -> None:
    if payload.cliente_id:
        _get_customer_or_fail(db, payload.cliente_id)
    if payload.os_id:
        _get_work_order_or_fail(db, payload.os_id)
        if _enum_value(payload.tipo) != "receita":
            raise BusinessRuleViolation("Lancamentos vinculados a OS devem ser do tipo receita.")
    if payload.nfe_id:
        from app.application.fiscal_services import _get_nfe_or_fail

        invoice = _get_nfe_or_fail(db, payload.nfe_id)
        if _enum_value(payload.tipo) != "receita":
            raise BusinessRuleViolation("Lancamentos vinculados a NF-e devem ser do tipo receita.")
        if payload.cliente_id and payload.cliente_id != invoice.cliente_id:
            raise BusinessRuleViolation("O cliente do lancamento financeiro deve ser o mesmo da NF-e vinculada.")
    if payload.parcela_atual > payload.total_parcelas:
        raise BusinessRuleViolation("A parcela atual nao pode ser maior que o total de parcelas.")
    if current_entry and _money(payload.valor) < _money(current_entry.valor_pago):
        raise BusinessRuleViolation("O valor total nao pode ser menor que o valor ja pago.")


def authenticate_user(db: Session, username: str, password: str) -> str:
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        raise BusinessRuleViolation("Credenciais invalidas.")
    ensure_license_allows_access(db, user)
    return create_access_token(subject=str(user.id), role=user.role)


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise BusinessRuleViolation("Usuario nao encontrado ou inativo.")
    return _serialize_user(user)


def _get_user_record_or_fail(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessRuleViolation("Usuario nao encontrado.")
    return user


def get_current_license(db: Session) -> Optional[License]:
    license_entry = db.query(License).order_by(License.end_date.desc(), License.id.desc()).first()
    return _serialize_license(license_entry) if license_entry else None


def license_is_valid(license_entry: Optional[License]) -> bool:
    if not license_entry:
        return False
    today = date.today()
    return (
        license_entry.status == "ativa"
        and license_entry.start_date <= today <= license_entry.end_date
    )


def ensure_license_allows_access(db: Session, user: User) -> None:
    if user.role == "master":
        return
    license_entry = _get_current_license_for_company(db, user.empresa_prestadora_id)
    if license_entry is None and user.empresa_prestadora_id is not None:
        raise BusinessRuleViolation("A empresa prestadora vinculada ao usuario nao possui licenca ativa cadastrada.")
    if license_entry is None:
        license_entry = get_current_license(db)
    if not license_is_valid(license_entry):
        raise BusinessRuleViolation("Licenca do sistema inativa, suspensa ou expirada.")


def _get_customer_or_fail(db: Session, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise BusinessRuleViolation("Cliente informado nao existe.")
    return customer


def _get_product_or_fail(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise BusinessRuleViolation(f"Produto {product_id} nao encontrado.")
    return product


def _parse_nfe_date(raw_value: Optional[str]) -> date:
    if not raw_value:
        raise BusinessRuleViolation("Nao foi possivel identificar a data de emissao no XML da nota.")
    cleaned = raw_value.strip()
    if "T" in cleaned:
        cleaned = cleaned.split("T", 1)[0]
    return date.fromisoformat(cleaned)


def _parse_decimal_input(value: Optional[str], field_name: str, default: Optional[Decimal] = None) -> Decimal:
    if value is None or str(value).strip() == "":
        if default is not None:
            return _money(default)
        raise BusinessRuleViolation(f"O campo '{field_name}' e obrigatorio no arquivo importado.")
    raw = str(value).strip()
    if "," in raw and "." in raw:
        normalized = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        normalized = raw.replace(",", ".")
    else:
        normalized = raw
    try:
        return _money(Decimal(normalized))
    except Exception as exc:
        raise BusinessRuleViolation(f"O campo '{field_name}' possui valor numerico invalido: {value}") from exc


def _parse_bool_input(value: Optional[str], default: bool = True) -> bool:
    if value is None or str(value).strip() == "":
        return default
    normalized = str(value).strip().lower()
    return normalized in {"1", "true", "sim", "s", "yes", "y"}


def _xml_find_text(node: ET.Element, tag_suffix: str) -> Optional[str]:
    for child in node.iter():
        if child.tag.endswith(tag_suffix):
            text = (child.text or "").strip()
            if text:
                return text
    return None


def _parse_invoice_xml(xml_content: bytes) -> dict:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise BusinessRuleViolation("XML da nota fiscal invalido.") from exc

    inf_nfe = None
    for node in root.iter():
        if node.tag.endswith("infNFe"):
            inf_nfe = node
            break
    if inf_nfe is None:
        raise BusinessRuleViolation("XML nao contem a estrutura infNFe esperada.")

    ide = next((node for node in inf_nfe if node.tag.endswith("ide")), None)
    emit = next((node for node in inf_nfe if node.tag.endswith("emit")), None)
    total = next((node for node in inf_nfe if node.tag.endswith("total")), None)
    if ide is None or emit is None or total is None:
        raise BusinessRuleViolation("XML da nota fiscal sem cabecalho completo para importacao.")

    icms_tot = next((node for node in total.iter() if node.tag.endswith("ICMSTot")), None)
    if icms_tot is None:
        raise BusinessRuleViolation("XML da nota fiscal sem totalizador ICMSTot.")

    chave_acesso = (inf_nfe.attrib.get("Id") or "").replace("NFe", "") or None
    nota_numero = _xml_find_text(ide, "nNF") or "SEM-NUMERO"
    data_emissao = _parse_nfe_date(_xml_find_text(ide, "dhEmi") or _xml_find_text(ide, "dEmi"))
    fornecedor_nome = _xml_find_text(emit, "xNome") or "Fornecedor nao informado"
    fornecedor_documento = _xml_find_text(emit, "CNPJ") or _xml_find_text(emit, "CPF")
    valor_total = _money(Decimal(_xml_find_text(icms_tot, "vNF") or "0"))

    items = []
    for det in [node for node in inf_nfe if node.tag.endswith("det")]:
        prod = next((node for node in det if node.tag.endswith("prod")), None)
        if prod is None:
            continue
        quantity = Decimal(_xml_find_text(prod, "qCom") or "0")
        if quantity <= 0:
            continue
        items.append(
            {
                "codigo": _xml_find_text(prod, "cProd") or "",
                "codigo_barras": _xml_find_text(prod, "cEAN") or "",
                "nome": _xml_find_text(prod, "xProd") or "Produto sem nome",
                "ncm": _xml_find_text(prod, "NCM") or "",
                "cfop": _xml_find_text(prod, "CFOP") or "",
                "unidade": _xml_find_text(prod, "uCom") or "UN",
                "quantidade": _money(quantity),
                "valor_unitario": _money(Decimal(_xml_find_text(prod, "vUnCom") or "0")),
                "valor_total": _money(Decimal(_xml_find_text(prod, "vProd") or "0")),
            }
        )

    if not items:
        raise BusinessRuleViolation("Nenhum item de produto foi encontrado no XML da nota.")

    return {
        "nota_numero": nota_numero,
        "chave_acesso": chave_acesso,
        "data_emissao": data_emissao,
        "fornecedor_nome": fornecedor_nome,
        "fornecedor_documento": fornecedor_documento,
        "valor_total": valor_total,
        "items": items,
    }


def _decode_csv_content(csv_content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return csv_content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise BusinessRuleViolation("Nao foi possivel decodificar o arquivo CSV.")


def _parse_products_csv(csv_content: bytes) -> dict:
    text = _decode_csv_content(csv_content)
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        class SimpleDialect(csv.Dialect):
            delimiter = ";"
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL
        dialect = SimpleDialect

    reader = csv.DictReader(StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise BusinessRuleViolation("O CSV esta vazio ou sem cabecalho.")

    required_columns = {"nome", "registro_ms", "quantidade_entrada"}
    normalized_fields = {field.strip() for field in reader.fieldnames if field}
    missing = required_columns - normalized_fields
    if missing:
        raise BusinessRuleViolation(f"CSV sem as colunas obrigatorias: {', '.join(sorted(missing))}.")

    rows = []
    for line_number, row in enumerate(reader, start=2):
        normalized_row = {str(key).strip(): (value.strip() if isinstance(value, str) else value) for key, value in row.items() if key}
        if not any(normalized_row.values()):
            continue
        rows.append((line_number, normalized_row))

    if not rows:
        raise BusinessRuleViolation("Nenhuma linha valida foi encontrada no CSV.")

    return {
        "rows": rows,
        "referencia_lote": f"CSV-{date.today().isoformat()}",
        "data_importacao": date.today(),
    }


def _find_product_for_import(db: Session, registro_ms: str, nome: str) -> Optional[Product]:
    product = db.query(Product).filter(Product.registro_ms == registro_ms).first()
    if product is None:
        product = db.query(Product).filter(Product.nome == nome).first()
    return product


def _get_pest_or_fail(db: Session, pest_id: int) -> Pest:
    pest = db.query(Pest).filter(Pest.id == pest_id).first()
    if not pest:
        raise BusinessRuleViolation(f"Praga {pest_id} nao encontrada.")
    return pest


def _get_technician_or_fail(db: Session, technician_id: int, require_active: bool = False) -> Technician:
    query = db.query(Technician).filter(Technician.id == technician_id)
    if require_active:
        query = query.filter(Technician.ativo.is_(True))
    technician = query.first()
    if not technician:
        raise BusinessRuleViolation("Tecnico responsavel nao encontrado ou inativo.")
    return technician


def _get_finance_entry_or_fail(db: Session, finance_entry_id: int) -> FinanceEntry:
    entry = db.query(FinanceEntry).filter(FinanceEntry.id == finance_entry_id).first()
    if not entry:
        raise BusinessRuleViolation("Lancamento financeiro nao encontrado.")
    _sync_finance_status(entry)
    return entry


def _clean_required_text(value: Optional[str], message: str) -> str:
    cleaned = " ".join(str(value or "").split()).strip()
    if not cleaned:
        raise BusinessRuleViolation(message)
    return cleaned


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def list_provider_companies(db: Session) -> List[ProviderCompany]:
    companies = db.query(ProviderCompany).options(joinedload(ProviderCompany.usuarios)).order_by(ProviderCompany.razao_social.asc()).all()
    return [_serialize_provider_company(item) for item in companies]


def get_provider_company(db: Session, provider_company_id: int) -> ProviderCompany:
    company = (
        db.query(ProviderCompany)
        .options(joinedload(ProviderCompany.usuarios), joinedload(ProviderCompany.licencas))
        .filter(ProviderCompany.id == provider_company_id)
        .first()
    )
    if not company:
        raise BusinessRuleViolation("Empresa prestadora nao encontrada.")
    return _serialize_provider_company(company)


def _sync_provider_company_users(db: Session, provider_company: ProviderCompany, user_ids: List[int]) -> None:
    selected_user_ids = set(int(user_id) for user_id in user_ids)
    current_users = db.query(User).filter(User.empresa_prestadora_id == provider_company.id).all()
    for user in current_users:
        if user.id not in selected_user_ids:
            user.empresa_prestadora_id = None

    if not selected_user_ids:
        return

    selected_users = db.query(User).filter(User.id.in_(selected_user_ids)).all()
    found_ids = {user.id for user in selected_users}
    missing_ids = selected_user_ids - found_ids
    if missing_ids:
        raise BusinessRuleViolation("Um ou mais usuarios selecionados nao foram encontrados para vinculo.")

    for user in selected_users:
        user.empresa_prestadora_id = provider_company.id


def create_provider_company(db: Session, payload: ProviderCompanyCreate) -> ProviderCompany:
    data = _normalize_company_payload(payload)
    if len(data["cnpj"]) != 14:
        raise BusinessRuleViolation("Informe um CNPJ valido para a empresa prestadora.")
    duplicate = db.query(ProviderCompany).filter(ProviderCompany.cnpj == data["cnpj"]).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe empresa prestadora cadastrada com este CNPJ.")
    user_ids = data.pop("usuarios_vinculados_ids", [])
    provider_company = ProviderCompany(**data)
    db.add(provider_company)
    db.flush()
    _sync_provider_company_users(db, provider_company, user_ids)
    return _serialize_provider_company(provider_company)


def update_provider_company(db: Session, provider_company_id: int, payload: ProviderCompanyUpdate) -> ProviderCompany:
    provider_company = _get_provider_company_or_fail(db, provider_company_id)
    data = _normalize_company_payload(payload)
    duplicate = (
        db.query(ProviderCompany)
        .filter(ProviderCompany.cnpj == data["cnpj"], ProviderCompany.id != provider_company_id)
        .first()
    )
    if duplicate:
        raise BusinessRuleViolation("Ja existe empresa prestadora cadastrada com este CNPJ.")

    user_ids = data.pop("usuarios_vinculados_ids", [])
    for field, value in data.items():
        setattr(provider_company, field, value)
    _sync_provider_company_users(db, provider_company, user_ids)
    db.commit()
    db.refresh(provider_company)
    return _serialize_provider_company(provider_company)


def delete_provider_company(db: Session, provider_company_id: int) -> None:
    provider_company = _get_provider_company_or_fail(db, provider_company_id)
    if provider_company.usuarios:
        raise BusinessRuleViolation("Nao e possivel excluir empresa prestadora com usuarios vinculados.")
    if provider_company.licencas:
        raise BusinessRuleViolation("Nao e possivel excluir empresa prestadora com licencas vinculadas.")
    db.delete(provider_company)
    db.commit()


def lookup_company_by_cnpj(cnpj: str) -> CustomerCnpjLookupRead:
    normalized_cnpj = _normalize_cnpj(cnpj)
    if len(normalized_cnpj) != 14:
        raise BusinessRuleViolation("Informe um CNPJ valido para consulta.")
    payload = _fetch_json(f"https://brasilapi.com.br/api/cnpj/v1/{normalized_cnpj}")
    if payload.get("message"):
        raise BusinessRuleViolation(payload["message"])
    return CustomerCnpjLookupRead(
        razao_social=payload.get("razao_social") or payload.get("nome_fantasia") or "",
        nome_fantasia=payload.get("nome_fantasia"),
        cnpj=normalized_cnpj,
        telefone=payload.get("ddd_telefone_1") or payload.get("ddd_telefone_2"),
        email=payload.get("email"),
        cep=_normalize_cep(payload.get("cep")),
        endereco=payload.get("logradouro"),
        numero=payload.get("numero"),
        complemento=payload.get("complemento"),
        bairro=payload.get("bairro"),
        cidade=payload.get("municipio"),
        estado=payload.get("uf"),
    )


def lookup_address_by_cep(cep: str) -> AddressLookupRead:
    normalized_cep = _normalize_cep(cep)
    if not normalized_cep or len(normalized_cep) != 8:
        raise BusinessRuleViolation("Informe um CEP valido para consulta.")
    payload = _fetch_json(f"https://viacep.com.br/ws/{normalized_cep}/json/")
    if payload.get("erro"):
        raise BusinessRuleViolation("CEP nao encontrado para consulta.")
    return AddressLookupRead(
        cep=normalized_cep,
        endereco=payload.get("logradouro") or "",
        bairro=payload.get("bairro"),
        cidade=payload.get("localidade") or "",
        estado=payload.get("uf") or "",
    )


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    data = _normalize_customer_payload(payload)
    duplicate = db.query(Customer).filter(Customer.cpf_cnpj == data["cpf_cnpj"]).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe cliente com este CPF/CNPJ.")
    customer = Customer(**data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def list_users(db: Session) -> List[User]:
    return [_serialize_user(item) for item in db.query(User).order_by(User.created_at.desc(), User.nome.asc()).all()]


def create_user(db: Session, payload: UserCreate) -> User:
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise BusinessRuleViolation("Ja existe usuario com este login.")

    provider_company_id = payload.empresa_prestadora_id
    if payload.nova_empresa_prestadora:
        provider_company = create_provider_company(db, payload.nova_empresa_prestadora)
        provider_company_id = provider_company.id
        if payload.licenca_inicial:
            license_payload = payload.licenca_inicial.model_dump(exclude={"empresa_prestadora_id"})
            create_license(
                db,
                LicenseCreate(
                    **license_payload,
                    empresa_prestadora_id=provider_company_id,
                ),
            )

    if payload.role != "master" and not provider_company_id:
        raise BusinessRuleViolation("Usuarios nao master devem estar vinculados a uma empresa prestadora.")

    if provider_company_id:
        _get_provider_company_or_fail(db, provider_company_id)

    active_users_count = db.query(User).filter(
        User.is_active.is_(True),
        User.empresa_prestadora_id == provider_company_id,
    ).count()
    license_entry = _get_current_license_for_company(db, provider_company_id) if payload.role != "master" else None
    max_users = license_entry.max_users if license_entry else 0
    if payload.is_active and payload.role != "master" and active_users_count >= max_users:
        raise BusinessRuleViolation("A licenca da empresa prestadora nao permite criar mais usuarios ativos.")

    user = User(
        nome=payload.nome,
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role.value,
        is_active=payload.is_active,
        empresa_prestadora_id=provider_company_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = _get_user_record_or_fail(db, user_id)
    duplicate = db.query(User).filter(User.username == payload.username, User.id != user_id).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe usuario com este login.")

    provider_company_id = payload.empresa_prestadora_id
    if payload.role != "master" and not provider_company_id:
        raise BusinessRuleViolation("Usuarios nao master devem estar vinculados a uma empresa prestadora.")
    if provider_company_id:
        _get_provider_company_or_fail(db, provider_company_id)

    active_users_count = db.query(User).filter(
        User.is_active.is_(True),
        User.id != user_id,
        User.empresa_prestadora_id == provider_company_id,
    ).count()
    license_entry = _get_current_license_for_company(db, provider_company_id) if payload.role != "master" else None
    max_users = license_entry.max_users if license_entry else 0
    if payload.is_active and payload.role != "master" and active_users_count >= max_users:
        raise BusinessRuleViolation("A licenca da empresa prestadora nao permite manter mais usuarios ativos.")

    user.nome = payload.nome
    user.username = payload.username
    user.role = payload.role.value
    user.is_active = payload.is_active
    user.empresa_prestadora_id = provider_company_id
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


def delete_user(db: Session, user_id: int) -> None:
    user = _get_user_record_or_fail(db, user_id)
    if user.role == "master":
        masters = db.query(User).filter(User.role == "master", User.is_active.is_(True)).count()
        if masters <= 1:
            raise BusinessRuleViolation("Nao e possivel excluir o ultimo usuario MASTER.")
    db.delete(user)
    db.commit()


def list_licenses(db: Session) -> List[License]:
    return [_serialize_license(item) for item in db.query(License).order_by(License.end_date.desc(), License.id.desc()).all()]


def create_license(db: Session, payload: LicenseCreate) -> License:
    if payload.end_date < payload.start_date:
        raise BusinessRuleViolation("A data final da licenca deve ser posterior ou igual a data inicial.")
    if payload.empresa_prestadora_id:
        _get_provider_company_or_fail(db, payload.empresa_prestadora_id)
    license_entry = License(**payload.model_dump())
    db.add(license_entry)
    db.commit()
    db.refresh(license_entry)
    return _serialize_license(license_entry)


def update_license(db: Session, license_id: int, payload: LicenseUpdate) -> License:
    license_entry = db.query(License).filter(License.id == license_id).first()
    if not license_entry:
        raise BusinessRuleViolation("Licenca nao encontrada.")
    if payload.end_date < payload.start_date:
        raise BusinessRuleViolation("A data final da licenca deve ser posterior ou igual a data inicial.")
    if payload.empresa_prestadora_id:
        _get_provider_company_or_fail(db, payload.empresa_prestadora_id)
    for field, value in payload.model_dump().items():
        setattr(license_entry, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(license_entry)
    return _serialize_license(license_entry)


def delete_license(db: Session, license_id: int) -> None:
    license_entry = db.query(License).filter(License.id == license_id).first()
    if not license_entry:
        raise BusinessRuleViolation("Licenca nao encontrada.")
    db.delete(license_entry)
    db.commit()


def list_customers(db: Session) -> List[Customer]:
    return db.query(Customer).order_by(Customer.razao_social.asc()).all()


def update_customer(db: Session, customer_id: int, payload: CustomerUpdate) -> Customer:
    customer = _get_customer_or_fail(db, customer_id)
    data = _normalize_customer_payload(payload)
    duplicate = (
        db.query(Customer)
        .filter(Customer.cpf_cnpj == data["cpf_cnpj"], Customer.id != customer_id)
        .first()
    )
    if duplicate:
        raise BusinessRuleViolation("Ja existe cliente com este CPF/CNPJ.")
    for field, value in data.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    customer = _get_customer_or_fail(db, customer_id)
    if customer.ordens_servico or customer.financeiros:
        raise BusinessRuleViolation("Nao e possivel excluir cliente com movimentacao vinculada.")
    db.delete(customer)
    db.commit()


def create_product(db: Session, payload: ProductCreate) -> Product:
    from app.application.fiscal_services import apply_tax_profile_to_product

    product = Product(**payload.model_dump())
    apply_tax_profile_to_product(
        db,
        product,
        ncm_code=payload.ncm,
        manual_override=payload.override_tributacao,
        manual_rates=payload.model_dump(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session) -> List[Product]:
    return db.query(Product).order_by(Product.nome.asc()).all()


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    from app.application.fiscal_services import apply_tax_profile_to_product

    product = _get_product_or_fail(db, product_id)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    apply_tax_profile_to_product(
        db,
        product,
        ncm_code=payload.ncm,
        manual_override=payload.override_tributacao,
        manual_rates=payload.model_dump(),
    )
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = _get_product_or_fail(db, product_id)
    if product.itens_ordem_servico:
        raise BusinessRuleViolation("Nao e possivel excluir produto ja utilizado em OS.")
    db.delete(product)
    db.commit()


def import_products_from_invoice_xml(
    db: Session,
    xml_content: bytes,
    create_finance_entry: bool = True,
) -> ProductXmlImportResult:
    invoice_data = _parse_invoice_xml(xml_content)
    reference = invoice_data["chave_acesso"] or f"NFE-{invoice_data['nota_numero']}"

    if db.query(FinanceEntry).filter(FinanceEntry.origem == "xml_nfe", FinanceEntry.referencia == reference).first():
        raise BusinessRuleViolation("Esta nota fiscal ja foi importada anteriormente.")

    created_count = 0
    updated_count = 0
    processed_items = []

    for index, item in enumerate(invoice_data["items"], start=1):
        product = None
        if item["codigo"]:
            product = db.query(Product).filter(Product.registro_ms == item["codigo"]).first()
        if product is None:
            product = db.query(Product).filter(Product.nome == item["nome"]).first()

        action = "atualizado"
        if product is None:
            product = Product(
                nome=item["nome"],
                principio_ativo="Nao informado",
                grupo_quimico="Nao informado",
                toxicidade="Nao informado",
                concentracao="Nao informado",
                registro_ms=item["codigo"] or item["codigo_barras"] or f"XML-{invoice_data['nota_numero']}-{index}",
                ncm=item["ncm"] or None,
                estoque_atual=Decimal("0.00"),
                estoque_minimo=Decimal("0.00"),
            )
            db.add(product)
            db.flush()
            created_count += 1
            action = "criado"
        else:
            updated_count += 1

        if item.get("ncm"):
            try:
                from app.application.fiscal_services import apply_tax_profile_to_product

                apply_tax_profile_to_product(db, product, ncm_code=item["ncm"], manual_override=False)
            except BusinessRuleViolation:
                product.ncm = item["ncm"]

        product.estoque_atual = _money(Decimal(product.estoque_atual) + Decimal(item["quantidade"]))

        processed_items.append(
            {
                "nome": item["nome"],
                "codigo": item["codigo"] or product.registro_ms,
                "quantidade": item["quantidade"],
                "produto_id": product.id,
                "acao": action,
            }
        )

    finance_entry_id = None
    if create_finance_entry:
        finance_entry = FinanceEntry(
            tipo="despesa",
            descricao=f"Compra por XML NF {invoice_data['nota_numero']} - {invoice_data['fornecedor_nome']}",
            valor=invoice_data["valor_total"],
            valor_pago=Decimal("0.00"),
            vencimento=invoice_data["data_emissao"],
            status=FinanceStatus.PENDENTE.value,
            categoria="Compra de estoque",
            fornecedor_nome=invoice_data["fornecedor_nome"],
            origem="xml_nfe",
            referencia=reference,
            total_parcelas=1,
            parcela_atual=1,
            observacoes=f"Importado automaticamente do XML da NF {invoice_data['nota_numero']}.",
        )
        db.add(finance_entry)
        db.flush()
        finance_entry_id = finance_entry.id

    db.commit()

    return ProductXmlImportResult(
        nota_numero=invoice_data["nota_numero"],
        chave_acesso=invoice_data["chave_acesso"],
        fornecedor_nome=invoice_data["fornecedor_nome"],
        fornecedor_documento=invoice_data["fornecedor_documento"],
        data_emissao=invoice_data["data_emissao"],
        valor_total=invoice_data["valor_total"],
        produtos_processados=len(processed_items),
        produtos_criados=created_count,
        produtos_atualizados=updated_count,
        financeiro_criado=create_finance_entry,
        finance_entry_id=finance_entry_id,
        itens=processed_items,
    )


def import_products_from_csv(
    db: Session,
    csv_content: bytes,
    create_finance_entry: bool = True,
) -> ProductCsvImportResult:
    parsed = _parse_products_csv(csv_content)
    created_count = 0
    updated_count = 0
    finance_count = 0
    finance_total = Decimal("0.00")
    processed_items = []

    for line_number, row in parsed["rows"]:
        nome = row.get("nome") or ""
        registro_ms = row.get("registro_ms") or ""
        if not nome or not registro_ms:
            raise BusinessRuleViolation(f"Linha {line_number}: os campos nome e registro_ms sao obrigatorios.")

        quantidade_entrada = _parse_decimal_input(row.get("quantidade_entrada"), f"quantidade_entrada (linha {line_number})")
        estoque_minimo = _parse_decimal_input(row.get("estoque_minimo"), f"estoque_minimo (linha {line_number})", Decimal("0.00"))
        custo_total = _parse_decimal_input(row.get("custo_total"), f"custo_total (linha {line_number})", Decimal("0.00"))
        data_entrada = date.fromisoformat(row["data_entrada"]) if row.get("data_entrada") else parsed["data_importacao"]
        registrar_financeiro_linha = create_finance_entry and _parse_bool_input(row.get("registrar_financeiro"), True)
        fornecedor_nome = row.get("fornecedor_nome") or None
        referencia = row.get("referencia") or f"{parsed['referencia_lote']}-L{line_number}"
        categoria_financeira = row.get("categoria_financeira") or "Compra de estoque"
        observacoes = row.get("observacoes") or None

        product = _find_product_for_import(db, registro_ms, nome)
        action = "atualizado"
        if product is None:
            product = Product(
                nome=nome,
                principio_ativo=row.get("principio_ativo") or "Nao informado",
                grupo_quimico=row.get("grupo_quimico") or "Nao informado",
                toxicidade=row.get("toxicidade") or "Nao informado",
                concentracao=row.get("concentracao") or "Nao informado",
                registro_ms=registro_ms,
                ncm=row.get("ncm") or None,
                estoque_atual=Decimal("0.00"),
                estoque_minimo=estoque_minimo,
            )
            db.add(product)
            db.flush()
            created_count += 1
            action = "criado"
        else:
            updated_count += 1
            if row.get("principio_ativo"):
                product.principio_ativo = row["principio_ativo"]
            if row.get("grupo_quimico"):
                product.grupo_quimico = row["grupo_quimico"]
            if row.get("toxicidade"):
                product.toxicidade = row["toxicidade"]
            if row.get("concentracao"):
                product.concentracao = row["concentracao"]
            product.estoque_minimo = estoque_minimo

        if row.get("ncm"):
            try:
                from app.application.fiscal_services import apply_tax_profile_to_product

                apply_tax_profile_to_product(db, product, ncm_code=row.get("ncm"), manual_override=False)
            except BusinessRuleViolation:
                product.ncm = row.get("ncm")

        product.estoque_atual = _money(Decimal(product.estoque_atual) + quantidade_entrada)

        finance_entry_id = None
        if registrar_financeiro_linha and custo_total > Decimal("0.00"):
            finance_entry = FinanceEntry(
                tipo="despesa",
                descricao=f"Entrada CSV - {nome}",
                valor=custo_total,
                valor_pago=Decimal("0.00"),
                vencimento=data_entrada,
                status=FinanceStatus.PENDENTE.value,
                categoria=categoria_financeira,
                fornecedor_nome=fornecedor_nome,
                origem="csv_import",
                referencia=referencia,
                total_parcelas=1,
                parcela_atual=1,
                observacoes=observacoes or f"Importado por CSV na linha {line_number}.",
            )
            db.add(finance_entry)
            db.flush()
            finance_entry_id = finance_entry.id
            finance_count += 1
            finance_total = _money(finance_total + custo_total)

        processed_items.append(
            {
                "nome": nome,
                "registro_ms": registro_ms,
                "quantidade_entrada": quantidade_entrada,
                "custo_total": custo_total,
                "produto_id": product.id,
                "finance_entry_id": finance_entry_id,
                "acao": action,
            }
        )

    db.commit()

    fornecedor_padrao = None
    if processed_items:
        supplier_values = [row.get("fornecedor_nome") for _, row in parsed["rows"] if row.get("fornecedor_nome")]
        fornecedor_padrao = supplier_values[0] if supplier_values else None

    return ProductCsvImportResult(
        referencia_lote=parsed["referencia_lote"],
        fornecedor_padrao=fornecedor_padrao,
        data_importacao=parsed["data_importacao"],
        produtos_processados=len(processed_items),
        produtos_criados=created_count,
        produtos_atualizados=updated_count,
        lancamentos_financeiros=finance_count,
        valor_financeiro_total=_money(finance_total),
        itens=processed_items,
    )


def create_pest(db: Session, payload: PestCreate) -> Pest:
    pest = Pest(**payload.model_dump())
    db.add(pest)
    db.commit()
    db.refresh(pest)
    return pest


def list_pests(db: Session) -> List[Pest]:
    return db.query(Pest).order_by(Pest.nome_comum.asc()).all()


def update_pest(db: Session, pest_id: int, payload: PestUpdate) -> Pest:
    pest = _get_pest_or_fail(db, pest_id)
    for field, value in payload.model_dump().items():
        setattr(pest, field, value)
    db.commit()
    db.refresh(pest)
    return pest


def delete_pest(db: Session, pest_id: int) -> None:
    pest = _get_pest_or_fail(db, pest_id)
    if pest.ordens_servico:
        raise BusinessRuleViolation("Nao e possivel excluir praga vinculada a OS.")
    db.delete(pest)
    db.commit()


def create_technician(db: Session, payload: TechnicianCreate) -> Technician:
    duplicate = db.query(Technician).filter(Technician.registro == payload.registro).first()
    if duplicate:
        raise BusinessRuleViolation("Ja existe tecnico com este registro.")
    technician = Technician(**payload.model_dump())
    db.add(technician)
    db.commit()
    db.refresh(technician)
    return technician


def list_technicians(db: Session) -> List[Technician]:
    return db.query(Technician).order_by(Technician.nome.asc()).all()


def update_technician(db: Session, technician_id: int, payload: TechnicianUpdate) -> Technician:
    technician = _get_technician_or_fail(db, technician_id)
    duplicate = (
        db.query(Technician)
        .filter(Technician.registro == payload.registro, Technician.id != technician_id)
        .first()
    )
    if duplicate:
        raise BusinessRuleViolation("Ja existe tecnico com este registro.")
    for field, value in payload.model_dump().items():
        setattr(technician, field, value)
    db.commit()
    db.refresh(technician)
    return technician


def delete_technician(db: Session, technician_id: int) -> None:
    technician = _get_technician_or_fail(db, technician_id)
    if technician.ordens_servico:
        raise BusinessRuleViolation("Nao e possivel excluir tecnico com OS vinculada.")
    db.delete(technician)
    db.commit()


def create_finance_entry(db: Session, payload: FinanceEntryCreate) -> FinanceEntry:
    _validate_finance_payload(db, payload)
    reference = payload.referencia or f"FIN-{int(datetime.now(timezone.utc).timestamp())}"
    installments = _split_installments(payload.valor, payload.total_parcelas)
    created_entries: List[FinanceEntry] = []

    for index, installment_value in enumerate(installments, start=1):
        due_date = _add_months(payload.vencimento, index - 1)
        entry = FinanceEntry(
            tipo=_enum_value(payload.tipo),
            descricao=payload.descricao if payload.total_parcelas == 1 else f"{payload.descricao} ({index}/{payload.total_parcelas})",
            valor=_money(installment_value),
            valor_pago=Decimal("0.00"),
            vencimento=due_date,
            categoria=payload.categoria,
            fornecedor_nome=payload.fornecedor_nome,
            origem=payload.origem,
            referencia=reference,
            parcela_atual=index,
            total_parcelas=payload.total_parcelas,
            observacoes=payload.observacoes,
            cliente_id=payload.cliente_id,
            os_id=payload.os_id,
            nfe_id=payload.nfe_id,
        )
        db.add(entry)
        created_entries.append(entry)

    db.flush()
    if payload.status == FinanceStatus.PAGO:
        for entry in created_entries:
            _apply_finance_payment(db, entry, entry.valor, payload.vencimento)

    db.commit()
    db.refresh(created_entries[0])
    return created_entries[0]


def list_finance_entries(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    cliente_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    tipo: Optional[str] = None,
    search: Optional[str] = None,
) -> List[FinanceEntry]:
    query = db.query(FinanceEntry)
    if start_date:
        query = query.filter(FinanceEntry.vencimento >= start_date)
    if end_date:
        query = query.filter(FinanceEntry.vencimento <= end_date)
    if cliente_id:
        query = query.filter(FinanceEntry.cliente_id == cliente_id)
    if status_filter:
        query = query.filter(FinanceEntry.status == status_filter)
    if tipo:
        query = query.filter(FinanceEntry.tipo == tipo)
    if search:
        lookup = search.strip()
        query = query.filter(
            (FinanceEntry.descricao.ilike(f"%{lookup}%"))
            | (FinanceEntry.referencia.ilike(f"%{lookup}%"))
            | (FinanceEntry.fornecedor_nome.ilike(f"%{lookup}%"))
        )
    entries = query.order_by(FinanceEntry.vencimento.asc(), FinanceEntry.id.desc()).all()
    _sync_finance_statuses(db, entries)
    return entries


def update_finance_entry(db: Session, finance_entry_id: int, payload: FinanceEntryUpdate) -> FinanceEntry:
    entry = _get_finance_entry_or_fail(db, finance_entry_id)
    if entry.recibo_id:
        raise BusinessRuleViolation("Lancamentos gerados por recibo devem ser alterados pelo proprio recibo.")
    if entry.os_id:
        raise BusinessRuleViolation("Lancamentos gerados por OS devem ser alterados pela propria ordem de servico.")
    if entry.nfe_id:
        raise BusinessRuleViolation("Lancamentos gerados por NF-e devem ser alterados pela propria nota fiscal.")
    _validate_finance_payload(db, payload, current_entry=entry)
    requested_status = _enum_value(payload.status)
    for field, value in payload.model_dump().items():
        setattr(entry, field, _enum_value(value))
    if requested_status == FinanceStatus.PAGO.value and _money(entry.valor_pago) < _money(entry.valor):
        _apply_finance_payment(db, entry, _money(entry.valor) - _money(entry.valor_pago), date.today())
    else:
        _sync_finance_status(entry)
    db.commit()
    db.refresh(entry)
    return entry


def mark_finance_entry_as_paid(
    db: Session,
    finance_entry_id: int,
    payload: Optional[FinancePaymentRequest] = None,
) -> FinanceEntry:
    entry = _get_finance_entry_or_fail(db, finance_entry_id)
    payment_payload = payload or FinancePaymentRequest()
    _apply_finance_payment(db, entry, payment_payload.valor, payment_payload.data_pagamento)
    db.commit()
    db.refresh(entry)
    return entry


def delete_finance_entry(db: Session, finance_entry_id: int) -> None:
    entry = _get_finance_entry_or_fail(db, finance_entry_id)
    if entry.recibo_id:
        raise BusinessRuleViolation("Lancamentos gerados por recibo devem ser excluidos pelo proprio recibo.")
    if entry.os_id:
        raise BusinessRuleViolation("Lancamentos gerados por OS devem ser excluidos pela propria ordem de servico.")
    if entry.nfe_id:
        raise BusinessRuleViolation("Lancamentos gerados por NF-e devem ser excluidos pela propria nota fiscal.")
    if entry.status == FinanceStatus.PAGO.value or Decimal(entry.valor_pago) > 0:
        raise BusinessRuleViolation("Nao e permitido excluir registros financeiros pagos ou com baixa parcial.")
    db.delete(entry)
    db.commit()


def list_cash_ledger_entries(db: Session) -> List[CashLedgerEntry]:
    return db.query(CashLedgerEntry).order_by(CashLedgerEntry.data_movimento.desc(), CashLedgerEntry.id.desc()).all()


def get_finance_dashboard(db: Session) -> dict:
    entries = db.query(FinanceEntry).order_by(FinanceEntry.id.asc()).all()
    _sync_finance_statuses(db, entries)
    ledger_entries = list_cash_ledger_entries(db)

    total_a_receber = sum(
        (_money(Decimal(entry.valor) - Decimal(entry.valor_pago)) for entry in entries if entry.tipo == "receita"),
        Decimal("0.00"),
    )
    total_a_pagar = sum(
        (_money(Decimal(entry.valor) - Decimal(entry.valor_pago)) for entry in entries if entry.tipo == "despesa"),
        Decimal("0.00"),
    )
    total_entradas = sum((Decimal(item.valor) for item in ledger_entries if item.tipo == "entrada"), Decimal("0.00"))
    total_saidas = sum((Decimal(item.valor) for item in ledger_entries if item.tipo == "saida"), Decimal("0.00"))
    inadimplentes = [
        entry for entry in entries
        if entry.tipo == "receita" and entry.status == FinanceStatus.ATRASADO.value and entry.saldo_aberto > 0
    ]
    inadimplencia_valor = sum((Decimal(entry.saldo_aberto) for entry in inadimplentes), Decimal("0.00"))

    return {
        "total_a_receber": _money(total_a_receber),
        "total_a_pagar": _money(total_a_pagar),
        "saldo_atual": _money(total_entradas - total_saidas),
        "inadimplencia_quantidade": len(inadimplentes),
        "inadimplencia_valor": _money(inadimplencia_valor),
    }


def _work_order_query(db: Session):
    return db.query(WorkOrder).options(
        joinedload(WorkOrder.cliente),
        joinedload(WorkOrder.tecnico),
        joinedload(WorkOrder.produtos).joinedload(WorkOrderProduct.produto),
        joinedload(WorkOrder.pragas).joinedload(WorkOrderPest.praga),
        joinedload(WorkOrder.fotos),
        joinedload(WorkOrder.financeiros),
    )


def _get_work_order_or_fail(db: Session, work_order_id: int) -> WorkOrder:
    work_order = _work_order_query(db).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise BusinessRuleViolation("Ordem de servico nao encontrada.")
    return work_order


def _validate_work_order_payload(
    db: Session,
    payload: WorkOrderCreate,
    current_work_order_id: Optional[int] = None,
) -> tuple[Customer, dict]:
    normalized_number = _clean_required_text(payload.numero, "Informe o numero da ordem de servico.")
    normalized_location = _clean_required_text(payload.local_execucao, "Informe o local de execucao da ordem de servico.")
    normalized_notes = _clean_optional_text(payload.observacoes)

    if payload.garantia_ate < payload.data_execucao:
        raise BusinessRuleViolation("A garantia deve possuir data limite igual ou posterior a execucao.")
    if payload.hora_fim and payload.hora_fim <= payload.hora_inicio:
        raise BusinessRuleViolation("A hora final deve ser posterior a hora inicial.")

    duplicate_query = db.query(WorkOrder).filter(WorkOrder.numero == normalized_number)
    if current_work_order_id is not None:
        duplicate_query = duplicate_query.filter(WorkOrder.id != current_work_order_id)
    if duplicate_query.first():
        raise BusinessRuleViolation("Ja existe ordem de servico com este numero.")

    customer = _get_customer_or_fail(db, payload.cliente_id)
    _get_technician_or_fail(db, payload.tecnico_id, require_active=True)

    target_status = _enum_value(payload.status)
    if not payload.produtos and target_status in {"em_execucao", "concluida"}:
        raise BusinessRuleViolation(
            "A OS precisa possuir ao menos um produto antes de ser marcada como em execucao ou concluida."
        )

    seen_product_ids = set()
    for item in payload.produtos:
        if item.produto_id in seen_product_ids:
            raise BusinessRuleViolation("Nao adicione o mesmo produto mais de uma vez na OS.")
        seen_product_ids.add(item.produto_id)
        _clean_required_text(item.diluicao, "Informe a diluicao de todos os produtos da ordem.")

    seen_pest_ids = set()
    for pest_id in payload.pragas_ids:
        if pest_id in seen_pest_ids:
            raise BusinessRuleViolation("A mesma praga nao pode ser selecionada mais de uma vez.")
        seen_pest_ids.add(pest_id)
        _get_pest_or_fail(db, pest_id)

    return customer, {
        "numero": normalized_number,
        "local_execucao": normalized_location,
        "observacoes": normalized_notes,
    }


def _restore_stock(work_order: WorkOrder) -> None:
    for item in work_order.produtos:
        item.produto.estoque_atual = Decimal(item.produto.estoque_atual) + Decimal(item.quantidade)


def _apply_work_order_products(
    db: Session,
    work_order: WorkOrder,
    product_items: Iterable,
) -> None:
    for item in product_items:
        product = _get_product_or_fail(db, item.produto_id)
        if Decimal(product.estoque_atual) < item.quantidade:
            raise BusinessRuleViolation(f"Estoque insuficiente para o produto '{product.nome}'.")
        product.estoque_atual = Decimal(product.estoque_atual) - item.quantidade
        db.add(
            WorkOrderProduct(
                os_id=work_order.id,
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                diluicao=item.diluicao,
            )
        )


def _sync_work_order_pests(db: Session, work_order: WorkOrder, pest_ids: List[int]) -> None:
    for item in list(work_order.pragas):
        db.delete(item)
    db.flush()
    for pest_id in pest_ids:
        _get_pest_or_fail(db, pest_id)
        db.add(WorkOrderPest(os_id=work_order.id, praga_id=pest_id))


def _sync_work_order_finance(
    db: Session,
    work_order: WorkOrder,
    customer: Customer,
    gerar_financeiro: bool,
    valor_servico: Decimal,
) -> None:
    linked_entries = list(work_order.financeiros)
    if gerar_financeiro and valor_servico > 0:
        entry = linked_entries[0] if linked_entries else FinanceEntry(os_id=work_order.id)
        if _money(valor_servico) < _money(entry.valor_pago):
            raise BusinessRuleViolation("Nao e possivel reduzir o valor da OS abaixo do que ja foi recebido.")
        entry.tipo = "receita"
        entry.descricao = f"Receita da OS {work_order.numero} - {customer.razao_social}"
        entry.valor = _money(valor_servico)
        entry.valor_pago = _money(entry.valor_pago)
        entry.vencimento = work_order.data_execucao
        entry.categoria = "ordem_servico"
        entry.origem = "ordem_servico"
        entry.referencia = f"OS-{work_order.numero}"
        entry.cliente_id = customer.id
        entry.os_id = work_order.id
        _sync_finance_status(entry)
        db.add(entry)
        for extra in linked_entries[1:]:
            if Decimal(extra.valor_pago) > 0:
                raise BusinessRuleViolation("Nao e possivel remover parcelas financeiras da OS que ja possuem baixa.")
            db.delete(extra)
    else:
        for entry in linked_entries:
            if Decimal(entry.valor_pago) > 0:
                raise BusinessRuleViolation("Nao e possivel remover o financeiro automatico de uma OS com recebimento registrado.")
            db.delete(entry)


def create_work_order(db: Session, payload: WorkOrderCreate, current_user_id: Optional[int] = None) -> WorkOrder:
    from app.application.scheduling_services import _sync_google_for_appointment, get_appointment, sync_work_order_appointment
    from app.domain.enums import AppointmentStatus
    from app.modules.whatsapp.service import send_appointment_whatsapp_message

    customer, normalized = _validate_work_order_payload(db, payload)

    work_order = WorkOrder(
        numero=normalized["numero"],
        cliente_id=payload.cliente_id,
        tecnico_id=payload.tecnico_id,
        data_execucao=payload.data_execucao,
        hora_inicio=payload.hora_inicio,
        hora_fim=payload.hora_fim,
        local_execucao=normalized["local_execucao"],
        observacoes=normalized["observacoes"],
        garantia_ate=payload.garantia_ate,
        status=payload.status.value,
        valor_servico=payload.valor_servico,
    )
    db.add(work_order)
    db.flush()

    _apply_work_order_products(db, work_order, payload.produtos)
    _sync_work_order_pests(db, work_order, payload.pragas_ids)
    _sync_work_order_finance(db, work_order, customer, payload.gerar_financeiro, payload.valor_servico)
    appointment, appointment_created = sync_work_order_appointment(
        db,
        work_order,
        current_user_id=current_user_id,
        generate_appointment=payload.gerar_agendamento,
        service_type=payload.tipo_servico_agendamento,
        duration_minutes=payload.duracao_prevista_minutos,
        internal_notes=payload.observacoes_internas_agendamento,
        technical_instructions=payload.instrucoes_tecnicas_agendamento,
        follow_up_notes=payload.retorno_revisita_agendamento,
        sync_google=payload.sincronizar_google_agenda,
    )

    db.commit()
    if get_settings().whatsapp_enabled and appointment_created and appointment:
        appointment = send_appointment_whatsapp_message(
            db,
            appointment.id,
            current_user_id=current_user_id,
            automatic=True,
        )
    if appointment and appointment.sincronizar_google:
        appointment = get_appointment(db, appointment.id)
        _sync_google_for_appointment(
            db,
            appointment,
            remove_event=appointment.status in {AppointmentStatus.CANCELADO.value, AppointmentStatus.NAO_REALIZADO.value},
            user_id=current_user_id,
        )
        db.commit()
    return get_work_order(db, work_order.id)


def list_work_orders(db: Session) -> List[WorkOrder]:
    return _work_order_query(db).order_by(WorkOrder.data_execucao.desc(), WorkOrder.numero.desc()).all()


def get_work_order(db: Session, work_order_id: int) -> WorkOrder:
    return _get_work_order_or_fail(db, work_order_id)


def update_work_order(
    db: Session,
    work_order_id: int,
    payload: WorkOrderUpdate,
    current_user_id: Optional[int] = None,
) -> WorkOrder:
    from app.application.scheduling_services import _sync_google_for_appointment, get_appointment, sync_work_order_appointment
    from app.domain.enums import AppointmentStatus
    from app.modules.whatsapp.service import send_appointment_whatsapp_message

    work_order = _get_work_order_or_fail(db, work_order_id)
    customer, normalized = _validate_work_order_payload(db, payload, current_work_order_id=work_order_id)

    _restore_stock(work_order)
    for item in list(work_order.produtos):
        db.delete(item)
    db.flush()

    work_order.numero = normalized["numero"]
    work_order.cliente_id = payload.cliente_id
    work_order.tecnico_id = payload.tecnico_id
    work_order.data_execucao = payload.data_execucao
    work_order.hora_inicio = payload.hora_inicio
    work_order.hora_fim = payload.hora_fim
    work_order.local_execucao = normalized["local_execucao"]
    work_order.observacoes = normalized["observacoes"]
    work_order.garantia_ate = payload.garantia_ate
    work_order.status = payload.status.value
    work_order.valor_servico = payload.valor_servico

    _apply_work_order_products(db, work_order, payload.produtos)
    _sync_work_order_pests(db, work_order, payload.pragas_ids)
    _sync_work_order_finance(db, work_order, customer, payload.gerar_financeiro, payload.valor_servico)
    appointment, appointment_created = sync_work_order_appointment(
        db,
        work_order,
        current_user_id=current_user_id,
        generate_appointment=payload.gerar_agendamento,
        service_type=payload.tipo_servico_agendamento,
        duration_minutes=payload.duracao_prevista_minutos,
        internal_notes=payload.observacoes_internas_agendamento,
        technical_instructions=payload.instrucoes_tecnicas_agendamento,
        follow_up_notes=payload.retorno_revisita_agendamento,
        sync_google=payload.sincronizar_google_agenda,
    )

    db.commit()
    if get_settings().whatsapp_enabled and appointment_created and appointment:
        appointment = send_appointment_whatsapp_message(
            db,
            appointment.id,
            current_user_id=current_user_id,
            automatic=True,
        )
    if appointment and appointment.sincronizar_google:
        appointment = get_appointment(db, appointment.id)
        _sync_google_for_appointment(
            db,
            appointment,
            remove_event=appointment.status in {AppointmentStatus.CANCELADO.value, AppointmentStatus.NAO_REALIZADO.value},
            user_id=current_user_id,
        )
        db.commit()
    return get_work_order(db, work_order.id)


def delete_work_order(db: Session, work_order_id: int) -> None:
    work_order = _get_work_order_or_fail(db, work_order_id)
    _restore_stock(work_order)
    for entry in list(work_order.financeiros):
        if Decimal(entry.valor_pago) > 0:
            raise BusinessRuleViolation("Nao e possivel excluir OS com recebimento financeiro ja registrado.")
        db.delete(entry)
    db.delete(work_order)
    db.commit()


def mark_work_order_as_completed(db: Session, work_order_id: int, current_user_id: Optional[int] = None) -> WorkOrder:
    from app.application.schemas import AppointmentStatusUpdate
    from app.application.scheduling_services import update_appointment_status
    from app.domain.enums import AppointmentSource, AppointmentStatus
    from app.infrastructure.models import Appointment

    work_order = _get_work_order_or_fail(db, work_order_id)
    if work_order.status == "cancelada":
        raise BusinessRuleViolation("Nao e possivel efetuar uma OS cancelada.")
    work_order.status = "concluida"
    db.commit()
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.os_id == work_order_id,
            Appointment.origem == AppointmentSource.ORDEM_SERVICO.value,
            Appointment.agendamento_pai_id.is_(None),
        )
        .order_by(Appointment.id.desc())
        .first()
    )
    if appointment and appointment.status != AppointmentStatus.CONCLUIDO.value:
        update_appointment_status(
            db,
            appointment.id,
            AppointmentStatusUpdate(
                status=AppointmentStatus.CONCLUIDO,
                detalhes=f"OS {work_order.numero} concluida a partir do modulo de ordens de servico.",
            ),
            current_user_id=current_user_id,
        )
    return get_work_order(db, work_order.id)


def settle_work_order(db: Session, work_order_id: int, current_user_id: Optional[int] = None) -> WorkOrder:
    from app.application.schemas import AppointmentStatusUpdate
    from app.application.scheduling_services import update_appointment_status
    from app.domain.enums import AppointmentSource, AppointmentStatus
    from app.infrastructure.models import Appointment

    work_order = _get_work_order_or_fail(db, work_order_id)
    if work_order.status == "cancelada":
        raise BusinessRuleViolation("Nao e possivel dar baixa em uma OS cancelada.")
    work_order.status = "concluida"
    for entry in list(work_order.financeiros):
        if _money(entry.saldo_aberto) > Decimal("0.00"):
            _apply_finance_payment(db, entry)
    db.commit()
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.os_id == work_order_id,
            Appointment.origem == AppointmentSource.ORDEM_SERVICO.value,
            Appointment.agendamento_pai_id.is_(None),
        )
        .order_by(Appointment.id.desc())
        .first()
    )
    if appointment and appointment.status != AppointmentStatus.CONCLUIDO.value:
        update_appointment_status(
            db,
            appointment.id,
            AppointmentStatusUpdate(
                status=AppointmentStatus.CONCLUIDO,
                detalhes=f"OS {work_order.numero} baixada e finalizada pelo financeiro.",
            ),
            current_user_id=current_user_id,
        )
    return get_work_order(db, work_order.id)


def _get_work_order_photo_or_fail(db: Session, photo_id: int) -> WorkOrderPhoto:
    photo = db.query(WorkOrderPhoto).filter(WorkOrderPhoto.id == photo_id).first()
    if not photo:
        raise BusinessRuleViolation("Foto da ordem de servico nao encontrada.")
    return photo


def add_work_order_photos(db: Session, work_order_id: int, files: Iterable[tuple[str, str, bytes]]) -> WorkOrder:
    work_order = _get_work_order_or_fail(db, work_order_id)
    prepared_files = list(files)
    if not prepared_files:
        raise BusinessRuleViolation("Selecione pelo menos uma foto para anexar na ordem de servico.")

    if len(work_order.fotos) + len(prepared_files) > MAX_WORK_ORDER_PHOTO_ITEMS:
        raise BusinessRuleViolation(f"A ordem permite no maximo {MAX_WORK_ORDER_PHOTO_ITEMS} fotos.")

    for filename, content_type, image_bytes in prepared_files:
        normalized_type = (content_type or "").lower()
        if normalized_type not in ALLOWED_WORK_ORDER_PHOTO_TYPES:
            raise BusinessRuleViolation("Envie fotos JPG, PNG ou WEBP.")
        if not image_bytes:
            raise BusinessRuleViolation("Uma das fotos enviadas esta vazia.")
        if len(image_bytes) > MAX_WORK_ORDER_PHOTO_BYTES:
            raise BusinessRuleViolation("Cada foto deve possuir no maximo 5 MB.")

        db.add(
            WorkOrderPhoto(
                os_id=work_order.id,
                filename=filename or "foto-os",
                content_type=normalized_type,
                image_data=image_bytes,
            )
        )

    db.commit()
    db.expire_all()
    return get_work_order(db, work_order.id)


def delete_work_order_photo(db: Session, work_order_id: int, photo_id: int) -> WorkOrder:
    work_order = _get_work_order_or_fail(db, work_order_id)
    photo = _get_work_order_photo_or_fail(db, photo_id)
    if photo.os_id != work_order.id:
        raise BusinessRuleViolation("A foto informada nao pertence a esta ordem de servico.")
    db.delete(photo)
    db.commit()
    db.expire_all()
    return get_work_order(db, work_order.id)


def get_work_order_photo_content(db: Session, photo_id: int) -> tuple[str, str, bytes]:
    photo = _get_work_order_photo_or_fail(db, photo_id)
    return photo.filename, photo.content_type, photo.image_data


def _draw_document_frame(pdf: canvas.Canvas, title: str, subtitle: str) -> float:
    width, height = A4
    pdf.setTitle(title)
    pdf.setStrokeColor(colors.HexColor("#0d7a68"))
    pdf.setFillColor(colors.HexColor("#0d7a68"))
    pdf.roundRect(18 * mm, height - 36 * mm, width - 36 * mm, 20 * mm, 5 * mm, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(24 * mm, height - 24 * mm, title)
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 24 * mm, height - 24 * mm, subtitle)
    return height - 46 * mm


def _draw_section_title(pdf: canvas.Canvas, y: float, title: str) -> float:
    pdf.setFillColor(colors.HexColor("#1d2a2b"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(20 * mm, y, title)
    pdf.setStrokeColor(colors.HexColor("#d9d3c4"))
    pdf.line(20 * mm, y - 2 * mm, 190 * mm, y - 2 * mm)
    return y - 8 * mm


def _draw_key_values(
    pdf: canvas.Canvas,
    y: float,
    items: List[tuple],
    *,
    value_x: float = 58 * mm,
    font_size: float = 10,
    row_height: float = 6 * mm,
    value_width_chars: Optional[int] = None,
) -> float:
    import textwrap

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", font_size)
    for label, value in items:
        pdf.setFont("Helvetica-Bold", font_size)
        pdf.drawString(20 * mm, y, f"{label}:")
        pdf.setFont("Helvetica", font_size)
        wrapped_values = textwrap.wrap(str(value), width=value_width_chars) if value_width_chars else [str(value)]
        wrapped_values = wrapped_values or [""]
        pdf.drawString(value_x, y, wrapped_values[0])
        y -= row_height
        for extra_line in wrapped_values[1:]:
            pdf.drawString(value_x, y, extra_line)
            y -= row_height
    return y


def _draw_paragraph(
    pdf: canvas.Canvas,
    y: float,
    text: str,
    width_chars: int = 92,
    *,
    font_size: float = 10,
    line_height: float = 5 * mm,
) -> float:
    import textwrap

    pdf.setFont("Helvetica", font_size)
    for line in textwrap.wrap(text or "", width=width_chars):
        pdf.drawString(20 * mm, y, line)
        y -= line_height
    return y


def _draw_bullets(
    pdf: canvas.Canvas,
    y: float,
    items: List[str],
    width_chars: int = 88,
    *,
    font_size: float = 10,
    line_height: float = 5 * mm,
) -> float:
    import textwrap

    pdf.setFont("Helvetica", font_size)
    for item in items:
        wrapped = textwrap.wrap(item, width=width_chars) or [""]
        pdf.drawString(22 * mm, y, f"- {wrapped[0]}")
        y -= line_height
        for line in wrapped[1:]:
            pdf.drawString(28 * mm, y, line)
            y -= line_height
    return y


def _document_subtitle(work_order: WorkOrder) -> str:
    return f"OS {work_order.numero} | {work_order.data_execucao.isoformat()}"


def _draw_logo_or_monogram(pdf: canvas.Canvas, x: float, y: float, box_w: float, box_h: float) -> None:
    settings = get_settings()
    logo_path = settings.company_logo_path
    if logo_path:
        candidate = Path(logo_path)
        if candidate.exists():
            pdf.drawImage(ImageReader(str(candidate)), x, y, width=box_w, height=box_h, preserveAspectRatio=True, mask="auto")
            return

    pdf.setFillColor(colors.HexColor("#0d7a68"))
    pdf.roundRect(x, y, box_w, box_h, 4 * mm, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(x + (box_w / 2), y + (box_h / 2) - 2 * mm, settings.company_name[:10].upper())


def _days_in_words(days: int) -> str:
    units = {
        0: "zero",
        1: "um",
        2: "dois",
        3: "tres",
        4: "quatro",
        5: "cinco",
        6: "seis",
        7: "sete",
        8: "oito",
        9: "nove",
        10: "dez",
        11: "onze",
        12: "doze",
        13: "treze",
        14: "quatorze",
        15: "quinze",
        16: "dezesseis",
        17: "dezessete",
        18: "dezoito",
        19: "dezenove",
    }
    tens = {
        20: "vinte",
        30: "trinta",
        40: "quarenta",
        50: "cinquenta",
        60: "sessenta",
        70: "setenta",
        80: "oitenta",
        90: "noventa",
    }
    if days < 20:
        return units[days]
    if days < 100:
        base = (days // 10) * 10
        remainder = days % 10
        return tens[base] if remainder == 0 else f"{tens[base]} e {units[remainder]}"
    hundreds = days // 100
    remainder = days % 100
    hundreds_map = {1: "cento", 2: "duzentos", 3: "trezentos"}
    prefix = "cem" if days == 100 else hundreds_map.get(hundreds, str(days))
    if remainder == 0:
        return prefix
    return f"{prefix} e {_days_in_words(remainder)}"


def _assistance_text(work_order: WorkOrder) -> str:
    delta = (work_order.garantia_ate - work_order.data_execucao).days
    if delta < 0:
        delta = 0
    return f"{delta} ({_days_in_words(delta)}) dias, ate {work_order.garantia_ate.strftime('%d/%m/%Y')}"


def _company_identification_lines() -> List[str]:
    settings = get_settings()
    return [
        f"Razao social: {settings.company_legal_name}",
        f"Nome fantasia: {settings.company_trade_name}",
        f"Endereco: {settings.company_address}",
        f"Telefone: {settings.company_phone}",
        f"Licenca sanitaria: {settings.sanitary_license_number} | validade: {settings.sanitary_license_expiry}",
        f"Licenca ambiental: {settings.environmental_license_number} | validade: {settings.environmental_license_expiry}",
    ]


def _company_identification_summary_lines() -> List[str]:
    settings = get_settings()
    return [
        f"Empresa especializada: {settings.company_trade_name} | {settings.company_legal_name}",
        f"Endereco e contato: {settings.company_address} | Telefone: {settings.company_phone}",
        f"Licenca sanitaria: {settings.sanitary_license_number} | validade: {settings.sanitary_license_expiry}",
        f"Licenca ambiental: {settings.environmental_license_number} | validade: {settings.environmental_license_expiry}",
    ]


def _resolve_sanitary_certificate_template_path() -> Optional[Path]:
    candidate = Path(__file__).resolve().parents[2] / "modelo" / "modelo.png"
    return candidate if candidate.exists() else None


def _split_text_to_width(pdf: canvas.Canvas, text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    words = str(text or "").split()
    if not words:
        return []

    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return lines


def _draw_centered_text_to_fit(
    pdf: canvas.Canvas,
    text: str,
    *,
    center_x: float,
    baseline_y: float,
    max_width: float,
    font_name: str,
    initial_size: float,
    min_size: float,
) -> float:
    size = initial_size
    while size > min_size and pdf.stringWidth(text, font_name, size) > max_width:
        size -= 0.5
    pdf.setFont(font_name, size)
    pdf.drawCentredString(center_x, baseline_y, text)
    return size


def _draw_centered_paragraph(
    pdf: canvas.Canvas,
    text: str,
    *,
    center_x: float,
    top_y: float,
    max_width: float,
    font_name: str,
    font_size: float,
    leading: float,
) -> None:
    lines = _split_text_to_width(pdf, text, font_name, font_size, max_width)
    if not lines:
        return

    pdf.setFont(font_name, font_size)
    current_y = top_y
    for line in lines:
        pdf.drawCentredString(center_x, current_y, line)
        current_y -= leading


def _draw_template_certificate_background(pdf: canvas.Canvas, template_path: Path, page_width: float, page_height: float) -> None:
    pdf.drawImage(ImageReader(str(template_path)), 0, 0, width=page_width, height=page_height, mask="auto")


def _classify_food_risk_environment(work_order: WorkOrder) -> str:
    context_fragments = [
        str(work_order.local_execucao or ""),
        str(work_order.observacoes or ""),
    ]
    context = " ".join(fragment.lower() for fragment in context_fragments if fragment)

    if any(keyword in context for keyword in ("armaz", "estoq", "deposit", "doca", "exped", "logist")):
        return "armazenagem e logistica de alimentos, insumos ou embalagens"
    if any(keyword in context for keyword in ("cozinha", "preparo", "manip", "produc", "refeic", "fracion")):
        return "manipulacao, preparo ou fracionamento de alimentos"
    return "potencial de armazenamento, logistica, manipulacao ou circulacao de alimentos"


def _short_food_risk_environment_label(risk_environment: str) -> str:
    if "armazenagem e logistica" in risk_environment:
        return "armazenagem/logistica de alimentos"
    if "manipulacao, preparo ou fracionamento" in risk_environment:
        return "manipulacao/preparo de alimentos"
    return "ambiente com risco alimentar"


def _summarize_certificate_pests(work_order: WorkOrder) -> str:
    pest_names = [item.praga.nome_comum for item in work_order.pragas if getattr(item, "praga", None) and item.praga.nome_comum]
    unique_names: List[str] = []
    for pest_name in pest_names:
        if pest_name not in unique_names:
            unique_names.append(pest_name)

    if not unique_names:
        return "monitoramento preventivo sem praga especifica registrada"
    if len(unique_names) == 1:
        return unique_names[0]
    if len(unique_names) == 2:
        return f"{unique_names[0]} e {unique_names[1]}"
    return f"{', '.join(unique_names[:2])} e outros vetores monitorados"


def _build_framed_sanitary_certificate_text(work_order: WorkOrder) -> str:
    risk_environment = _classify_food_risk_environment(work_order)
    return (
        "Certificamos, para fins de evidencia sanitaria e rastreabilidade operacional, que o estabelecimento acima "
        f"identificado, inserido em ambiente com {risk_environment}, recebeu servico especializado de controle de "
        "vetores e pragas urbanas em conformidade com a RDC 622/2022 e em alinhamento as Boas Praticas Sanitarias "
        "previstas nas RDC 216/2004 e RDC 275/2002, com foco na seguranca dos alimentos, no controle de contaminacao, "
        "na minimizacao de riscos a saude e na seguranca ambiental."
    )


def _build_standard_sanitary_certificate_text(work_order: WorkOrder) -> str:
    risk_environment = _classify_food_risk_environment(work_order)
    return (
        f"Certificamos que o estabelecimento de {work_order.cliente.razao_social}, inserido em ambiente com "
        f"{risk_environment}, recebeu servico tecnico especializado de controle de vetores e pragas urbanas, em "
        "conformidade com a RDC 622/2022, com foco na seguranca dos alimentos, no controle de contaminacao e na "
        "minimizacao de riscos a saude."
    )


def _build_standard_sanitary_declaration(work_order: WorkOrder) -> str:
    return (
        "Este certificado deve permanecer disponivel para verificacoes internas, auditorias e fiscalizacoes sanitarias, "
        "como evidencia de rastreabilidade do servico, em alinhamento as boas praticas sanitarias das RDC 216/2004 e "
        "RDC 275/2002 e as medidas de seguranca ambiental aplicaveis."
    )


def _draw_certificate_corner(pdf: canvas.Canvas, x: float, y: float, *, size: float, mirrored_x: bool = False, mirrored_y: bool = False) -> None:
    direction_x = -1 if mirrored_x else 1
    direction_y = -1 if mirrored_y else 1
    path = pdf.beginPath()
    path.moveTo(x, y)
    path.curveTo(
        x + direction_x * size * 0.18,
        y + direction_y * size * 0.44,
        x + direction_x * size * 0.56,
        y + direction_y * size * 0.58,
        x + direction_x * size * 0.9,
        y + direction_y * size * 0.24,
    )
    path.moveTo(x + direction_x * size * 0.12, y + direction_y * size * 0.1)
    path.curveTo(
        x + direction_x * size * 0.32,
        y + direction_y * size * 0.02,
        x + direction_x * size * 0.48,
        y + direction_y * size * 0.1,
        x + direction_x * size * 0.5,
        y + direction_y * size * 0.3,
    )
    pdf.drawPath(path)
    pdf.circle(x + direction_x * size * 0.26, y + direction_y * size * 0.18, size * 0.04, stroke=1, fill=0)


def _draw_certificate_flourish(pdf: canvas.Canvas, center_x: float, y: float, span: float) -> None:
    pdf.line(center_x - span, y, center_x - 20 * mm, y)
    pdf.line(center_x + 20 * mm, y, center_x + span, y)
    pdf.circle(center_x, y, 1.4 * mm, stroke=1, fill=0)
    pdf.circle(center_x - 5 * mm, y, 0.9 * mm, stroke=1, fill=0)
    pdf.circle(center_x + 5 * mm, y, 0.9 * mm, stroke=1, fill=0)
    path = pdf.beginPath()
    path.moveTo(center_x - 14 * mm, y)
    path.curveTo(center_x - 10 * mm, y + 2 * mm, center_x - 7 * mm, y + 2 * mm, center_x - 4 * mm, y)
    path.moveTo(center_x + 14 * mm, y)
    path.curveTo(center_x + 10 * mm, y + 2 * mm, center_x + 7 * mm, y + 2 * mm, center_x + 4 * mm, y)
    pdf.drawPath(path)


def _draw_certificate_info_box(
    pdf: canvas.Canvas,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    lines: List[str],
) -> None:
    pdf.setStrokeColor(colors.HexColor("#c8a75d"))
    pdf.setFillColor(colors.HexColor("#f8f1e5"))
    pdf.roundRect(x, y, width, height, 4 * mm, stroke=1, fill=1)
    pdf.setFillColor(colors.HexColor("#6f5521"))
    pdf.setFont("Times-Bold", 11)
    pdf.drawCentredString(x + width / 2, y + height - 7 * mm, title)
    pdf.setStrokeColor(colors.HexColor("#dcc288"))
    pdf.line(x + 8 * mm, y + height - 10 * mm, x + width - 8 * mm, y + height - 10 * mm)

    font_name = "Times-Roman"
    font_size = 9.6
    leading = 4.2 * mm
    max_width = width - 16 * mm
    wrapped_lines: List[str] = []
    for line in lines:
        split_lines = _split_text_to_width(pdf, line, font_name, font_size, max_width)
        wrapped_lines.extend(split_lines or [""])

    max_lines = max(1, int((height - 18 * mm) // leading))
    if len(wrapped_lines) > max_lines:
        wrapped_lines = wrapped_lines[:max_lines]
        last_line = wrapped_lines[-1].rstrip(". ")
        while last_line and pdf.stringWidth(f"{last_line}...", font_name, font_size) > max_width:
            last_line = last_line[:-1]
        wrapped_lines[-1] = f"{last_line.rstrip() or '...'}..."

    text = pdf.beginText(x + 8 * mm, y + height - 15.5 * mm)
    text.setFont(font_name, font_size)
    text.setLeading(leading)
    text.setFillColor(colors.HexColor("#3f3527"))
    for line in wrapped_lines:
        text.textLine(line)
    pdf.drawText(text)


def _draw_certificate_badge(pdf: canvas.Canvas, center_x: float, center_y: float, radius: float) -> None:
    pdf.setFillColor(colors.HexColor("#1f3556"))
    pdf.setStrokeColor(colors.HexColor("#b3873a"))
    pdf.setLineWidth(2)
    pdf.circle(center_x, center_y, radius, stroke=1, fill=1)
    pdf.setLineWidth(1.2)
    pdf.setStrokeColor(colors.HexColor("#d7b56b"))
    pdf.circle(center_x, center_y, radius - 3 * mm, stroke=1, fill=0)
    pdf.setFillColor(colors.HexColor("#f1d48f"))
    pdf.setFont("Times-Bold", 8.2)
    pdf.drawCentredString(center_x, center_y + 4.6 * mm, "VETORES E")
    pdf.drawCentredString(center_x, center_y + 0.7 * mm, "PRAGAS")
    pdf.drawCentredString(center_x, center_y - 3.2 * mm, "URBANAS")
    pdf.setFont("Helvetica-Bold", 5.8)
    pdf.drawCentredString(center_x, center_y - 8.4 * mm, "RDC 622/2022")
    pdf.setFillColor(colors.HexColor("#d7b56b"))
    for offset in (-10 * mm, -5 * mm, 0, 5 * mm, 10 * mm):
        pdf.circle(center_x + offset, center_y + radius - 7 * mm, 0.8 * mm, stroke=0, fill=1)


def generate_work_order_pdf(db: Session, work_order_id: int) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = _draw_document_frame(
        pdf,
        "Comprovante de Execucao / Ordem de Servico",
        "Conforme requisitos aplicaveis da RDC 622/2022",
    )

    y = _draw_section_title(pdf, y, "Identificacao do atendimento")
    y = _draw_key_values(
        pdf,
        y,
        [
            ("Cliente", work_order.cliente.razao_social),
            ("Endereco do imovel", f"{work_order.cliente.endereco} - {work_order.cliente.cidade}/{work_order.cliente.estado}"),
            ("Praga(s) alvo", ", ".join([item.praga.nome_comum for item in work_order.pragas]) if work_order.pragas else "Nao informada"),
            ("Data de execucao", work_order.data_execucao.strftime("%d/%m/%Y")),
            ("Prazo de assistencia tecnica", _assistance_text(work_order)),
            ("Horario", f"{work_order.hora_inicio} ate {work_order.hora_fim or '--:--'}"),
            ("Local", work_order.local_execucao),
            ("Responsavel tecnico", f"{settings.technical_responsible_name} - {settings.technical_responsible_registry}"),
            ("Centro de Informacao Toxicologica", settings.toxicology_center_phone),
            ("Valor", f"R$ {Decimal(work_order.valor_servico):.2f}"),
        ],
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Produtos aplicados")
    y = _draw_bullets(
        pdf,
        y,
        [
            f"{item.produto.nome} | Grupo quimico: {item.produto.grupo_quimico} | Concentracao de uso: {item.produto.concentracao} | Quantidade: {item.quantidade} | Diluicao: {item.diluicao}"
            for item in work_order.produtos
        ],
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Orientacoes pertinentes ao servico executado")
    y = _draw_bullets(
        pdf,
        y,
        [
            "Manter pessoas e animais afastados das areas tratadas durante o periodo de seguranca definido pela empresa.",
            "Nao remover residuos de barreiras quimicas ou iscas tecnicas sem orientacao profissional.",
            "Em caso de intercorrencia com o produto utilizado, contatar imediatamente o Centro de Informacao Toxicologica informado neste comprovante.",
        ],
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Observacoes")
    y = _draw_paragraph(pdf, y, work_order.observacoes or "Sem observacoes registradas.")

    y = _draw_section_title(pdf, y - 2 * mm, "Identificacao da empresa prestadora")
    y = _draw_bullets(pdf, y, _company_identification_lines(), width_chars=84)

    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, 24 * mm, "Assinatura do tecnico: ______________________________")
    pdf.drawRightString(190 * mm, 24 * mm, "Assinatura do cliente: ______________________________")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def generate_technical_report_pdf(db: Session, work_order_id: int) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = _draw_document_frame(
        pdf,
        "Relatorio Tecnico",
        "Estruturado com base nos requisitos aplicaveis da RDC 622/2022",
    )

    y = _draw_section_title(pdf, y, "Resumo tecnico")
    y = _draw_key_values(
        pdf,
        y,
        [
            ("OS", work_order.numero),
            ("Cliente", work_order.cliente.razao_social),
            ("Tecnico executor", work_order.tecnico.nome),
            ("Responsavel tecnico", f"{settings.technical_responsible_name} - {settings.technical_responsible_registry}"),
            ("Data da vistoria", work_order.data_execucao.isoformat()),
            ("Status da OS", work_order.status.replace("_", " ")),
            ("Garantia", work_order.garantia_ate.isoformat()),
        ],
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Diagnostico")
    diagnostic = (
        f"Foram avaliadas as condicoes do local '{work_order.local_execucao}' para controle de vetores e pragas urbanas. "
        f"O atendimento foi executado conforme os dados operacionais registrados na OS {work_order.numero}."
    )
    y = _draw_paragraph(pdf, y, diagnostic)

    y = _draw_section_title(pdf, y - 2 * mm, "Pragas e riscos observados")
    pest_items = [f"{item.praga.nome_comum} ({item.praga.nome_cientifico})" for item in work_order.pragas]
    if not pest_items:
        pest_items = ["Nao houve praga especifica registrada; manter monitoramento preventivo."]
    y = _draw_bullets(pdf, y, pest_items)

    y = _draw_section_title(pdf, y - 2 * mm, "Produtos e metodologia")
    y = _draw_bullets(
        pdf,
        y,
        [
            f"{item.produto.nome} com principio ativo {item.produto.principio_ativo}, quantidade {item.quantidade} e diluicao {item.diluicao}"
            for item in work_order.produtos
        ],
    )

    y = _draw_section_title(pdf, y - 2 * mm, "Recomendacoes")
    recommendations = [
        "Manter o ambiente higienizado, sem aculo de residuos e umidade excessiva.",
        "Reforcar vedacao de acessos, ralos, frestas e pontos de abrigo identificados.",
        f"Agendar reavaliacao antes do termino da garantia em {work_order.garantia_ate.isoformat()}.",
    ]
    y = _draw_bullets(pdf, y, recommendations)

    y = _draw_section_title(pdf, y - 2 * mm, "Observacoes complementares")
    y = _draw_paragraph(pdf, y, work_order.observacoes or "Sem observacoes complementares.")

    y = _draw_section_title(pdf, y - 2 * mm, "Dados regulatorios da empresa")
    y = _draw_bullets(pdf, y, _company_identification_lines(), width_chars=84)

    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, 24 * mm, "Responsavel tecnico: ______________________________")
    pdf.drawRightString(190 * mm, 24 * mm, "Cliente/ciente: ______________________________")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _generate_standard_sanitary_certificate_pdf(db: Session, work_order_id: int) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = _draw_document_frame(
        pdf,
        "Certificado Sanitario",
        "Conformidade sanitaria e rastreabilidade operacional",
    )

    y = _draw_section_title(pdf, y, "Certificacao")
    risk_environment = _classify_food_risk_environment(work_order)
    certificate_text = _build_standard_sanitary_certificate_text(work_order)
    y = _draw_paragraph(pdf, y, certificate_text, width_chars=108, font_size=9.0, line_height=4.0 * mm)

    y = _draw_section_title(pdf, y - 1 * mm, "Dados do estabelecimento")
    y = _draw_key_values(
        pdf,
        y,
        [
            ("Razao social", work_order.cliente.razao_social),
            ("CPF/CNPJ", work_order.cliente.cpf_cnpj),
            ("Endereco", f"{work_order.cliente.endereco} - {work_order.cliente.cidade}/{work_order.cliente.estado}"),
            ("Area atendida", work_order.local_execucao),
            ("Referencia sanitaria", _short_food_risk_environment_label(risk_environment)),
            ("Data do servico", work_order.data_execucao.strftime("%d/%m/%Y")),
            ("Validade tecnica", work_order.garantia_ate.strftime("%d/%m/%Y")),
            ("Responsavel tecnico", f"{settings.technical_responsible_name} - {settings.technical_responsible_registry}"),
        ],
        value_x=55 * mm,
        font_size=8.8,
        row_height=4.8 * mm,
        value_width_chars=48,
    )

    y = _draw_section_title(pdf, y - 1 * mm, "Escopo e base normativa")
    covered_items = [f"Produto: {item.produto.nome} | Registro MS: {item.produto.registro_ms}" for item in work_order.produtos]
    if work_order.pragas:
        covered_items.extend([f"Praga controlada: {item.praga.nome_comum}" for item in work_order.pragas])
    covered_items.extend(
        [
            "Escopo sanitario: controle de vetores e pragas urbanas com foco em seguranca alimentar.",
            "Base normativa: RDC 622/2022, RDC 216/2004 e RDC 275/2002.",
        ]
    )
    y = _draw_bullets(pdf, y, covered_items, width_chars=102, font_size=8.9, line_height=4.0 * mm)

    y = _draw_section_title(pdf, y - 1 * mm, "Declaracao sanitaria")
    declaration = _build_standard_sanitary_declaration(work_order)
    y = _draw_paragraph(pdf, y, declaration, width_chars=108, font_size=8.9, line_height=4.0 * mm)

    y = _draw_section_title(pdf, y - 1 * mm, "Empresa especializada")
    y = _draw_bullets(pdf, y, _company_identification_summary_lines(), width_chars=106, font_size=8.8, line_height=4.0 * mm)

    emission_date = date.today().strftime("%d/%m/%Y")
    responsible_name = settings.technical_responsible_name
    if responsible_name == "Responsavel tecnico nao configurado":
        responsible_name = work_order.tecnico.nome

    pdf.setFillColor(colors.HexColor("#273431"))
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawCentredString(105 * mm, 38 * mm, "DOCUMENTO EMITIDO PELO SISTEMA SYSPRAGAS")
    pdf.setStrokeColor(colors.HexColor("#7f8d86"))
    pdf.line(26 * mm, 28 * mm, 91 * mm, 28 * mm)
    pdf.line(119 * mm, 28 * mm, 184 * mm, 28 * mm)
    pdf.setFillColor(colors.black)
    _draw_centered_text_to_fit(
        pdf,
        responsible_name,
        center_x=58.5 * mm,
        baseline_y=21.5 * mm,
        max_width=60 * mm,
        font_name="Helvetica",
        initial_size=8.6,
        min_size=7.0,
    )
    pdf.setFont("Helvetica", 8.6)
    pdf.drawCentredString(151.5 * mm, 21.5 * mm, emission_date)
    pdf.setFont("Helvetica-Oblique", 8.1)
    pdf.drawCentredString(58.5 * mm, 15.2 * mm, "Responsavel tecnico")
    pdf.drawCentredString(151.5 * mm, 15.2 * mm, "Data de emissao")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _generate_template_sanitary_certificate_pdf(db: Session, work_order_id: int, template_path: Path) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.setTitle("Certificado Sanitario")

    _draw_template_certificate_background(pdf, template_path, page_width, page_height)

    overlay_color = colors.HexColor("#f7f1e6")
    overlay_boxes = [
        (44 * mm, 118 * mm, 210 * mm, 18 * mm),
        (44 * mm, 79 * mm, 210 * mm, 38 * mm),
        (72 * mm, 55 * mm, 74 * mm, 31 * mm),
        (146 * mm, 55 * mm, 10 * mm, 31 * mm),
        (160 * mm, 55 * mm, 92 * mm, 31 * mm),
        (84 * mm, 13 * mm, 54 * mm, 14 * mm),
        (186 * mm, 13 * mm, 66 * mm, 14 * mm),
    ]
    pdf.setFillColor(overlay_color)
    for x, y, width, height in overlay_boxes:
        pdf.roundRect(x, y, width, height, 2 * mm, stroke=0, fill=1)

    client_name = str(work_order.cliente.razao_social or "").upper()
    pdf.setFillColor(colors.HexColor("#3e3732"))
    _draw_centered_text_to_fit(
        pdf,
        client_name,
        center_x=page_width / 2,
        baseline_y=126.5 * mm,
        max_width=200 * mm,
        font_name="Times-Bold",
        initial_size=18,
        min_size=11,
    )

    certificate_text = (
        "Certificamos que o estabelecimento acima identificado recebeu servico tecnico "
        "especializado de controle de pragas urbanas, executado em conformidade com os "
        "requisitos sanitarios aplicaveis, conforme registro da ordem de servico emitida."
    )
    _draw_centered_paragraph(
        pdf,
        certificate_text,
        center_x=page_width / 2,
        top_y=103 * mm,
        max_width=180 * mm,
        font_name="Times-Roman",
        font_size=11.5,
        leading=5.2 * mm,
    )

    left_info_lines = [
        f"CNPJ/CPF: {work_order.cliente.cpf_cnpj}",
        f"Endereco: {work_order.cliente.endereco}",
        f"{work_order.cliente.cidade}/{work_order.cliente.estado}",
    ]
    right_info_lines = [
        f"Data do servico: {work_order.data_execucao.strftime('%d/%m/%Y')}",
        f"Validade tecnica: {work_order.garantia_ate.strftime('%d/%m/%Y')}",
        f"Ordem de Servico: {work_order.numero}",
    ]

    pdf.setFillColor(colors.HexColor("#4b433d"))
    left_text = pdf.beginText(81 * mm, 67.5 * mm)
    left_text.setFont("Times-Roman", 10.6)
    left_text.setLeading(4.7 * mm)
    for line in left_info_lines:
        left_text.textLine(line)
    pdf.drawText(left_text)

    right_text = pdf.beginText(171 * mm, 67.5 * mm)
    right_text.setFont("Times-Roman", 10.6)
    right_text.setLeading(4.7 * mm)
    for line in right_info_lines:
        right_text.textLine(line)
    pdf.drawText(right_text)

    emission_date = date.today().strftime("%d/%m/%Y")
    responsible_name = settings.technical_responsible_name
    if responsible_name == "Responsavel tecnico nao configurado":
        responsible_name = work_order.tecnico.nome

    pdf.setFillColor(colors.HexColor("#3e3732"))
    pdf.setFont("Times-Roman", 11)
    pdf.drawCentredString(111 * mm, 18.5 * mm, emission_date)
    _draw_centered_text_to_fit(
        pdf,
        responsible_name,
        center_x=219 * mm,
        baseline_y=18.5 * mm,
        max_width=58 * mm,
        font_name="Times-Roman",
        initial_size=11,
        min_size=8,
    )

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def generate_sanitary_certificate_pdf(db: Session, work_order_id: int) -> bytes:
    return _generate_standard_sanitary_certificate_pdf(db, work_order_id)


def _generate_ornamental_sanitary_certificate_pdf(db: Session, work_order_id: int) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle("Certificado Sanitario para Moldura")
    pdf.setStrokeColor(colors.HexColor("#b58a2f"))
    pdf.setLineWidth(2.5)
    pdf.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm)
    pdf.setLineWidth(0.8)
    pdf.rect(16 * mm, 16 * mm, width - 32 * mm, height - 32 * mm)

    _draw_logo_or_monogram(pdf, 22 * mm, height - 42 * mm, 28 * mm, 20 * mm)

    pdf.setFillColor(colors.HexColor("#0d7a68"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, height - 24 * mm, settings.company_name.upper())
    pdf.setFillColor(colors.HexColor("#1d2a2b"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 48 * mm, "CERTIFICADO SANITARIO")
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 57 * mm, "Modelo ornamental com informacoes compativeis com os requisitos aplicaveis")

    pdf.setStrokeColor(colors.HexColor("#d9d3c4"))
    pdf.line(34 * mm, height - 63 * mm, width - 34 * mm, height - 63 * mm)

    text = pdf.beginText(28 * mm, height - 80 * mm)
    text.setFont("Helvetica", 13)
    text.setLeading(9 * mm)
    body_lines = [
        "Certificamos que o estabelecimento abaixo identificado",
        f"recebeu servico tecnico especializado de controle de pragas urbanas,",
        f"executado em {work_order.data_execucao.strftime('%d/%m/%Y')}, com validade tecnica ate",
        f"{work_order.garantia_ate.strftime('%d/%m/%Y')}, conforme registro da Ordem de Servico {work_order.numero}.",
        "",
        f"Cliente: {work_order.cliente.razao_social}",
        f"CPF/CNPJ: {work_order.cliente.cpf_cnpj}",
        f"Endereco: {work_order.cliente.endereco} - {work_order.cliente.cidade}/{work_order.cliente.estado}",
        f"Area atendida: {work_order.local_execucao}",
        f"Tecnico responsavel: {work_order.tecnico.nome}",
        "",
        "Principais produtos utilizados:",
    ]
    for line in body_lines:
        text.textLine(line)
    for item in work_order.produtos:
        text.textLine(f"  • {item.produto.nome} | Registro MS {item.produto.registro_ms}")
    if work_order.pragas:
        text.textLine("")
        text.textLine("Pragas contempladas:")
        for item in work_order.pragas:
            text.textLine(f"  • {item.praga.nome_comum}")
    pdf.drawText(text)

    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width / 2, 52 * mm, "Documento emitido conforme requisitos aplicaveis da RDC 622/2022, sem implicar endosso oficial.")

    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(
        width / 2,
        46 * mm,
        f"Licenca sanitaria: {settings.sanitary_license_number} | Licenca ambiental: {settings.environmental_license_number}",
    )

    pdf.setFont("Helvetica", 10)
    pdf.line(35 * mm, 30 * mm, 90 * mm, 30 * mm)
    pdf.line(width - 90 * mm, 30 * mm, width - 35 * mm, 30 * mm)
    pdf.drawCentredString(62.5 * mm, 25 * mm, "Responsavel tecnico")
    pdf.drawCentredString(width - 62.5 * mm, 25 * mm, "Data de emissao")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _generate_premium_framed_sanitary_certificate_pdf(db: Session, work_order_id: int) -> bytes:
    work_order = get_work_order(db, work_order_id)
    settings = get_settings()
    buffer = BytesIO()
    width, height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setTitle("Certificado Sanitario para Moldura")

    paper = colors.HexColor("#f6efe1")
    gold = colors.HexColor("#a97821")
    gold_soft = colors.HexColor("#d7b15d")
    ink = colors.HexColor("#3a2d22")
    accent = colors.HexColor("#8a6420")

    pdf.setFillColor(paper)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)

    pdf.setStrokeColor(gold)
    pdf.setLineWidth(3)
    pdf.rect(8 * mm, 8 * mm, width - 16 * mm, height - 16 * mm, stroke=1, fill=0)
    pdf.setLineWidth(1.2)
    pdf.rect(13 * mm, 13 * mm, width - 26 * mm, height - 26 * mm, stroke=1, fill=0)
    pdf.setLineWidth(0.8)
    pdf.rect(18 * mm, 18 * mm, width - 36 * mm, height - 36 * mm, stroke=1, fill=0)

    pdf.setStrokeColor(gold)
    _draw_certificate_corner(pdf, 24 * mm, height - 24 * mm, size=20 * mm)
    _draw_certificate_corner(pdf, width - 24 * mm, height - 24 * mm, size=20 * mm, mirrored_x=True)
    _draw_certificate_corner(pdf, 24 * mm, 24 * mm, size=20 * mm, mirrored_y=True)
    _draw_certificate_corner(pdf, width - 24 * mm, 24 * mm, size=20 * mm, mirrored_x=True, mirrored_y=True)

    pdf.setStrokeColor(gold_soft)
    _draw_certificate_flourish(pdf, width / 2, height - 27 * mm, 78 * mm)
    _draw_certificate_flourish(pdf, width / 2, 27 * mm, 78 * mm)

    company_name = (settings.company_name or settings.company_trade_name or settings.company_legal_name).upper()
    pdf.setFillColor(accent)
    pdf.setFont("Times-Bold", 16)
    pdf.drawCentredString(width / 2, height - 38 * mm, company_name[:48])

    pdf.setFillColor(ink)
    pdf.setFont("Times-Bold", 30)
    pdf.drawCentredString(width / 2, height - 55 * mm, "CERTIFICADO SANITARIO")
    pdf.setFillColor(gold)
    pdf.setFont("Times-Italic", 14)
    pdf.drawCentredString(width / 2, height - 66 * mm, "Certificado de Conformidade Sanitaria")

    pdf.setStrokeColor(gold_soft)
    pdf.line(66 * mm, height - 73 * mm, width - 66 * mm, height - 73 * mm)

    pdf.setFillColor(colors.HexColor("#fbf7ee"))
    pdf.setStrokeColor(colors.HexColor("#ead3a4"))
    pdf.roundRect(41 * mm, height - 101 * mm, width - 82 * mm, 15 * mm, 3 * mm, stroke=1, fill=1)
    pdf.setFillColor(ink)
    _draw_centered_text_to_fit(
        pdf,
        str(work_order.cliente.razao_social or "").upper(),
        center_x=width / 2,
        baseline_y=height - 94 * mm,
        max_width=width - 96 * mm,
        font_name="Times-Bold",
        initial_size=20,
        min_size=12,
    )

    risk_environment = _classify_food_risk_environment(work_order)
    certificate_text = _build_framed_sanitary_certificate_text(work_order)
    pdf.setFillColor(ink)
    _draw_centered_paragraph(
        pdf,
        certificate_text,
        center_x=width / 2,
        top_y=height - 109 * mm,
        max_width=181 * mm,
        font_name="Times-Roman",
        font_size=10.4,
        leading=4.7 * mm,
    )

    _draw_certificate_badge(pdf, 47 * mm, 58 * mm, 15.8 * mm)

    left_lines = [
        f"CNPJ/CPF: {work_order.cliente.cpf_cnpj}",
        f"Endereco: {work_order.cliente.endereco}, {work_order.cliente.cidade}/{work_order.cliente.estado}",
        f"Area atendida: {work_order.local_execucao}",
        f"Ambiente critico: {risk_environment}",
    ]
    right_lines = [
        "Escopo: controle de vetores e pragas urbanas",
        f"Alvos monitorados: {_summarize_certificate_pests(work_order)}",
        "Base legal: RDC 622/2022, RDC 216/2004 e RDC 275/2002",
        f"Execucao: {work_order.data_execucao.strftime('%d/%m/%Y')} | OS: {work_order.numero}",
        f"Tecnico executor: {work_order.tecnico.nome}",
        f"Validade tecnica: {work_order.garantia_ate.strftime('%d/%m/%Y')}",
    ]

    _draw_certificate_info_box(
        pdf,
        x=74 * mm,
        y=40 * mm,
        width=82 * mm,
        height=42 * mm,
        title="Enquadramento Sanitario",
        lines=left_lines,
    )
    _draw_certificate_info_box(
        pdf,
        x=163 * mm,
        y=40 * mm,
        width=87 * mm,
        height=42 * mm,
        title="Rastreabilidade Tecnica",
        lines=right_lines,
    )

    pdf.setStrokeColor(gold_soft)
    pdf.line(74 * mm, 40 * mm, width - 31 * mm, 40 * mm)
    pdf.setFillColor(ink)
    pdf.setFont("Times-Italic", 9.6)
    pdf.drawCentredString(
        width / 2,
        35 * mm,
        "Seguranca dos alimentos, controle de contaminacao, minimizacao de riscos a saude e seguranca ambiental.",
    )
    pdf.setFont("Times-Roman", 8.9)
    pdf.drawCentredString(
        width / 2,
        29 * mm,
        (
            f"Licenca sanitaria: {settings.sanitary_license_number} | "
            f"Licenca ambiental: {settings.environmental_license_number} | "
            "Documento tecnico sem implicar endosso oficial."
        ),
    )

    emission_date = date.today().strftime("%d/%m/%Y")
    responsible_name = settings.technical_responsible_name
    if responsible_name == "Responsavel tecnico nao configurado":
        responsible_name = work_order.tecnico.nome

    pdf.setStrokeColor(colors.HexColor("#8f7650"))
    pdf.line(84 * mm, 31 * mm, 132 * mm, 31 * mm)
    pdf.line(width - 116 * mm, 31 * mm, width - 56 * mm, 31 * mm)
    pdf.setFillColor(ink)
    pdf.setFont("Times-Roman", 10)
    pdf.drawCentredString(108 * mm, 24 * mm, emission_date)
    pdf.setFont("Times-Italic", 9.6)
    pdf.drawCentredString(108 * mm, 10.5 * mm, "Data de emissao")
    _draw_centered_text_to_fit(
        pdf,
        responsible_name,
        center_x=width - 86 * mm,
        baseline_y=24 * mm,
        max_width=52 * mm,
        font_name="Times-Roman",
        initial_size=10.5,
        min_size=8,
    )
    pdf.setFont("Times-Italic", 9.6)
    pdf.drawCentredString(width - 86 * mm, 10.5 * mm, "Responsavel tecnico")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def generate_framed_sanitary_certificate_pdf(db: Session, work_order_id: int) -> bytes:
    return _generate_premium_framed_sanitary_certificate_pdf(db, work_order_id)
