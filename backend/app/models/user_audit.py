from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class UserAuditAction(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"
    PASSWORD_RESET = "PASSWORD_RESET"
    INVITATION_ACCEPTED = "INVITATION_ACCEPTED"


class UserAuditLog(SQLModel, table=True):
    __tablename__ = "user_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", index=True)
    actor_user_id: int = Field(foreign_key="users.id", index=True)
    target_user_id: int = Field(foreign_key="users.id", index=True)
    action: UserAuditAction = Field(index=True)
    changes: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
