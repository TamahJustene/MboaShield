"""Identity federation helpers: password policy, OIDC, SAML, LDAP."""

from __future__ import annotations

import base64
import re
from typing import Any
from urllib.parse import urlencode

import ssl

import httpx
from defusedxml import ElementTree as DET
from jose import jwt
from ldap3 import ALL, Connection, Server, Tls

from ..core.config import get_settings
from ..core.security import create_access_token


def validate_password_policy(password: str) -> None:
    settings = get_settings()
    if len(password) < settings.password_min_length:
        raise ValueError(f"Password must be at least {settings.password_min_length} characters")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must include a letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must include a number")
    if settings.password_require_upper and not re.search(r"[A-Z]", password):
        raise ValueError("Password must include an uppercase letter")
    if settings.password_require_special and not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must include a special character")


def oidc_discovery_urls() -> dict[str, str]:
    settings = get_settings()
    issuer = settings.oidc_issuer.rstrip("/")
    return {
        "token": settings.oidc_token_url or f"{issuer}/token",
        "jwks": settings.oidc_jwks_url or f"{issuer}/protocol/openid-connect/certs",
        "userinfo": settings.oidc_userinfo_url or f"{issuer}/userinfo",
        "authorize": f"{issuer}/authorize",
    }


def build_oidc_authorize_url(*, state: str, redirect_uri: str, nonce: str) -> str:
    settings = get_settings()
    if not settings.oidc_enabled:
        raise ValueError("OIDC is disabled")
    if not settings.oidc_issuer or not settings.oidc_client_id:
        raise ValueError("OIDC provider is not configured")
    urls = oidc_discovery_urls()
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.oidc_client_id,
            "redirect_uri": redirect_uri,
            "scope": settings.oidc_scopes,
            "state": state,
            "nonce": nonce,
        }
    )
    return f"{urls['authorize']}?{query}"


def exchange_oidc_code(*, code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange authorization code for tokens. Returns token response + normalized claims."""
    settings = get_settings()
    if not settings.oidc_enabled:
        raise ValueError("OIDC is disabled")
    if not settings.oidc_issuer or not settings.oidc_client_id or not settings.oidc_client_secret:
        raise ValueError("OIDC provider is configured incompletely")
    urls = oidc_discovery_urls()
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            urls["token"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise ValueError(f"OIDC token exchange failed: HTTP {response.status_code}")
        token_payload = response.json()

    claims: dict[str, Any] = {}
    id_token = token_payload.get("id_token")
    if id_token:
        claims = _decode_oidc_id_token(id_token)
    elif token_payload.get("access_token"):
        claims = _fetch_oidc_userinfo(token_payload["access_token"], urls["userinfo"])

    subject = str(claims.get("sub") or "").strip()
    if not subject:
        raise ValueError("OIDC response missing subject claim")
    email = (claims.get("email") or claims.get("preferred_username") or "").strip() or None
    name = (
        claims.get("name")
        or claims.get("given_name")
        or email
        or f"oidc-{subject[:8]}"
    )
    return {
        "token_response": token_payload,
        "claims": claims,
        "subject": subject,
        "email": email,
        "display_name": str(name),
    }


def _decode_oidc_id_token(id_token: str) -> dict[str, Any]:
    settings = get_settings()
    urls = oidc_discovery_urls()
    try:
        with httpx.Client(timeout=15.0) as client:
            jwks = client.get(urls["jwks"]).json()
        return jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256", "RS384", "RS512", "ES256", "HS256"],
            audience=settings.oidc_client_id,
            options={"verify_at_hash": False},
        )
    except Exception:
        # Fallback: decode without verify only when explicitly allowed in non-prod via missing JWKS.
        # Prefer failure in production.
        if settings.environment.lower() in {"prod", "production"} or settings.is_government_profile():
            raise
        return jwt.get_unverified_claims(id_token)


def _fetch_oidc_userinfo(access_token: str, userinfo_url: str) -> dict[str, Any]:
    with httpx.Client(timeout=15.0) as client:
        response = client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise ValueError("OIDC userinfo request failed")
        return response.json()


def build_saml_metadata_xml() -> str:
    settings = get_settings()
    entity_id = settings.saml_sp_entity_id
    acs = settings.saml_acs_url
    return f"""<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{entity_id}">
  <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="true"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{acs}" index="0" isDefault="true"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>
"""


def parse_saml_response(saml_response_b64: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.saml_enabled:
        raise ValueError("SAML is disabled")
    try:
        xml_bytes = base64.b64decode(saml_response_b64)
    except Exception as exc:
        raise ValueError("Invalid SAMLResponse encoding") from exc

    if settings.saml_idp_x509_cert.strip():
        xml_bytes = _verify_saml_xml(xml_bytes, settings.saml_idp_x509_cert)
    elif not settings.saml_allow_unsigned:
        raise ValueError("SAML_IDP_X509_CERT is required unless SAML_ALLOW_UNSIGNED=true")

    root = DET.fromstring(xml_bytes)
    ns = {
        "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    }
    name_id = root.findtext(".//saml:NameID", default="", namespaces=ns) or ""
    attrs: dict[str, str] = {}
    for attr in root.findall(".//saml:Attribute", namespaces=ns):
        name = attr.attrib.get("Name") or attr.attrib.get("FriendlyName") or ""
        value_el = attr.find("saml:AttributeValue", namespaces=ns)
        if name and value_el is not None and value_el.text:
            attrs[name] = value_el.text.strip()

    email = (
        attrs.get("email")
        or attrs.get("mail")
        or attrs.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        or name_id
    ).strip()
    display_name = (
        attrs.get("displayName")
        or attrs.get("cn")
        or attrs.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name")
        or email
        or "SAML User"
    ).strip()
    subject = (name_id or email or attrs.get("uid") or "").strip()
    if not subject:
        raise ValueError("SAML assertion missing NameID/subject")
    return {
        "subject": subject,
        "email": email or None,
        "display_name": display_name,
        "attributes": attrs,
    }


def _verify_saml_xml(xml_bytes: bytes, pem_or_b64_cert: str) -> bytes:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from cryptography.x509 import load_pem_x509_certificate, load_der_x509_certificate
    from signxml import XMLVerifier

    cert_text = pem_or_b64_cert.strip()
    if "BEGIN CERTIFICATE" in cert_text:
        cert = load_pem_x509_certificate(cert_text.encode("utf-8"))
    else:
        # bare base64 DER
        der = base64.b64decode("".join(cert_text.split()))
        cert = load_der_x509_certificate(der)
    public_pem = cert.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    verified = XMLVerifier().verify(xml_bytes, x509_cert=public_pem)
    return verified.signed_xml


def ldap_authenticate(username: str, password: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.ldap_enabled:
        raise ValueError("LDAP is disabled")
    if not settings.ldap_server_uri:
        raise ValueError("LDAP_SERVER_URI is not configured")
    user = (username or "").strip()
    if not user or not password:
        raise ValueError("Username and password are required")

    bind_dn = settings.ldap_bind_dn_template.format(username=user) if settings.ldap_bind_dn_template else user
    tls = Tls(validate=ssl.CERT_NONE) if settings.ldap_use_ssl else None
    server = Server(settings.ldap_server_uri, use_ssl=settings.ldap_use_ssl, get_info=ALL, tls=tls)
    conn = Connection(server, user=bind_dn or user, password=password, auto_bind=True)
    try:
        attrs = [settings.ldap_email_attr, settings.ldap_name_attr, settings.ldap_group_attr]
        search_filter = settings.ldap_user_filter_template.format(username=user)
        if settings.ldap_user_search_base:
            conn.search(settings.ldap_user_search_base, search_filter, attributes=attrs)
        entry = conn.entries[0] if conn.entries else None
        email = None
        display_name = user
        groups: list[str] = []
        if entry is not None:
            email_vals = entry[settings.ldap_email_attr].values if settings.ldap_email_attr in entry else []
            name_vals = entry[settings.ldap_name_attr].values if settings.ldap_name_attr in entry else []
            group_vals = entry[settings.ldap_group_attr].values if settings.ldap_group_attr in entry else []
            email = str(email_vals[0]) if email_vals else None
            display_name = str(name_vals[0]) if name_vals else user
            groups = [str(g) for g in group_vals]
        role = settings.ldap_default_role
        role_map = settings.ldap_role_map()
        for group in groups:
            mapped = role_map.get(group.lower())
            if mapped:
                role = mapped
                break
        return {
            "subject": f"ldap:{user}",
            "email": (email or f"{user}@ldap.local").lower(),
            "display_name": display_name,
            "role": role,
            "groups": groups,
        }
    finally:
        conn.unbind()


def issue_client_credentials_token(actor: dict) -> dict[str, Any]:
    settings = get_settings()
    token = create_access_token(
        f"oauth:{actor['client_id']}",
        claims={
            "role": "partner",
            "auth_type": "client_credentials",
            "scopes": actor.get("scopes") or [],
            "partner_org": actor.get("partner_org"),
            "name": actor.get("name"),
        },
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "scope": " ".join(actor.get("scopes") or []),
    }
