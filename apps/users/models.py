from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class User(Base):
    __tablename__ = "Users"

    first_name: Mapped[str] = mapped_column(String(30))
    last_name: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(30))
    date_joined: Mapped[datetime | None] = mapped_column(DateTime)

    password: Mapped[str] = mapped_column(String(500))

    last_login: Mapped[datetime | None] = mapped_column(DateTime)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Role(Base):
    __tablename__ = "Roles"

    name: Mapped[str] = mapped_column(String(30))
