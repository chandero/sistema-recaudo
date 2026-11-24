from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime
from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.process import CobroProcess, ProcessHistory, ProcessStatus
from app.models.user import User
from app.models.client import Client
from app.models.obligation import Obligation
from app.models.workflow import WorkflowState, WorkflowStateCode
from app.schemas.process import (
    CobroProcessResponse, CobroProcessCreate, CobroProcessUpdate, ProcessHistoryResponse,
    ProcessPaginatedResponse, TransitionRequest, AvailableTransition,
    ProcessDetailResponse, ProcessStateInfo, TimelineEntry,
    ProcessStatsResponse, ProcessStatsByState,
    ProcessNoteCreate, ProcessNoteResponse,
    ExpedientResponse, ExpedientObligation, ExpedientDocument,
)
from pydantic import BaseModel, Field
import math
from app.models.tenant import Tenant
from app.models.process_config import TenantProcessConfig
from app.models.process_note import ProcessNote
from app.models.document import GeneratedDocument
from app.models.workflow import WorkflowTransition
from app.models.payment_agreement import PaymentAgreement, AgreementInstallment, InstallmentStatus
from app.models.user import User as UserModel
from app.core.db_utils import days_since

router = APIRouter()


class ProcessConfig(BaseModel):
    prefijo_resolucion: str = "RES-2024"
    numero_inicial: int = 1000
    numero_actual: int = 1050
    prefijo_radicado: str = "RAD-2024"
    radicado_inicial: int = 5000


class ProcessConfigUpdate(BaseModel):
    prefijo_resolucion: Optional[str] = None
    numero_inicial: Optional[int] = None
    numero_actual: Optional[int] = None
    prefijo_radicado: Optional[str] = None
    radicado_inicial: Optional[int] = None


class AssignResolutionRequest(BaseModel):
    obligation_ids: List[int]
    resolution_initial: int = Field(ge=1)
    radicado_inicial: int
    prefijo_radicado: str = "RAD-2024"
    resolution_year: int = Field(ge=1900, le=9999)
    resolution_date: date
    state_code: str = WorkflowStateCode.PENDIENTE_ASIGNACION_RESOLUCION.value
    observaciones: Optional[str] = None
    overwrite: bool = False


def _get_or_create_config(session: Session, tenant_id: int) -> TenantProcessConfig:
    """Obtiene la configuración de procesos del tenant, o crea una por defecto."""
    config = session.exec(
        select(TenantProcessConfig).where(
            TenantProcessConfig.tenant_id == tenant_id
        )
    ).first()
    if not config:
        config = TenantProcessConfig(tenant_id=tenant_id)
        session.add(config)
        session.commit()
        session.refresh(config)
    return config


def _get_state_by_code(session: Session, tenant_id: int, state_code: str) -> WorkflowState:
    state = session.exec(
        select(WorkflowState).where(
            WorkflowState.tenant_id == tenant_id,
            WorkflowState.code == state_code,
            WorkflowState.is_active == True
        )
    ).first()
    if not state:
        raise HTTPException(status_code=400, detail=f"No existe el estado activo {state_code}")
    return state


@router.get("/config", response_model=ProcessConfig)
async def get_process_config(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener la configuración de procesos para el tenant actual."""
    try:
        config = _get_or_create_config(session, current_user.tenant_id)
        return ProcessConfig(
            prefijo_resolucion=config.prefijo_resolucion,
            numero_inicial=config.numero_inicial,
            numero_actual=config.numero_actual,
            prefijo_radicado=config.prefijo_radicado,
            radicado_inicial=config.radicado_inicial,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración de procesos: {str(e)}")


@router.post("/config", response_model=ProcessConfig)
async def update_process_config(
    config_update: ProcessConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Actualizar la configuración de procesos para el tenant actual."""
    try:
        config = _get_or_create_config(session, current_user.tenant_id)

        for field, value in config_update.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        session.add(config)
        session.commit()
        session.refresh(config)

        return ProcessConfig(
            prefijo_resolucion=config.prefijo_resolucion,
            numero_inicial=config.numero_inicial,
            numero_actual=config.numero_actual,
            prefijo_radicado=config.prefijo_radicado,
            radicado_inicial=config.radicado_inicial,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración de procesos: {str(e)}")


@router.get("/", response_model=ProcessPaginatedResponse)
async def get_processes(
    page: int = 1,
    page_size: int = 20,
    state_id: Optional[int] = None,
    status_filter: Optional[ProcessStatus] = None,
    search: Optional[str] = None,
    agreement_eligible: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener procesos de cobro del tenant con paginación y filtros."""
    try:
        base_statement = select(CobroProcess).where(
            CobroProcess.tenant_id == current_user.tenant_id
        )

        if state_id:
            base_statement = base_statement.where(CobroProcess.current_state_id == state_id)

        if status_filter:
            base_statement = base_statement.where(CobroProcess.status == status_filter)

        if search:
            search_term = f"%{search}%"
            # Buscar por referencia directamente
            base_statement = base_statement.where(
                CobroProcess.reference.like(search_term)
            )

        # Filtrar procesos elegibles para acuerdo de pago:
        # solo procesos en estado COBRO_PERSUASIVO (estado previo al acuerdo)
        if agreement_eligible:
            from app.models.workflow import WorkflowState, WorkflowStateCode
            eligible_state = session.exec(select(WorkflowState).where(
                WorkflowState.code == WorkflowStateCode.COBRO_PERSUASIVO,
                WorkflowState.tenant_id == current_user.tenant_id,
                WorkflowState.is_active == True,
            )).first()
            if eligible_state:
                base_statement = base_statement.where(
                    CobroProcess.current_state_id == eligible_state.id
                )

        # Contar total
        from sqlmodel import func
        count_statement = select(func.count()).select_from(base_statement.subquery())
        total = session.exec(count_statement).one()

        # Paginar
        offset = (page - 1) * page_size
        statement = base_statement.order_by(CobroProcess.updated_at.desc()).offset(offset).limit(page_size)
        processes = session.exec(statement).all()

        pages = math.ceil(total / page_size) if page_size > 0 else 0

        # Si se solicitan procesos elegibles para acuerdo, incluir monto de obligación
        items = []
        for p in processes:
            resp = CobroProcessResponse.model_validate(p)
            if agreement_eligible:
                from app.models.obligation import Obligation
                obligation = session.exec(select(Obligation).where(
                    Obligation.process_id == p.id,
                ).order_by(Obligation.created_at.desc())).first()
                if obligation:
                    resp.obligation_amount = obligation.amount
            items.append(resp)

        return ProcessPaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo procesos: {str(e)}")


@router.get("/resolution-obligations")
async def get_resolution_obligations(
    state_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener obligaciones candidatas para asignación de resolución por estado actual."""
    try:
        pending_state = _get_state_by_code(
            session,
            current_user.tenant_id,
            WorkflowStateCode.PENDIENTE_ASIGNACION_RESOLUCION.value,
        )
        statement = (
            select(Obligation, Client, CobroProcess, WorkflowState)
            .join(Client, Obligation.client_id == Client.id)
            .outerjoin(CobroProcess, Obligation.process_id == CobroProcess.id)
            .outerjoin(WorkflowState, CobroProcess.current_state_id == WorkflowState.id)
            .where(Client.tenant_id == current_user.tenant_id)
        )

        if state_code == WorkflowStateCode.PENDIENTE_ASIGNACION_RESOLUCION.value:
            statement = statement.where(
                (WorkflowState.code == state_code) | (Obligation.process_id == None)
            )
        elif state_code:
            statement = statement.where(WorkflowState.code == state_code)

        rows = session.exec(statement.offset(skip).limit(limit)).all()
        result = []
        for obligation, client, process, current_state in rows:
            state = current_state or pending_state
            result.append({
                "id": obligation.process_id or obligation.id,
                "process_id": obligation.process_id,
                "obligation_id": obligation.id,
                "reference": process.reference if process else f"OBL-{obligation.id}",
                "created_at": obligation.created_at,
                "cliente": {
                    "id": client.id,
                    "nombre": client.name,
                    "identification": client.identification,
                },
                "obligacion": {
                    "id": obligation.id,
                    "numero_obligacion": obligation.description or f"Obligación {obligation.id}",
                    "valor_total": obligation.amount,
                    "resolution_number": obligation.resolution_number,
                    "radicado_number": obligation.radicado_number,
                },
                "valor_total": obligation.amount,
                "current_state": {
                    "id": state.id,
                    "code": state.code,
                    "name": state.name,
                },
                "estado": state.name,
                "resolution_number": obligation.resolution_number,
                "resolution_year": obligation.resolution_year,
                "resolution_date": obligation.resolution_date,
                "radicado_number": obligation.radicado_number,
            })
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo obligaciones para resolución: {str(e)}")


@router.post("/assign-resolution/")
async def assign_resolution_to_obligations(
    payload: AssignResolutionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Asignar una resolución y un radicado consecutivo a cada obligación seleccionada."""
    try:
        if not payload.obligation_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos una obligación")

        source_state = _get_state_by_code(session, current_user.tenant_id, payload.state_code)
        assigned_state = _get_state_by_code(
            session,
            current_user.tenant_id,
            WorkflowStateCode.RESOLUCION_RADICADOS_ASIGNADOS.value
        )

        assigned = []
        now = datetime.utcnow()
        for index, obligation_id in enumerate(payload.obligation_ids):
            obligation = session.get(Obligation, obligation_id)
            if not obligation:
                raise HTTPException(status_code=404, detail=f"Obligación {obligation_id} no encontrada")

            client = session.get(Client, obligation.client_id)
            if not client or client.tenant_id != current_user.tenant_id:
                raise HTTPException(status_code=404, detail=f"Obligación {obligation_id} no encontrada para este tenant")

            if obligation.resolution_number and not payload.overwrite:
                raise HTTPException(status_code=400, detail=f"La obligación {obligation_id} ya tiene resolución asignada")

            process = session.get(CobroProcess, obligation.process_id) if obligation.process_id else None
            if not process:
                process = CobroProcess(
                    tenant_id=current_user.tenant_id,
                    reference=f"OBL-{obligation.id}",
                    observation="Proceso creado automáticamente para asignación de resolución",
                    current_state_id=source_state.id,
                    status=ProcessStatus.ACTIVE,
                    state_changed_at=now,
                )
                session.add(process)
                session.flush()
                obligation.process_id = process.id
            elif process.tenant_id != current_user.tenant_id:
                raise HTTPException(status_code=404, detail=f"Proceso de obligación {obligation_id} no encontrado para este tenant")
            elif process.current_state_id != source_state.id and not payload.overwrite:
                raise HTTPException(status_code=400, detail=f"La obligación {obligation_id} no está en el estado {payload.state_code}")

            resolution_number = str(payload.resolution_initial + index)
            radicado_number = f"{payload.prefijo_radicado}-{payload.radicado_inicial + index}"
            existing_resolution = session.exec(
                select(Obligation).where(Obligation.resolution_number == resolution_number)
            ).first()
            existing_radicado = session.exec(
                select(Obligation).where(Obligation.radicado_number == radicado_number)
            ).first()
            if existing_resolution and existing_resolution.id not in payload.obligation_ids:
                raise HTTPException(status_code=400, detail=f"La resolución {resolution_number} ya está asignada")
            if existing_radicado and existing_radicado.id not in payload.obligation_ids:
                raise HTTPException(status_code=400, detail=f"El radicado {radicado_number} ya está asignado")

            obligation.resolution_number = resolution_number
            obligation.resolution_year = payload.resolution_year
            obligation.resolution_date = payload.resolution_date
            obligation.radicado_number = radicado_number
            obligation.resolution_assigned_at = now
            obligation.resolution_observations = payload.observaciones
            obligation.updated_at = now

            previous_state_id = process.current_state_id
            process.current_state_id = assigned_state.id
            process.state_changed_at = now
            process.updated_at = now
            session.add(obligation)
            session.add(process)
            session.add(ProcessHistory(
                tenant_id=current_user.tenant_id,
                process_id=process.id,
                user_id=current_user.id,
                previous_state_id=previous_state_id,
                new_state_id=assigned_state.id,
                action="ASIGNACION_RESOLUCION",
                description=f"Asignada resolución {resolution_number} y radicado {radicado_number}",
                extra_data={
                    "obligation_id": obligation.id,
                    "resolution_number": resolution_number,
                    "resolution_year": payload.resolution_year,
                    "resolution_date": payload.resolution_date.isoformat(),
                    "radicado_number": radicado_number,
                    "observaciones": payload.observaciones,
                    "overwrite": payload.overwrite,
                },
            ))
            assigned.append({
                "obligation_id": obligation.id,
                "process_id": process.id,
                "resolution_number": resolution_number,
                "resolution_year": payload.resolution_year,
                "resolution_date": payload.resolution_date,
                "radicado_number": radicado_number,
            })

        # Actualizar configuración persistida del tenant
        config = _get_or_create_config(session, current_user.tenant_id)
        config.prefijo_radicado = payload.prefijo_radicado
        config.numero_inicial = payload.resolution_initial
        config.numero_actual = payload.resolution_initial + len(payload.obligation_ids) - 1
        config.radicado_inicial = payload.radicado_inicial
        config.radicado_actual = payload.radicado_inicial + len(payload.obligation_ids) - 1
        config.updated_at = datetime.utcnow()
        session.add(config)

        session.commit()
        return {"assigned_count": len(assigned), "items": assigned, "config": ProcessConfig(
            prefijo_resolucion=config.prefijo_resolucion,
            numero_inicial=config.numero_inicial,
            numero_actual=config.numero_actual,
            prefijo_radicado=config.prefijo_radicado,
            radicado_inicial=config.radicado_inicial,
        )}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error asignando resoluciones: {str(e)}")


@router.get("/stats", response_model=ProcessStatsResponse)
async def get_process_stats(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener métricas de procesos del tenant."""
    try:
        from sqlmodel import func
        tenant_id = current_user.tenant_id
        now = datetime.utcnow()

        # Totales por status
        total = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id
            )
        ).one()
        active = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.ACTIVE
            )
        ).one()
        suspended = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.SUSPENDED
            )
        ).one()
        closed = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.CLOSED
            )
        ).one()

        # Procesos por estado con días promedio
        rows = session.exec(
            select(
                WorkflowState.code,
                WorkflowState.name,
                func.count(CobroProcess.id),
                func.avg(
                    days_since(CobroProcess.state_changed_at)
                )
            )
            .join(CobroProcess, CobroProcess.current_state_id == WorkflowState.id)
            .where(CobroProcess.tenant_id == tenant_id)
            .group_by(WorkflowState.id)
        ).all()

        by_state = []
        for code, name, count, avg_days in rows:
            by_state.append(ProcessStatsByState(
                state_code=code,
                state_name=name,
                count=count,
                avg_days=round(avg_days or 0, 1),
            ))

        # Monto total de cartera
        total_amount = session.exec(
            select(func.coalesce(func.sum(Obligation.amount), 0))
            .join(CobroProcess, Obligation.process_id == CobroProcess.id)
            .where(CobroProcess.tenant_id == tenant_id)
        ).one()

        # Promedio de días en estado actual
        avg_days_current = session.exec(
            select(func.avg(days_since(CobroProcess.state_changed_at))).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.ACTIVE
            )
        ).one()

        return ProcessStatsResponse(
            total_processes=total,
            active_processes=active,
            suspended_processes=suspended,
            closed_processes=closed,
            by_state=by_state,
            total_amount=float(total_amount or 0),
            avg_days_in_current_state=round(float(avg_days_current or 0), 1),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.get("/{process_id}/detail", response_model=ProcessDetailResponse)
async def get_process_detail(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener detalle completo de un proceso con transiciones disponibles."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        # Obtener estado actual
        current_state = session.get(WorkflowState, process.current_state_id)
        now = datetime.utcnow()
        days_in_state = (now - (process.state_changed_at or process.created_at)).days

        # Obtener cliente a través de obligaciones
        client_name = None
        client_identification = None
        total_obligations = 0
        total_amount = 0.0
        obligations = session.exec(
            select(Obligation).where(Obligation.process_id == process_id)
        ).all()
        total_obligations = len(obligations)
        for obl in obligations:
            total_amount += obl.amount or 0
            if not client_name:
                client = session.get(Client, obl.client_id)
                if client:
                    client_name = client.name
                    client_identification = client.identification

        # Transiciones disponibles desde el estado actual
        transitions = session.exec(
            select(WorkflowTransition).where(
                WorkflowTransition.source_state_id == process.current_state_id,
                WorkflowTransition.is_active == True,
                WorkflowTransition.tenant_id == current_user.tenant_id,
            )
        ).all()

        available_transitions = []
        for t in transitions:
            target_state = session.get(WorkflowState, t.target_state_id)
            if target_state:
                available_transitions.append(AvailableTransition(
                    id=t.id,
                    name=t.name,
                    target_state_id=target_state.id,
                    target_state_code=target_state.code,
                    target_state_name=target_state.name,
                    is_automatic=t.is_automatic,
                ))

        state_info = None
        if current_state:
            state_info = ProcessStateInfo(
                state_id=current_state.id,
                state_code=current_state.code,
                state_name=current_state.name,
                days_in_state=days_in_state,
                max_days=current_state.max_days,
                changed_at=process.state_changed_at or process.created_at,
            )

        # Buscar acuerdo de pago asociado al proceso
        payment_agreement_info = None
        agreement = session.exec(
            select(PaymentAgreement).where(
                PaymentAgreement.process_id == process_id,
                PaymentAgreement.tenant_id == current_user.tenant_id,
            )
        ).first()
        if agreement:
            # Contar cuotas pagadas
            installments = session.exec(
                select(AgreementInstallment).where(
                    AgreementInstallment.agreement_id == agreement.id
                )
            ).all()
            paid_count = sum(1 for i in installments if i.status == InstallmentStatus.PAGADA)
            total_paid = sum(i.paid_amount for i in installments)
            payment_agreement_info = {
                "id": agreement.id,
                "agreement_number": agreement.agreement_number,
                "status": agreement.status.value if hasattr(agreement.status, 'value') else agreement.status,
                "total_debt": agreement.total_debt,
                "total_agreed": agreement.total_agreed,
                "installment_count": agreement.installment_count,
                "installment_amount": agreement.installment_amount,
                "paid_installments": paid_count,
                "total_paid": total_paid,
                "first_payment_date": str(agreement.first_payment_date),
            }

        return ProcessDetailResponse(
            **CobroProcessResponse.model_validate(process).model_dump(),
            client_name=client_name,
            client_identification=client_identification,
            total_obligations=total_obligations,
            total_amount=total_amount,
            state_info=state_info,
            available_transitions=available_transitions,
            payment_agreement=payment_agreement_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalle del proceso: {str(e)}")


@router.post("/{process_id}/transition")
async def transition_process(
    process_id: int,
    payload: TransitionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Ejecutar una transición de workflow en un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        # Validar que la transición existe y es válida
        transition = session.exec(
            select(WorkflowTransition).where(
                WorkflowTransition.id == payload.target_state_id,
                WorkflowTransition.source_state_id == process.current_state_id,
                WorkflowTransition.is_active == True,
                WorkflowTransition.tenant_id == current_user.tenant_id,
            )
        ).first()

        # Si no hay transición explícita, verificar que el estado destino sea válido
        if not transition:
            target_state = session.get(WorkflowState, payload.target_state_id)
            if not target_state or not target_state.is_active:
                raise HTTPException(status_code=400, detail="Estado destino no válido")
            # Permitir transición directa si el estado destino existe
            source_state = session.get(WorkflowState, process.current_state_id)
        else:
            target_state = session.get(WorkflowState, transition.target_state_id)
            source_state = session.get(WorkflowState, transition.source_state_id)

        previous_state_id = process.current_state_id
        now = datetime.utcnow()

        process.current_state_id = target_state.id
        process.state_changed_at = now
        process.updated_at = now

        # Si es estado final, cerrar el proceso
        if target_state.is_final:
            process.status = ProcessStatus.CLOSED

        session.add(process)

        # Registrar en historial
        history = ProcessHistory(
            tenant_id=current_user.tenant_id,
            process_id=process.id,
            user_id=current_user.id,
            previous_state_id=previous_state_id,
            new_state_id=target_state.id,
            action="TRANSICION_MANUAL",
            description=payload.observations or f"Transición de {source_state.name if source_state else 'anterior'} a {target_state.name}",
            extra_data={"observations": payload.observations} if payload.observations else None,
        )
        session.add(history)
        session.commit()
        session.refresh(process)

        return {"message": "Transición ejecutada exitosamente", "new_state": target_state.name}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error ejecutando transición: {str(e)}")


@router.get("/{process_id}/timeline", response_model=List[TimelineEntry])
async def get_process_timeline(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener historial enriquecido de un proceso con nombres de usuario y estado."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        history_entries = session.exec(
            select(ProcessHistory).where(
                ProcessHistory.process_id == process_id
            ).order_by(ProcessHistory.created_at.desc())
        ).all()

        timeline = []
        for entry in history_entries:
            user_name = None
            if entry.user_id:
                user = session.get(UserModel, entry.user_id)
                if user:
                    user_name = user.full_name

            prev_state_name = None
            if entry.previous_state_id:
                prev_state = session.get(WorkflowState, entry.previous_state_id)
                if prev_state:
                    prev_state_name = prev_state.name

            new_state_name = None
            if entry.new_state_id:
                new_state = session.get(WorkflowState, entry.new_state_id)
                if new_state:
                    new_state_name = new_state.name

            timeline.append(TimelineEntry(
                id=entry.id,
                action=entry.action,
                description=entry.description,
                user_name=user_name,
                previous_state_name=prev_state_name,
                new_state_name=new_state_name,
                extra_data=entry.extra_data,
                created_at=entry.created_at,
            ))

        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo timeline: {str(e)}")


@router.get("/{process_id}/expedient", response_model=ExpedientResponse)
async def get_process_expedient(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener expediente digital completo de un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        # Estado actual
        current_state = session.get(WorkflowState, process.current_state_id)
        now = datetime.utcnow()
        days_in_state = (now - (process.state_changed_at or process.created_at)).days

        # Cliente a través de obligaciones
        client_name = client_identification = client_phone = client_email = client_address = None
        obligations = session.exec(
            select(Obligation).where(Obligation.process_id == process_id)
        ).all()

        for obl in obligations:
            client = session.get(Client, obl.client_id)
            if client:
                client_name = client.name
                client_identification = client.identification
                client_phone = client.phone
                client_email = client.email
                client_address = client.address
                break

        # Obligaciones
        exp_obligations = [
            ExpedientObligation.model_validate(obl) for obl in obligations
        ]

        # Documentos generados
        docs = session.exec(
            select(GeneratedDocument).where(
                GeneratedDocument.process_id == process_id
            ).order_by(GeneratedDocument.created_at.desc())
        ).all()

        exp_documents = []
        for doc in docs:
            creator_name = None
            if doc.created_by:
                creator = session.get(UserModel, doc.created_by)
                if creator:
                    creator_name = creator.full_name
            exp_documents.append(ExpedientDocument(
                id=doc.id,
                filename=doc.filename,
                document_type=doc.document_type,
                file_size=doc.file_size,
                created_at=doc.created_at,
                created_by_name=creator_name,
                is_sent=doc.is_sent,
                resolution_number=doc.resolution_number,
                radicado_number=doc.radicado_number,
            ))

        # Notas
        notes = session.exec(
            select(ProcessNote).where(
                ProcessNote.process_id == process_id
            ).order_by(ProcessNote.is_pinned.desc(), ProcessNote.created_at.desc())
        ).all()

        exp_notes = []
        for note in notes:
            user_name = None
            if note.user_id:
                u = session.get(UserModel, note.user_id)
                if u:
                    user_name = u.full_name
            exp_notes.append(ProcessNoteResponse(
                id=note.id,
                tenant_id=note.tenant_id,
                process_id=note.process_id,
                user_id=note.user_id,
                note_type=note.note_type,
                title=note.title,
                content=note.content,
                is_pinned=note.is_pinned,
                created_at=note.created_at,
                updated_at=note.updated_at,
                user_name=user_name,
            ))

        # Timeline
        history_entries = session.exec(
            select(ProcessHistory).where(
                ProcessHistory.process_id == process_id
            ).order_by(ProcessHistory.created_at.desc())
        ).all()

        timeline = []
        for entry in history_entries:
            user_name = None
            if entry.user_id:
                u = session.get(UserModel, entry.user_id)
                if u:
                    user_name = u.full_name
            prev_name = new_name = None
            if entry.previous_state_id:
                ps = session.get(WorkflowState, entry.previous_state_id)
                if ps:
                    prev_name = ps.name
            if entry.new_state_id:
                ns = session.get(WorkflowState, entry.new_state_id)
                if ns:
                    new_name = ns.name
            timeline.append(TimelineEntry(
                id=entry.id,
                action=entry.action,
                description=entry.description,
                user_name=user_name,
                previous_state_name=prev_name,
                new_state_name=new_name,
                extra_data=entry.extra_data,
                created_at=entry.created_at,
            ))

        return ExpedientResponse(
            process=CobroProcessResponse.model_validate(process),
            client_name=client_name,
            client_identification=client_identification,
            client_phone=client_phone,
            client_email=client_email,
            client_address=client_address,
            state_name=current_state.name if current_state else None,
            state_code=current_state.code if current_state else None,
            days_in_state=days_in_state,
            obligations=exp_obligations,
            documents=exp_documents,
            notes=exp_notes,
            timeline=timeline,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo expediente: {str(e)}")


@router.get("/{process_id}/notes", response_model=List[ProcessNoteResponse])
async def get_process_notes(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener notas/actuaciones de un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        notes = session.exec(
            select(ProcessNote).where(
                ProcessNote.process_id == process_id
            ).order_by(ProcessNote.is_pinned.desc(), ProcessNote.created_at.desc())
        ).all()

        result = []
        for note in notes:
            user_name = None
            if note.user_id:
                u = session.get(UserModel, note.user_id)
                if u:
                    user_name = u.full_name
            result.append(ProcessNoteResponse(
                id=note.id,
                tenant_id=note.tenant_id,
                process_id=note.process_id,
                user_id=note.user_id,
                note_type=note.note_type,
                title=note.title,
                content=note.content,
                is_pinned=note.is_pinned,
                created_at=note.created_at,
                updated_at=note.updated_at,
                user_name=user_name,
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo notas: {str(e)}")


@router.post("/{process_id}/notes", response_model=ProcessNoteResponse)
async def create_process_note(
    process_id: int,
    note_in: ProcessNoteCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear una nota/actuación en un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        note = ProcessNote(
            tenant_id=current_user.tenant_id,
            process_id=process_id,
            user_id=current_user.id,
            note_type=note_in.note_type,
            title=note_in.title,
            content=note_in.content,
            is_pinned=note_in.is_pinned,
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        user_name = current_user.full_name if current_user else None
        return ProcessNoteResponse(
            id=note.id,
            tenant_id=note.tenant_id,
            process_id=note.process_id,
            user_id=note.user_id,
            note_type=note.note_type,
            title=note.title,
            content=note.content,
            is_pinned=note.is_pinned,
            created_at=note.created_at,
            updated_at=note.updated_at,
            user_name=user_name,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando nota: {str(e)}")


@router.get("/{process_id}/documents", response_model=List[ExpedientDocument])
async def get_process_documents(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener documentos de un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        docs = session.exec(
            select(GeneratedDocument).where(
                GeneratedDocument.process_id == process_id
            ).order_by(GeneratedDocument.created_at.desc())
        ).all()

        result = []
        for doc in docs:
            creator_name = None
            if doc.created_by:
                creator = session.get(UserModel, doc.created_by)
                if creator:
                    creator_name = creator.full_name
            result.append(ExpedientDocument(
                id=doc.id,
                filename=doc.filename,
                document_type=doc.document_type,
                file_size=doc.file_size,
                created_at=doc.created_at,
                created_by_name=creator_name,
                is_sent=doc.is_sent,
                resolution_number=doc.resolution_number,
                radicado_number=doc.radicado_number,
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")


@router.get("/{process_id}", response_model=CobroProcessResponse)
async def get_process(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener un proceso específico."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proceso: {str(e)}")


@router.post("/", response_model=CobroProcessResponse)
async def create_process(
    process_in: CobroProcessCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear un nuevo proceso de cobro."""
    try:
        # Crear proceso directamente desde el schema
        process_data = process_in.model_dump()
        process_data['tenant_id'] = current_user.tenant_id
        process = CobroProcess(**process_data)
        
        session.add(process)
        session.commit()
        session.refresh(process)
        
        # Crear registro en historial
        history = ProcessHistory(
            process_id=process.id,
            action="CREACION",
            description=f"Proceso creado con estado inicial: {process.current_state_id}",
            user_id=current_user.id,
            new_state_id=process.current_state_id
        )
        session.add(history)
        session.commit()
        
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando proceso: {str(e)}")


@router.patch("/{process_id}", response_model=CobroProcessResponse)
async def update_process(
    process_id: int,
    process_in: CobroProcessUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Actualizar un proceso existente."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        update_data = process_in.model_dump(exclude_unset=True)
        
        # Si cambia el estado, registrar en historial
        old_state_id = process.current_state_id
        new_state_id = update_data.get('current_state_id')
        
        for key, value in update_data.items():
            setattr(process, key, value)
        
        session.add(process)
        session.commit()
        session.refresh(process)
        
        # Registrar cambio de estado en historial
        if new_state_id and new_state_id != old_state_id:
            history = ProcessHistory(
                process_id=process.id,
                action="CAMBIO_ESTADO",
                description=f"Cambio de estado de {old_state_id} a {new_state_id}",
                user_id=current_user.id,
                previous_state_id=old_state_id,
                new_state_id=new_state_id
            )
            session.add(history)
            session.commit()
        
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando proceso: {str(e)}")


@router.get("/{process_id}/history", response_model=List[ProcessHistoryResponse])
async def get_process_history(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener historial de un proceso."""
    try:
        process = session.get(CobroProcess, process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        statement = select(ProcessHistory).where(
            ProcessHistory.process_id == process_id
        ).order_by(ProcessHistory.created_at.desc())
        
        history = session.exec(statement).all()
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial de proceso: {str(e)}")
