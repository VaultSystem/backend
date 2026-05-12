from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.access.service import AccessService
from apps.audit.service import AuditService
from apps.secrets.models import Secret, SecretVersion
from apps.secrets.repository import SecretRepository
from apps.secrets.schemas import (
    PaginatedSecrets,
    SecretCreate,
    SecretGrantRequest,
    SecretRead,
    SecretRollbackRequest,
    SecretUpdate,
    SecretValueRead,
    SecretVersionRead,
)
from apps.users.models import User
from apps.users.repository import UserRepository
from core.exceptions import ConflictError, NotFoundError
from core.security.encryption import EnvelopeEncryptionService
from core.settings import settings


class SecretService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.secrets = SecretRepository(session)
        self.users = UserRepository(session)
        self.access = AccessService(session)
        self.audit = AuditService(session)
        self.crypto = EnvelopeEncryptionService(
            settings.MASTER_KEY,
            allow_derived_dev_key=settings.ENVIRONMENT.lower() != "prod",
        )

    async def create_secret(self, *, actor: User, payload: SecretCreate) -> SecretRead:
        existing = await self.secrets.get_by_owner_and_name(
            owner_id=actor.id,
            name=payload.name,
        )
        if existing is not None:
            raise ConflictError("A secret with this name already exists for this owner.")

        encrypted = self.crypto.encrypt_secret(payload.value)
        secret = await self.secrets.create_secret(
            name=payload.name,
            description=payload.description,
            owner_id=actor.id,
        )
        version = await self.secrets.create_version(
            secret_id=secret.id,
            encrypted_value=encrypted.encrypted_value,
            encrypted_data_key=encrypted.encrypted_data_key,
            version=1,
        )
        await self.secrets.set_current_version(secret, version)
        await self.access.grant_owner(user_id=actor.id, secret_id=secret.id)
        await self.audit.record(
            action="secret.created",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={"version": 1},
        )

        await self.session.commit()
        await self.session.refresh(secret)
        return SecretRead.model_validate(secret)

    async def list_secrets(
        self,
        *,
        actor: User,
        search: str | None,
        limit: int,
        offset: int,
    ) -> PaginatedSecrets:
        items, total = await self.secrets.list_accessible(
            user_id=actor.id,
            search=search,
            limit=limit,
            offset=offset,
        )
        return PaginatedSecrets(
            items=[SecretRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def read_secret(
        self,
        *,
        actor: User,
        secret_id: int,
        version: int | None = None,
    ) -> SecretValueRead:
        secret = await self._get_active_secret(secret_id)
        await self.access.require_permission(actor, secret, "read")

        secret_version = await self._get_secret_version(secret, version)
        value = self.crypto.decrypt_secret(
            secret_version.encrypted_value,
            secret_version.encrypted_data_key,
        )
        await self.audit.record(
            action="secret.read",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={"version": secret_version.version},
        )
        await self.session.commit()

        return self._to_value_read(secret, secret_version, value)

    async def update_secret(
        self,
        *,
        actor: User,
        secret_id: int,
        payload: SecretUpdate,
    ) -> SecretRead:
        secret = await self._get_active_secret(secret_id)
        await self.access.require_permission(actor, secret, "write")

        encrypted = self.crypto.encrypt_secret(payload.value)
        version_number = await self.secrets.next_version_number(secret.id)
        version = await self.secrets.create_version(
            secret_id=secret.id,
            encrypted_value=encrypted.encrypted_value,
            encrypted_data_key=encrypted.encrypted_data_key,
            version=version_number,
        )
        await self.secrets.set_current_version(secret, version)
        if payload.description is not None:
            await self.secrets.update_description(secret, payload.description)

        await self.audit.record(
            action="secret.updated",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={"version": version_number},
        )
        await self.session.commit()
        await self.session.refresh(secret)
        return SecretRead.model_validate(secret)

    async def delete_secret(self, *, actor: User, secret_id: int) -> None:
        secret = await self._get_active_secret(secret_id)
        await self.access.require_permission(actor, secret, "delete")
        await self.secrets.soft_delete(secret)
        await self.audit.record(
            action="secret.deleted",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={},
        )
        await self.session.commit()

    async def list_versions(self, *, actor: User, secret_id: int) -> list[SecretVersionRead]:
        secret = await self._get_active_secret(secret_id)
        await self.access.require_permission(actor, secret, "read")
        versions = await self.secrets.list_versions(secret_id=secret.id)
        return [SecretVersionRead.model_validate(version) for version in versions]

    async def rollback(
        self,
        *,
        actor: User,
        secret_id: int,
        payload: SecretRollbackRequest,
    ) -> SecretRead:
        secret = await self._get_active_secret(secret_id)
        await self.access.require_permission(actor, secret, "write")

        source_version = await self._get_secret_version(secret, payload.version)
        source_value = self.crypto.decrypt_secret(
            source_version.encrypted_value,
            source_version.encrypted_data_key,
        )

        encrypted = self.crypto.encrypt_secret(source_value)
        new_version_number = await self.secrets.next_version_number(secret.id)
        new_version = await self.secrets.create_version(
            secret_id=secret.id,
            encrypted_value=encrypted.encrypted_value,
            encrypted_data_key=encrypted.encrypted_data_key,
            version=new_version_number,
        )
        await self.secrets.set_current_version(secret, new_version)
        await self.audit.record(
            action="secret.rolled_back",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={
                "source_version": source_version.version,
                "new_version": new_version_number,
            },
        )
        await self.session.commit()
        await self.session.refresh(secret)
        return SecretRead.model_validate(secret)

    async def grant_access(
        self,
        *,
        actor: User,
        secret_id: int,
        payload: SecretGrantRequest,
    ) -> None:
        secret = await self._get_active_secret(secret_id)
        target_user = await self.users.get_by_id(payload.user_id)
        await self.access.grant(
            actor=actor,
            target_user=target_user,
            secret=secret,
            role_name=payload.role,
        )
        await self.session.commit()

    async def _get_active_secret(self, secret_id: int) -> Secret:
        secret = await self.secrets.get_active_by_id(secret_id)
        if secret is None:
            raise NotFoundError("Secret was not found.")
        return secret

    async def _get_secret_version(self, secret: Secret, version: int | None) -> SecretVersion:
        if version is None:
            secret_version = await self.secrets.get_current_version(secret)
        else:
            secret_version = await self.secrets.get_version(
                secret_id=secret.id,
                version=version,
            )

        if secret_version is None:
            raise NotFoundError("Secret version was not found.")
        return secret_version

    def _to_value_read(
        self,
        secret: Secret,
        version: SecretVersion,
        value: str,
    ) -> SecretValueRead:
        return SecretValueRead(
            id=secret.id,
            name=secret.name,
            description=secret.description,
            owner_id=secret.owner_id,
            current_version_id=secret.current_version_id,
            created_at=secret.created_at,
            updated_at=secret.updated_at,
            value=value,
            version=version.version,
        )
