from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON as SAJSON, Column, DECIMAL
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.process import CobroProcess


class AgreementStatus(str, Enum):
    PROPUESTA = "PROPUESTA"
    VIGENTE = "VIGENTE"
    CUMPLIDO = "CUMPLIDO"
    INCUMPLIDO = "INCUMPLIDO"
    CANCELADO = "CANCELADO"


class PaymentAgreement(SQLModel, table=True):
    """Acuerdo de pago entre el deudor y la entidad."""
    __tablename__ = "payment_agreements"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    process_id: int = Field(..., foreign_key="cobro_processes.id", index=True)
    agreement_number: Optional[str] = Field(default=None, max_length=100, index=True)
    status: AgreementStatus = Field(default=AgreementStatus.PROPUESTA)
    total_debt: float = Field(default=0)
    total_agreed: float = Field(default=0)
    interest_rate: float = Field(default=0)
    installment_count: int = Field(default=1)
    installment_amount: float = Field(default=0)
    first_payment_date: date = Field(default_factory=date.today)
    payment_day: int = Field(default=1, ge=1, le=31)  # Día del mes para pagos
    grace_period_months: int = Field(default=0)
    default_interest_rate: float = Field(default=0)
    observations: Optional[str] = Field(default=None, max_length=2000)
    accepted_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    process: Optional["CobroProcess"] = Relationship()
    installments: List["AgreementInstallment"] = Relationship(back_populates="agreement")


class InstallmentStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    VENCIDA = "VENCIDA"
    PARCIAL = "PARCIAL"


class AgreementInstallment(SQLModel, table=True):
    """Cuota individual de un acuerdo de pago."""
    __tablename__ = "agreement_installments"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    agreement_id: int = Field(..., foreign_key="payment_agreements.id", index=True)
    installment_number: int = Field(ge=1)
    due_date: date
    amount: float = Field(gt=0)
    paid_amount: float = Field(default=0)
    status: InstallmentStatus = Field(default=InstallmentStatus.PENDIENTE)
    paid_at: Optional[datetime] = Field(default=None)
    observations: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    agreement: Optional["PaymentAgreement"] = Relationship(back_populates="installments")
