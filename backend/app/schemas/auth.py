from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: str = "OPERATOR"
    tenant_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    is_platform_admin: bool
    tenant_id: Optional[int] = None
    
    class Config:
        from_attributes = True
