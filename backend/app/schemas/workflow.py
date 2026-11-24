from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


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
    NOTIFICACION_WEB_PUBLICADA = "NOTIFICACION_WEB_PUBLICADA"
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


class WorkflowStateBase(BaseModel):
    code: WorkflowStateCode
    name: str
    description: Optional[str] = None
    order: int
    max_days: Optional[int] = None
    is_final: bool = False
    is_active: bool = True


class WorkflowStateCreate(WorkflowStateBase):
    pass


class WorkflowStateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    max_days: Optional[int] = None
    is_final: Optional[bool] = None
    is_active: Optional[bool] = None


class WorkflowStateResponse(WorkflowStateBase):
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowTransitionBase(BaseModel):
    name: Optional[str] = None
    is_automatic: bool = False
    condition_days: Optional[int] = None
    condition_type: Optional[str] = None
    is_active: bool = True


class WorkflowTransitionCreate(WorkflowTransitionBase):
    source_state_id: int
    target_state_id: int


class WorkflowTransitionResponse(WorkflowTransitionBase):
    id: int
    source_state_id: int
    target_state_id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class KanbanCard(BaseModel):
    process_id: int
    reference: str
    client_name: Optional[str] = None
    total_amount: float = 0
    days_in_state: int = 0
    max_days: Optional[int] = None
    state_changed_at: Optional[datetime] = None
    status: str = "ACTIVE"


class KanbanColumn(BaseModel):
    state_id: int
    state_code: str
    state_name: str
    order: int
    max_days: Optional[int] = None
    is_final: bool = False
    count: int = 0
    cards: List[KanbanCard] = []
    transitions: List[int] = []  # target_state_ids available from this column


class KanbanResponse(BaseModel):
    columns: List[KanbanColumn] = []
    total_processes: int = 0


class TransitionRuleResponse(BaseModel):
    """Regla de transición con nombres de estados (para el diseñador)."""
    id: int
    source_state_id: int
    source_state_name: str
    source_state_code: str
    target_state_id: int
    target_state_name: str
    target_state_code: str
    name: Optional[str] = None
    is_automatic: bool = False
    condition_days: Optional[int] = None
    condition_type: Optional[str] = None
    is_active: bool = True


class WorkflowDesignerResponse(BaseModel):
    """Datos completos del workflow para el diseñador visual."""
    states: List[WorkflowStateResponse] = []
    transitions: List[WorkflowTransitionResponse] = []
    state_process_counts: Dict[int, int] = {}
    total_active_processes: int = 0
    tenant_name: str = ""
