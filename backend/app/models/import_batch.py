from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ImportStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    MAPPING = "MAPPING"  # Esperando mapeo del usuario
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"  # Completado con errores


class ImportBatchBase(SQLModel):
    total_rows: int = Field(default=0)
    processed_rows: int = Field(default=0)
    success_rows: int = Field(default=0)
    error_rows: int = Field(default=0)
    status: ImportStatus = Field(default=ImportStatus.PENDING)
    mapping_template_id: Optional[int] = Field(default=None)
    import_options: Dict[str, Any] = Field(default={}, sa_column=Column("import_options", JSON))
    errors_log: List[Dict[str, Any]] = Field(default=[], sa_column=Column("errors_log", JSON))
    completed_at: Optional[datetime] = Field(default=None)


class ImportBatch(ImportBatchBase, table=True):
    __tablename__ = "import_batches"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    user_id: int = Field(..., foreign_key="users.id", index=True)
    filename: str = Field(...)
    original_filename: str = Field(...)
    file_path: Optional[str] = Field(default=None)
    custom_mapping: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column("custom_mapping", JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    tenant: Optional["Tenant"] = Relationship(back_populates="import_batches")
    user: Optional["User"] = Relationship(back_populates="import_batches")
    # mapping_template: Optional["ImportMappingTemplate"] = Relationship(back_populates="batches")  # TODO: Corregir foreign_key
