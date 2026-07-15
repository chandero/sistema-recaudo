from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.process import CobroProcess
from app.schemas.process import CobroProcessCreate, CobroProcessUpdate
from .base import BaseRepository


class ProcessRepository(BaseRepository[CobroProcess]):
    """
    Repositorio para operaciones CRUD relacionadas con procesos de cobro.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, CobroProcess)

    def get_by_client(self, client_id: int) -> List[CobroProcess]:
        """
        Obtiene todos los procesos de cobro de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de procesos de cobro del cliente
        """
        try:
            # Buscar procesos asociados con obligaciones del cliente
            from sqlalchemy import and_
            from app.models.obligation import Obligation
            return (
                self.db_session.query(CobroProcess)
                .join(Obligation, CobroProcess.id == Obligation.process_id)
                .filter(Obligation.client_id == client_id)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_workflow_state(self, state_id: int) -> List[CobroProcess]:
        """
        Obtiene procesos por estado de flujo de trabajo.
        
        Args:
            state_id: ID del estado del flujo de trabajo
            
        Returns:
            Lista de procesos en el estado especificado
        """
        try:
            return self.db_session.query(CobroProcess).filter(CobroProcess.current_state_id == state_id).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_status(self, status: str) -> List[CobroProcess]:
        """
        Obtiene procesos por estado.
        
        Args:
            status: Estado del proceso
            
        Returns:
            Lista de procesos con el estado especificado
        """
        try:
            return self.db_session.query(CobroProcess).filter(CobroProcess.status == status).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_reference(self, reference: str) -> Optional[CobroProcess]:
        """
        Obtiene un proceso por su referencia.
        
        Args:
            reference: Referencia del proceso
            
        Returns:
            Proceso con la referencia especificada o None si no se encuentra
        """
        try:
            return self.db_session.query(CobroProcess).filter(CobroProcess.reference == reference).first()
        except Exception:
            self.db_session.rollback()
            raise

    def create_process(self, process_create: CobroProcessCreate) -> CobroProcess:
        """
        Crea un nuevo proceso de cobro.
        
        Args:
            process_create: Datos del proceso a crear
            
        Returns:
            Proceso de cobro creado
        """
        try:
            process = CobroProcess(
                reference=process_create.reference,
                observation=process_create.observation,
                tenant_id=process_create.tenant_id,
                current_state_id=process_create.current_state_id,
                status=process_create.status
            )
            self.db_session.add(process)
            self.db_session.commit()
            self.db_session.refresh(process)
            return process
        except Exception:
            self.db_session.rollback()
            raise

    def update_process(self, process_id: int, process_update: CobroProcessUpdate) -> Optional[CobroProcess]:
        """
        Actualiza un proceso de cobro existente.
        
        Args:
            process_id: ID del proceso a actualizar
            process_update: Datos actualizados del proceso
            
        Returns:
            Proceso actualizado o None si no se encuentra
        """
        try:
            process = self.get(process_id)
            if process:
                update_data = process_update.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(process, field, value)
                
                self.db_session.commit()
                self.db_session.refresh(process)
            return process
        except Exception:
            self.db_session.rollback()
            raise

    def get_processes_by_tenant_and_status(self, tenant_id: int, status: str) -> List[CobroProcess]:
        """
        Obtiene procesos de un tenant específico por estado.
        
        Args:
            tenant_id: ID del tenant
            status: Estado del proceso
            
        Returns:
            Lista de procesos del tenant y estado especificados
        """
        try:
            return (
                self.db_session.query(CobroProcess)
                .filter(CobroProcess.tenant_id == tenant_id)
                .filter(CobroProcess.status == status)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise