from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class UserService:
    """
    Servicio para operaciones relacionadas con usuarios.
    Este servicio actúa como intermediario entre las capas de presentación y persistencia,
    utilizando el repositorio correspondiente para las operaciones de base de datos.
    """
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario con el ID especificado o None si no se encuentra
        """
        return self.repository.get(user_id)

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtiene una lista de usuarios con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de usuarios
        """
        return self.repository.get_all(skip, limit)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su nombre de usuario.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Usuario con el nombre de usuario especificado o None si no se encuentra
        """
        return self.repository.get_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su correo electrónico.
        
        Args:
            email: Correo electrónico del usuario
            
        Returns:
            Usuario con el correo electrónico especificado o None si no se encuentra
        """
        return self.repository.get_by_email(email)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un usuario verificando su nombre de usuario y contraseña.
        
        Args:
            username: Nombre de usuario
            password: Contraseña sin encriptar
            
        Returns:
            Usuario autenticado o None si la autenticación falla
        """
        return self.repository.authenticate_user(username, password)

    def create_user(self, user_create: UserCreate) -> User:
        """
        Crea un nuevo usuario.
        
        Args:
            user_create: Datos del usuario a crear
            
        Returns:
            Usuario creado
        """
        return self.repository.create_user(user_create)

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Actualiza un usuario existente.
        
        Args:
            user_id: ID del usuario a actualizar
            user_update: Datos actualizados del usuario
            
        Returns:
            Usuario actualizado o None si no se encuentra
        """
        return self.repository.update_user(user_id, user_update)

    def delete_user(self, user_id: int) -> bool:
        """
        Elimina un usuario por su ID.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        return self.repository.delete(user_id)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
            old_password: Contraseña actual sin encriptar
            new_password: Nueva contraseña sin encriptar
            
        Returns:
            True si la contraseña se cambió correctamente, False si la contraseña actual es incorrecta
        """
        return self.repository.change_password(user_id, old_password, new_password)

    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activa un usuario.
        
        Args:
            user_id: ID del usuario a activar
            
        Returns:
            Usuario actualizado o None si no se encuentra
        """
        return self.repository.activate_user(user_id)

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Desactiva un usuario.
        
        Args:
            user_id: ID del usuario a desactivar
            
        Returns:
            Usuario actualizado o None si no se encuentra
        """
        return self.repository.deactivate_user(user_id)

    def count_users(self) -> int:
        """
        Cuenta el número total de usuarios.
        
        Returns:
            Número total de usuarios
        """
        return self.repository.count()