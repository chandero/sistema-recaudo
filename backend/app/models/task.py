from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.process import CobroProcess
    from app.models.user import User


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskBase(SQLModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = Field(default=None)
    assigned_to_role: Optional[str] = Field(default=None, max_length=50)


class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    process_id: Optional[int] = Field(default=None, foreign_key="cobro_processes.id", index=True)
    assigned_user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    completed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    tenant: Optional["Tenant"] = Relationship()
    # assigned_user: Optional["User"] = Relationship()  # TODO: Especificar foreign_keys correctamente
    process: Optional["CobroProcess"] = Relationship()
