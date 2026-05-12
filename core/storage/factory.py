from functools import lru_cache

from core.settings import settings

from .base import Storage
from .local import LocalStorage


@lru_cache
def get_storage() -> Storage:
    if settings.USE_S3:
        from .s3 import S3Storage

        return S3Storage()
    return LocalStorage()
