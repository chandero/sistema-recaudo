from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole
from app.models.user_audit import UserAuditAction
from app.schemas.auth import UserCreate, UserResponse


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_platform_admin: Optional[bool] = None
    tenant_id: Optional[int] = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.OPERATOR
    tenant_id: Optional[int] = None
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    tenant_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class PasswordReset(BaseModel):
    password: str


class PaginatedUsers(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UserAuditResponse(BaseModel):
    id: int
    tenant_id: Optional[int] = None
    actor_user_id: int
    target_user_id: int
    action: UserAuditAction
    changes: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedUserAudit(BaseModel):
    items: List[UserAuditResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UserInvitationCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.OPERATOR
    tenant_id: Optional[int] = None


class UserInvitationResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    tenant_id: Optional[int] = None
    expires_at: datetime
    email_sent: bool
    invitation_url: str


class UserInvitationAccept(BaseModel):
    token: str
    password: str


__all__ = [
    "UserCreate", "UserResponse", "UserUpdate", "AdminUserCreate",
    "AdminUserUpdate", "UserStatusUpdate", "PasswordReset", "PaginatedUsers",
    "UserAuditResponse", "PaginatedUserAudit", "UserInvitationCreate",
    "UserInvitationResponse", "UserInvitationAccept"
]
