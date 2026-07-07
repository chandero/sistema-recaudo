from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Optional, Dict
from app.core.database import get_session
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.client import Client, Obligation
from app.models.tenant import Tenant
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate, ObligationCreate, ObligationResponse, ObligationUpdate, ImportData
from app.models.user import User

router = APIRouter()


@router.get("/clients/", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener lista de clientes filtrados por tenant."""
    statement = select(Client).where(Client.tenant_id == current_user.tenant_id)
    
    if search:
        statement = statement.where(
            (Client.name.ilike(f"%{search}%")) | 
            (Client.identification.ilike(f"%{search}%"))
        )
    
    statement = statement.offset(skip).limit(limit)
    clients = session.exec(statement).all()
    return clients


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener un cliente específico."""
    client = session.get(Client, client_id)
    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.post("/clients/", response_model=ClientResponse)
async def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear un nuevo cliente."""
    # Verificar si ya existe cliente con misma identificación en el tenant
    statement = select(Client).where(
        Client.identification == client_in.identification,
        Client.tenant_id == current_user.tenant_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con esta identificación")
    
    client = Client.from_orm(client_in)
    client.tenant_id = current_user.tenant_id
    
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Actualizar un cliente existente."""
    client = session.get(Client, client_id)
    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = client_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)
    
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Eliminar lógicamente un cliente."""
    client = session.get(Client, client_id)
    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    client.is_active = False
    session.add(client)
    session.commit()
    return {"message": "Cliente eliminado exitosamente"}


@router.get("/obligations/", response_model=List[ObligationResponse])
async def get_obligations(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener lista de obligaciones filtradas por tenant."""
    statement = select(Obligation).where(Obligation.tenant_id == current_user.tenant_id)
    
    if client_id:
        statement = statement.where(Obligation.client_id == client_id)
    
    statement = statement.offset(skip).limit(limit)
    obligations = session.exec(statement).all()
    return obligations


@router.get("/obligations/{obligation_id}", response_model=ObligationResponse)
async def get_obligation(
    obligation_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener una obligación específica."""
    obligation = session.get(Obligation, obligation_id)
    if not obligation or obligation.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    return obligation


@router.post("/obligations/", response_model=ObligationResponse)
async def create_obligation(
    obligation_in: ObligationCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear una nueva obligación."""
    # Verificar que el cliente pertenezca al tenant
    client = session.get(Client, obligation_in.client_id)
    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Cliente no pertenece a este tenant")
    
    # Verificar duplicados
    statement = select(Obligation).where(
        Obligation.numero_obligacion == obligation_in.numero_obligacion,
        Obligation.tenant_id == current_user.tenant_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una obligación con este número")
    
    obligation = Obligation.from_orm(obligation_in)
    obligation.tenant_id = current_user.tenant_id
    
    session.add(obligation)
    session.commit()
    session.refresh(obligation)
    return obligation


@router.post("/import/excel")
async def import_from_excel(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    save_template: bool = Form(default=False),
    template_name: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Importar clientes y obligaciones desde archivo Excel."""
    import json
    from app.services.import_service import process_import_file
    
    try:
        mapping = json.loads(column_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de mapeo inválido")
    
    result = await process_import_file(
        file=file,
        column_mapping=mapping,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        save_template=save_template,
        template_name=template_name,
        session=session
    )
    
    return result
