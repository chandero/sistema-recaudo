from sqlmodel import SQLModel, Field, Relationship
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


class ObligationBase(SQLModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="COP", max_length=3)
    due_date: datetime
    issue_date: datetime
    status: ObligationStatus = Field(default=ObligationStatus.pending)
    type: ObligationType = Field(default=ObligationType.invoice)
    description: Optional[str] = Field(default=None, max_length=500)
    client_id: int = Field(foreign_key="clients.id")
    process_id: Optional[int] = Field(default=None, foreign_key="cobro_processes.id")
    resolution_number: Optional[str] = Field(default=None, max_length=100, index=True)
    resolution_year: Optional[int] = Field(default=None, ge=1900, le=9999, index=True)
    resolution_date: Optional[date] = Field(default=None)
    radicado_number: Optional[str] = Field(default=None, max_length=100, index=True)
    resolution_assigned_at: Optional[datetime] = Field(default=None)
    resolution_observations: Optional[str] = Field(default=None, max_length=1000)


class Obligation(ObligationBase, table=True):
    __tablename__ = "obligations"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    client: "Client" = Relationship(back_populates="obligations")
    process: Optional["CobroProcess"] = Relationship(back_populates="obligations")


class ObligationRead(ObligationBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ObligationCreate(ObligationBase):
    pass


class ObligationUpdate(SQLModel):
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
