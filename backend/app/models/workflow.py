from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class WorkflowStateCode(str, Enum):
    CARTERA_CARGADA = "CARTERA_CARGADA"
    OBLIGACION_VALIDADA = "OBLIGACION_VALIDADA"
    PENDIENTE_ASIGNACION_RESOLUCION = "PENDIENTE_ASIGNACION_RESOLUCION"
    RESOLUCION_RADICADOS_ASIGNADOS = "RESOLUCION_RADICADOS_ASIGNADOS"
    DOCUMENTO_NOTIFICACION_GENERADO = "DOCUMENTO_NOTIFICACION_GENERADO"
    NOTIFICACION_ENVIADA = "NOTIFICACION_ENVIADA"
    ESPERANDO_RESULTADO_NOTIFICACION = "ESPERANDO_RESULTADO_NOTIFICACION"
    NOTIFICACION_ENTREGADA = "NOTIFICACION_ENTREGADA"
    NOTIFICACION_DEVUELTA = "NOTIFICACION_DEVUELTA"
    REINTENTO_NOTIFICACION = "REINTENTO_NOTIFICACION"
    ESPERANDO_PAGO_VOLUNTARIO = "ESPERANDO_PAGO_VOLUNTARIO"
    COBRO_PERSUASIVO = "COBRO_PERSUASIVO"
    ACUERDO_DE_PAGO = "ACUERDO_DE_PAGO"
    SEGUIMIENTO_ACUERDO = "SEGUIMIENTO_ACUERDO"
    ACUERDO_INCUMPLIDO = "ACUERDO_INCUMPLIDO"
    COBRO_PREJURIDICO = "COBRO_PREJURIDICO"
    COBRO_COACTIVO = "COBRO_COACTIVO"
    PAGADO = "PAGADO"
    ARCHIVADO = "ARCHIVADO"
    INCOBRABLE = "INCOBRABLE"


class WorkflowStateBase(SQLModel):
    code: WorkflowStateCode = Field(..., index=True)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    order: int = Field(..., ge=0)
    max_days: Optional[int] = Field(default=None, ge=0)
    is_final: bool = Field(default=False)
    is_active: bool = Field(default=True)


class WorkflowState(WorkflowStateBase, table=True):
    __tablename__ = "workflow_states"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", nullable=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="workflow_states")


class WorkflowTransitionBase(SQLModel):
    name: Optional[str] = Field(default=None, max_length=200)
    is_automatic: bool = Field(default=False)
    condition_days: Optional[int] = Field(default=None, ge=0)
    condition_type: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class WorkflowTransition(WorkflowTransitionBase, table=True):
    __tablename__ = "workflow_transitions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source_state_id: int = Field(..., foreign_key="workflow_states.id", index=True)
    target_state_id: int = Field(..., foreign_key="workflow_states.id", index=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
