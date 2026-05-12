from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.audit.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        action: str,
        user_id: int | None = None,
        secret_id: int | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            secret_id=secret_id,
            action=action,
            event_metadata=metadata or {},
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log
