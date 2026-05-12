from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.audit.repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.audit = AuditRepository(session)

    async def record(
        self,
        *,
        action: str,
        user_id: int | None = None,
        secret_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self.audit.record(
            action=action,
            user_id=user_id,
            secret_id=secret_id,
            metadata=metadata,
        )
