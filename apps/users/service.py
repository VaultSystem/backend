from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User
from apps.users.repository import UserRepository
from apps.users.schemas import LoginRequest, TokenResponse, UserCreate
from core.exceptions import ConflictError, UnauthorizedError
from core.security.hashing import hash_password, verify_password
from core.security.tokens import create_access_token
from core.settings import settings


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing is not None:
            raise ConflictError("A user with this email already exists.")

        user = await self.users.create(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            password_hash=hash_password(payload.password),
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("This user account is disabled.")

        await self.users.mark_login(user)
        await self.session.commit()

        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            subject=str(user.id),
            secret_key=settings.SECRET_KEY,
            expires_delta=expires,
        )
        return TokenResponse(
            access_token=token,
            expires_in=int(expires.total_seconds()),
        )
