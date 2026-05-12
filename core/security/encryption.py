from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from core.exceptions import CryptoError
from core.security.key_manager import load_master_key

ENVELOPE_PREFIX = "v1"
NONCE_BYTES = 12
DEK_BYTES = 32


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _aesgcm() -> type:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:
        raise CryptoError(
            "The 'cryptography' package is required for AES-GCM envelope encryption.",
        ) from exc

    return AESGCM


@dataclass(frozen=True)
class EncryptedSecret:
    encrypted_value: str
    encrypted_data_key: str


class EnvelopeEncryptionService:
    def __init__(self, master_key_material: str, *, allow_derived_dev_key: bool = False) -> None:
        self._master_key = load_master_key(
            master_key_material,
            allow_derived_dev_key=allow_derived_dev_key,
        )

    def encrypt_secret(self, plaintext: str) -> EncryptedSecret:
        data_key = os.urandom(DEK_BYTES)
        encrypted_value = self._encrypt_bytes(plaintext.encode("utf-8"), data_key)
        encrypted_data_key = self._encrypt_bytes(data_key, self._master_key)

        return EncryptedSecret(
            encrypted_value=encrypted_value,
            encrypted_data_key=encrypted_data_key,
        )

    def decrypt_secret(self, encrypted_value: str, encrypted_data_key: str) -> str:
        data_key = self._decrypt_bytes(encrypted_data_key, self._master_key)
        plaintext = self._decrypt_bytes(encrypted_value, data_key)
        return plaintext.decode("utf-8")

    def _encrypt_bytes(self, value: bytes, key: bytes) -> str:
        nonce = os.urandom(NONCE_BYTES)
        ciphertext = _aesgcm()(key).encrypt(nonce, value, None)
        return f"{ENVELOPE_PREFIX}:{_b64encode(nonce)}:{_b64encode(ciphertext)}"

    def _decrypt_bytes(self, payload: str, key: bytes) -> bytes:
        try:
            version, nonce, ciphertext = payload.split(":", 2)
            if version != ENVELOPE_PREFIX:
                raise ValueError("unsupported envelope version")

            return _aesgcm()(key).decrypt(_b64decode(nonce), _b64decode(ciphertext), None)
        except CryptoError:
            raise
        except Exception as exc:
            raise CryptoError("Could not decrypt secret payload.") from exc
