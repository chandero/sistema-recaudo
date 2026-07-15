from sqlalchemy import JSON as SAJSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.process import CobroProcess
    from app.models.user import User


class TemplateType(str, Enum):
    DOCX = "DOCX"
    PDF = "PDF"


class DocumentTemplateBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=100, index=True)
    template_type: TemplateType = Field(default=TemplateType.DOCX)
    description: Optional[str] = Field(default=None, max_length=500)
    version: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)


class DocumentTemplate(DocumentTemplateBase, table=True):
    __tablename__ = "document_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    content: bytes = Field(...)
    variables_schema: Optional[dict] = Field(sa_column=Column(SAJSON), default={})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="document_templates")


class GeneratedDocumentBase(SQLModel):
    filename: str = Field(..., min_length=1, max_length=300)
    document_type: str = Field(..., max_length=100)


class GeneratedDocument(GeneratedDocumentBase, table=True):
    __tablename__ = "generated_documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    process_id: Optional[int] = Field(default=None, foreign_key="cobro_processes.id", index=True)
    template_id: Optional[int] = Field(default=None, foreign_key="document_templates.id")
    client_id: Optional[int] = Field(default=None, foreign_key="clients.id")
    obligation_id: Optional[int] = Field(default=None, foreign_key="obligations.id")
    file_path: str = Field(..., max_length=500)
    file_size: int = Field(default=0)
    variables_used: Optional[dict] = Field(sa_column=Column(SAJSON), default={})
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_sent: bool = Field(default=False)
    sent_at: Optional[datetime] = Field(default=None)
    resolution_number: Optional[str] = Field(default=None, max_length=100)
    radicado_number: Optional[str] = Field(default=None, max_length=100)
    
    tenant: Optional["Tenant"] = Relationship()
    creator: Optional["User"] = Relationship()
