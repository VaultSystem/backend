from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.access.models import AccessPolicy
from apps.secrets.models import Secret, SecretVersion


class SecretRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, secret_id: int) -> Secret | None:
        return await self.session.get(Secret, secret_id)

    async def get_active_by_id(self, secret_id: int) -> Secret | None:
        result = await self.session.execute(
            select(Secret).where(Secret.id == secret_id, Secret.deleted_at.is_(None)),
        )
        return result.scalar_one_or_none()

    async def get_by_owner_and_name(self, *, owner_id: int, name: str) -> Secret | None:
        result = await self.session.execute(
            select(Secret).where(
                Secret.owner_id == owner_id,
                Secret.name == name,
                Secret.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def create_secret(
        self,
        *,
        name: str,
        description: str | None,
        owner_id: int,
    ) -> Secret:
        secret = Secret(name=name, description=description, owner_id=owner_id)
        self.session.add(secret)
        await self.session.flush()
        return secret

    async def create_version(
        self,
        *,
        secret_id: int,
        encrypted_value: str,
        encrypted_data_key: str,
        version: int,
    ) -> SecretVersion:
        secret_version = SecretVersion(
            secret_id=secret_id,
            encrypted_value=encrypted_value,
            encrypted_data_key=encrypted_data_key,
            version=version,
        )
        self.session.add(secret_version)
        await self.session.flush()
        return secret_version

    async def set_current_version(self, secret: Secret, secret_version: SecretVersion) -> None:
        secret.current_version_id = secret_version.id
        await self.session.flush()

    async def update_description(self, secret: Secret, description: str | None) -> None:
        secret.description = description
        await self.session.flush()

    async def soft_delete(self, secret: Secret) -> None:
        secret.deleted_at = datetime.now(UTC)
        await self.session.flush()

    async def get_current_version(self, secret: Secret) -> SecretVersion | None:
        if secret.current_version_id is None:
            return None
        return await self.session.get(SecretVersion, secret.current_version_id)

    async def get_version(self, *, secret_id: int, version: int) -> SecretVersion | None:
        result = await self.session.execute(
            select(SecretVersion).where(
                SecretVersion.secret_id == secret_id,
                SecretVersion.version == version,
            ),
        )
        return result.scalar_one_or_none()

    async def list_versions(self, *, secret_id: int) -> list[SecretVersion]:
        result = await self.session.execute(
            select(SecretVersion)
            .where(SecretVersion.secret_id == secret_id)
            .order_by(SecretVersion.version.desc()),
        )
        return list(result.scalars().all())

    async def next_version_number(self, secret_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(SecretVersion.version), 0)).where(
                SecretVersion.secret_id == secret_id,
            ),
        )
        return int(result.scalar_one()) + 1

    async def list_accessible(
        self,
        *,
        user_id: int,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Secret], int]:
        base_query = (
            select(Secret)
            .outerjoin(
                AccessPolicy,
                AccessPolicy.secret_id == Secret.id,
            )
            .where(
                Secret.deleted_at.is_(None),
                or_(Secret.owner_id == user_id, AccessPolicy.user_id == user_id),
            )
            .distinct()
        )

        if search:
            base_query = base_query.where(Secret.name.ilike(f"%{search}%"))

        total = await self._count(base_query)
        result = await self.session.execute(
            base_query.order_by(Secret.updated_at.desc()).limit(limit).offset(offset),
        )
        return list(result.scalars().all()), total

    async def _count(self, query: Select[tuple[Secret]]) -> int:
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        result = await self.session.execute(count_query)
        return int(result.scalar_one())
