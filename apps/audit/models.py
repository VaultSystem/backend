from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base

if TYPE_CHECKING:
    from apps.secrets.models import Secret
    from apps.users.models import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    secret_id: Mapped[int | None] = mapped_column(
        ForeignKey("secrets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
    secret: Mapped["Secret | None"] = relationship("Secret", back_populates="audit_logs")
