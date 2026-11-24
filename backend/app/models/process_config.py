from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class TenantProcessConfigBase(SQLModel):
    prefijo_resolucion: str = Field(default="RES-2024", max_length=50)
    numero_inicial: int = Field(default=1000, ge=0)
    numero_actual: int = Field(default=1000, ge=0)
    prefijo_radicado: str = Field(default="RAD-2024", max_length=50)
    radicado_inicial: int = Field(default=5000, ge=0)
    radicado_actual: int = Field(default=5000, ge=0)


class TenantProcessConfig(TenantProcessConfigBase, table=True):
    __tablename__ = "tenant_process_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
