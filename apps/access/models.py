from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.secrets.models import Secret
from apps.users.models import Role, User
from core.db.base import Base


class AccessPolicies(Base):
    __tablename__ = "AccessPolicies"

    user_id: Mapped[int] = mapped_column(Integer)
    secret_id: Mapped[int] = mapped_column(Integer)
    role_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="policies")
    secret: Mapped[Secret] = relationship(back_populates="applied_policies")
    role: Mapped[Role] = relationship(back_populates="roles")


class Permission(Base):
    __tablename__ = "Permissions"

    name: Mapped[str] = mapped_column(String(30), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class RolePermission(Base):
    __tablename__ = "RolePermissions"

    permission_id: Mapped[int] = mapped_column(Integer)
    role_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    permission: Mapped[Permission] = relationship(back_populates="role_permissions")
    role: Mapped[Role] = relationship(back_populates="permissions")
