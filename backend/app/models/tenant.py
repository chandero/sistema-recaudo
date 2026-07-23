from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.client import Client
    from app.models.process import CobroProcess
    from app.models.workflow import WorkflowState
    from app.models.document import DocumentTemplate
    from app.models.import_template import ImportTemplate
    from app.models.import_batch import ImportBatch
    from app.models.import_map import ImportMappingTemplate


class TenantBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, unique=True, index=True)
    is_active: bool = Field(default=True)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)


class Tenant(TenantBase, table=True):
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    users: List["User"] = Relationship(back_populates="tenant")
    clients: List["Client"] = Relationship(back_populates="tenant")
    processes: List["CobroProcess"] = Relationship(back_populates="tenant")
    workflow_states: List["WorkflowState"] = Relationship(back_populates="tenant")
    document_templates: List["DocumentTemplate"] = Relationship(back_populates="tenant")
    import_templates: List["ImportTemplate"] = Relationship(back_populates="tenant")
    import_batches: List["ImportBatch"] = Relationship(back_populates="tenant")
    import_mapping_templates: List["ImportMappingTemplate"] = Relationship(back_populates="tenant")
