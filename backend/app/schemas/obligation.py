from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from enum import Enum


class ObligationStatus(str, Enum):
    pending = "pending"
    active = "active"
    paid = "paid"
    cancelled = "cancelled"
    overdue = "overdue"


class ObligationType(str, Enum):
    invoice = "invoice"
    credit_note = "credit_note"
    debit_note = "debit_note"
    payment_agreement = "payment_agreement"
    other = "other"


class ObligationBase(BaseModel):
    amount: float
    currency: str = "COP"
    due_date: datetime
    issue_date: datetime
    status: ObligationStatus = ObligationStatus.pending
    type: ObligationType = ObligationType.invoice
    description: Optional[str] = None
    client_id: int
    process_id: Optional[int] = None
    resolution_number: Optional[str] = None
    resolution_year: Optional[int] = None
    resolution_date: Optional[date] = None
    radicado_number: Optional[str] = None
    resolution_assigned_at: Optional[datetime] = None
    resolution_observations: Optional[str] = None


class ObligationCreate(ObligationBase):
    pass


class ObligationUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    due_date: Optional[datetime] = None
    issue_date: Optional[datetime] = None
    status: Optional[ObligationStatus] = None
    type: Optional[ObligationType] = None
    description: Optional[str] = None
    client_id: Optional[int] = None
    process_id: Optional[int] = None
    resolution_number: Optional[str] = None
    resolution_year: Optional[int] = None
    resolution_date: Optional[date] = None
    radicado_number: Optional[str] = None
    resolution_assigned_at: Optional[datetime] = None
    resolution_observations: Optional[str] = None


class ObligationResponse(ObligationBase):
    id: int
    created_at: datetime
    updated_at: datetime
