from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime


class ImportMappingTemplateBase(SQLModel):
    name: str = Field(..., index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    mapping_config: Dict[str, Any] = Field(..., sa_column=Column(JSON))
    supported_fields: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)


class ImportMappingTemplate(ImportMappingTemplateBase, table=True):
    __tablename__ = "import_mapping_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    tenant: Optional["Tenant"] = Relationship(back_populates="import_mapping_templates")
    # batches: List["ImportBatch"] = Relationship(back_populates="mapping_template")  # TODO: Corregir foreign_key
