from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User
from apps.users.repository import UserRepository
from core.db.engine import get_db
from core.exceptions import UnauthorizedError
from core.security.tokens import decode_access_token
from core.settings import settings
from core.storage.base import Storage
from core.storage.factory import get_storage

DBSession = Annotated[AsyncSession, Depends(get_db)]

StorageSession = Annotated[Storage, Depends(get_storage)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: DBSession,
) -> User:
    payload = decode_access_token(token, secret_key=settings.SECRET_KEY)
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid authentication token.")

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    user = await UserRepository(session).get_by_id(parsed_user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid authentication token.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
