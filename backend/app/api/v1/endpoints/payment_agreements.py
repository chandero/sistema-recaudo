"""Endpoints para gestión de acuerdos de pago."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.process import CobroProcess, ProcessStatus, ProcessHistory
from app.models.workflow import WorkflowState, WorkflowStateCode
from app.models.payment_agreement import (
    PaymentAgreement, AgreementStatus, AgreementInstallment, InstallmentStatus,
)
from app.schemas.payment_agreement import (
    AgreementCreate, AgreementResponse, AgreementListResponse,
    InstallmentResponse, InstallmentPayment, AgreementAccept,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _transition_process_to_state(
    session: Session,
    process_id: int,
    target_state_code: WorkflowStateCode,
    tenant_id: int,
    user_id: int,
    action_description: str,
) -> bool:
    """Transiciona un proceso a un estado del workflow por código.
    Retorna True si la transición fue exitosa, False si el estado no existe.
    """
    try:
        target_state = session.exec(
            select(WorkflowState).where(
                WorkflowState.code == target_state_code,
                WorkflowState.tenant_id == tenant_id,
                WorkflowState.is_active == True,
            )
        ).first()
        if not target_state:
            logger.warning(f"Estado {target_state_code.value} no encontrado para tenant {tenant_id}")
            return False

        process = session.get(CobroProcess, process_id)
        if not process:
            logger.warning(f"Proceso {process_id} no encontrado")
            return False

        previous_state_id = process.current_state_id
        now = datetime.utcnow()

        process.current_state_id = target_state.id
        process.state_changed_at = now
        process.updated_at = now

        # Si es estado final, cerrar el proceso
        if target_state.is_final:
            process.status = ProcessStatus.CLOSED

        session.add(process)

        # Registrar en historial
        history = ProcessHistory(
            tenant_id=tenant_id,
            process_id=process_id,
            user_id=user_id,
            previous_state_id=previous_state_id,
            new_state_id=target_state.id,
            action=action_description,
            description=f"Transición automática por gestión de acuerdo de pago",
            extra_data={"source": "payment_agreement", "target_state_code": target_state_code.value},
        )
        session.add(history)
        session.flush()
        return True
    except Exception as e:
        logger.error(f"Error transicionando proceso {process_id} a {target_state_code.value}: {e}")
        return False


def _generate_installments(
    agreement: PaymentAgreement, tenant_id: int
) -> List[AgreementInstallment]:
    """Genera las cuotas de un acuerdo de pago."""
    installments = []
    installment_amount = agreement.installment_amount
    first_date = agreement.first_payment_date

    for i in range(1, agreement.installment_count + 1):
        due_date = first_date + relativedelta(months=i - 1 + agreement.grace_period_months)
        inst = AgreementInstallment(
            tenant_id=tenant_id,
            agreement_id=agreement.id,
            installment_number=i,
            due_date=due_date,
            amount=installment_amount,
            status=InstallmentStatus.PENDIENTE,
        )
        installments.append(inst)
    return installments


@router.get("/", response_model=List[AgreementListResponse])
async def get_agreements(
    process_id: Optional[int] = None,
    status: Optional[AgreementStatus] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Listar acuerdos de pago del tenant."""
    statement = select(PaymentAgreement).where(
        PaymentAgreement.tenant_id == current_user.tenant_id
    )
    if process_id:
        statement = statement.where(PaymentAgreement.process_id == process_id)
    if status:
        statement = statement.where(PaymentAgreement.status == status)

    agreements = session.exec(statement.order_by(PaymentAgreement.created_at.desc())).all()
    return agreements


@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement(
    agreement_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Obtener detalle de un acuerdo con sus cuotas."""
    agreement = session.get(PaymentAgreement, agreement_id)
    if not agreement or agreement.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Acuerdo no encontrado")

    installments = session.exec(
        select(AgreementInstallment)
        .where(AgreementInstallment.agreement_id == agreement_id)
        .order_by(AgreementInstallment.installment_number)
    ).all()

    resp = AgreementResponse.model_validate(agreement)
    resp.installments = [InstallmentResponse.model_validate(i) for i in installments]
    return resp


@router.post("/", response_model=AgreementResponse)
async def create_agreement(
    data: AgreementCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Crear un nuevo acuerdo de pago."""
    try:
        process = session.get(CobroProcess, data.process_id)
        if not process or process.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")

        installment_amount = round(data.total_agreed / data.installment_count, 2) if data.installment_count > 0 else data.total_agreed

        # Generar número de acuerdo
        count = session.exec(
            select(PaymentAgreement).where(PaymentAgreement.tenant_id == current_user.tenant_id)
        ).all()
        agreement_number = f"AC-{len(count) + 1:04d}-{datetime.utcnow().year}"

        agreement = PaymentAgreement(
            tenant_id=current_user.tenant_id,
            process_id=data.process_id,
            agreement_number=agreement_number,
            status=AgreementStatus.PROPUESTA,
            total_debt=data.total_debt,
            total_agreed=data.total_agreed,
            interest_rate=data.interest_rate,
            installment_count=data.installment_count,
            installment_amount=installment_amount,
            first_payment_date=data.first_payment_date,
            payment_day=data.payment_day,
            grace_period_months=data.grace_period_months,
            default_interest_rate=data.default_interest_rate,
            observations=data.observations,
            created_by=current_user.id,
        )
        session.add(agreement)
        session.flush()

        # Generar cuotas
        installments = _generate_installments(agreement, current_user.tenant_id)
        session.add_all(installments)

        # Transicionar el proceso a ACUERDO_DE_PAGO
        _transition_process_to_state(
            session, data.process_id, WorkflowStateCode.ACUERDO_DE_PAGO,
            current_user.tenant_id, current_user.id,
            "Acuerdo de pago creado",
        )

        session.commit()
        session.refresh(agreement)

        # Recargar cuotas
        saved_installments = session.exec(
            select(AgreementInstallment)
            .where(AgreementInstallment.agreement_id == agreement.id)
            .order_by(AgreementInstallment.installment_number)
        ).all()

        resp = AgreementResponse.model_validate(agreement)
        resp.installments = [InstallmentResponse.model_validate(i) for i in saved_installments]
        return resp

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando acuerdo: {str(e)}")


@router.post("/{agreement_id}/accept", response_model=AgreementResponse)
async def accept_agreement(
    agreement_id: int,
    data: AgreementAccept = AgreementAccept(),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Aceptar un acuerdo de pago (cambia estado a VIGENTE)."""
    try:
        agreement = session.get(PaymentAgreement, agreement_id)
        if not agreement or agreement.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Acuerdo no encontrado")

        if agreement.status != AgreementStatus.PROPUESTA:
            raise HTTPException(status_code=400, detail="Solo se pueden aceptar acuerdos en estado PROPUESTA")

        agreement.status = AgreementStatus.VIGENTE
        agreement.accepted_at = datetime.utcnow()
        agreement.updated_at = datetime.utcnow()
        if data.observations:
            agreement.observations = (agreement.observations or "") + f"\n[Aceptación]: {data.observations}"

        session.add(agreement)

        # Transicionar el proceso a SEGUIMIENTO_ACUERDO
        _transition_process_to_state(
            session, agreement.process_id, WorkflowStateCode.SEGUIMIENTO_ACUERDO,
            current_user.tenant_id, current_user.id,
            "Acuerdo de pago aceptado",
        )

        session.commit()
        session.refresh(agreement)

        installments = session.exec(
            select(AgreementInstallment)
            .where(AgreementInstallment.agreement_id == agreement.id)
            .order_by(AgreementInstallment.installment_number)
        ).all()

        resp = AgreementResponse.model_validate(agreement)
        resp.installments = [InstallmentResponse.model_validate(i) for i in installments]
        return resp

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error aceptando acuerdo: {str(e)}")


@router.post("/{agreement_id}/installments/{installment_id}/pay", response_model=InstallmentResponse)
async def pay_installment(
    agreement_id: int,
    installment_id: int,
    data: InstallmentPayment,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Registrar pago de una cuota."""
    try:
        agreement = session.get(PaymentAgreement, agreement_id)
        if not agreement or agreement.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Acuerdo no encontrado")

        installment = session.get(AgreementInstallment, installment_id)
        if not installment or installment.agreement_id != agreement_id:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")

        if installment.status == InstallmentStatus.PAGADA:
            raise HTTPException(status_code=400, detail="Esta cuota ya está pagada")

        installment.paid_amount += data.paid_amount
        if data.observations:
            installment.observations = (installment.observations or "") + f"\n[Pago]: {data.observations}"

        if installment.paid_amount >= installment.amount:
            installment.status = InstallmentStatus.PAGADA
            installment.paid_at = datetime.utcnow()
        elif installment.paid_amount > 0:
            installment.status = InstallmentStatus.PARCIAL

        installment.updated_at = datetime.utcnow()
        session.add(installment)

        # Verificar si todas las cuotas están pagadas
        all_installments = session.exec(
            select(AgreementInstallment).where(AgreementInstallment.agreement_id == agreement_id)
        ).all()
        all_paid = all(i.status == InstallmentStatus.PAGADA for i in all_installments)
        if all_paid:
            agreement.status = AgreementStatus.CUMPLIDO
            agreement.updated_at = datetime.utcnow()
            session.add(agreement)

            # Transicionar el proceso a PAGADO
            _transition_process_to_state(
                session, agreement.process_id, WorkflowStateCode.PAGADO,
                current_user.tenant_id, current_user.id,
                "Acuerdo de pago cumplido",
            )

        session.commit()
        session.refresh(installment)
        return installment

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error registrando pago: {str(e)}")


@router.post("/{agreement_id}/cancel")
async def cancel_agreement(
    agreement_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Cancelar un acuerdo de pago."""
    try:
        agreement = session.get(PaymentAgreement, agreement_id)
        if not agreement or agreement.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Acuerdo no encontrado")

        if agreement.status in [AgreementStatus.CUMPLIDO, AgreementStatus.CANCELADO]:
            raise HTTPException(status_code=400, detail="No se puede cancelar un acuerdo en este estado")

        agreement.status = AgreementStatus.CANCELADO
        agreement.cancelled_at = datetime.utcnow()
        agreement.updated_at = datetime.utcnow()
        session.add(agreement)

        # Transicionar el proceso de vuelta a COBRO_PERSUASIVO
        _transition_process_to_state(
            session, agreement.process_id, WorkflowStateCode.COBRO_PERSUASIVO,
            current_user.tenant_id, current_user.id,
            "Acuerdo de pago cancelado",
        )

        session.commit()

        return {"message": "Acuerdo cancelado exitosamente"}

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error cancelando acuerdo: {str(e)}")
