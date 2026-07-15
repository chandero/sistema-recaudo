from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate
from app.models.client import Client
from app.core.logging.logger import get_logger, log_database_operation, log_error_occurred


class ClientService:
    """
    Servicio para operaciones relacionadas con clientes.
    Este servicio actúa como intermediario entre las capas de presentación y persistencia,
    utilizando el repositorio correspondiente para las operaciones de base de datos.
    """
    
    def __init__(self, db: Session):
        self.repository = ClientRepository(db)
        self.logger = get_logger("client_service")

    def get_client(self, client_id: int) -> Optional[Client]:
        """
        Obtiene un cliente por su ID.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Cliente con el ID especificado o None si no se encuentra
        """
        try:
            client = self.repository.get(client_id)
            if client:
                self.logger.info(
                    module="client_service",
                    action="get_client",
                    message=f"Cliente obtenido exitosamente con ID {client_id}",
                    data={"client_id": client_id, "client_name": client.name}
                )
            else:
                self.logger.info(
                    module="client_service",
                    action="get_client_not_found",
                    message=f"No se encontró cliente con ID {client_id}",
                    data={"client_id": client_id}
                )
            return client
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_client",
                additional_data={"client_id": client_id}
            )
            raise

    def get_clients(self, skip: int = 0, limit: int = 100, search: str = "") -> List[Client]:
        """
        Obtiene una lista de clientes con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de clientes
        """
        try:
            clients = self.repository.get_page(skip, limit, search.strip())
            self.logger.info(
                module="client_service",
                action="get_clients",
                message=f"Obtenidos {len(clients)} clientes",
                data={"skip": skip, "limit": limit, "total_found": len(clients)}
            )
            return clients
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_clients",
                additional_data={"skip": skip, "limit": limit}
            )
            raise

    def count_filtered_clients(self, search: str = "") -> int:
        """Cuenta clientes usando el mismo filtro que el listado paginado."""
        return self.repository.count_search(search.strip())

    def get_client_by_identification(self, identification: str) -> Optional[Client]:
        """
        Obtiene un cliente por su identificación.
        
        Args:
            identification: Identificación del cliente
            
        Returns:
            Cliente con la identificación especificada o None si no se encuentra
        """
        try:
            client = self.repository.get_by_identification(identification)
            if client:
                self.logger.info(
                    module="client_service",
                    action="get_client_by_identification",
                    message=f"Cliente encontrado con identificación {identification}",
                    data={"identification": identification, "client_id": client.id}
                )
            else:
                self.logger.info(
                    module="client_service",
                    action="get_client_by_identification_not_found",
                    message=f"No se encontró cliente con identificación {identification}",
                    data={"identification": identification}
                )
            return client
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_client_by_identification",
                additional_data={"identification": identification}
            )
            raise

    def get_client_by_email(self, email: str) -> Optional[Client]:
        """
        Obtiene un cliente por su correo electrónico.
        
        Args:
            email: Correo electrónico del cliente
            
        Returns:
            Cliente con el correo electrónico especificado o None si no se encuentra
        """
        try:
            client = self.repository.get_by_email(email)
            if client:
                self.logger.info(
                    module="client_service",
                    action="get_client_by_email",
                    message=f"Cliente encontrado con email {email}",
                    data={"email": email, "client_id": client.id}
                )
            else:
                self.logger.info(
                    module="client_service",
                    action="get_client_by_email_not_found",
                    message=f"No se encontró cliente con email {email}",
                    data={"email": email}
                )
            return client
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_client_by_email",
                additional_data={"email": email}
            )
            raise

    def search_clients(self, search_term: str) -> List[Client]:
        """
        Busca clientes por nombre o identificación.
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de clientes que coinciden con el término de búsqueda
        """
        try:
            clients = self.repository.search(search_term)
            self.logger.info(
                module="client_service",
                action="search_clients",
                message=f"Encontrados {len(clients)} clientes para la búsqueda '{search_term}'",
                data={"search_term": search_term, "results_count": len(clients)}
            )
            return clients
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="search_clients",
                additional_data={"search_term": search_term}
            )
            raise

    def get_active_clients(self) -> List[Client]:
        """
        Obtiene todos los clientes activos.
        
        Returns:
            Lista de clientes activos
        """
        try:
            clients = self.repository.get_active_clients()
            self.logger.info(
                module="client_service",
                action="get_active_clients",
                message=f"Obtenidos {len(clients)} clientes activos",
                data={"active_count": len(clients)}
            )
            return clients
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_active_clients",
                additional_data={"status": "active"}
            )
            raise

    def get_inactive_clients(self) -> List[Client]:
        """
        Obtiene todos los clientes inactivos.
        
        Returns:
            Lista de clientes inactivos
        """
        try:
            clients = self.repository.get_inactive_clients()
            self.logger.info(
                module="client_service",
                action="get_inactive_clients",
                message=f"Obtenidos {len(clients)} clientes inactivos",
                data={"inactive_count": len(clients)}
            )
            return clients
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="get_inactive_clients",
                additional_data={"status": "inactive"}
            )
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
            client = self.repository.create_client(client_create)
            log_database_operation(
                operation="CREATE",
                table="clients",
                record_id=client.id,
                data={
                    "identification": client.identification,
                    "name": client.name,
                    "email": client.email
                }
            )
            self.logger.info(
                module="client_service",
                action="create_client",
                message=f"Cliente creado exitosamente con ID {client.id}",
                data={
                    "client_id": client.id,
                    "identification": client.identification,
                    "name": client.name
                }
            )
            return client
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="create_client",
                additional_data={"client_data": client_create.model_dump()}
            )
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
            existing_client = self.get_client(client_id)
            if not existing_client:
                self.logger.warning(
                    module="client_service",
                    action="update_client_not_found",
                    message=f"No se encontró cliente con ID {client_id} para actualizar",
                    data={"client_id": client_id}
                )
                return None

            updated_client = self.repository.update_client(client_id, client_update)
            if updated_client:
                log_database_operation(
                    operation="UPDATE",
                    table="clients",
                    user_id=None,  # Este valor se puede establecer si se conoce el usuario
                    record_id=updated_client.id,
                    data={
                        "identification": updated_client.identification,
                        "name": updated_client.name,
                        "email": updated_client.email
                    }
                )
                self.logger.info(
                    module="client_service",
                    action="update_client",
                    message=f"Cliente actualizado exitosamente con ID {client_id}",
                    data={
                        "client_id": client_id,
                        "identification": updated_client.identification,
                        "name": updated_client.name
                    }
                )
            return updated_client
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="update_client",
                additional_data={"client_id": client_id, "update_data": client_update.model_dump()}
            )
            raise

    def delete_client(self, client_id: int) -> bool:
        """
        Elimina un cliente por su ID.
        
        Args:
            client_id: ID del cliente a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        try:
            existing_client = self.get_client(client_id)
            if not existing_client:
                self.logger.info(
                    module="client_service",
                    action="delete_client_not_found",
                    message=f"No se encontró cliente con ID {client_id} para eliminar",
                    data={"client_id": client_id}
                )
                return False

            success = self.repository.delete(client_id)
            if success:
                log_database_operation(
                    operation="DELETE",
                    table="clients",
                    user_id=None,  # Este valor se puede establecer si se conoce el usuario
                    record_id=client_id
                )
                self.logger.info(
                    module="client_service",
                    action="delete_client",
                    message=f"Cliente eliminado exitosamente con ID {client_id}",
                    data={"client_id": client_id}
                )
            return success
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="delete_client",
                additional_data={"client_id": client_id}
            )
            raise

    def count_clients(self) -> int:
        """
        Cuenta el número total de clientes.
        
        Returns:
            Número total de clientes
        """
        try:
            count = self.repository.count()
            self.logger.info(
                module="client_service",
                action="count_clients",
                message=f"Contados {count} clientes en total",
                data={"total_count": count}
            )
            return count
        except Exception as e:
            log_error_occurred(
                error=e,
                module="client_service",
                action="count_clients"
            )
            raise
