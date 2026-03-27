from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional, Union
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation

NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
ET.register_namespace("", NFE_NAMESPACE)

MONEY_QUANTIZER = Decimal("0.01")
FOUR_DECIMAL_QUANTIZER = Decimal("0.0001")

UF_CODE_MAP = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27", "SE": "28", "BA": "29",
    "MG": "31", "ES": "32", "RJ": "33", "SP": "35",
    "PR": "41", "SC": "42", "RS": "43",
    "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}


@dataclass
class GeneratedNfeXml:
    access_key: str
    lote_id: str
    nfe_xml: str
    envi_nfe_xml: str


def _digits_only(value: Any) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _money(value: Optional[Union[Decimal, int, float, str]]) -> Decimal:
    return Decimal(str(value or "0")).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def _decimal4(value: Optional[Union[Decimal, int, float, str]]) -> Decimal:
    return Decimal(str(value or "0")).quantize(FOUR_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _format_money(value: Decimal) -> str:
    return f"{_money(value):.2f}"


def _format_decimal4(value: Decimal) -> str:
    return f"{_decimal4(value):.4f}"


def _append_text(parent: ET.Element, tag: str, value: Any) -> Optional[ET.Element]:
    if value in (None, "", []):
        return None
    element = ET.SubElement(parent, f"{{{NFE_NAMESPACE}}}{tag}")
    element.text = str(value)
    return element


def _mod11_dv(base: str) -> str:
    multiplier = 2
    total = 0
    for digit in reversed(base):
        total += int(digit) * multiplier
        multiplier += 1
        if multiplier > 9:
            multiplier = 2
    remainder = total % 11
    dv = 11 - remainder
    if dv >= 10:
        dv = 0
    return str(dv)


def _resolve_emit_state(settings) -> str:
    state = (settings.sefaz_nfe_uf or settings.company_state or "").upper()
    if not state or state not in UF_CODE_MAP:
        raise BusinessRuleViolation("Configure a UF do emitente em SEFAZ_NFE_UF ou COMPANY_STATE.")
    return state


def _resolve_emit_city_code(settings) -> str:
    code = _digits_only(settings.company_city_code)
    if len(code) != 7:
        raise BusinessRuleViolation("Configure COMPANY_CITY_CODE com o codigo IBGE de 7 digitos do municipio do emitente.")
    return code


def _resolve_emitente(settings) -> dict[str, str]:
    cnpj = _digits_only(settings.company_cnpj)
    ie = _digits_only(settings.company_ie)
    emit = {
        "cnpj": cnpj,
        "ie": ie,
        "xNome": settings.company_legal_name or settings.company_name,
        "xFant": settings.company_trade_name or settings.company_name,
        "xLgr": settings.company_street or settings.company_address,
        "nro": settings.company_number or "S/N",
        "xBairro": settings.company_district or "",
        "cMun": _resolve_emit_city_code(settings),
        "xMun": settings.company_city or "",
        "UF": _resolve_emit_state(settings),
        "CEP": _digits_only(settings.company_zip_code),
        "fone": _digits_only(settings.company_phone),
        "CRT": str(settings.company_crt or "1"),
        "IM": _digits_only(settings.company_im),
        "CNAE": _digits_only(settings.company_cnae),
    }
    required = {
        "cnpj": "Configure COMPANY_CNPJ.",
        "ie": "Configure COMPANY_IE.",
        "xNome": "Configure COMPANY_LEGAL_NAME ou COMPANY_NAME.",
        "xLgr": "Configure COMPANY_STREET ou COMPANY_ADDRESS.",
        "xMun": "Configure COMPANY_CITY.",
    }
    for field, message in required.items():
        if not emit[field]:
            raise BusinessRuleViolation(message)
    return emit


def _resolve_destinatario(customer) -> dict[str, str]:
    document = _digits_only(customer.cpf_cnpj)
    if len(document) not in {11, 14}:
        raise BusinessRuleViolation("Cliente da NF-e precisa ter CPF ou CNPJ valido.")
    state = (customer.estado or "").upper()
    city = customer.cidade or ""
    city_code = "9999999"
    return {
        "cpf": document if len(document) == 11 else "",
        "cnpj": document if len(document) == 14 else "",
        "xNome": customer.razao_social,
        "xLgr": customer.endereco,
        "nro": customer.numero or "S/N",
        "xBairro": customer.bairro or "Centro",
        "cMun": city_code,
        "xMun": city,
        "UF": state,
        "CEP": _digits_only(customer.cep),
        "fone": _digits_only(customer.telefone),
    }


def _resolve_invoice_number(invoice) -> str:
    digits = _digits_only(getattr(invoice, "numero_nfe", "")) or _digits_only(getattr(invoice, "id", "")) or "1"
    normalized = str(int(digits))
    if len(normalized) > 9:
        raise BusinessRuleViolation("O numero da NF-e deve ter no maximo 9 digitos numericos.")
    return normalized


def _resolve_issue_datetime(settings, invoice) -> datetime:
    tz_name = settings.company_timezone or "America/Sao_Paulo"
    try:
        timezone_info = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        timezone_info = datetime.now().astimezone().tzinfo
        if timezone_info is None:
            raise BusinessRuleViolation(f"Timezone invalida para emissao da NF-e: {tz_name}.")
    now_local = datetime.now(timezone_info).replace(microsecond=0)
    issue_date = getattr(invoice, "data_emissao", None) or now_local.date()
    return datetime.combine(issue_date, now_local.timetz().replace(microsecond=0), tzinfo=timezone_info)


def _compute_access_key(settings, invoice, issue_datetime: datetime) -> tuple[str, str]:
    emit_state = _resolve_emit_state(settings)
    cuf = settings.company_state_code or UF_CODE_MAP[emit_state]
    aamm = issue_datetime.strftime("%y%m")
    cnpj = _digits_only(settings.company_cnpj)
    model = "55"
    serie = str(settings.sefaz_nfe_serie).zfill(3)
    numero = _resolve_invoice_number(invoice).zfill(9)
    tp_emis = "1"
    code_seed = hashlib.sha1(f"{invoice.numero_nfe}{invoice.cliente_id}{invoice.id}".encode("utf-8")).hexdigest()[:8]
    c_nf = str(int(code_seed, 16) % 100000000).zfill(8)
    base = f"{cuf}{aamm}{cnpj}{model}{serie}{numero}{tp_emis}{c_nf}"
    dv = _mod11_dv(base)
    return f"{base}{dv}", c_nf


def build_nfe_xml(invoice, customer, items: list[dict[str, Any]]) -> GeneratedNfeXml:
    settings = get_settings()
    emit = _resolve_emitente(settings)
    dest = _resolve_destinatario(customer)
    issue_datetime = _resolve_issue_datetime(settings, invoice)
    invoice_number = _resolve_invoice_number(invoice)
    access_key, c_nf = _compute_access_key(settings, invoice, issue_datetime)
    lote_id = str(random.randint(1, 999999999999999)).zfill(15)

    nfe = ET.Element(f"{{{NFE_NAMESPACE}}}NFe")
    inf_nfe = ET.SubElement(nfe, f"{{{NFE_NAMESPACE}}}infNFe", attrib={"Id": f"NFe{access_key}", "versao": "4.00"})

    ide = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}ide")
    _append_text(ide, "cUF", settings.company_state_code or UF_CODE_MAP[emit["UF"]])
    _append_text(ide, "cNF", c_nf)
    _append_text(ide, "natOp", "Venda")
    _append_text(ide, "mod", "55")
    _append_text(ide, "serie", str(settings.sefaz_nfe_serie))
    _append_text(ide, "nNF", invoice_number)
    _append_text(ide, "dhEmi", issue_datetime.isoformat(timespec="seconds"))
    _append_text(ide, "tpNF", "1")
    _append_text(ide, "idDest", "1")
    _append_text(ide, "cMunFG", emit["cMun"])
    _append_text(ide, "tpImp", "1")
    _append_text(ide, "tpEmis", "1")
    _append_text(ide, "cDV", access_key[-1])
    _append_text(ide, "tpAmb", "2" if (invoice.ambiente or "homologacao") == "homologacao" else "1")
    _append_text(ide, "finNFe", "1")
    _append_text(ide, "indFinal", "1")
    _append_text(ide, "indPres", "1")
    _append_text(ide, "procEmi", "0")
    _append_text(ide, "verProc", "SysPragas 3.2.0")

    emit_tag = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}emit")
    _append_text(emit_tag, "CNPJ", emit["cnpj"])
    _append_text(emit_tag, "xNome", emit["xNome"])
    _append_text(emit_tag, "xFant", emit["xFant"])
    ender_emit = ET.SubElement(emit_tag, f"{{{NFE_NAMESPACE}}}enderEmit")
    _append_text(ender_emit, "xLgr", emit["xLgr"])
    _append_text(ender_emit, "nro", emit["nro"])
    _append_text(ender_emit, "xBairro", emit["xBairro"])
    _append_text(ender_emit, "cMun", emit["cMun"])
    _append_text(ender_emit, "xMun", emit["xMun"])
    _append_text(ender_emit, "UF", emit["UF"])
    _append_text(ender_emit, "CEP", emit["CEP"])
    _append_text(ender_emit, "fone", emit["fone"])
    _append_text(emit_tag, "IE", emit["ie"])
    _append_text(emit_tag, "IM", emit["IM"])
    _append_text(emit_tag, "CNAE", emit["CNAE"])
    _append_text(emit_tag, "CRT", emit["CRT"])

    dest_tag = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}dest")
    if dest["cnpj"]:
        _append_text(dest_tag, "CNPJ", dest["cnpj"])
    else:
        _append_text(dest_tag, "CPF", dest["cpf"])
    _append_text(dest_tag, "xNome", dest["xNome"])
    ender_dest = ET.SubElement(dest_tag, f"{{{NFE_NAMESPACE}}}enderDest")
    _append_text(ender_dest, "xLgr", dest["xLgr"])
    _append_text(ender_dest, "nro", dest["nro"])
    _append_text(ender_dest, "xBairro", dest["xBairro"])
    _append_text(ender_dest, "cMun", dest["cMun"])
    _append_text(ender_dest, "xMun", dest["xMun"])
    _append_text(ender_dest, "UF", dest["UF"])
    _append_text(ender_dest, "CEP", dest["CEP"])
    _append_text(ender_dest, "fone", dest["fone"])
    _append_text(dest_tag, "indIEDest", "9")

    total_products = Decimal("0.00")
    total_icms = Decimal("0.00")
    total_pis = Decimal("0.00")
    total_cofins = Decimal("0.00")
    crt_simples = emit["CRT"] == "1"

    for index, item in enumerate(items, start=1):
        quantity = _decimal4(item["quantidade"])
        unit_price = _decimal4(item["valor_unitario"])
        total_price = _money(quantity * unit_price)
        total_products += total_price

        det = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}det", attrib={"nItem": str(index)})
        prod = ET.SubElement(det, f"{{{NFE_NAMESPACE}}}prod")
        _append_text(prod, "cProd", _digits_only(item.get("produto_id")) or str(index))
        _append_text(prod, "cEAN", "SEM GTIN")
        _append_text(prod, "xProd", item["descricao"])
        _append_text(prod, "NCM", _digits_only(item["ncm"]).zfill(8))
        _append_text(prod, "CFOP", _digits_only(item.get("cfop")) or "5102")
        _append_text(prod, "uCom", item.get("unidade_comercial") or "UN")
        _append_text(prod, "qCom", _format_decimal4(quantity))
        _append_text(prod, "vUnCom", _format_decimal4(unit_price))
        _append_text(prod, "vProd", _format_money(total_price))
        _append_text(prod, "cEANTrib", "SEM GTIN")
        _append_text(prod, "uTrib", item.get("unidade_comercial") or "UN")
        _append_text(prod, "qTrib", _format_decimal4(quantity))
        _append_text(prod, "vUnTrib", _format_decimal4(unit_price))
        _append_text(prod, "indTot", "1")

        imposto = ET.SubElement(det, f"{{{NFE_NAMESPACE}}}imposto")
        icms = ET.SubElement(imposto, f"{{{NFE_NAMESPACE}}}ICMS")
        if crt_simples:
            icms_sn = ET.SubElement(icms, f"{{{NFE_NAMESPACE}}}ICMSSN102")
            _append_text(icms_sn, "orig", "0")
            _append_text(icms_sn, "CSOSN", "102")
        else:
            icms_00 = ET.SubElement(icms, f"{{{NFE_NAMESPACE}}}ICMS00")
            aliquot_icms = _decimal4(item.get("aliquota_icms") or 0)
            icms_value = _money(total_price * aliquot_icms / Decimal("100"))
            total_icms += icms_value
            _append_text(icms_00, "orig", "0")
            _append_text(icms_00, "CST", "00")
            _append_text(icms_00, "modBC", "3")
            _append_text(icms_00, "vBC", _format_money(total_price))
            _append_text(icms_00, "pICMS", _format_decimal4(aliquot_icms))
            _append_text(icms_00, "vICMS", _format_money(icms_value))

        pis_aliquot = _decimal4(item.get("aliquota_pis") or 0)
        pis_value = _money(total_price * pis_aliquot / Decimal("100"))
        total_pis += pis_value
        pis = ET.SubElement(imposto, f"{{{NFE_NAMESPACE}}}PIS")
        pis_aliq = ET.SubElement(pis, f"{{{NFE_NAMESPACE}}}PISAliq")
        _append_text(pis_aliq, "CST", "01")
        _append_text(pis_aliq, "vBC", _format_money(total_price))
        _append_text(pis_aliq, "pPIS", _format_decimal4(pis_aliquot))
        _append_text(pis_aliq, "vPIS", _format_money(pis_value))

        cofins_aliquot = _decimal4(item.get("aliquota_cofins") or 0)
        cofins_value = _money(total_price * cofins_aliquot / Decimal("100"))
        total_cofins += cofins_value
        cofins = ET.SubElement(imposto, f"{{{NFE_NAMESPACE}}}COFINS")
        cofins_aliq = ET.SubElement(cofins, f"{{{NFE_NAMESPACE}}}COFINSAliq")
        _append_text(cofins_aliq, "CST", "01")
        _append_text(cofins_aliq, "vBC", _format_money(total_price))
        _append_text(cofins_aliq, "pCOFINS", _format_decimal4(cofins_aliquot))
        _append_text(cofins_aliq, "vCOFINS", _format_money(cofins_value))

    total = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}total")
    icms_tot = ET.SubElement(total, f"{{{NFE_NAMESPACE}}}ICMSTot")
    _append_text(icms_tot, "vBC", _format_money(total_products if not crt_simples else Decimal("0.00")))
    _append_text(icms_tot, "vICMS", _format_money(total_icms))
    _append_text(icms_tot, "vICMSDeson", "0.00")
    _append_text(icms_tot, "vFCP", "0.00")
    _append_text(icms_tot, "vBCST", "0.00")
    _append_text(icms_tot, "vST", "0.00")
    _append_text(icms_tot, "vFCPST", "0.00")
    _append_text(icms_tot, "vFCPSTRet", "0.00")
    _append_text(icms_tot, "vProd", _format_money(total_products))
    _append_text(icms_tot, "vFrete", "0.00")
    _append_text(icms_tot, "vSeg", "0.00")
    _append_text(icms_tot, "vDesc", "0.00")
    _append_text(icms_tot, "vII", "0.00")
    _append_text(icms_tot, "vIPI", "0.00")
    _append_text(icms_tot, "vIPIDevol", "0.00")
    _append_text(icms_tot, "vPIS", _format_money(total_pis))
    _append_text(icms_tot, "vCOFINS", _format_money(total_cofins))
    _append_text(icms_tot, "vOutro", "0.00")
    _append_text(icms_tot, "vNF", _format_money(total_products))

    transp = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}transp")
    _append_text(transp, "modFrete", "9")

    pag = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}pag")
    det_pag = ET.SubElement(pag, f"{{{NFE_NAMESPACE}}}detPag")
    _append_text(det_pag, "tPag", "90")
    _append_text(det_pag, "vPag", _format_money(total_products))

    inf_adic = ET.SubElement(inf_nfe, f"{{{NFE_NAMESPACE}}}infAdic")
    _append_text(inf_adic, "infCpl", invoice.observacoes or "Documento gerado por emissor proprio SysPragas.")

    nfe_xml = ET.tostring(nfe, encoding="utf-8", xml_declaration=False).decode("utf-8")

    envi_nfe = ET.Element(f"{{{NFE_NAMESPACE}}}enviNFe", attrib={"versao": "4.00"})
    _append_text(envi_nfe, "idLote", lote_id)
    _append_text(envi_nfe, "indSinc", "1")
    envi_nfe.append(ET.fromstring(nfe_xml.encode("utf-8")))
    envi_nfe_xml = ET.tostring(envi_nfe, encoding="utf-8", xml_declaration=False).decode("utf-8")

    return GeneratedNfeXml(
        access_key=access_key,
        lote_id=lote_id,
        nfe_xml=nfe_xml,
        envi_nfe_xml=envi_nfe_xml,
    )


def validate_xml_against_xsd(xml_content: str, schema_name: str, *, environment: Optional[str] = None) -> None:
    settings = get_settings()
    current_environment = str(environment or settings.focus_nfe_environment or "homologacao").strip().lower()
    if not settings.sefaz_nfe_xsd_dir:
        if current_environment == "homologacao":
            return
        raise BusinessRuleViolation(
            "Configure SEFAZ_NFE_XSD_DIR com os schemas oficiais da NF-e para validar o XML em producao."
        )

    try:
        from lxml import etree  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise BusinessRuleViolation("Dependencia lxml nao instalada. Ela e obrigatoria para validacao XSD da NF-e.") from exc

    xsd_path = Path(settings.sefaz_nfe_xsd_dir) / schema_name
    if not xsd_path.exists():
        raise BusinessRuleViolation(f"Schema XSD nao encontrado: {xsd_path}")

    xml_doc = etree.fromstring(xml_content.encode("utf-8"))
    with xsd_path.open("rb") as schema_file:
        schema_doc = etree.parse(schema_file)
    schema = etree.XMLSchema(schema_doc)
    if not schema.validate(xml_doc):
        errors = "; ".join(error.message for error in schema.error_log)
        raise BusinessRuleViolation(f"XML da NF-e invalido para o schema {schema_name}: {errors}")
