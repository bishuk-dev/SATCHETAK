import ssl
import urllib.error

import pytest

from satchetak import tls


def test_native_tls_context_verifies_certificates(monkeypatch):
    monkeypatch.delenv("SATCHETAK_CA_BUNDLE", raising=False)
    tls.ssl_context.cache_clear()
    context = tls.ssl_context()
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_invalid_explicit_ca_bundle_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("SATCHETAK_CA_BUNDLE", str(tmp_path / "missing.pem"))
    tls.ssl_context.cache_clear()
    with pytest.raises(tls.TLSVerificationError, match="readable file"):
        tls.ssl_context()
    monkeypatch.delenv("SATCHETAK_CA_BUNDLE", raising=False)
    tls.ssl_context.cache_clear()


def test_certificate_error_has_actionable_safe_message():
    source = urllib.error.URLError(ssl.SSLCertVerificationError(1, "self-signed certificate"))
    translated = tls.translate_tls_error(source, "Copernicus catalogue")
    assert translated is not None
    assert "SATCHETAK_CA_BUNDLE" in str(translated)
    assert "not been disabled" in str(translated)
