from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.engine import get_db
from core.storage.base import Storage
from core.storage.factory import get_storage

DBSession = Annotated[AsyncSession, Depends(get_db)]

StorageSession = Annotated[Storage, Depends(get_storage)]
