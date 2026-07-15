from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository(ABC, Generic[T]):
    """
    Clase base para todos los repositorios que implementan el patrón Repository.
    Proporciona métodos CRUD básicos y operaciones comunes de acceso a datos.
    """
    
    def __init__(self, db_session: Session, model: type[T]):
        """
        Inicializa el repositorio con una sesión de base de datos y un modelo.
        
        Args:
            db_session: Sesión de base de datos SQLAlchemy
            model: Modelo SQLAlchemy asociado al repositorio
        """
        self.db_session = db_session
        self.model = model

    def get(self, id: int) -> Optional[T]:
        """
        Obtiene un registro por su ID.
        
        Args:
            id: ID del registro a obtener
            
        Returns:
            Instancia del modelo o None si no se encuentra
        """
        try:
            return self.db_session.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Obtiene todos los registros con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de instancias del modelo
        """
        try:
            return self.db_session.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def create(self, obj: T) -> T:
        """
        Crea un nuevo registro.
        
        Args:
            obj: Instancia del modelo a crear
            
        Returns:
            Instancia del modelo creada
        """
        try:
            self.db_session.add(obj)
            self.db_session.commit()
            self.db_session.refresh(obj)
            return obj
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[T]:
        """
        Actualiza un registro existente.
        
        Args:
            id: ID del registro a actualizar
            obj_data: Diccionario con los campos a actualizar
            
        Returns:
            Instancia del modelo actualizada o None si no se encuentra
        """
        try:
            obj = self.get(id)
            if obj:
                for key, value in obj_data.items():
                    setattr(obj, key, value)
                self.db_session.commit()
                self.db_session.refresh(obj)
            return obj
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def delete(self, id: int) -> bool:
        """
        Elimina un registro por su ID.
        
        Args:
            id: ID del registro a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        try:
            obj = self.get(id)
            if obj:
                self.db_session.delete(obj)
                self.db_session.commit()
                return True
            return False
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def count(self) -> int:
        """
        Cuenta el número total de registros.
        
        Returns:
            Número total de registros
        """
        try:
            return self.db_session.query(self.model).count()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def filter_by(self, **kwargs) -> List[T]:
        """
        Filtra registros por campos específicos.
        
        Args:
            **kwargs: Argumentos clave-valor para filtrar
            
        Returns:
            Lista de instancias del modelo que coinciden con el filtro
        """
        try:
            return self.db_session.query(self.model).filter_by(**kwargs).all()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def first_by(self, **kwargs) -> Optional[T]:
        """
        Obtiene el primer registro que coincide con los filtros.
        
        Args:
            **kwargs: Argumentos clave-valor para filtrar
            
        Returns:
            Primera instancia del modelo que coincide o None si no se encuentra
        """
        try:
            return self.db_session.query(self.model).filter_by(**kwargs).first()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise