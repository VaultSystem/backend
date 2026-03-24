import os
from functools import lru_cache

from .base import Settings


class DevSettings(Settings):
    DEBUG: bool = True


class ProdSettings(Settings):
    DEBUG: bool = False


class TestSettings(Settings):
    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "dev").lower()

    if env == "prod":
        return ProdSettings()
    elif env == "test":
        return TestSettings()
    return DevSettings()
