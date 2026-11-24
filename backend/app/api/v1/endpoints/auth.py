from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlmodel import select
from typing import Any
from pydantic import BaseModel

import re

def validate_password(password: str) -> bool:
    """Valida que la contraseña cumpla con los requisitos de seguridad"""
    # Ejemplo: al menos 8 caracteres, una letra mayúscula, una letra minúscula y un número
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
    return re.match(pattern, password) is not None


def authenticate_user(db: Session, username: str, password: str):
    """Autentica un usuario con su nombre de usuario y contraseña"""
    from app.services.user_service import UserService
    user_service = UserService(db)
    return user_service.authenticate_user(username, password)


from app.core.database import get_db
from app.services.user_service import UserService
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.core.security import create_access_token
from app.core.config import settings
from app.core.dependencies import get_current_active_user, get_current_platform_admin
from app.models.user import User, UserTenant
from app.models.tenant import Tenant
from app.core.logging.logger import log_authentication_event, get_logger

router = APIRouter()
logger = get_logger(__name__)


def build_token_response(user, session=None, active_tenant_id=None) -> dict:
    user_role = user.role.value if hasattr(user.role, "value") else user.role
    
    # Load user's tenant assignments
    tenants = []
    if session:
        user_tenants = session.exec(
            select(UserTenant).where(UserTenant.user_id == user.id)
        ).all()
        for ut in user_tenants:
            tenant = session.get(Tenant, ut.tenant_id)
            tenants.append({
                "tenant_id": ut.tenant_id,
                "tenant_name": tenant.name if tenant else f"Tenant #{ut.tenant_id}",
                "role": ut.role.value if hasattr(ut.role, 'value') else ut.role,
            })
    
    # Fallback: if no user_tenants yet, use user.tenant_id
    if not tenants and user.tenant_id:
        tenant_name = "Default"
        if session:
            t = session.get(Tenant, user.tenant_id)
            tenant_name = t.name if t else f"Tenant #{user.tenant_id}"
        tenants = [{"tenant_id": user.tenant_id, "tenant_name": tenant_name, "role": user_role}]
    
    # Determine active tenant
    effective_tenant_id = active_tenant_id or (tenants[0]["tenant_id"] if tenants else user.tenant_id)
    
    access_token = create_access_token(data={
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": effective_tenant_id,
        "role": user_role,
    })
    return {
        "access_token": access_token,
        "refresh_token": "",
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user_role,
            "tenant_id": effective_tenant_id,
            "is_platform_admin": user.is_platform_admin,
        },
        "available_tenants": tenants,
        "active_tenant_id": effective_tenant_id,
    }


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin),
):
    """Registro administrativo legado. La creación normal se realiza en /users."""
    try:
        # Validar contraseña
        if not validate_password(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña no cumple con los requisitos de seguridad"
            )
        
        user_service = UserService(db)
        user = user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para autenticar un usuario y obtener un token JWT"""
    db = next(get_db())
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user or not user.is_active:
            # Log failed authentication attempt
            log_authentication_event(
                event="LOGIN_FAILED",
                username=form_data.username,
                success=False,
                ip_address="",  # Will be populated by middleware
                user_agent=""  # Will be populated by middleware
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log successful authentication
        log_authentication_event(
            event="LOGIN_SUCCESS",
            username=form_data.username,
            success=True,
            ip_address="",  # Will be populated by middleware
            user_agent=""  # Will be populated by middleware
        )
        
        return build_token_response(user, session=db)
    finally:
        db.close()


@router.post("/login", response_model=Token)
def login_json(credentials: UserLogin, db: Session = Depends(get_db)):
    """Endpoint JSON para autenticar desde el frontend."""
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user or not user.is_active:
        # Log failed authentication attempt
        log_authentication_event(
            event="LOGIN_FAILED",
            username=credentials.email,
            success=False,
            ip_address="",  # Will be populated by middleware
            user_agent=""  # Will be populated by middleware
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful authentication
    log_authentication_event(
        event="LOGIN_SUCCESS",
        username=credentials.email,
        success=True,
        ip_address="",  # Will be populated by middleware
        user_agent=""  # Will be populated by middleware
    )

    return build_token_response(user, session=db)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Endpoint para cerrar la sesión del usuario actual.
    """
    try:
        # Log the logout event
        log_authentication_event(
            event="LOGOUT",
            username=current_user.email,  # Using email as username for consistency
            success=True,
            ip_address="",  # Will be populated by middleware
            user_agent=""  # Will be populated by middleware
        )
        
        logger.info(
            module="auth",
            action="user_logout",
            message=f"Usuario {current_user.email} ha cerrado sesión",
            user_id=current_user.id,
            data={"user_email": current_user.email}
        )
        
        return {"message": "Sesión cerrada exitosamente"}
    except Exception as e:
        logger.error(
            module="auth",
            action="logout_error",
            message=f"Error durante el cierre de sesión: {str(e)}",
            user_id=current_user.id if current_user else None,
            error_code="LOGOUT_ERROR"
        )
        raise HTTPException(status_code=500, detail="Error al cerrar la sesión")


@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(get_current_active_user)):
    """
    Obtiene la información del usuario actual.
    """
    return current_user


class SwitchTenantRequest(BaseModel):
    tenant_id: int


@router.post("/switch-tenant")
def switch_tenant(
    payload: SwitchTenantRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cambia el tenant activo del usuario. Valida que el usuario tenga acceso al tenant solicitado."""
    user_tenant = db.exec(
        select(UserTenant).where(
            UserTenant.user_id == current_user.id,
            UserTenant.tenant_id == payload.tenant_id,
        )
    ).first()
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este tenant",
        )
    
    return build_token_response(current_user, session=db, active_tenant_id=payload.tenant_id)