from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )

    ENVIRONMENT: str = "dev"
    DEBUG: bool = False

    SECRET_KEY: str = "dev-only-change-me"
    MASTER_KEY: str = "dev-only-master-key-change-me"
    ALLOWED_HOSTS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    POSTGRES_USER: str = "vault"
    POSTGRES_PASSWORD: str = "vault"
    POSTGRES_DB: str = "vault"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: Optional[str] = None
    DATABASE_ECHO: bool = False

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_SECRET_VALUE_BYTES: int = 64 * 1024

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    MEDIA_URL: Optional[str] = "media"
    USE_S3: bool = False
    USE_S3_FOR_STATIC: bool = False
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_STORAGE_BUCKET_NAME: Optional[str] = None
    AWS_S3_REGION_NAME: Optional[str] = None
    AWS_S3_VERIFY: bool = True
    AWS_QUERYSTRING_AUTH: bool = True
    AWS_QUERYSTRING_EXPIRE: int = 10800

    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USER: Optional[str] = None
    EMAIL_HOST_PASSWORD: Optional[str] = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @model_validator(mode="after")
    def build_database_url(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
                f"/{self.POSTGRES_DB}"
            )
        return self

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() == "prod":
            if self.SECRET_KEY == "dev-only-change-me":
                raise ValueError("SECRET_KEY must be set in production.")
            if self.MASTER_KEY == "dev-only-master-key-change-me":
                raise ValueError("MASTER_KEY must be set in production.")
        return self
