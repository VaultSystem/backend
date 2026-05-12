from __future__ import annotations

import base64
import hashlib

from core.exceptions import CryptoError

MASTER_KEY_BYTES = 32


def _decode_base64_key(value: str) -> bytes | None:
    normalized = value.strip()
    padding = "=" * (-len(normalized) % 4)

    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            decoded = decoder(normalized + padding)
        except Exception:
            continue
        if len(decoded) == MASTER_KEY_BYTES:
            return decoded

    return None


def load_master_key(key_material: str, *, allow_derived_dev_key: bool) -> bytes:
    decoded = _decode_base64_key(key_material)
    if decoded is not None:
        return decoded

    raw = key_material.encode("utf-8")
    if len(raw) == MASTER_KEY_BYTES:
        return raw

    if allow_derived_dev_key:
        return hashlib.sha256(raw).digest()

    raise CryptoError(
        "MASTER_KEY must be a 32-byte raw string or a base64-encoded 32-byte key.",
    )
