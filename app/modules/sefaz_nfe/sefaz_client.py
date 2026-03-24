from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import httpx

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.modules.sefaz_nfe.signer import load_certificate_transport_material

SOAP12_ENV = "http://www.w3.org/2003/05/soap-envelope"
NFE_NS = "http://www.portalfiscal.inf.br/nfe"
SOAP_ACTIONS = {
    "NFeAutorizacao": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4/nfeAutorizacaoLote",
    "NFeRetAutorizacao": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4/nfeRetAutorizacaoLote",
    "RecepcaoEvento": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento",
}
SOAP_WSDL_NAMESPACES = {
    "NFeAutorizacao": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4",
    "NFeRetAutorizacao": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4",
    "RecepcaoEvento": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4",
}


@dataclass
class SefazResponse:
    service: str
    status_code: int
    raw_response: str
    c_stat: Optional[str] = None
    x_motivo: Optional[str] = None
    receipt_number: Optional[str] = None
    protocol_number: Optional[str] = None
    access_key: Optional[str] = None
    inner_xml: Optional[str] = None


DEFAULT_SEFAZ_URLS = {
    "homologacao": {
        "SP": {
            "NFeAutorizacao": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NFeRetAutorizacao": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "RecepcaoEvento": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
        },
        "AN": {
            "NFeAutorizacao": "https://hom.nfe.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx",
            "NFeRetAutorizacao": "https://hom.nfe.fazenda.gov.br/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx",
            "RecepcaoEvento": "https://hom.nfe.fazenda.gov.br/RecepcaoEvento4/RecepcaoEvento4.asmx",
        }
    },
    "producao": {
        "SP": {
            "NFeAutorizacao": "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NFeRetAutorizacao": "https://nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "RecepcaoEvento": "https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
        },
        "AN": {
            "NFeAutorizacao": "https://www.nfe.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx",
            "NFeRetAutorizacao": "https://www.nfe.fazenda.gov.br/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx",
            "RecepcaoEvento": "https://www.nfe.fazenda.gov.br/RecepcaoEvento4/RecepcaoEvento4.asmx",
        }
    },
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_text(root: ET.Element, name: str) -> Optional[str]:
    for node in root.iter():
        if _local_name(node.tag) == name:
            value = (node.text or "").strip()
            if value:
                return value
    return None


def _find_first_node(root: ET.Element, name: str) -> Optional[ET.Element]:
    for node in root.iter():
        if _local_name(node.tag) == name:
            return node
    return None


def _extract_soap_fault_reason(raw_response: str) -> Optional[str]:
    try:
        root = ET.fromstring(raw_response)
    except ET.ParseError:
        return None
    for node in root.iter():
        if _local_name(node.tag) == "Text":
            value = (node.text or "").strip()
            if value:
                return value
    return None


class SefazSoapClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.timeout_seconds = settings.focus_nfe_timeout_seconds
        self.url_map = self._load_url_map(settings.sefaz_nfe_ws_urls_json)

    @staticmethod
    def _load_url_map(raw_json: Optional[str]) -> dict:
        if not raw_json:
            return DEFAULT_SEFAZ_URLS
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise BusinessRuleViolation("SEFAZ_NFE_WS_URLS_JSON contem JSON invalido.") from exc

    def _resolve_url(self, ambiente: str, uf: str, service: str) -> str:
        env_map = self.url_map.get(ambiente, {})
        uf_map = env_map.get(uf) or env_map.get("AN")
        if not uf_map or service not in uf_map:
            raise BusinessRuleViolation(
                f"URL do servico {service} nao configurada para a UF {uf} no ambiente {ambiente}."
            )
        return uf_map[service]

    @staticmethod
    def _resolve_tls_verify(ambiente: str) -> bool:
        settings = get_settings()
        if ambiente == "homologacao" and not settings.sefaz_nfe_verify_tls:
            return False
        return True

    @staticmethod
    def _soap_envelope(body_xml: str, cuf: str, service: str, versao_dados: str = "4.00") -> str:
        wsdl_ns = SOAP_WSDL_NAMESPACES.get(service, NFE_NS)
        return f"""
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="{SOAP12_ENV}">
  <soap12:Header>
    <nfeCabecMsg xmlns="{wsdl_ns}">
      <cUF>{cuf}</cUF>
      <versaoDados>{versao_dados}</versaoDados>
    </nfeCabecMsg>
  </soap12:Header>
  <soap12:Body>
    <nfeDadosMsg xmlns="{wsdl_ns}">
      {body_xml}
    </nfeDadosMsg>
  </soap12:Body>
</soap12:Envelope>
""".strip()

    def _post(self, url: str, service: str, xml_payload: str, cuf: str, ambiente: str) -> SefazResponse:
        envelope = self._soap_envelope(xml_payload, cuf, service)
        action = SOAP_ACTIONS.get(service)
        headers = {
            "Content-Type": f'application/soap+xml; charset=utf-8; action="{action}"' if action else "application/soap+xml; charset=utf-8",
        }
        if action:
            headers["SOAPAction"] = action
        try:
            cert_pem, key_pem = load_certificate_transport_material()
            with tempfile.TemporaryDirectory(prefix="sefaz-cert-") as temp_dir:
                cert_path = Path(temp_dir) / "cert.pem"
                key_path = Path(temp_dir) / "key.pem"
                cert_path.write_bytes(cert_pem)
                key_path.write_bytes(key_pem)
                with httpx.Client(
                    cert=(str(cert_path), str(key_path)),
                    verify=self._resolve_tls_verify(ambiente),
                    timeout=self.timeout_seconds,
                ) as client:
                    response = client.post(url, content=envelope.encode("utf-8"), headers=headers)
        except httpx.ConnectError as exc:
            raise BusinessRuleViolation(
                f"Nao foi possivel conectar ao endpoint da SEFAZ no servico {service}. "
                "Verifique acesso HTTPS ao host da UF, firewall/proxy da maquina e disponibilidade do ambiente SEFAZ."
            ) from exc
        except httpx.HTTPError as exc:
            raise BusinessRuleViolation(
                f"Falha de rede ao comunicar com a SEFAZ no servico {service}: {exc.__class__.__name__}."
            ) from exc

        if response.status_code >= 400:
            fault_reason = _extract_soap_fault_reason(response.text)
            if fault_reason:
                raise BusinessRuleViolation(
                    f"SEFAZ respondeu HTTP {response.status_code} no servico {service}: {fault_reason}"
                )
            raise BusinessRuleViolation(f"SEFAZ respondeu HTTP {response.status_code} no servico {service}.")
        return self._parse_response(service, response.status_code, response.text)

    def _parse_response(self, service: str, status_code: int, raw_response: str) -> SefazResponse:
        try:
            root = ET.fromstring(raw_response)
        except ET.ParseError as exc:
            raise BusinessRuleViolation(f"Resposta SOAP invalida recebida da SEFAZ no servico {service}.") from exc

        body = next((node for node in root.iter() if _local_name(node.tag) == "Body"), None)
        if body is None:
            raise BusinessRuleViolation(f"Resposta da SEFAZ no servico {service} nao contem SOAP Body.")

        payload_node = None
        for node in body.iter():
            if _local_name(node.tag) in {
                "retEnviNFe",
                "retConsReciNFe",
                "retEnvEvento",
                "retEvento",
                "retConsSitNFe",
            }:
                payload_node = node
                break

        inner_xml = ET.tostring(payload_node, encoding="unicode") if payload_node is not None else None
        response_scope = payload_node if payload_node is not None else body
        protocol_scope = _find_first_node(response_scope, "infProt") if payload_node is not None else None
        c_stat = _first_text(protocol_scope, "cStat") if protocol_scope is not None else None
        x_motivo = _first_text(protocol_scope, "xMotivo") if protocol_scope is not None else None
        protocol_number = _first_text(protocol_scope, "nProt") if protocol_scope is not None else None
        access_key = _first_text(protocol_scope, "chNFe") if protocol_scope is not None else None

        return SefazResponse(
            service=service,
            status_code=status_code,
            raw_response=raw_response,
            c_stat=c_stat or _first_text(response_scope, "cStat"),
            x_motivo=x_motivo or _first_text(response_scope, "xMotivo"),
            receipt_number=_first_text(response_scope, "nRec"),
            protocol_number=protocol_number or _first_text(response_scope, "nProt"),
            access_key=access_key or _first_text(response_scope, "chNFe"),
            inner_xml=inner_xml,
        )

    def authorize_batch(self, *, uf: str, ambiente: str, cuf: str, envi_nfe_xml: str) -> SefazResponse:
        return self._post(
            self._resolve_url(ambiente, uf, "NFeAutorizacao"),
            "NFeAutorizacao",
            envi_nfe_xml,
            cuf,
            ambiente,
        )

    def query_receipt(self, *, uf: str, ambiente: str, cuf: str, recibo: str) -> SefazResponse:
        xml = f'<consReciNFe xmlns="{NFE_NS}" versao="4.00"><tpAmb>{"2" if ambiente == "homologacao" else "1"}</tpAmb><nRec>{recibo}</nRec></consReciNFe>'
        return self._post(
            self._resolve_url(ambiente, uf, "NFeRetAutorizacao"),
            "NFeRetAutorizacao",
            xml,
            cuf,
            ambiente,
        )

    def send_event(self, *, uf: str, ambiente: str, cuf: str, event_xml: str) -> SefazResponse:
        return self._post(
            self._resolve_url(ambiente, uf, "RecepcaoEvento"),
            "RecepcaoEvento",
            event_xml,
            cuf,
            ambiente,
        )
