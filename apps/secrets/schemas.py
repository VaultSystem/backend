from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.settings import settings

SECRET_NAME_PATTERN = r"^[A-Za-z0-9_.:/-]+$"
MAX_SECRET_VALUE_CHARS = 65_536


class SecretCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=SECRET_NAME_PATTERN)
    description: str | None = Field(default=None, max_length=500)
    value: str = Field(min_length=1, max_length=MAX_SECRET_VALUE_CHARS)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("value")
    @classmethod
    def validate_secret_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > settings.MAX_SECRET_VALUE_BYTES:
            raise ValueError("Secret value exceeds the configured size limit.")
        return value


class SecretUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=MAX_SECRET_VALUE_CHARS)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("value")
    @classmethod
    def validate_secret_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > settings.MAX_SECRET_VALUE_BYTES:
            raise ValueError("Secret value exceeds the configured size limit.")
        return value


class SecretRollbackRequest(BaseModel):
    version: int = Field(ge=1)


class SecretGrantRequest(BaseModel):
    user_id: int = Field(gt=0)
    role: str = Field(pattern=r"^(viewer|editor|owner)$")


class SecretRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    current_version_id: int | None
    created_at: datetime
    updated_at: datetime


class SecretValueRead(SecretRead):
    value: str
    version: int


class SecretVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    secret_id: int
    version: int
    created_at: datetime


class PaginatedSecrets(BaseModel):
    items: list[SecretRead]
    total: int
    limit: int
    offset: int
