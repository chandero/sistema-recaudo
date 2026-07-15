from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories import ProcessRepository
from app.schemas.process import ProcessCreate, ProcessUpdate
from app.models.process import Process


class ProcessService:
    """
    Servicio para operaciones relacionadas con procesos.
    Este servicio actúa como intermediario entre las capas de presentación y persistencia,
    utilizando el repositorio correspondiente para las operaciones de base de datos.
    """
    
    def __init__(self, db: Session):
        self.repository = ProcessRepository(db)

    def get_process(self, process_id: int) -> Optional[Process]:
        """
        Obtiene un proceso por su ID.
        
        Args:
            process_id: ID del proceso
            
        Returns:
            Proceso con el ID especificado o None si no se encuentra
        """
        return self.repository.get(process_id)

    def get_processes(self, skip: int = 0, limit: int = 100) -> List[Process]:
        """
        Obtiene una lista de procesos con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de procesos
        """
        return self.repository.get_all(skip, limit)

    def get_processes_by_client(self, client_id: int) -> List[Process]:
        """
        Obtiene todos los procesos de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de procesos del cliente
        """
        return self.repository.get_by_client(client_id)

    def get_processes_by_obligation(self, obligation_id: int) -> List[Process]:
        """
        Obtiene todos los procesos relacionados con una obligación específica.
        
        Args:
            obligation_id: ID de la obligación
            
        Returns:
            Lista de procesos relacionados con la obligación
        """
        return self.repository.get_by_obligation(obligation_id)

    def get_processes_by_status(self, status: str) -> List[Process]:
        """
        Obtiene procesos por estado.
        
        Args:
            status: Estado del proceso
            
        Returns:
            Lista de procesos con el estado especificado
        """
        return self.repository.get_by_status(status)

    def get_processes_by_workflow_state(self, workflow_state: str) -> List[Process]:
        """
        Obtiene procesos por estado de flujo de trabajo.
        
        Args:
            workflow_state: Estado del flujo de trabajo
            
        Returns:
            Lista de procesos con el estado de flujo de trabajo especificado
        """
        return self.repository.get_by_workflow_state(workflow_state)

    def get_active_processes(self) -> List[Process]:
        """
        Obtiene todos los procesos activos (no finalizados).
        
        Returns:
            Lista de procesos activos
        """
        return self.repository.get_active_processes()

    def create_process(self, process_create: ProcessCreate) -> Process:
        """
        Crea un nuevo proceso.
        
        Args:
            process_create: Datos del proceso a crear
            
        Returns:
            Proceso creado
        """
        return self.repository.create_process(process_create)

    def update_process(self, process_id: int, process_update: ProcessUpdate) -> Optional[Process]:
        """
        Actualiza un proceso existente.
        
        Args:
            process_id: ID del proceso a actualizar
            process_update: Datos actualizados del proceso
            
        Returns:
            Proceso actualizado o None si no se encuentra
        """
        return self.repository.update_process(process_id, process_update)

    def delete_process(self, process_id: int) -> bool:
        """
        Elimina un proceso por su ID.
        
        Args:
            process_id: ID del proceso a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        return self.repository.delete(process_id)

    def get_processes_by_priority(self, priority: str) -> List[Process]:
        """
        Obtiene procesos por prioridad.
        
        Args:
            priority: Prioridad del proceso
            
        Returns:
            Lista de procesos con la prioridad especificada
        """
        return self.repository.get_processes_by_priority(priority)

    def get_processes_by_date_range(self, start_date: str, end_date: str) -> List[Process]:
        """
        Obtiene procesos dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de procesos dentro del rango de fechas
        """
        return self.repository.get_processes_by_date_range(start_date, end_date)

    def count_processes(self) -> int:
        """
        Cuenta el número total de procesos.
        
        Returns:
            Número total de procesos
        """
        return self.repository.count()