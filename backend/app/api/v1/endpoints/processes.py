from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.process import CobroProcess, ProcessHistory, ProcessStatus
from app.models.user import User
from app.schemas.process import CobroProcessResponse, CobroProcessCreate, CobroProcessUpdate, ProcessHistoryResponse
from pydantic import BaseModel
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


# Almacenamiento temporal de configuración por tenant (en producción esto iría en DB)
config_storage = {}


@router.get("/config", response_model=ProcessConfig)
async def get_process_config(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener la configuración de procesos para el tenant actual."""
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


@router.post("/config", response_model=ProcessConfig)
async def update_process_config(
    config_update: ProcessConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Actualizar la configuración de procesos para el tenant actual."""
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
    statement = select(CobroProcess).where(CobroProcess.tenant_id == current_user.tenant_id)
    
    if state_id:
        statement = statement.where(CobroProcess.current_state_id == state_id)
    
    if status_filter:
        statement = statement.where(CobroProcess.status == status_filter)
    
    statement = statement.offset(skip).limit(limit)
    processes = session.exec(statement).all()
    return processes


@router.get("/{process_id}", response_model=CobroProcessResponse)
async def get_process(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener un proceso específico."""
    process = session.get(CobroProcess, process_id)
    if not process or process.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return process


@router.post("/", response_model=CobroProcessResponse)
async def create_process(
    process_in: CobroProcessCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear un nuevo proceso de cobro."""
    process = CobroProcess.from_orm(process_in)
    process.tenant_id = current_user.tenant_id
    
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


@router.patch("/{process_id}", response_model=CobroProcessResponse)
async def update_process(
    process_id: int,
    process_in: CobroProcessUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Actualizar un proceso existente."""
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


@router.get("/{process_id}/history", response_model=List[ProcessHistoryResponse])
async def get_process_history(
    process_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener historial de un proceso."""
    process = session.get(CobroProcess, process_id)
    if not process or process.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    
    statement = select(ProcessHistory).where(
        ProcessHistory.process_id == process_id
    ).order_by(ProcessHistory.created_at.desc())
    
    history = session.exec(statement).all()
    return history