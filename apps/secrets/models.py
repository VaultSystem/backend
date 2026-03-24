from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.users.models import User
from core.db.base import Base


class Secret(Base):
    __tablename__ = "Secrets"

    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(10000), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    current_version_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(DateTime, nullable=True, default=datetime.now)
    updated_at: Mapped[int] = mapped_column(DateTime, default=datetime.now)

    owner: Mapped["User"] = relationship(back_populates="secrets")

    def __repr__(self) -> str:
        return f"Secret(id={self.id!r}, name={self.name!r}, user={self.owner.email!r})"


class SecretVersion(Base):
    __tablename__ = "SecretVersions"

    secret_id: Mapped[int] = mapped_column(Integer)
    encrypted_value: Mapped[str] = mapped_column(String)
    encrypted_data_key: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    secret: Mapped["Secret"] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return (
            f"secretVersion(id={self.id!r}, secret=(id={self.secret.id}), version={self.version!r})"
        )
