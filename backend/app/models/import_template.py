from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class ImportTemplateBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    column_mapping: Dict[str, str] = Field(...)
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)


class ImportTemplate(ImportTemplateBase, table=True):
    __tablename__ = "import_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="import_templates")
    creator: Optional["User"] = Relationship()
