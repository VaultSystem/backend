from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.access.models import Role
from apps.access.repository import AccessRepository
from apps.audit.service import AuditService
from apps.secrets.models import Secret
from apps.users.models import User
from core.exceptions import BadRequestError, ForbiddenError, NotFoundError

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "viewer": ("read",),
    "editor": ("read", "write"),
    "owner": ("read", "write", "delete", "grant"),
}


class AccessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.access = AccessRepository(session)
        self.audit = AuditService(session)

    async def ensure_builtin_roles(self) -> None:
        permission_cache = {}
        for permission_name in sorted({p for values in ROLE_PERMISSIONS.values() for p in values}):
            permission = await self.access.get_permission_by_name(permission_name)
            if permission is None:
                permission = await self.access.create_permission(permission_name)
            permission_cache[permission_name] = permission

        for role_name, permission_names in ROLE_PERMISSIONS.items():
            role = await self.access.get_role_by_name(role_name)
            if role is None:
                role = await self.access.create_role(role_name)

            for permission_name in permission_names:
                role_permission = await self.access.get_role_permission(
                    role.id,
                    permission_cache[permission_name].id,
                )
                if role_permission is None:
                    await self.access.create_role_permission(
                        role.id,
                        permission_cache[permission_name].id,
                    )

    async def get_role(self, role_name: str) -> Role:
        await self.ensure_builtin_roles()
        role = await self.access.get_role_by_name(role_name)
        if role is None:
            raise BadRequestError("Unknown access role.", details={"role": role_name})
        return role

    async def grant_owner(self, *, user_id: int, secret_id: int) -> None:
        role = await self.get_role("owner")
        await self.access.grant_policy(user_id=user_id, secret_id=secret_id, role_id=role.id)

    async def grant(
        self,
        *,
        actor: User,
        target_user: User | None,
        secret: Secret,
        role_name: str,
    ) -> None:
        if target_user is None:
            raise NotFoundError("Target user was not found.")

        await self.require_permission(actor, secret, "grant")
        role = await self.get_role(role_name)
        await self.access.grant_policy(
            user_id=target_user.id,
            secret_id=secret.id,
            role_id=role.id,
        )
        await self.audit.record(
            action="access.granted",
            user_id=actor.id,
            secret_id=secret.id,
            metadata={"target_user_id": target_user.id, "role": role.name},
        )

    async def require_permission(self, user: User, secret: Secret, permission: str) -> None:
        if secret.owner_id == user.id:
            return

        await self.ensure_builtin_roles()
        allowed = await self.access.user_has_permission(
            user_id=user.id,
            secret_id=secret.id,
            permission=permission,
        )
        if not allowed:
            raise ForbiddenError(
                "You do not have permission to perform this action on this secret.",
                details={"permission": permission},
            )
