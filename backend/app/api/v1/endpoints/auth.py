import re

def validate_password(password: str) -> bool:
    """Valida que la contraseña cumpla con los requisitos de seguridad"""
    # Ejemplo: al menos 8 caracteres, una letra mayúscula, una letra minúscula y un número
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
    return re.match(pattern, password) is not None
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.services.user_service import UserService

def authenticate_user(db: Session, username: str, password: str):
    """Autentica un usuario con su nombre de usuario y contraseña"""
    user_service = UserService(db)
    return user_service.authenticate_user(username, password)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db  # Corregido: era app.database
from app.services.user_service import UserService
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.core.security import create_access_token
from app.core.config import settings
from app.core.dependencies import get_current_active_user, get_current_platform_admin
from app.models.user import User

router = APIRouter()


def build_token_response(user) -> dict:
    user_role = user.role.value if hasattr(user.role, "value") else user.role
    access_token = create_access_token(data={
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": user.tenant_id,
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
            "tenant_id": user.tenant_id,
            "is_platform_admin": user.is_platform_admin,
        },
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return build_token_response(user)
    finally:
        db.close()


@router.post("/login", response_model=Token)
def login_json(credentials: UserLogin, db: Session = Depends(get_db)):
    """Endpoint JSON para autenticar desde el frontend."""
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return build_token_response(user)


@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(get_current_active_user)):
    """
    Obtiene la información del usuario actual.
    """
    return current_user
