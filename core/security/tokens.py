from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from core.exceptions import UnauthorizedError

JWT_ALGORITHM = "HS256"


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def create_access_token(
    *,
    subject: str,
    secret_key: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}

    signing_input = f"{_b64encode(_json_bytes(header))}.{_b64encode(_json_bytes(payload))}"
    signature = _sign(signing_input, secret_key)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str, *, secret_key: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = _sign(signing_input, secret_key)

        if not hmac.compare_digest(signature, expected_signature):
            raise UnauthorizedError("Invalid authentication token.")

        header = json.loads(_b64decode(header_part))
        if header.get("alg") != JWT_ALGORITHM:
            raise UnauthorizedError("Unsupported authentication token.")

        payload = json.loads(_b64decode(payload_part))
        if payload.get("type") != "access":
            raise UnauthorizedError("Unsupported authentication token.")

        expires_at = int(payload["exp"])
        if expires_at < int(datetime.now(UTC).timestamp()):
            raise UnauthorizedError("Authentication token has expired.")

        return payload
    except UnauthorizedError:
        raise
    except Exception as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc


def _sign(signing_input: str, secret_key: str) -> str:
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64encode(signature)
