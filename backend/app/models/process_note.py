from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.process import CobroProcess


class ProcessNote(SQLModel, table=True):
    """Actuaciones y notas de gestión de un proceso de cobro."""
    __tablename__ = "process_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(..., foreign_key="tenants.id", index=True)
    process_id: int = Field(..., foreign_key="cobro_processes.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    note_type: str = Field(default="general", max_length=50, index=True)  # general, compromiso, recordatorio, gestion
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    is_pinned: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    process: Optional["CobroProcess"] = Relationship()
    user: Optional["User"] = Relationship()
