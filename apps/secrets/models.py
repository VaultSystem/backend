from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base

if TYPE_CHECKING:
    from apps.access.models import AccessPolicy
    from apps.audit.models import AuditLog
    from apps.users.models import User


class Secret(Base):
    __tablename__ = "secrets"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_secrets_owner_name"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("secret_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_secrets",
        foreign_keys=[owner_id],
    )
    current_version: Mapped["SecretVersion | None"] = relationship(
        "SecretVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    versions: Mapped[list["SecretVersion"]] = relationship(
        "SecretVersion",
        back_populates="secret",
        cascade="all, delete-orphan",
        foreign_keys="SecretVersion.secret_id",
        order_by="SecretVersion.version",
    )
    access_policies: Mapped[list["AccessPolicy"]] = relationship(
        "AccessPolicy",
        back_populates="secret",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="secret",
    )

    def __repr__(self) -> str:
        return f"Secret(id={self.id!r}, name={self.name!r}, owner_id={self.owner_id!r})"


class SecretVersion(Base):
    __tablename__ = "secret_versions"
    __table_args__ = (
        UniqueConstraint("secret_id", "version", name="uq_secret_versions_secret_version"),
    )

    secret_id: Mapped[int] = mapped_column(
        ForeignKey("secrets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_data_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    secret: Mapped["Secret"] = relationship(
        "Secret",
        back_populates="versions",
        foreign_keys=[secret_id],
    )

    def __repr__(self) -> str:
        return (
            f"SecretVersion(id={self.id!r}, "
            f"secret_id={self.secret_id!r}, version={self.version!r})"
        )
