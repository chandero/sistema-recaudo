from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories import ObligationRepository
from app.schemas.obligation import ObligationCreate, ObligationUpdate
from app.models.obligation import Obligation
from datetime import datetime


class ObligationService:
    """
    Servicio para operaciones relacionadas con obligaciones.
    Este servicio actúa como intermediario entre las capas de presentación y persistencia,
    utilizando el repositorio correspondiente para las operaciones de base de datos.
    """
    
    def __init__(self, db: Session):
        self.repository = ObligationRepository(db)

    def get_obligation(self, obligation_id: int) -> Optional[Obligation]:
        """
        Obtiene una obligación por su ID.
        
        Args:
            obligation_id: ID de la obligación
            
        Returns:
            Obligación con el ID especificado o None si no se encuentra
        """
        return self.repository.get(obligation_id)

    def get_obligations(self, skip: int = 0, limit: int = 100) -> List[Obligation]:
        """
        Obtiene una lista de obligaciones con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de obligaciones
        """
        return self.repository.get_all(skip, limit)

    def get_obligations_by_client(self, client_id: int) -> List[Obligation]:
        """
        Obtiene todas las obligaciones de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de obligaciones del cliente
        """
        return self.repository.get_by_client(client_id)

    def get_obligation_by_number(self, number: str) -> Optional[Obligation]:
        """
        Obtiene una obligación por su número.
        
        Args:
            number: Número de la obligación
            
        Returns:
            Obligación con el número especificado o None si no se encuentra
        """
        return self.repository.get_by_number(number)

    def get_obligations_by_status(self, status: str) -> List[Obligation]:
        """
        Obtiene obligaciones por estado.
        
        Args:
            status: Estado de las obligaciones
            
        Returns:
            Lista de obligaciones con el estado especificado
        """
        return self.repository.get_by_status(status)

    def get_overdue_obligations(self) -> List[Obligation]:
        """
        Obtiene obligaciones vencidas.
        
        Returns:
            Lista de obligaciones vencidas
        """
        return self.repository.get_overdue_obligations()

    def get_total_amount_by_client(self, client_id: int) -> float:
        """
        Obtiene el monto total de obligaciones de un cliente.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Monto total de obligaciones del cliente
        """
        return self.repository.get_total_amount_by_client(client_id)

    def create_obligation(self, obligation_create: ObligationCreate) -> Obligation:
        """
        Crea una nueva obligación.
        
        Args:
            obligation_create: Datos de la obligación a crear
            
        Returns:
            Obligación creada
        """
        return self.repository.create_obligation(obligation_create)

    def update_obligation(self, obligation_id: int, obligation_update: ObligationUpdate) -> Optional[Obligation]:
        """
        Actualiza una obligación existente.
        
        Args:
            obligation_id: ID de la obligación a actualizar
            obligation_update: Datos actualizados de la obligación
            
        Returns:
            Obligación actualizada o None si no se encuentra
        """
        return self.repository.update_obligation(obligation_id, obligation_update)

    def delete_obligation(self, obligation_id: int) -> bool:
        """
        Elimina una obligación por su ID.
        
        Args:
            obligation_id: ID de la obligación a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        return self.repository.delete(obligation_id)

    def get_obligations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Obligation]:
        """
        Obtiene obligaciones dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de obligaciones dentro del rango de fechas
        """
        return self.repository.get_obligations_by_date_range(start_date, end_date)

    def count_obligations(self) -> int:
        """
        Cuenta el número total de obligaciones.
        
        Returns:
            Número total de obligaciones
        """
        return self.repository.count()