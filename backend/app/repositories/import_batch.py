from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.import_batch import ImportBatch
from app.schemas.import_batch import ImportBatchCreate, ImportBatchUpdate
from .base import BaseRepository


class ImportBatchRepository(BaseRepository[ImportBatch]):
    """
    Repositorio para operaciones CRUD relacionadas con lotes de importación.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, ImportBatch)

    def get_by_status(self, status: str) -> List[ImportBatch]:
        """
        Obtiene lotes de importación por estado.
        
        Args:
            status: Estado del lote de importación
            
        Returns:
            Lista de lotes de importación con el estado especificado
        """
        try:
            return self.db_session.query(ImportBatch).filter(ImportBatch.status == status).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_user(self, user_id: int) -> List[ImportBatch]:
        """
        Obtiene lotes de importación por usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de lotes de importación del usuario
        """
        try:
            return self.db_session.query(ImportBatch).filter(ImportBatch.user_id == user_id).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_recent_batches(self, limit: int = 10) -> List[ImportBatch]:
        """
        Obtiene los lotes de importación recientes.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de lotes de importación recientes
        """
        try:
            return (
                self.db_session.query(ImportBatch)
                .order_by(ImportBatch.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_date_range(self, start_date: str, end_date: str) -> List[ImportBatch]:
        """
        Obtiene lotes de importación dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de lotes de importación dentro del rango de fechas
        """
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            return (
                self.db_session.query(ImportBatch)
                .filter(ImportBatch.created_at >= start_dt)
                .filter(ImportBatch.created_at <= end_dt)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def create_batch(self, batch_create: ImportBatchCreate) -> ImportBatch:
        """
        Crea un nuevo lote de importación.
        
        Args:
            batch_create: Datos del lote de importación a crear
            
        Returns:
            Lote de importación creado
        """
        try:
            batch = ImportBatch(
                original_filename=batch_create.original_filename,
                user_id=batch_create.user_id,
                status=batch_create.status,
                total_rows=batch_create.total_rows,
                success_rows=batch_create.success_rows,
                error_rows=batch_create.error_rows,
                detected_columns=batch_create.detected_columns,
                errors_log=batch_create.errors_log,
                processing_metadata=batch_create.processing_metadata
            )
            self.db_session.add(batch)
            self.db_session.commit()
            self.db_session.refresh(batch)
            return batch
        except Exception:
            self.db_session.rollback()
            raise

    def update_batch(self, batch_id: int, batch_update: ImportBatchUpdate) -> Optional[ImportBatch]:
        """
        Actualiza un lote de importación existente.
        
        Args:
            batch_id: ID del lote de importación a actualizar
            batch_update: Datos actualizados del lote de importación
            
        Returns:
            Lote de importación actualizado o None si no se encuentra
        """
        try:
            batch = self.get(batch_id)
            if batch:
                update_data = batch_update.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(batch, field, value)
                
                self.db_session.commit()
                self.db_session.refresh(batch)
            return batch
        except Exception:
            self.db_session.rollback()
            raise

    def get_successful_batches(self) -> List[ImportBatch]:
        """
        Obtiene lotes de importación completados exitosamente.
        
        Returns:
            Lista de lotes de importación completados exitosamente
        """
        try:
            return (
                self.db_session.query(ImportBatch)
                .filter(ImportBatch.status == 'COMPLETED')
                .filter(ImportBatch.error_rows == 0)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def get_failed_batches(self) -> List[ImportBatch]:
        """
        Obtiene lotes de importación fallidos.
        
        Returns:
            Lista de lotes de importación fallidos
        """
        try:
            return (
                self.db_session.query(ImportBatch)
                .filter(ImportBatch.status == 'FAILED')
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise