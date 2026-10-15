"""Enterprise identity-provider configuration guards.

This module intentionally does not claim to complete an SSO integration merely
because values were supplied. It validates safe configuration shape and emits a
redacted pending-verification record; an IdP metadata/login round trip remains
an external production closure gate.
"""

from typing import Any
from urllib.parse import urlparse


class SSOConfigurationError(ValueError):
    """Raised when a provider setup request is malformed or unsafe."""


def _require_nonempty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise SSOConfigurationError(f"{field_name} is required")
    return value.strip()


def _require_secure_url(value: str, field_name: str, allowed_schemes: set[str]) -> str:
    value = _require_nonempty(value, field_name)
    parsed = urlparse(value)
    if parsed.scheme not in allowed_schemes or not parsed.netloc:
        expected = ", ".join(sorted(allowed_schemes))
        raise SSOConfigurationError(f"{field_name} must be an absolute {expected} URL")
    return value


def _pending_configuration(provider_type: str, **details: Any) -> dict[str, Any]:
    return {
        "type": provider_type,
        "status": "pending_provider_validation",
        "validation_required": [
            "store credentials in a secret manager",
            "verify provider metadata and callback/ACS endpoint",
            "complete an authenticated login round trip",
            "record security-owner approval",
        ],
        **details,
    }


def setup_saml(entity_id: str, sso_url: str, x509_cert: str) -> dict[str, Any]:
    """Validate SAML metadata without storing certificate material."""
    entity_id = _require_nonempty(entity_id, "entity_id")
    sso_url = _require_secure_url(sso_url, "sso_url", {"https"})
    _require_nonempty(x509_cert, "x509_cert")
    if "BEGIN CERTIFICATE" not in x509_cert:
        raise SSOConfigurationError("x509_cert must contain a PEM certificate")
    return _pending_configuration(
        "saml", entity_id=entity_id, sso_url=sso_url, certificate_supplied=True
    )


def setup_oauth(
    provider: str,
    client_id: str,
    client_secret: str,
    authorization_url: str,
    token_url: str,
) -> dict[str, Any]:
    """Validate OAuth endpoints and return a redacted verification record."""
    provider = _require_nonempty(provider, "provider")
    client_id = _require_nonempty(client_id, "client_id")
    _require_nonempty(client_secret, "client_secret")
    authorization_url = _require_secure_url(authorization_url, "authorization_url", {"https"})
    token_url = _require_secure_url(token_url, "token_url", {"https"})
    return _pending_configuration(
        "oauth",
        provider=provider,
        client_id=client_id,
        authorization_url=authorization_url,
        token_url=token_url,
        client_secret_supplied=True,
    )


def setup_ldap(
    server_url: str,
    base_dn: str,
    bind_dn: str | None = None,
    bind_password: str | None = None,
) -> dict[str, Any]:
    """Validate LDAPS settings and return a redacted verification record."""
    server_url = _require_secure_url(server_url, "server_url", {"ldaps"})
    base_dn = _require_nonempty(base_dn, "base_dn")
    if bind_password and not bind_dn:
        raise SSOConfigurationError("bind_dn is required when bind_password is supplied")
    return _pending_configuration(
        "ldap",
        server_url=server_url,
        base_dn=base_dn,
        bind_dn=bind_dn,
        bind_password_supplied=bool(bind_password),
    )
