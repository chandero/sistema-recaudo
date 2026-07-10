from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.process import CobroProcess


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
    
    tenant: Optional["Tenant"] = Relationship(back_populates="clients")
    obligations: List["Obligation"] = Relationship(back_populates="client")


class ObligationBase(SQLModel):
    numero_obligacion: str = Field(..., min_length=1, max_length=100, index=True)
    vigencia: str = Field(..., min_length=1, max_length=20)
    valor_total: float = Field(..., ge=0)
    capital: float = Field(default=0, ge=0)
    intereses: float = Field(default=0, ge=0)
    mora: float = Field(default=0, ge=0)
    fecha_emision: Optional[datetime] = Field(default=None)
    fecha_vencimiento: Optional[datetime] = Field(default=None)


class Obligation(ObligationBase, table=True):
    __tablename__ = "obligations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    client_id: int = Field(..., foreign_key="clients.id", index=True)
    process_id: Optional[int] = Field(default=None, foreign_key="cobro_processes.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="obligations")
    client: Optional["Client"] = Relationship(back_populates="obligations")
    process: Optional["CobroProcess"] = Relationship(back_populates="obligations")
