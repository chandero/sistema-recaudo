from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.obligation import Obligation
from app.schemas.obligation import ObligationCreate, ObligationUpdate
from .base import BaseRepository


class ObligationRepository(BaseRepository[Obligation]):
    """
    Repositorio para operaciones CRUD relacionadas con obligaciones.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, Obligation)

    def get_by_client(self, client_id: int) -> List[Obligation]:
        """
        Obtiene todas las obligaciones de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de obligaciones del cliente
        """
        try:
            return self.db_session.query(Obligation).filter(Obligation.client_id == client_id).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_number(self, number: str) -> Optional[Obligation]:
        """
        Obtiene una obligación por su número.
        
        Args:
            number: Número de la obligación
            
        Returns:
            Obligación con el número especificado o None si no se encuentra
        """
        try:
            return self.db_session.query(Obligation).filter(Obligation.number == number).first()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_status(self, status: str) -> List[Obligation]:
        """
        Obtiene obligaciones por estado.
        
        Args:
            status: Estado de las obligaciones
            
        Returns:
            Lista de obligaciones con el estado especificado
        """
        try:
            return self.db_session.query(Obligation).filter(Obligation.status == status).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_overdue_obligations(self) -> List[Obligation]:
        """
        Obtiene obligaciones vencidas.
        
        Returns:
            Lista de obligaciones vencidas
        """
        try:
            return (
                self.db_session.query(Obligation)
                .filter(Obligation.due_date < datetime.now())
                .filter(Obligation.status != 'PAID')
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def get_obligations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Obligation]:
        """
        Obtiene obligaciones dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de obligaciones dentro del rango de fechas
        """
        try:
            return (
                self.db_session.query(Obligation)
                .filter(Obligation.issue_date >= start_date)
                .filter(Obligation.issue_date <= end_date)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise