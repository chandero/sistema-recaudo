from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional
from app.core.config import settings
from app.core.database import get_session
from app.models.user import User, UserRole, UserTenant
from app.core.exceptions import CredentialsException, ForbiddenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise CredentialsException()
        user_id = int(user_id)
    except JWTError:
        raise CredentialsException()
    except (TypeError, ValueError):
        raise CredentialsException()
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if user is None:
        raise CredentialsException()
    
    return user


def get_current_active_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> User:
    """Devuelve el usuario activo, aplicando override de tenant_id y role
    si el header X-Tenant-Id esta presente y el usuario tiene acceso a ese tenant."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Override tenant_id y role si X-Tenant-Id header esta presente
    tenant_id_header = request.headers.get("X-Tenant-Id")
    if tenant_id_header:
        try:
            tenant_id = int(tenant_id_header)
            user_tenant = session.exec(
                select(UserTenant).where(
                    UserTenant.user_id == current_user.id,
                    UserTenant.tenant_id == tenant_id,
                )
            ).first()
            if user_tenant:
                current_user.tenant_id = tenant_id
                current_user.role = user_tenant.role
        except (ValueError, TypeError):
            pass
    
    return current_user


def get_current_platform_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_platform_admin and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def get_current_user_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Permite administrar usuarios a administradores de plataforma o tenant."""
    if current_user.role not in (UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar usuarios")
    return current_user
