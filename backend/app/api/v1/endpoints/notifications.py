"""Endpoints para notificaciones y búsqueda global."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, or_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.models.process import CobroProcess, ProcessStatus
from app.models.client import Client
from app.models.obligation import Obligation

router = APIRouter()


# --- Notifications ---

class NotificationResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    process_id: Optional[int] = None
    link: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCount(BaseModel):
    total: int
    unread: int


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Obtener notificaciones del usuario actual."""
    statement = select(Notification).where(
        Notification.user_id == current_user.id,
    )
    if unread_only:
        statement = statement.where(Notification.is_read == False)

    notifications = session.exec(
        statement.order_by(Notification.created_at.desc()).limit(limit)
    ).all()
    return notifications


@router.get("/notifications/count", response_model=NotificationCount)
async def get_notification_count(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Obtener conteo de notificaciones (total y no leídas)."""
    total = session.exec(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
        )
    ).one()
    unread = session.exec(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    ).one()
    return NotificationCount(total=total, unread=unread)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Marcar una notificación como leída."""
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    session.add(notification)
    session.commit()
    return {"message": "Notificación marcada como leída"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Marcar todas las notificaciones como leídas."""
    notifications = session.exec(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    ).all()
    now = datetime.utcnow()
    for n in notifications:
        n.is_read = True
        n.read_at = now
        session.add(n)
    session.commit()
    return {"message": f"{len(notifications)} notificaciones marcadas como leídas"}


# --- Global Search ---

class SearchResult(BaseModel):
    type: str  # process, client, obligation
    id: int
    title: str
    subtitle: Optional[str] = None
    link: str
    extra: Optional[dict] = None


@router.get("/search", response_model=List[SearchResult])
async def global_search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(default=20, le=50),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Búsqueda global por referencia, cliente, identificación, número de obligación, resolución."""
    tenant_id = current_user.tenant_id
    term = f"%{q}%"
    results = []

    # Buscar en procesos por referencia
    processes = session.exec(
        select(CobroProcess).where(
            CobroProcess.tenant_id == tenant_id,
            CobroProcess.reference.like(term),
        ).limit(limit)
    ).all()
    for p in processes:
        results.append(SearchResult(
            type="process",
            id=p.id,
            title=f"Proceso: {p.reference}",
            subtitle=p.observation,
            link=f"/procesos/{p.id}/expediente",
            extra={"status": p.status.value if hasattr(p.status, 'value') else str(p.status)},
        ))

    # Buscar en clientes por nombre o identificación
    clients = session.exec(
        select(Client).where(
            Client.tenant_id == tenant_id,
            or_(Client.name.like(term), Client.identification.like(term)),
        ).limit(limit)
    ).all()
    for c in clients:
        results.append(SearchResult(
            type="client",
            id=c.id,
            title=c.name,
            subtitle=f"ID: {c.identification}",
            link=f"/clientes",
            extra={"identification": c.identification, "city": c.city},
        ))

    # Buscar en obligaciones por resolución o radicado
    obligations = session.exec(
        select(Obligation).join(Client, Obligation.client_id == Client.id).where(
            Client.tenant_id == tenant_id,
            or_(
                Obligation.resolution_number.like(term),
                Obligation.radicado_number.like(term),
            ),
        ).limit(limit)
    ).all()
    for o in obligations:
        client = session.get(Client, o.client_id)
        results.append(SearchResult(
            type="obligation",
            id=o.id,
            title=f"Obligación #{o.id}",
            subtitle=f"Res: {o.resolution_number or '-'} | Rad: {o.radicado_number or '-'}",
            link=f"/obligaciones",
            extra={
                "amount": o.amount,
                "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                "client_name": client.name if client else None,
            },
        ))

    return results[:limit]
