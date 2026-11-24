"""Tarea Celery para expiración automática de estados del workflow.

Revisa procesos activos cuyo estado actual tiene max_days configurado y
ha sido superado. Ejecuta la transición automática al siguiente estado
si existe una transición automática configurada.
"""
from datetime import datetime
from sqlmodel import Session, select

from app.celery_app import celery_app
from app.core.database import engine
from app.models.process import CobroProcess, ProcessHistory, ProcessStatus
from app.models.workflow import WorkflowState, WorkflowTransition


@celery_app.task(name="app.tasks.state_expiration.check_state_expirations")
def check_state_expirations():
    """Revisa todos los procesos activos y ejecuta transiciones automáticas
    cuando se supera el max_days del estado actual."""
    expired_count = 0
    error_count = 0

    with Session(engine) as session:
        # Buscar procesos activos con estado que tenga max_days
        processes = session.exec(
            select(CobroProcess).where(
                CobroProcess.status == ProcessStatus.ACTIVE
            )
        ).all()

        for process in processes:
            try:
                state = session.get(WorkflowState, process.current_state_id)
                if not state or not state.max_days:
                    continue

                # Calcular días en estado actual
                now = datetime.utcnow()
                changed_at = process.state_changed_at or process.created_at
                days_in_state = (now - changed_at).days

                if days_in_state <= state.max_days:
                    continue

                # Buscar transición automática desde este estado
                auto_transition = session.exec(
                    select(WorkflowTransition).where(
                        WorkflowTransition.source_state_id == state.id,
                        WorkflowTransition.is_automatic == True,
                        WorkflowTransition.is_active == True,
                        WorkflowTransition.tenant_id == process.tenant_id,
                    )
                ).first()

                if not auto_transition:
                    # No hay transición automática configurada, solo registrar
                    continue

                target_state = session.get(WorkflowState, auto_transition.target_state_id)
                if not target_state:
                    continue

                # Ejecutar transición automática
                previous_state_id = process.current_state_id
                process.current_state_id = target_state.id
                process.state_changed_at = now
                process.updated_at = now

                if target_state.is_final:
                    process.status = ProcessStatus.CLOSED

                session.add(process)

                # Registrar en historial
                history = ProcessHistory(
                    tenant_id=process.tenant_id,
                    process_id=process.id,
                    user_id=None,  # Sistema
                    previous_state_id=previous_state_id,
                    new_state_id=target_state.id,
                    action="TRANSICION_AUTOMATICA",
                    description=f"Transición automática por vencimiento de {state.max_days} días en estado '{state.name}'. Proceso estuvo {days_in_state} días.",
                    extra_data={
                        "automatic": True,
                        "days_in_state": days_in_state,
                        "max_days": state.max_days,
                        "source_state": state.name,
                        "target_state": target_state.name,
                    },
                )
                session.add(history)
                expired_count += 1

            except Exception as e:
                error_count += 1
                # Continuar con el siguiente proceso
                continue

        session.commit()

    return {
        "expired": expired_count,
        "errors": error_count,
        "timestamp": datetime.utcnow().isoformat(),
    }
