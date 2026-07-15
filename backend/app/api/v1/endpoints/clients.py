from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db  # Corregido: era app.database
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.services.client_service import ClientService

router = APIRouter()


@router.post("/", response_model=ClientResponse)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    return client_service.create_client(client)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    client = client_service.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    updated_client = client_service.update_client(client_id, client_update)
    if not updated_client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return updated_client


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    success = client_service.delete_client(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado exitosamente"}


@router.get("/", response_model=List[ClientResponse])
def get_clients(
    response: Response,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    search: str = Query(default="", max_length=300),
    db: Session = Depends(get_db),
):
    client_service = ClientService(db)
    response.headers["X-Total-Count"] = str(client_service.count_filtered_clients(search))
    return client_service.get_clients(skip, limit, search)
