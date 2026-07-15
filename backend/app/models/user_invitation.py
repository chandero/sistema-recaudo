from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.user import UserRole


class UserInvitation(SQLModel, table=True):
    __tablename__ = "user_invitations"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", index=True)
    created_by_user_id: int = Field(foreign_key="users.id", index=True)
    email: str = Field(max_length=200, index=True)
    username: str = Field(max_length=100, index=True)
    full_name: str = Field(max_length=200)
    role: UserRole
    token_hash: str = Field(max_length=64, unique=True, index=True)
    expires_at: datetime = Field(index=True)
    accepted_at: Optional[datetime] = Field(default=None)
    revoked_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
