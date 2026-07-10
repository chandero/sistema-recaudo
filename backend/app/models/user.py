from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.task import Task
    from app.models.import_batch import ImportBatch


class UserRole(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class UserBase(SQLModel):
    email: str = Field(..., min_length=1, max_length=200, index=True)
    username: str = Field(..., min_length=1, max_length=100, index=True)
    full_name: str = Field(..., min_length=1, max_length=200)
    role: UserRole = Field(default=UserRole.OPERATOR)
    is_active: bool = Field(default=True)
    is_platform_admin: bool = Field(default=False)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", nullable=True, index=True)
    hashed_password: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    # permissions: List["Permission"] = Relationship(back_populates="users")  # TODO: Implementar tabla intermedia para many-to-many
    # assigned_tasks: List["Task"] = Relationship(back_populates="assigned_user")  # TODO: Corregir foreign_keys
    import_batches: List["ImportBatch"] = Relationship(back_populates="user")


class PermissionBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)


class Permission(PermissionBase, table=True):
    __tablename__ = "permissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # users: List["User"] = Relationship(back_populates="permissions")  # TODO: Implementar tabla intermedia para many-to-many
