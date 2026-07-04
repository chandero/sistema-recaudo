from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.client import Client, Obligation
    from app.models.process import CobroProcess
    from app.models.workflow import WorkflowState
    from app.models.document import DocumentTemplate
    from app.models.import_template import ImportTemplate


class TenantBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, unique=True, index=True)
    is_active: bool = Field(default=True)


class Tenant(TenantBase, table=True):
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    users: List["User"] = Relationship(back_populates="tenant")
    clients: List["Client"] = Relationship(back_populates="tenant")
    obligations: List["Obligation"] = Relationship(back_populates="tenant")
    processes: List["CobroProcess"] = Relationship(back_populates="tenant")
    workflow_states: List["WorkflowState"] = Relationship(back_populates="tenant")
    document_templates: List["DocumentTemplate"] = Relationship(back_populates="tenant")
    import_templates: List["ImportTemplate"] = Relationship(back_populates="tenant")
