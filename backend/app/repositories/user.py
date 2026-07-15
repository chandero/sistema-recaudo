from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .base import BaseRepository
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["pbkdf2_sha256", "sha256_crypt"], deprecated="auto")


class UserRepository(BaseRepository[User]):
    """
    Repositorio para operaciones CRUD relacionadas con usuarios.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su nombre de usuario.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Usuario con el nombre de usuario especificado o None si no se encuentra
        """
        try:
            return self.db_session.query(User).filter(User.username == username).first()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su correo electrónico.
        
        Args:
            email: Correo electrónico del usuario
            
        Returns:
            Usuario con el correo electrónico especificado o None si no se encuentra
        """
        try:
            return self.db_session.query(User).filter(User.email == email).first()
        except Exception:
            self.db_session.rollback()
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un usuario verificando su nombre de usuario/email y contraseña.
        
        Args:
            username: Nombre de usuario o email
            password: Contraseña sin encriptar
            
        Returns:
            Usuario autenticado o None si la autenticación falla
        """
        try:
            # Primero intenta buscar por username
            user = self.get_by_username(username)
            # Si no se encuentra por username, intenta buscar por email
            if not user:
                user = self.get_by_email(username)
            if not user:
                return None
            if not pwd_context.verify(password, user.hashed_password):
                return None
            return user
        except Exception:
            self.db_session.rollback()
            raise

    def create_user(self, user_create: UserCreate) -> User:
        """
        Crea un nuevo usuario con la contraseña encriptada.

        Args:
            user_create: Datos del usuario a crear

        Returns:
            Usuario creado
        """
        try:
            user = User(
                email=user_create.email,
                username=user_create.username,
                full_name=user_create.full_name,
                hashed_password=pwd_context.hash(user_create.password),
                role=user_create.role,
                tenant_id=user_create.tenant_id,
                is_platform_admin=user_create.role == "PLATFORM_ADMIN",
            )
            self.db_session.add(user)
            self.db_session.commit()
            self.db_session.refresh(user)
            return user
        except Exception:
            self.db_session.rollback()
            raise

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Actualiza un usuario existente.

        Args:
            user_id: ID del usuario a actualizar
            user_update: Datos actualizados del usuario

        Returns:
            Usuario actualizado o None si no se encuentra
        """
        try:
            user = self.get(user_id)
            if not user:
                return None

            update_data = user_update.model_dump(exclude_unset=True)
            password = update_data.pop("password", None)
            if password:
                user.hashed_password = pwd_context.hash(password)

            for key, value in update_data.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()

            self.db_session.commit()
            self.db_session.refresh(user)
            return user
        except Exception:
            self.db_session.rollback()
            raise

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Cambia la contraseña si la contraseña actual es válida.

        Args:
            user_id: ID del usuario
            old_password: Contraseña actual sin encriptar
            new_password: Nueva contraseña sin encriptar

        Returns:
            True si se cambió correctamente, False en caso contrario
        """
        try:
            user = self.get(user_id)
            if not user or not pwd_context.verify(old_password, user.hashed_password):
                return False

            user.hashed_password = pwd_context.hash(new_password)
            user.updated_at = datetime.utcnow()
            self.db_session.commit()
            return True
        except Exception:
            self.db_session.rollback()
            raise

    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activa un usuario.

        Args:
            user_id: ID del usuario a activar

        Returns:
            Usuario actualizado o None si no se encuentra
        """
        return self._set_active(user_id, True)

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Desactiva un usuario.

        Args:
            user_id: ID del usuario a desactivar

        Returns:
            Usuario actualizado o None si no se encuentra
        """
        return self._set_active(user_id, False)

    def _set_active(self, user_id: int, is_active: bool) -> Optional[User]:
        try:
            user = self.get(user_id)
            if not user:
                return None

            user.is_active = is_active
            user.updated_at = datetime.utcnow()
            self.db_session.commit()
            self.db_session.refresh(user)
            return user
        except Exception:
            self.db_session.rollback()
            raise