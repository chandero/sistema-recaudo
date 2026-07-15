from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole
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


__all__ = ["UserCreate", "UserResponse", "UserUpdate"]