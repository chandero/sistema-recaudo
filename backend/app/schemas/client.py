from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ClientBase(BaseModel):
    identification: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    identification: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ObligationBase(BaseModel):
    numero_obligacion: str
    vigencia: str
    valor_total: float
    capital: float = 0
    intereses: float = 0
    mora: float = 0
    fecha_emision: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None


class ObligationCreate(ObligationBase):
    client_id: int


class ObligationUpdate(BaseModel):
    numero_obligacion: Optional[str] = None
    vigencia: Optional[str] = None
    valor_total: Optional[float] = None
    capital: Optional[float] = None
    intereses: Optional[float] = None
    mora: Optional[float] = None
    fecha_emision: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None
    process_id: Optional[int] = None
    is_active: Optional[bool] = None


class ObligationResponse(ObligationBase):
    id: int
    tenant_id: int
    client_id: int
    process_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ImportData(BaseModel):
    """Schema for bulk import of clients and obligations"""
    column_mapping: Dict[str, str]
    data: List[Dict[str, str]]
    save_template: bool = False
    template_name: Optional[str] = None
