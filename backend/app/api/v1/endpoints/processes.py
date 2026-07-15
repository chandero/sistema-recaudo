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
from app.schemas.process import CobroProcessResponse, CobroProcessCreate, CobroProcessUpdate, ProcessHistoryResponse
from pydantic import BaseModel, Field
from app.models.tenant import Tenant

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


# Almacenamiento temporal de configuración por tenant (en producción esto iría en DB)
config_storage = {}


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
        tenant_id = current_user.tenant_id
        
        if tenant_id not in config_storage:
            # Configuración por defecto
            config_storage[tenant_id] = {
                "prefijo_resolucion": "RES-2024",
                "numero_inicial": 1000,
                "numero_actual": 1050,
                "prefijo_radicado": "RAD-2024",
                "radicado_inicial": 5000
            }
        
        return ProcessConfig(**config_storage[tenant_id])
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
        tenant_id = current_user.tenant_id
        
        if tenant_id not in config_storage:
            config_storage[tenant_id] = {
                "prefijo_resolucion": "RES-2024",
                "numero_inicial": 1000,
                "numero_actual": 1050,
                "prefijo_radicado": "RAD-2024",
                "radicado_inicial": 5000
            }
        
        # Actualizar solo los campos que vienen en la solicitud
        for field, value in config_update.model_dump(exclude_unset=True).items():
            if value is not None:
                config_storage[tenant_id][field] = value
        
        return ProcessConfig(**config_storage[tenant_id])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración de procesos: {str(e)}")


@router.get("/", response_model=List[CobroProcessResponse])
async def get_processes(
    skip: int = 0,
    limit: int = 100,
    state_id: Optional[int] = None,
    status_filter: Optional[ProcessStatus] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener procesos de cobro del tenant."""
    try:
        statement = select(CobroProcess).where(CobroProcess.tenant_id == current_user.tenant_id)
        
        if state_id:
            statement = statement.where(CobroProcess.current_state_id == state_id)
        
        if status_filter:
            statement = statement.where(CobroProcess.status == status_filter)
        
        statement = statement.offset(skip).limit(limit)
        processes = session.exec(statement).all()
        return processes
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

        tenant_config = config_storage.setdefault(current_user.tenant_id, {
            "prefijo_resolucion": "",
            "numero_inicial": payload.resolution_initial,
            "numero_actual": payload.resolution_initial - 1,
            "prefijo_radicado": payload.prefijo_radicado,
            "radicado_inicial": payload.radicado_inicial - 1,
        })
        tenant_config["prefijo_radicado"] = payload.prefijo_radicado
        tenant_config["numero_inicial"] = payload.resolution_initial
        tenant_config["numero_actual"] = payload.resolution_initial + len(payload.obligation_ids) - 1
        tenant_config["radicado_inicial"] = payload.radicado_inicial + len(payload.obligation_ids) - 1

        session.commit()
        return {"assigned_count": len(assigned), "items": assigned, "config": ProcessConfig(**tenant_config)}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error asignando resoluciones: {str(e)}")


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
