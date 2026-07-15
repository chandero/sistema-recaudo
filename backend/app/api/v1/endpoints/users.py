import re
import hashlib
import secrets
from math import ceil
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.database import get_session
from app.core.config import settings
from app.core.dependencies import get_current_user_admin
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.user_audit import UserAuditAction, UserAuditLog
from app.models.user_invitation import UserInvitation
from app.repositories.user import pwd_context
from app.services.email_service import EmailService
from app.schemas.auth import UserResponse
from app.schemas.user import (
    AdminUserCreate,
    AdminUserUpdate,
    PaginatedUsers,
    PaginatedUserAudit,
    PasswordReset,
    UserStatusUpdate,
    UserInvitationAccept,
    UserInvitationCreate,
    UserInvitationResponse,
)

router = APIRouter()
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


def validate_password(password: str) -> None:
    if not PASSWORD_PATTERN.match(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres, mayúscula, minúscula y número",
        )


def is_platform_admin(user: User) -> bool:
    return user.role == UserRole.PLATFORM_ADMIN or user.is_platform_admin


def scoped_user(session: Session, current_user: User, user_id: int) -> User:
    query = session.query(User).filter(User.id == user_id)
    if not is_platform_admin(current_user):
        query = query.filter(User.tenant_id == current_user.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def ensure_role_allowed(current_user: User, role: UserRole) -> None:
    if not is_platform_admin(current_user) and role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="No puede asignar el rol de administrador de plataforma")


def effective_tenant(current_user: User, tenant_id: Optional[int]) -> Optional[int]:
    if is_platform_admin(current_user):
        return tenant_id
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="El administrador no está asociado a un tenant")
    return current_user.tenant_id


def ensure_tenant_exists(session: Session, tenant_id: Optional[int], role: UserRole) -> None:
    if role == UserRole.PLATFORM_ADMIN:
        return
    if tenant_id is None or session.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=400, detail="Debe seleccionar un tenant válido")


def ensure_unique(session: Session, email: str, username: str, exclude_id: Optional[int] = None) -> None:
    query = session.query(User).filter(or_(User.email == email, User.username == username))
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    duplicate = query.first()
    if duplicate:
        field = "correo" if duplicate.email == email else "nombre de usuario"
        raise HTTPException(status_code=409, detail=f"Ya existe un usuario con ese {field}")


def commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="El correo o nombre de usuario ya está registrado")


def audit_value(value):
    return value.value if hasattr(value, "value") else value


def add_audit(
    session: Session,
    current_user: User,
    target_user: User,
    action: UserAuditAction,
    changes: dict,
) -> None:
    safe_changes = {
        key: {name: audit_value(value) for name, value in change.items()}
        for key, change in changes.items()
        if key not in {"password", "hashed_password"}
    }
    session.add(UserAuditLog(
        tenant_id=target_user.tenant_id,
        actor_user_id=current_user.id,
        target_user_id=target_user.id,
        action=action,
        changes=safe_changes,
    ))


def invitation_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_invitation_email(invitation: UserInvitation, invitation_url: str) -> bool:
    if not all((settings.SMTP_SERVER, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD)):
        return False
    return EmailService.send_user_invitation(
        to_email=invitation.email,
        full_name=invitation.full_name,
        invitation_url=invitation_url,
        smtp_config={
            "smtp_host": settings.SMTP_SERVER,
            "smtp_port": settings.SMTP_PORT,
            "smtp_user": settings.SMTP_USER,
            "smtp_password": settings.SMTP_PASSWORD,
            "from_email": settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
        },
    )


@router.get("/", response_model=PaginatedUsers)
def list_users(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    tenant_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    query = session.query(User)
    if is_platform_admin(current_user):
        if tenant_id is not None:
            query = query.filter(User.tenant_id == tenant_id)
    else:
        query = query.filter(User.tenant_id == current_user.tenant_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.full_name.ilike(term), User.username.ilike(term), User.email.ilike(term)))
    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    items = query.order_by(User.full_name, User.id).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedUsers(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.post("/invitations", response_model=UserInvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    data: UserInvitationCreate,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    ensure_role_allowed(current_user, data.role)
    tenant_id = effective_tenant(current_user, data.tenant_id)
    ensure_tenant_exists(session, tenant_id, data.role)
    ensure_unique(session, data.email, data.username)

    now = datetime.utcnow()
    pending = session.query(UserInvitation).filter(
        or_(UserInvitation.email == data.email, UserInvitation.username == data.username),
        UserInvitation.accepted_at.is_(None),
        UserInvitation.revoked_at.is_(None),
        UserInvitation.expires_at > now,
    ).all()
    for existing in pending:
        if not is_platform_admin(current_user) and existing.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=409, detail="Ya existe una invitación para ese correo o usuario")
        existing.revoked_at = now

    token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        tenant_id=tenant_id,
        created_by_user_id=current_user.id,
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        role=data.role,
        token_hash=invitation_hash(token),
        expires_at=now + timedelta(hours=settings.USER_INVITATION_EXPIRE_HOURS),
    )
    session.add(invitation)
    commit(session)
    session.refresh(invitation)
    invitation_url = f"{settings.FRONTEND_URL.rstrip('/')}/aceptar-invitacion?token={token}"
    email_sent = send_invitation_email(invitation, invitation_url)
    return UserInvitationResponse(
        id=invitation.id,
        email=invitation.email,
        username=invitation.username,
        full_name=invitation.full_name,
        role=invitation.role,
        tenant_id=invitation.tenant_id,
        expires_at=invitation.expires_at,
        email_sent=email_sent,
        invitation_url=invitation_url,
    )


@router.post("/invitations/accept", response_model=UserResponse)
def accept_invitation(
    data: UserInvitationAccept,
    session: Session = Depends(get_session),
):
    validate_password(data.password)
    now = datetime.utcnow()
    invitation = session.query(UserInvitation).filter(
        UserInvitation.token_hash == invitation_hash(data.token),
        UserInvitation.accepted_at.is_(None),
        UserInvitation.revoked_at.is_(None),
        UserInvitation.expires_at > now,
    ).first()
    if not invitation:
        raise HTTPException(status_code=400, detail="La invitación no es válida o ha vencido")
    ensure_unique(session, invitation.email, invitation.username)
    user = User(
        email=invitation.email,
        username=invitation.username,
        full_name=invitation.full_name,
        hashed_password=pwd_context.hash(data.password),
        role=invitation.role,
        tenant_id=invitation.tenant_id,
        is_active=True,
        is_platform_admin=invitation.role == UserRole.PLATFORM_ADMIN,
    )
    session.add(user)
    session.flush()
    invitation.accepted_at = now
    inviter = session.get(User, invitation.created_by_user_id)
    if inviter:
        add_audit(session, inviter, user, UserAuditAction.INVITATION_ACCEPTED, {
            "email": {"new": user.email},
            "username": {"new": user.username},
            "role": {"new": user.role},
            "tenant_id": {"new": user.tenant_id},
        })
    commit(session)
    session.refresh(user)
    return user


@router.get("/audit", response_model=PaginatedUserAudit)
def list_user_audit(
    target_user_id: Optional[int] = None,
    action: Optional[UserAuditAction] = None,
    tenant_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    query = session.query(UserAuditLog)
    if is_platform_admin(current_user):
        if tenant_id is not None:
            query = query.filter(UserAuditLog.tenant_id == tenant_id)
    else:
        query = query.filter(UserAuditLog.tenant_id == current_user.tenant_id)
    if target_user_id is not None:
        query = query.filter(UserAuditLog.target_user_id == target_user_id)
    if action is not None:
        query = query.filter(UserAuditLog.action == action)
    total = query.count()
    items = query.order_by(UserAuditLog.created_at.desc(), UserAuditLog.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return PaginatedUserAudit(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    return scoped_user(session, current_user, user_id)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminUserCreate,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    validate_password(data.password)
    ensure_role_allowed(current_user, data.role)
    tenant_id = effective_tenant(current_user, data.tenant_id)
    ensure_tenant_exists(session, tenant_id, data.role)
    ensure_unique(session, data.email, data.username)
    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=pwd_context.hash(data.password),
        role=data.role,
        tenant_id=tenant_id,
        is_active=data.is_active,
        is_platform_admin=data.role == UserRole.PLATFORM_ADMIN,
    )
    session.add(user)
    session.flush()
    add_audit(session, current_user, user, UserAuditAction.CREATED, {
        "email": {"new": user.email},
        "username": {"new": user.username},
        "full_name": {"new": user.full_name},
        "role": {"new": user.role},
        "tenant_id": {"new": user.tenant_id},
        "is_active": {"new": user.is_active},
    })
    commit(session)
    session.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    user = scoped_user(session, current_user, user_id)
    update = data.model_dump(exclude_unset=True)
    previous = {key: getattr(user, key) for key in update}
    new_role = update.get("role", user.role)
    ensure_role_allowed(current_user, new_role)
    if not is_platform_admin(current_user):
        update.pop("tenant_id", None)
        if user.role == UserRole.PLATFORM_ADMIN:
            raise HTTPException(status_code=403, detail="No puede modificar un administrador de plataforma")
    tenant_id = update.get("tenant_id", user.tenant_id)
    ensure_tenant_exists(session, tenant_id, new_role)
    email = update.get("email", user.email)
    username = update.get("username", user.username)
    ensure_unique(session, email, username, user.id)
    if update.get("is_active") is False:
        validate_deactivation(session, current_user, user)
    for key, value in update.items():
        setattr(user, key, value)
    user.is_platform_admin = new_role == UserRole.PLATFORM_ADMIN
    user.updated_at = datetime.utcnow()
    changes = {
        key: {"old": previous[key], "new": getattr(user, key)}
        for key in update
        if previous[key] != getattr(user, key)
    }
    if changes:
        add_audit(session, current_user, user, UserAuditAction.UPDATED, changes)
    commit(session)
    session.refresh(user)
    return user


def validate_deactivation(session: Session, current_user: User, user: User) -> None:
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puede desactivar su propia cuenta")
    if user.role == UserRole.TENANT_ADMIN and user.tenant_id is not None:
        active_admins = session.query(User).filter(
            User.tenant_id == user.tenant_id,
            User.role == UserRole.TENANT_ADMIN,
            User.is_active == True,
        ).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="No puede desactivar al último administrador activo del tenant")


@router.patch("/{user_id}/status", response_model=UserResponse)
def change_status(
    user_id: int,
    data: UserStatusUpdate,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    user = scoped_user(session, current_user, user_id)
    if not is_platform_admin(current_user) and user.role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="No puede modificar un administrador de plataforma")
    if not data.is_active:
        validate_deactivation(session, current_user, user)
    previous_status = user.is_active
    user.is_active = data.is_active
    user.updated_at = datetime.utcnow()
    if previous_status != user.is_active:
        action = UserAuditAction.ACTIVATED if user.is_active else UserAuditAction.DEACTIVATED
        add_audit(session, current_user, user, action, {
            "is_active": {"old": previous_status, "new": user.is_active}
        })
    commit(session)
    session.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int,
    data: PasswordReset,
    current_user: User = Depends(get_current_user_admin),
    session: Session = Depends(get_session),
):
    user = scoped_user(session, current_user, user_id)
    if not is_platform_admin(current_user) and user.role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="No puede modificar un administrador de plataforma")
    validate_password(data.password)
    user.hashed_password = pwd_context.hash(data.password)
    user.updated_at = datetime.utcnow()
    add_audit(session, current_user, user, UserAuditAction.PASSWORD_RESET, {})
    commit(session)
    return None
