from __future__ import annotations

import os
import ssl
from functools import lru_cache
from pathlib import Path

import truststore


class TLSVerificationError(RuntimeError):
    pass


def _certificate_failure(error: BaseException) -> bool:
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, ssl.SSLCertVerificationError):
            return True
        if "CERTIFICATE_VERIFY_FAILED" in str(current):
            return True
        reason = getattr(current, "reason", None)
        current = current.__cause__ or current.__context__ or (reason if isinstance(reason, BaseException) else None)
    return False


@lru_cache(maxsize=1)
def ssl_context() -> ssl.SSLContext:
    """Return a verifying TLS context using an explicit CA or the native OS store."""
    ca_bundle = os.environ.get("SATCHETAK_CA_BUNDLE")
    if ca_bundle:
        path = Path(ca_bundle).expanduser().resolve()
        if not path.is_file():
            raise TLSVerificationError(f"SATCHETAK_CA_BUNDLE does not point to a readable file: {path}")
        return ssl.create_default_context(cafile=str(path))
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def translate_tls_error(error: BaseException, service: str) -> TLSVerificationError | None:
    if not _certificate_failure(error):
        return None
    return TLSVerificationError(
        f"{service} TLS certificate verification failed. SATCHETAK uses the native OS trust store. "
        "If your network uses a TLS-inspection proxy, install its root CA in the Windows trust store "
        "or set SATCHETAK_CA_BUNDLE to a PEM CA bundle, then restart the backend. "
        "Certificate verification has not been disabled."
    )
