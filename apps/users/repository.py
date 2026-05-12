from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip()),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str | None,
        password_hash: str,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip() if last_name else None,
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def mark_login(self, user: User) -> None:
        user.last_login = datetime.now(UTC)
        await self.session.flush()
