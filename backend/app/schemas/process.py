from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class ProcessStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class CobroProcessBase(BaseModel):
    reference: str
    observation: Optional[str] = None


class CobroProcessCreate(CobroProcessBase):
    current_state_id: int
    client_ids: List[int] = []
    obligation_ids: List[int] = []


class CobroProcessUpdate(BaseModel):
    reference: Optional[str] = None
    observation: Optional[str] = None
    current_state_id: Optional[int] = None
    status: Optional[ProcessStatus] = None


class CobroProcessResponse(CobroProcessBase):
    id: int
    tenant_id: int
    current_state_id: int
    status: ProcessStatus
    created_at: datetime
    updated_at: datetime
    state_changed_at: datetime
    
    class Config:
        from_attributes = True


class ProcessHistoryBase(BaseModel):
    action: str
    description: Optional[str] = None
    metadata: Optional[Dict] = None


class ProcessHistoryCreate(ProcessHistoryBase):
    process_id: int
    new_state_id: Optional[int] = None
    previous_state_id: Optional[int] = None


class ProcessHistoryResponse(ProcessHistoryBase):
    id: int
    process_id: int
    user_id: Optional[int] = None
    previous_state_id: Optional[int] = None
    new_state_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
