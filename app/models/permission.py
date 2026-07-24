"""Permission database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, Uuid as UUID
from sqlalchemy.orm import relationship

from apps.api.app.models.base import Base
from apps.api.app.models.enums import PermissionAction, PermissionCategory

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    resource = Column(
        String(50),
        nullable=False
    )
    action = Column(
        SQLEnum(PermissionAction, name="permissionaction", create_type=False),
        nullable=False
    )
    description = Column(
        Text,
        nullable=True
    )
    category = Column(
        SQLEnum(PermissionCategory, name="permissioncategory", create_type=False),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )
