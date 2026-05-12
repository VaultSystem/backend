class VaultError(Exception):
    status_code = 400
    code = "vault_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BadRequestError(VaultError):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(VaultError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(VaultError):
    status_code = 403
    code = "forbidden"


class NotFoundError(VaultError):
    status_code = 404
    code = "not_found"


class ConflictError(VaultError):
    status_code = 409
    code = "conflict"


class CryptoError(VaultError):
    status_code = 500
    code = "crypto_error"
