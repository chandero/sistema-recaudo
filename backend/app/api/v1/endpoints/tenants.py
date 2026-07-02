from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.core.dependencies import get_current_platform_admin, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter()


@router.get("/", response_model=List[TenantResponse])
async def get_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_platform_admin),
    session: Session = Depends(get_session)
):
    statement = select(Tenant).offset(skip).limit(limit)
    tenants = session.exec(statement).all()
    return tenants


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant_in: TenantCreate,
    current_user: User = Depends(get_current_platform_admin),
    session: Session = Depends(get_session)
):
    # Check if code already exists
    statement = select(Tenant).where(Tenant.code == tenant_in.code)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant code already exists")
    
    tenant = Tenant.from_orm(tenant_in)
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_platform_admin),
    session: Session = Depends(get_session)
):
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_in: TenantUpdate,
    current_user: User = Depends(get_current_platform_admin),
    session: Session = Depends(get_session)
):
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = tenant_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return tenant
