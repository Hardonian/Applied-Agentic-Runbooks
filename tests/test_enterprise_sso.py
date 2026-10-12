"""Tests for enterprise IdP configuration guards."""

import pytest

from agent_factory.enterprise.sso import SSOConfigurationError, setup_ldap, setup_oauth, setup_saml


def test_oauth_configuration_is_redacted_and_pending_validation():
    configuration = setup_oauth(
        "example-idp",
        "client-id",
        "super-secret",
        "https://idp.example.test/authorize",
        "https://idp.example.test/token",
    )

    assert configuration["status"] == "pending_provider_validation"
    assert configuration["client_secret_supplied"] is True
    assert "super-secret" not in str(configuration)


def test_saml_requires_https_and_pem_certificate():
    with pytest.raises(SSOConfigurationError, match="https"):
        setup_saml("entity", "http://idp.example.test/sso", "-----BEGIN CERTIFICATE-----x")
    with pytest.raises(SSOConfigurationError, match="PEM"):
        setup_saml("entity", "https://idp.example.test/sso", "not a certificate")


def test_ldap_requires_ldaps_and_valid_bind_pair():
    with pytest.raises(SSOConfigurationError, match="ldaps"):
        setup_ldap("ldap://directory.example.test", "dc=example,dc=test")
    with pytest.raises(SSOConfigurationError, match="bind_dn"):
        setup_ldap("ldaps://directory.example.test", "dc=example,dc=test", bind_password="secret")
