from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON as SAJSON, Column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.process import CobroProcess
    from app.models.obligation import Obligation


class ClientBase(SQLModel):
    identification: str = Field(..., min_length=1, max_length=50, index=True)
    name: str = Field(..., min_length=1, max_length=300)
    address: Optional[str] = Field(default=None, max_length=500)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    city: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)


class Client(ClientBase, table=True):
    __tablename__ = "clients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    additional_attributes: dict = Field(default={}, sa_column=Column("additional_attributes", SAJSON))
    
    tenant: Optional["Tenant"] = Relationship(back_populates="clients")
    obligations: List["Obligation"] = Relationship(back_populates="client")