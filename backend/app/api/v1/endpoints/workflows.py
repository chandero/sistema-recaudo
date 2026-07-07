from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.workflow import WorkflowState, WorkflowStateCode, WorkflowTransition
from app.models.user import User
from app.schemas.workflow import WorkflowStateResponse, WorkflowTransitionResponse

router = APIRouter()


@router.get("/states/", response_model=List[WorkflowStateResponse])
async def get_workflow_states(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener estados del workflow del tenant."""
    statement = select(WorkflowState).where(
        WorkflowState.tenant_id == current_user.tenant_id,
        WorkflowState.is_active == True
    ).order_by(WorkflowState.order)
    
    states = session.exec(statement).all()
    return states


@router.get("/states/{state_id}", response_model=WorkflowStateResponse)
async def get_workflow_state(
    state_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener un estado específico del workflow."""
    state = session.get(WorkflowState, state_id)
    if not state or (state.tenant_id and state.tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return state


@router.post("/states/", response_model=WorkflowStateResponse)
async def create_workflow_state(
    state_in: WorkflowStateResponse,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear un nuevo estado del workflow."""
    # Verificar si ya existe código
    statement = select(WorkflowState).where(
        WorkflowState.code == state_in.code,
        WorkflowState.tenant_id == current_user.tenant_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un estado con este código")
    
    state = WorkflowState.from_orm(state_in)
    state.tenant_id = current_user.tenant_id
    
    session.add(state)
    session.commit()
    session.refresh(state)
    return state


@router.get("/transitions/", response_model=List[WorkflowTransitionResponse])
async def get_workflow_transitions(
    state_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener transiciones del workflow."""
    statement = select(WorkflowTransition).where(
        WorkflowTransition.tenant_id == current_user.tenant_id,
        WorkflowTransition.is_active == True
    )
    
    if state_id:
        statement = statement.where(WorkflowTransition.source_state_id == state_id)
    
    transitions = session.exec(statement).all()
    return transitions


@router.post("/transitions/", response_model=WorkflowTransitionResponse)
async def create_workflow_transition(
    transition_in: WorkflowTransitionResponse,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear una nueva transición del workflow."""
    transition = WorkflowTransition.from_orm(transition_in)
    transition.tenant_id = current_user.tenant_id
    
    session.add(transition)
    session.commit()
    session.refresh(transition)
    return transition
