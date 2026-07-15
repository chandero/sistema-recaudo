from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.obligation_service import ObligationService
from app.schemas.obligation import ObligationCreate, ObligationUpdate, ObligationResponse
from app.models.obligation import Obligation

router = APIRouter()


@router.post("/", response_model=ObligationResponse)
def create_obligation(obligation: ObligationCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva obligación.
    """
    service = ObligationService(db)
    return service.create_obligation(obligation)


@router.get("/stats/count", response_model=int)
def get_obligations_count(db: Session = Depends(get_db)):
    """
    Obtiene el número total de obligaciones.
    """
    service = ObligationService(db)
    return service.count_obligations()


@router.get("/{obligation_id}", response_model=ObligationResponse)
def get_obligation(obligation_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una obligación por su ID.
    """
    service = ObligationService(db)
    obligation = service.get_obligation(obligation_id)
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    return obligation


@router.get("/", response_model=List[ObligationResponse])
def get_obligations(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a devolver"),
    client_id: int = Query(None, description="Filtrar por ID de cliente"),
    status: str = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista de obligaciones con opción de paginación y filtrado.
    """
    service = ObligationService(db)
    
    obligations = []
    if client_id:
        obligations = service.get_obligations_by_client(client_id)
    elif status:
        obligations = service.get_obligations_by_status(status)
    else:
        obligations = service.get_obligations(skip, limit)
    
    return obligations


@router.put("/{obligation_id}", response_model=ObligationResponse)
def update_obligation(
    obligation_id: int, 
    obligation_update: ObligationUpdate, 
    db: Session = Depends(get_db)
):
    """
    Actualiza una obligación existente.
    """
    service = ObligationService(db)
    existing_obligation = service.get_obligation(obligation_id)
    if not existing_obligation:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    
    updated_obligation = service.update_obligation(obligation_id, obligation_update)
    if not updated_obligation:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    
    return updated_obligation


@router.delete("/{obligation_id}")
def delete_obligation(obligation_id: int, db: Session = Depends(get_db)):
    """
    Elimina una obligación por su ID.
    """
    service = ObligationService(db)
    success = service.delete_obligation(obligation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    return {"message": "Obligación eliminada exitosamente"}


@router.get("/client/{client_id}", response_model=List[ObligationResponse])
def get_obligations_by_client(client_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las obligaciones de un cliente específico.
    """
    service = ObligationService(db)
    return service.get_obligations_by_client(client_id)


@router.get("/status/{status}", response_model=List[ObligationResponse])
def get_obligations_by_status(status: str, db: Session = Depends(get_db)):
    """
    Obtiene obligaciones por estado.
    """
    service = ObligationService(db)
    return service.get_obligations_by_status(status)


@router.get("/overdue", response_model=List[ObligationResponse])
def get_overdue_obligations(db: Session = Depends(get_db)):
    """
    Obtiene obligaciones vencidas.
    """
    service = ObligationService(db)
    return service.get_overdue_obligations()


@router.get("/client/{client_id}/total-amount", response_model=float)
def get_total_amount_by_client(client_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el monto total de obligaciones de un cliente.
    """
    service = ObligationService(db)
    return service.get_total_amount_by_client(client_id)


@router.get("/date-range", response_model=List[ObligationResponse])
def get_obligations_by_date_range(
    start_date: str = Query(..., description="Fecha de inicio (formato ISO)"),
    end_date: str = Query(..., description="Fecha de fin (formato ISO)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene obligaciones dentro de un rango de fechas.
    """
    service = ObligationService(db)
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    return service.get_obligations_by_date_range(start_dt, end_dt)