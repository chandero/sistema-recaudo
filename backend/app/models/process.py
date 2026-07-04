from sqlalchemy import JSON as SAJSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.workflow import WorkflowState
    from app.models.user import User


class ProcessStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class CobroProcessBase(SQLModel):
    reference: str = Field(..., min_length=1, max_length=100, index=True)
    observation: Optional[str] = Field(default=None, max_length=1000)


class CobroProcess(CobroProcessBase, table=True):
    __tablename__ = "cobro_processes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    current_state_id: int = Field(..., foreign_key="workflow_states.id", index=True)
    status: ProcessStatus = Field(default=ProcessStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    state_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship(back_populates="processes")
    current_state: Optional["WorkflowState"] = Relationship()


class ProcessHistory(SQLModel, table=True):
    __tablename__ = "process_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    process_id: int = Field(..., foreign_key="cobro_processes.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    previous_state_id: Optional[int] = Field(default=None, foreign_key="workflow_states.id")
    new_state_id: Optional[int] = Field(default=None, foreign_key="workflow_states.id")
    action: str = Field(..., max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    extra_data: Optional[dict] = Field(sa_column=Column(SAJSON), default={})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    process: Optional["CobroProcess"] = Relationship(back_populates="history")
    user: Optional["User"] = Relationship()
    previous_state: Optional["WorkflowState"] = Relationship()
    new_state: Optional["WorkflowState"] = Relationship()
