"""Authenticated encryption for user-supplied provider API credentials.

Uses Fernet (AES-128-CBC with HMAC-SHA256, from the pinned ``cryptography``
package). The key is read from ``PROVIDER_CREDENTIAL_ENCRYPTION_KEY`` and is
never stored in the database or source tree. ``MultiFernet`` accepts a
comma-separated list of keys: the first key encrypts new values, and every key
decrypts, which allows rotation without re-encrypting in place.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import Settings
from app.core.errors import ServiceUnavailableError


class CredentialEncryptionError(ServiceUnavailableError):
    """Raised when credential encryption is unavailable or misconfigured."""


def _build_cipher(settings: Settings) -> MultiFernet:
    secret = settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY
    raw = secret.get_secret_value().strip() if secret else ""
    if not raw:
        raise CredentialEncryptionError(
            message=(
                "Provider credential storage is not configured. Set "
                "PROVIDER_CREDENTIAL_ENCRYPTION_KEY on the server."
            ),
            details={"reason": "encryption_key_missing"},
        )
    try:
        keys = [
            Fernet(part.strip().encode()) for part in raw.split(",") if part.strip()
        ]
    except (ValueError, TypeError) as exc:
        # Do not include the key material in the error or logs.
        raise CredentialEncryptionError(
            message="PROVIDER_CREDENTIAL_ENCRYPTION_KEY is malformed.",
            details={"reason": "encryption_key_invalid"},
        ) from exc
    if not keys:
        raise CredentialEncryptionError(
            message="PROVIDER_CREDENTIAL_ENCRYPTION_KEY is malformed.",
            details={"reason": "encryption_key_invalid"},
        )
    return MultiFernet(keys)


def encrypt_credential(settings: Settings, plaintext: str) -> str:
    """Encrypt a credential and return an opaque token safe to persist."""
    return _build_cipher(settings).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_credential(settings: Settings, token: str) -> str:
    """Decrypt a persisted token. Raises CredentialEncryptionError on failure."""
    try:
        return _build_cipher(settings).decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialEncryptionError(
            message="Stored provider credential could not be decrypted.",
            details={"reason": "decryption_failed"},
        ) from exc
