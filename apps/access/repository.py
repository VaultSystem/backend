from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.access.models import AccessPolicy, Permission, Role, RolePermission


class AccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_permission_by_name(self, name: str) -> Permission | None:
        result = await self.session.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()

    async def create_role(self, name: str) -> Role:
        role = Role(name=name)
        self.session.add(role)
        await self.session.flush()
        return role

    async def create_permission(self, name: str) -> Permission:
        permission = Permission(name=name)
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def get_role_permission(self, role_id: int, permission_id: int) -> RolePermission | None:
        result = await self.session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            ),
        )
        return result.scalar_one_or_none()

    async def create_role_permission(self, role_id: int, permission_id: int) -> RolePermission:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        self.session.add(role_permission)
        await self.session.flush()
        return role_permission

    async def get_policy(self, *, user_id: int, secret_id: int) -> AccessPolicy | None:
        result = await self.session.execute(
            select(AccessPolicy).where(
                AccessPolicy.user_id == user_id,
                AccessPolicy.secret_id == secret_id,
            ),
        )
        return result.scalar_one_or_none()

    async def grant_policy(self, *, user_id: int, secret_id: int, role_id: int) -> AccessPolicy:
        policy = await self.get_policy(user_id=user_id, secret_id=secret_id)
        if policy is None:
            policy = AccessPolicy(user_id=user_id, secret_id=secret_id, role_id=role_id)
            self.session.add(policy)
        else:
            policy.role_id = role_id

        await self.session.flush()
        return policy

    async def user_has_permission(self, *, user_id: int, secret_id: int, permission: str) -> bool:
        result = await self.session.execute(
            select(AccessPolicy.id)
            .join(Role, AccessPolicy.role_id == Role.id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                AccessPolicy.user_id == user_id,
                AccessPolicy.secret_id == secret_id,
                Permission.name == permission,
            )
            .limit(1),
        )
        return result.scalar_one_or_none() is not None
