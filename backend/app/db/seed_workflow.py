"""
Seed inicial para el workflow de cobro de alumbrado público.
Crea los estados, transiciones y reglas automáticas del workflow.
"""

from sqlmodel import Session, select
from app.core.database import engine
from app.models.workflow import WorkflowState, WorkflowStateCode, WorkflowTransition
from app.models.tenant import Tenant


def get_or_create_state(
    session: Session,
    code: WorkflowStateCode,
    name: str,
    description: str,
    order: int,
    max_days: int | None = None,
    is_final: bool = False,
    tenant_id: int | None = None
):
    """Obtiene o crea un estado del workflow."""
    statement = select(WorkflowState).where(
        WorkflowState.code == code,
        WorkflowState.tenant_id == tenant_id
    )
    state = session.exec(statement).first()
    
    if not state:
        state = WorkflowState(
            code=code,
            name=name,
            description=description,
            order=order,
            max_days=max_days,
            is_final=is_final,
            tenant_id=tenant_id,
            is_active=True
        )
        session.add(state)
        session.commit()
        session.refresh(state)
    
    return state


def create_transition(
    session: Session,
    source_state: WorkflowState,
    target_state: WorkflowState,
    name: str | None = None,
    is_automatic: bool = False,
    condition_days: int | None = None,
    condition_type: str | None = None,
    tenant_id: int | None = None
):
    """Crea una transición entre estados."""
    transition = WorkflowTransition(
        source_state_id=source_state.id,
        target_state_id=target_state.id,
        name=name,
        is_automatic=is_automatic,
        condition_days=condition_days,
        condition_type=condition_type,
        tenant_id=tenant_id,
        is_active=True
    )
    session.add(transition)
    session.commit()
    return transition


def seed_workflow_states(session: Session, tenant_id: int | None = None):
    """Crea todos los estados del workflow de cobro de alumbrado público."""
    
    states_config = [
        {
            "code": WorkflowStateCode.CARTERA_CARGADA,
            "name": "Cartera Cargada",
            "description": "Cartera importada desde archivo o creada manualmente",
            "order": 1,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.OBLIGACION_VALIDADA,
            "name": "Obligación Validada",
            "description": "Validación de datos, duplicados y valores completada",
            "order": 2,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.PENDIENTE_ASIGNACION_RESOLUCION,
            "name": "Pendiente Asignación Resolución",
            "description": "Pendiente asignación de resolución/radicados",
            "order": 3,
            "max_days": 5,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.RESOLUCION_RADICADOS_ASIGNADOS,
            "name": "Resolución y Radicados Asignados",
            "description": "Consecutivos reservados y asignados",
            "order": 4,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.DOCUMENTO_NOTIFICACION_GENERADO,
            "name": "Documento de Notificación Generado",
            "description": "Cartas o actos administrativos generados",
            "order": 5,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.NOTIFICACION_ENVIADA,
            "name": "Notificación Enviada",
            "description": "Correspondencia registrada con guía de envío",
            "order": 6,
            "max_days": 10,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.ESPERANDO_RESULTADO_NOTIFICACION,
            "name": "Esperando Resultado Notificación",
            "description": "En espera de confirmación de entrega o devolución",
            "order": 7,
            "max_days": 15,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.NOTIFICACION_ENTREGADA,
            "name": "Notificación Entregada",
            "description": "Entrega de correspondencia confirmada",
            "order": 8,
            "max_days": 10,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.NOTIFICACION_DEVUELTA,
            "name": "Notificación Devuelta",
            "description": "Correspondencia devuelta o no entregada",
            "order": 9,
            "max_days": 5,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.NOTIFICACION_WEB_PUBLICADA,
            "name": "Notificación Web Publicada",
            "description": "Notificación publicada en página web de la entidad (fijación en lista)",
            "order": 10,
            "max_days": 10,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.REINTENTO_NOTIFICACION,
            "name": "Reintento Notificación",
            "description": "Corrección de datos y nuevo envío de correspondencia",
            "order": 11,
            "max_days": 5,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.ESPERANDO_PAGO_VOLUNTARIO,
            "name": "Esperando Pago Voluntario",
            "description": "Plazo de pago voluntario después de notificación efectiva",
            "order": 12,
            "max_days": 15,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.COBRO_PERSUASIVO,
            "name": "Cobro Persuasivo",
            "description": "Gestiones persuasivas de cobro (llamadas, visitas, mensajes)",
            "order": 13,
            "max_days": 30,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.ACUERDO_DE_PAGO,
            "name": "Acuerdo de Pago",
            "description": "Acuerdo de pago registrado con el contribuyente",
            "order": 14,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.SEGUIMIENTO_ACUERDO,
            "name": "Seguimiento Acuerdo",
            "description": "Seguimiento de cuotas del acuerdo de pago",
            "order": 15,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.ACUERDO_INCUMPLIDO,
            "name": "Acuerdo Incumplido",
            "description": "Incumplimiento detectado en acuerdo de pago",
            "order": 16,
            "max_days": 5,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.COBRO_PREJURIDICO,
            "name": "Cobro Prejurídico",
            "description": "Escalamiento a etapa prejudicial",
            "order": 17,
            "max_days": 30,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.COBRO_COACTIVO,
            "name": "Cobro Coactivo",
            "description": "Proceso coactivo/jurídico iniciado",
            "order": 18,
            "max_days": None,
            "is_final": False
        },
        {
            "code": WorkflowStateCode.PAGADO,
            "name": "Pagado",
            "description": "Obligación pagada totalmente",
            "order": 19,
            "max_days": None,
            "is_final": True
        },
        {
            "code": WorkflowStateCode.ARCHIVADO,
            "name": "Archivado",
            "description": "Expediente cerrado/archivado",
            "order": 20,
            "max_days": None,
            "is_final": True
        },
        {
            "code": WorkflowStateCode.INCOBRABLE,
            "name": "Incobrable",
            "description": "Obligación marcada como incobrable",
            "order": 21,
            "max_days": None,
            "is_final": True
        }
    ]
    
    states_map = {}
    for config in states_config:
        state = get_or_create_state(session, **config, tenant_id=tenant_id)
        states_map[state.code] = state
    
    return states_map


def seed_workflow_transitions(session: Session, states_map: dict, tenant_id: int | None = None):
    """Crea las transiciones del workflow según las reglas de negocio."""
    
    transitions = [
        # Flujo normal inicial
        ("CARTERA_CARGADA", "OBLIGACION_VALIDADA", "Validar obligación", False, None, None),
        ("OBLIGACION_VALIDADA", "PENDIENTE_ASIGNACION_RESOLUCION", "Asignar resolución", False, None, None),
        ("PENDIENTE_ASIGNACION_RESOLUCION", "RESOLUCION_RADICADOS_ASIGNADOS", "Resolución asignada", False, None, None),
        ("RESOLUCION_RADICADOS_ASIGNADOS", "DOCUMENTO_NOTIFICACION_GENERADO", "Generar documento", False, None, None),
        ("DOCUMENTO_NOTIFICACION_GENERADO", "NOTIFICACION_ENVIADA", "Enviar notificación", False, None, None),
        
        # Resultados de notificación
        ("NOTIFICACION_ENVIADA", "ESPERANDO_RESULTADO_NOTIFICACION", "Esperar resultado", True, 10, "days_without_confirmation"),
        ("ESPERANDO_RESULTADO_NOTIFICACION", "NOTIFICACION_ENTREGADA", "Confirmar entrega", False, None, "delivery_confirmed"),
        ("ESPERANDO_RESULTADO_NOTIFICACION", "NOTIFICACION_DEVUELTA", "Registrar devolución", False, None, "mail_returned"),
        ("ESPERANDO_RESULTADO_NOTIFICACION", "NOTIFICACION_WEB_PUBLICADA", "Publicar en web", False, None, "web_publication"),
        
        # Manejo de notificación devuelta
        ("NOTIFICACION_DEVUELTA", "REINTENTO_NOTIFICACION", "Corregir dirección", False, None, "address_corrected"),
        ("REINTENTO_NOTIFICACION", "NOTIFICACION_ENVIADA", "Reenviar notificación", False, None, "new_mail_sent"),
        ("NOTIFICACION_DEVUELTA", "NOTIFICACION_WEB_PUBLICADA", "Publicar en web por devolución", False, None, "web_after_return"),
        
        # Después de notificación efectiva
        ("NOTIFICACION_ENTREGADA", "ESPERANDO_PAGO_VOLUNTARIO", "Iniciar plazo pago", False, None, None),
        ("NOTIFICACION_WEB_PUBLICADA", "ESPERANDO_PAGO_VOLUNTARIO", "Iniciar plazo pago web", False, None, None),
        ("ESPERANDO_PAGO_VOLUNTARIO", "COBRO_PERSUASIVO", "Iniciar cobro persuasivo", True, 15, "no_payment"),
        
        # Cobro persuasivo y acuerdos
        ("COBRO_PERSUASIVO", "ACUERDO_DE_PAGO", "Aceptar acuerdo", False, None, "payment_agreement_accepted"),
        ("COBRO_PERSUASIVO", "COBRO_PREJURIDICO", "Sin respuesta", True, 30, "no_response"),
        ("COBRO_PERSUASIVO", "PAGADO", "Pago total", False, None, "full_payment"),
        
        # Seguimiento de acuerdos
        ("ACUERDO_DE_PAGO", "SEGUIMIENTO_ACUERDO", "Iniciar seguimiento", False, None, None),
        ("SEGUIMIENTO_ACUERDO", "ACUERDO_INCUMPLIDO", "Cuota vencida", True, None, "installment_overdue"),
        ("SEGUIMIENTO_ACUERDO", "PAGADO", "Acuerdo completado", False, None, "agreement_completed"),
        
        # Incumplimiento y escalamiento
        ("ACUERDO_INCUMPLIDO", "COBRO_COACTIVO", "Escalar a coactivo", True, 5, "escalation"),
        ("COBRO_PREJURIDICO", "COBRO_COACTIVO", "Escalar a coactivo", False, None, "legal_escalation"),
        
        # Estados finales
        ("COBRO_COACTIVO", "PAGADO", "Pago en etapa coactiva", False, None, "payment_coactive"),
        ("COBRO_COACTIVO", "ARCHIVADO", "Archivar proceso", False, None, "archive_process"),
        ("COBRO_PERSUASIVO", "INCOBRABLE", "Marcar como incobrable", False, None, "uncollectible"),
        ("COBRO_PREJURIDICO", "INCOBRABLE", "Marcar como incobrable", False, None, "uncollectible_prelegal"),
        
        # Pago desde cualquier estado (se manejará en lógica de negocio)
        # Esto es conceptual, en la práctica se valida en el servicio
    ]
    
    for transition_data in transitions:
        source_code, target_code, name, is_auto, cond_days, cond_type = transition_data
        
        if source_code in states_map and target_code in states_map:
            create_transition(
                session=session,
                source_state=states_map[source_code],
                target_state=states_map[target_code],
                name=name,
                is_automatic=is_auto,
                condition_days=cond_days,
                condition_type=cond_type,
                tenant_id=tenant_id
            )


def seed_initial_workflow():
    """Función principal para sembrar el workflow inicial."""
    with Session(engine) as session:
        print("Creando estados del workflow...")
        states_map = seed_workflow_states(session)
        print(f"✓ {len(states_map)} estados creados")
        
        print("Creando transiciones del workflow...")
        seed_workflow_transitions(session, states_map)
        print("✓ Transiciones creadas")
        
        print("\n✅ Seed del workflow completado exitosamente!")
        print("\nEstados disponibles:")
        for code, state in sorted(states_map.items(), key=lambda x: x[1].order):
            final_marker = " [FINAL]" if state.is_final else ""
            days_info = f" (max {state.max_days} días)" if state.max_days else ""
            print(f"  {state.order}. {state.name}{final_marker}{days_info}")


if __name__ == "__main__":
    seed_initial_workflow()
