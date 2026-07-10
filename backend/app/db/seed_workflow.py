"""
Seed data para los estados del workflow de cobro.
Este archivo crea los 20 estados predefinidos para el proceso de cobro.
"""

from sqlmodel import Session
from app.models.workflow import WorkflowState, WorkflowStateCode


WORKFLOW_STATES = [
    {
        "code": WorkflowStateCode.CARTERA_CARGADA,
        "name": "Cartera Cargada",
        "description": "Cartera cargada en el sistema",
        "order": 1,
        "max_days": 0,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.OBLIGACION_VALIDADA,
        "name": "Obligación Validada",
        "description": "Obligación validada por el usuario",
        "order": 2,
        "max_days": 0,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.PENDIENTE_ASIGNACION_RESOLUCION,
        "name": "Pendiente Asignación Resolución",
        "description": "Esperando asignación de radicado",
        "order": 3,
        "max_days": 5,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.RESOLUCION_RADICADOS_ASIGNADOS,
        "name": "Resolución/Radicados Asignados",
        "description": "Radicado y resolución asignados",
        "order": 4,
        "max_days": 10,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.DOCUMENTO_NOTIFICACION_GENERADO,
        "name": "Documento Notificación Generado",
        "description": "Carta de notificación generada",
        "order": 5,
        "max_days": 3,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.NOTIFICACION_ENVIADA,
        "name": "Notificación Enviada",
        "description": "Carta enviada por correo u otro medio",
        "order": 6,
        "max_days": 15,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.ESPERANDO_RESULTADO_NOTIFICACION,
        "name": "Esperando Resultado Notificación",
        "description": "Esperando confirmación de entrega",
        "order": 7,
        "max_days": 10,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.NOTIFICACION_ENTREGADA,
        "name": "Notificación Entregada",
        "description": "Notificación entregada al deudor",
        "order": 8,
        "max_days": 30,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.NOTIFICACION_DEVUELTA,
        "name": "Notificación Devuelta",
        "description": "Carta devuelta por_correo",
        "order": 9,
        "max_days": 5,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.REINTENTO_NOTIFICACION,
        "name": "Reintento Notificación",
        "description": "Reintento de notificación",
        "order": 10,
        "max_days": 10,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.ESPERANDO_PAGO_VOLUNTARIO,
        "name": "Esperando Pago Voluntario",
        "description": "Período de pago voluntario",
        "order": 11,
        "max_days": 30,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.COBRO_PERSUASIVO,
        "name": "Cobro Persuasivo",
        "description": "Llamadas, visitas y negociaciones",
        "order": 12,
        "max_days": 45,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.ACUERDO_DE_PAGO,
        "name": "Acuerdo de Pago",
        "description": "Acuerdo formal de pago",
        "order": 13,
        "max_days": 0,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.SEGUIMIENTO_ACUERDO,
        "name": "Seguimiento Acuerdo",
        "description": "Seguimiento a pagos acordados",
        "order": 14,
        "max_days": 60,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.ACUERDO_INCUMPLIDO,
        "name": "Acuerdo Incumplido",
        "description": "No se cumplió el acuerdo",
        "order": 15,
        "max_days": 5,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.COBRO_PREJURIDICO,
        "name": "Cobro Prejurídico",
        "description": "Intimidación legal formal",
        "order": 16,
        "max_days": 60,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.COBRO_COACTIVO,
        "name": "Cobro Coactivo",
        "description": "Ejecución coactiva",
        "order": 17,
        "max_days": 180,
        "is_final": False
    },
    {
        "code": WorkflowStateCode.PAGADO,
        "name": "Pagado",
        "description": "Deuda completamente pagada",
        "order": 18,
        "max_days": 0,
        "is_final": True
    },
    {
        "code": WorkflowStateCode.ARCHIVADO,
        "name": "Archivado",
        "description": "Carpeta archivada sin actividad",
        "order": 19,
        "max_days": 0,
        "is_final": True
    },
    {
        "code": WorkflowStateCode.INCOBRABLE,
        "name": "Incobrable",
        "description": "Deuda declarada incobrable",
        "order": 20,
        "max_days": 0,
        "is_final": True
    },
]


def seed_workflow(session: Session, tenant_id: int):
    """
    Seed los estados del workflow para un tenant específico.
    
    Args:
        session: Sesión de base de datos
        tenant_id: ID del tenant
    
    Returns:
        Dict con estadísticas del seed
    """
    stats = {
        "created": 0,
        "updated": 0,
        "errors": 0
    }
    
    for state_data in WORKFLOW_STATES:
        try:
            # Verificar si ya existe
            from sqlmodel import select
            statement = select(WorkflowState).where(
                WorkflowState.code == state_data["code"].value,
                WorkflowState.tenant_id == tenant_id
            )
            existing = session.exec(statement).first()
            
            if existing:
                # Actualizar si es necesario
                if existing.name != state_data["name"]:
                    existing.name = state_data["name"]
                    existing.description = state_data["description"]
                    existing.order = state_data["order"]
                    existing.max_days = state_data["max_days"]
                    existing.is_final = state_data["is_final"]
                    session.add(existing)
                    stats["updated"] += 1
            else:
                # Crear nuevo estado
                state = WorkflowState(
                    code=state_data["code"].value,
                    name=state_data["name"],
                    description=state_data["description"],
                    order=state_data["order"],
                    max_days=state_data["max_days"],
                    is_final=state_data["is_final"],
                    tenant_id=tenant_id,
                    is_active=True
                )
                session.add(state)
                stats["created"] += 1
                
        except Exception as e:
            stats["errors"] += 1
            print(f"Error seeding state {state_data['code']}: {str(e)}")
    
    session.commit()
    
    return stats


def get_initial_workflow_states():
    """
    Obtener los estados iniciales del workflow.
    
    Returns:
        List[Dict]: Lista de estados
    """
    return WORKFLOW_STATES