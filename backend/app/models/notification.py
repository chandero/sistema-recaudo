from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    STATE_CHANGE = "STATE_CHANGE"
    STATE_EXPIRING = "STATE_EXPIRING"
    ASSIGNMENT = "ASSIGNMENT"
    AGREEMENT = "AGREEMENT"
    INSTALLMENT_DUE = "INSTALLMENT_DUE"
    GENERAL = "GENERAL"


class Notification(SQLModel, table=True):
    """Notificaciones del sistema para usuarios."""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    user_id: int = Field(..., foreign_key="users.id", index=True)
    notification_type: NotificationType = Field(default=NotificationType.GENERAL)
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    is_read: bool = Field(default=False)
    process_id: Optional[int] = Field(default=None, foreign_key="cobro_processes.id")
    link: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = Field(default=None)
