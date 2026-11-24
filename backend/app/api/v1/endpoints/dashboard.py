from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.client import Client
from app.models.obligation import Obligation
from app.models.process import CobroProcess, ProcessStatus
from app.models.workflow import WorkflowState
from app.core.db_utils import days_since

router = APIRouter()


class StateDistribution(BaseModel):
    state_name: str
    state_code: str
    count: int


class TopDebtor(BaseModel):
    client_id: int
    client_name: str
    identification: Optional[str] = None
    total_amount: float
    obligation_count: int


class DashboardStats(BaseModel):
    total_clients: int
    active_obligations: int
    processes_in_progress: int
    paid_processes: int
    total_portfolio_value: float
    recovered_value: float
    overdue_value: float
    state_distribution: List[StateDistribution]
    top_debtors: List[TopDebtor]
    avg_days_in_process: float


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener estadísticas reales del dashboard para el tenant actual."""
    try:
        tenant_id = current_user.tenant_id
        now = datetime.utcnow()

        # Total clientes activos
        total_clients = session.exec(
            select(func.count()).select_from(Client).where(
                Client.tenant_id == tenant_id,
                Client.is_active == True
            )
        ).one()

        # Obligaciones activas (no pagados ni cancelados)
        active_obligations = session.exec(
            select(func.count()).select_from(Obligation).where(
                Obligation.client_id.in_(
                    select(Client.id).where(Client.tenant_id == tenant_id)
                ),
                Obligation.status.in_(["pending", "active", "overdue"])
            )
        ).one()

        # Procesos en curso (activos)
        processes_in_progress = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.ACTIVE
            )
        ).one()

        # Procesos pagados/cerrados
        paid_processes = session.exec(
            select(func.count()).select_from(CobroProcess).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.CLOSED
            )
        ).one()

        # Valor total de cartera (obligaciones activas)
        total_portfolio = session.exec(
            select(func.coalesce(func.sum(Obligation.amount), 0)).where(
                Obligation.client_id.in_(
                    select(Client.id).where(Client.tenant_id == tenant_id)
                ),
                Obligation.status.in_(["pending", "active", "overdue"])
            )
        ).one()

        # Valor vencido
        overdue_value = session.exec(
            select(func.coalesce(func.sum(Obligation.amount), 0)).where(
                Obligation.client_id.in_(
                    select(Client.id).where(Client.tenant_id == tenant_id)
                ),
                Obligation.status == "overdue"
            )
        ).one()

        # Valor recuperado (obligaciones pagadas)
        recovered_value = session.exec(
            select(func.coalesce(func.sum(Obligation.amount), 0)).where(
                Obligation.client_id.in_(
                    select(Client.id).where(Client.tenant_id == tenant_id)
                ),
                Obligation.status == "paid"
            )
        ).one()

        # Distribución por estado
        state_rows = session.exec(
            select(WorkflowState.name, WorkflowState.code, func.count(CobroProcess.id))
            .join(CobroProcess, CobroProcess.current_state_id == WorkflowState.id)
            .where(CobroProcess.tenant_id == tenant_id)
            .group_by(WorkflowState.id, WorkflowState.name, WorkflowState.code)
            .order_by(WorkflowState.order)
        ).all()

        state_distribution = [
            StateDistribution(state_name=name, state_code=code, count=count)
            for name, code, count in state_rows
        ]

        # Top 10 deudores
        debtor_rows = session.exec(
            select(
                Client.id,
                Client.name,
                Client.identification,
                func.sum(Obligation.amount),
                func.count(Obligation.id)
            )
            .join(Obligation, Obligation.client_id == Client.id)
            .where(
                Client.tenant_id == tenant_id,
                Obligation.status.in_(["pending", "active", "overdue"])
            )
            .group_by(Client.id, Client.name, Client.identification)
            .order_by(func.sum(Obligation.amount).desc())
            .limit(10)
        ).all()

        top_debtors = [
            TopDebtor(
                client_id=cid,
                client_name=cname,
                identification=cident,
                total_amount=float(total or 0),
                obligation_count=ocount,
            )
            for cid, cname, cident, total, ocount in debtor_rows
        ]

        # Promedio de días en proceso
        avg_days = session.exec(
            select(func.avg(days_since(CobroProcess.state_changed_at))).where(
                CobroProcess.tenant_id == tenant_id,
                CobroProcess.status == ProcessStatus.ACTIVE
            )
        ).one()

        return DashboardStats(
            total_clients=total_clients,
            active_obligations=active_obligations,
            processes_in_progress=processes_in_progress,
            paid_processes=paid_processes,
            total_portfolio_value=float(total_portfolio or 0),
            recovered_value=float(recovered_value or 0),
            overdue_value=float(overdue_value or 0),
            state_distribution=state_distribution,
            top_debtors=top_debtors,
            avg_days_in_process=round(float(avg_days or 0), 1),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas del dashboard: {str(e)}")
