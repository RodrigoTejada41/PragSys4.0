from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation


def _require_signxml():
    try:
        from signxml import DigestAlgorithm, SignatureMethod, XMLSigner, methods  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise BusinessRuleViolation(
            "Dependencia signxml nao instalada. Adicione a biblioteca de assinatura XML para operar NF-e direta."
        ) from exc
    return XMLSigner, methods, SignatureMethod, DigestAlgorithm


def _load_certificate_material():
    settings = get_settings()
    cert_path = Path(settings.sefaz_nfe_certificate_path or "")
    cert_password = settings.sefaz_nfe_certificate_password
    if not cert_path.exists():
        raise BusinessRuleViolation("Configure SEFAZ_NFE_CERTIFICATE_PATH apontando para um certificado A1 .pfx valido.")
    if not cert_password:
        raise BusinessRuleViolation("Configure SEFAZ_NFE_CERTIFICATE_PASSWORD para usar o certificado A1.")

    try:
        from cryptography.hazmat.primitives import serialization  # type: ignore
        from cryptography.hazmat.primitives.serialization import pkcs12  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise BusinessRuleViolation(
            "Dependencia cryptography nao instalada. Ela e obrigatoria para carregar o certificado A1."
        ) from exc

    try:
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            cert_path.read_bytes(),
            cert_password.encode("utf-8"),
        )
    except Exception as exc:  # pragma: no cover - depends on certificate validity
        raise BusinessRuleViolation("Nao foi possivel abrir o certificado A1 informado.") from exc

    if private_key is None or certificate is None:
        raise BusinessRuleViolation("O certificado A1 informado nao contem chave privada utilizavel.")

    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    return key_pem, cert_pem


def load_certificate_transport_material() -> tuple[bytes, bytes]:
    key_pem, cert_pem = _load_certificate_material()
    return cert_pem, key_pem


def sign_xml_document(xml_content: str, reference_uri: str) -> str:
    XMLSigner, methods, SignatureMethod, DigestAlgorithm = _require_signxml()

    try:
        from lxml import etree  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise BusinessRuleViolation("Dependencia lxml nao instalada. Ela e obrigatoria para assinatura NF-e.") from exc

    key_pem, cert_pem = _load_certificate_material()

    parser = etree.XMLParser(remove_blank_text=True)
    document = etree.fromstring(xml_content.encode("utf-8"), parser=parser)

    class SefazXMLSigner(XMLSigner):
        # NF-e ainda exige assinatura RSA-SHA1 em partes do ecossistema fiscal.
        # Restringimos esse bypass ao assinador da SEFAZ em vez de afrouxar globalmente.
        def check_deprecated_methods(self):  # type: ignore[override]
            return None

    signer = SefazXMLSigner(
        method=methods.enveloped,
        signature_algorithm=SignatureMethod.RSA_SHA1,
        digest_algorithm=DigestAlgorithm.SHA1,
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    try:
        signed = signer.sign(
            document,
            key=key_pem,
            cert=cert_pem,
            reference_uri=reference_uri,
            always_add_key_value=False,
        )
    except Exception as exc:  # pragma: no cover - depends on runtime signer/cert behavior
        raise BusinessRuleViolation(f"Nao foi possivel assinar o XML da NF-e: {exc}") from exc
    return etree.tostring(signed, encoding="utf-8", xml_declaration=False).decode("utf-8")
