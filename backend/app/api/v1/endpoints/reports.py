"""Endpoints para reportes ejecutivos exportables."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, date
import io

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.client import Client
from app.models.obligation import Obligation, ObligationStatus
from app.models.process import CobroProcess, ProcessStatus
from app.models.workflow import WorkflowState
from app.models.payment_agreement import PaymentAgreement, AgreementStatus, AgreementInstallment, InstallmentStatus

router = APIRouter()


@router.get("/aging")
async def get_aging_report(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Reporte de cartera por antigüedad (aging): 0-30, 31-60, 61-90, 90+ días."""
    tenant_id = current_user.tenant_id
    now = datetime.utcnow()

    rows = session.exec(
        select(Obligation, Client).join(Client, Obligation.client_id == Client.id).where(
            Client.tenant_id == tenant_id,
            Obligation.status.in_(["pending", "active", "overdue"]),
        )
    ).all()

    buckets = {
        "0-30": {"count": 0, "amount": 0, "items": []},
        "31-60": {"count": 0, "amount": 0, "items": []},
        "61-90": {"count": 0, "amount": 0, "items": []},
        "90+": {"count": 0, "amount": 0, "items": []},
    }

    for obl, client in rows:
        days = (now - (obl.issue_date or now)).days
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        buckets[bucket]["count"] += 1
        buckets[bucket]["amount"] += obl.amount or 0

    return {
        "tenant_id": tenant_id,
        "generated_at": now.isoformat(),
        "buckets": buckets,
        "total_amount": sum(b["amount"] for b in buckets.values()),
        "total_count": sum(b["count"] for b in buckets.values()),
    }


@router.get("/performance")
async def get_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Indicadores de gestión: procesos nuevos vs cerrados por período."""
    tenant_id = current_user.tenant_id
    now = datetime.utcnow()

    if not start_date:
        start_date = now.date().replace(day=1)
    if not end_date:
        end_date = now.date()

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    new_processes = session.exec(
        select(func.count()).select_from(CobroProcess).where(
            CobroProcess.tenant_id == tenant_id,
            CobroProcess.created_at >= start_dt,
            CobroProcess.created_at <= end_dt,
        )
    ).one()

    closed_processes = session.exec(
        select(func.count()).select_from(CobroProcess).where(
            CobroProcess.tenant_id == tenant_id,
            CobroProcess.status == ProcessStatus.CLOSED,
            CobroProcess.updated_at >= start_dt,
            CobroProcess.updated_at <= end_dt,
        )
    ).one()

    # Acuerdos vigentes
    active_agreements = session.exec(
        select(func.count()).select_from(PaymentAgreement).where(
            PaymentAgreement.tenant_id == tenant_id,
            PaymentAgreement.status == AgreementStatus.VIGENTE,
        )
    ).one()

    # Cuotas pagadas vs vencidas
    paid_installments = session.exec(
        select(func.count()).select_from(AgreementInstallment).where(
            AgreementInstallment.tenant_id == tenant_id,
            AgreementInstallment.status == InstallmentStatus.PAGADA,
        )
    ).one()

    overdue_installments = session.exec(
        select(func.count()).select_from(AgreementInstallment).where(
            AgreementInstallment.tenant_id == tenant_id,
            AgreementInstallment.status == InstallmentStatus.VENCIDA,
        )
    ).one()

    return {
        "tenant_id": tenant_id,
        "period": {"start": str(start_date), "end": str(end_date)},
        "new_processes": new_processes,
        "closed_processes": closed_processes,
        "active_agreements": active_agreements,
        "paid_installments": paid_installments,
        "overdue_installments": overdue_installments,
        "generated_at": now.isoformat(),
    }


@router.get("/operator/{user_id}")
async def get_operator_report(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Reporte de gestión por operador."""
    from app.models.process import ProcessHistory
    tenant_id = current_user.tenant_id

    # Transiciones realizadas por el operador
    transitions = session.exec(
        select(func.count()).select_from(ProcessHistory).where(
            ProcessHistory.tenant_id == tenant_id,
            ProcessHistory.user_id == user_id,
        )
    ).one()

    # Procesos activos asignados (a través de historial)
    active_managed = session.exec(
        select(func.count(func.distinct(ProcessHistory.process_id))).where(
            ProcessHistory.tenant_id == tenant_id,
            ProcessHistory.user_id == user_id,
        )
    ).one()

    # Notas creadas
    from app.models.process_note import ProcessNote
    notes_count = session.exec(
        select(func.count()).select_from(ProcessNote).where(
            ProcessNote.tenant_id == tenant_id,
            ProcessNote.user_id == user_id,
        )
    ).one()

    # Obtener nombre del operador
    operator = session.get(User, user_id)
    operator_name = operator.full_name if operator else "Desconocido"

    return {
        "operator_id": user_id,
        "operator_name": operator_name,
        "transitions_made": transitions,
        "processes_managed": active_managed,
        "notes_created": notes_count,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/export/processes-excel")
async def export_processes_excel(
    state_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Exportar procesos a Excel."""
    from openpyxl import Workbook

    tenant_id = current_user.tenant_id
    statement = select(CobroProcess).where(CobroProcess.tenant_id == tenant_id)

    if state_id:
        statement = statement.where(CobroProcess.current_state_id == state_id)
    if status_filter:
        statement = statement.where(CobroProcess.status == status_filter)

    processes = session.exec(statement.order_by(CobroProcess.created_at.desc())).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Procesos"
    ws.append(["ID", "Referencia", "Estado ID", "Status", "Fecha Creación", "Última Actualización", "Observación"])

    for p in processes:
        ws.append([
            p.id, p.reference, p.current_state_id, p.status.value if hasattr(p.status, 'value') else str(p.status),
            p.created_at.strftime("%Y-%m-%d %H:%M"), p.updated_at.strftime("%Y-%m-%d %H:%M"),
            p.observation or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"procesos_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
