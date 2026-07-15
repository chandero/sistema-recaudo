from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional
from app.core.config import settings
from app.core.database import get_session
from app.models.user import User, UserRole
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
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
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
