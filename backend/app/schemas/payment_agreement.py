from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class InstallmentResponse(BaseModel):
    id: int
    installment_number: int
    due_date: date
    amount: float
    paid_amount: float
    status: str
    paid_at: Optional[datetime] = None
    observations: Optional[str] = None

    class Config:
        from_attributes = True


class AgreementCreate(BaseModel):
    process_id: int
    total_debt: float
    total_agreed: float
    interest_rate: float = 0
    installment_count: int = 1
    first_payment_date: date
    payment_day: int = 1
    grace_period_months: int = 0
    default_interest_rate: float = 0
    observations: Optional[str] = None


class AgreementResponse(BaseModel):
    id: int
    tenant_id: int
    process_id: int
    agreement_number: Optional[str] = None
    status: str
    total_debt: float
    total_agreed: float
    interest_rate: float
    installment_count: int
    installment_amount: float
    first_payment_date: date
    payment_day: int
    grace_period_months: int
    default_interest_rate: float
    observations: Optional[str] = None
    accepted_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    installments: List[InstallmentResponse] = []

    class Config:
        from_attributes = True


class AgreementListResponse(BaseModel):
    id: int
    process_id: int
    agreement_number: Optional[str] = None
    status: str
    total_debt: float
    total_agreed: float
    installment_count: int
    installment_amount: float
    first_payment_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class InstallmentPayment(BaseModel):
    paid_amount: float
    observations: Optional[str] = None


class AgreementAccept(BaseModel):
    observations: Optional[str] = None
