from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from .base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """
    Repositorio para operaciones CRUD relacionadas con clientes.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, Client)

    def get_by_identification(self, identification: str) -> Optional[Client]:
        """
        Obtiene un cliente por su identificación.
        
        Args:
            identification: Identificación del cliente
            
        Returns:
            Cliente con la identificación especificada o None si no se encuentra
        """
        try:
            return self.db_session.query(Client).filter(Client.identification == identification).first()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_email(self, email: str) -> Optional[Client]:
        """
        Obtiene un cliente por su correo electrónico.
        
        Args:
            email: Correo electrónico del cliente
            
        Returns:
            Cliente con el correo electrónico especificado o None si no se encuentra
        """
        try:
            return self.db_session.query(Client).filter(Client.email == email).first()
        except Exception:
            self.db_session.rollback()
            raise

    def search(self, search_term: str) -> List[Client]:
        """
        Busca clientes por nombre o identificación.
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de clientes que coinciden con el término de búsqueda
        """
        try:
            return (
                self.db_session.query(Client)
                .filter(
                    (Client.name.ilike(f"%{search_term}%")) |
                    (Client.identification.ilike(f"%{search_term}%"))
                )
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def get_page(self, skip: int = 0, limit: int = 100, search_term: str = "") -> List[Client]:
        """Obtiene una página de clientes, aplicando el filtro de búsqueda."""
        try:
            query = self.db_session.query(Client)
            if search_term:
                pattern = f"%{search_term}%"
                query = query.filter(
                    (Client.name.ilike(pattern)) |
                    (Client.identification.ilike(pattern))
                )
            return query.order_by(Client.id).offset(skip).limit(limit).all()
        except Exception:
            self.db_session.rollback()
            raise

    def count_search(self, search_term: str = "") -> int:
        """Cuenta los clientes que coinciden con el filtro de búsqueda."""
        try:
            query = self.db_session.query(Client)
            if search_term:
                pattern = f"%{search_term}%"
                query = query.filter(
                    (Client.name.ilike(pattern)) |
                    (Client.identification.ilike(pattern))
                )
            return query.count()
        except Exception:
            self.db_session.rollback()
            raise

    def get_active_clients(self) -> List[Client]:
        """
        Obtiene todos los clientes activos.
        
        Returns:
            Lista de clientes activos
        """
        try:
            return self.db_session.query(Client).filter(Client.is_active == True).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_inactive_clients(self) -> List[Client]:
        """
        Obtiene todos los clientes inactivos.
        
        Returns:
            Lista de clientes inactivos
        """
        try:
            return self.db_session.query(Client).filter(Client.is_active == False).all()
        except Exception:
            self.db_session.rollback()
            raise

    def create_client(self, client_create: ClientCreate) -> Client:
        """
        Crea un nuevo cliente.
        
        Args:
            client_create: Datos del cliente a crear
            
        Returns:
            Cliente creado
        """
        try:
            client = Client(
                identification=client_create.identification,
                name=client_create.name,
                email=client_create.email,
                phone=client_create.phone,
                address=client_create.address,
                is_active=client_create.is_active
            )
            self.db_session.add(client)
            self.db_session.commit()
            self.db_session.refresh(client)
            return client
        except Exception:
            self.db_session.rollback()
            raise

    def update_client(self, client_id: int, client_update: ClientUpdate) -> Optional[Client]:
        """
        Actualiza un cliente existente.
        
        Args:
            client_id: ID del cliente a actualizar
            client_update: Datos actualizados del cliente
            
        Returns:
            Cliente actualizado o None si no se encuentra
        """
        try:
            client = self.get(client_id)
            if client:
                update_data = client_update.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(client, field, value)
                
                self.db_session.commit()
                self.db_session.refresh(client)
            return client
        except Exception:
            self.db_session.rollback()
            raise
