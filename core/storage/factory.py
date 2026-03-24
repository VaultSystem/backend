from functools import lru_cache

from core.settings import settings

from .base import Storage
from .local import LocalStorage
from .s3 import S3Storage


@lru_cache
def get_storage() -> Storage:
    if settings.USE_S3:
        return S3Storage()
    return LocalStorage()
