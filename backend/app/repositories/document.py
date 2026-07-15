from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import GeneratedDocument
from app.schemas.document import GeneratedDocumentCreate, GeneratedDocumentResponse
from .base import BaseRepository


class DocumentRepository(BaseRepository[GeneratedDocument]):
    """
    Repositorio para operaciones CRUD relacionadas con documentos generados.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, GeneratedDocument)

    def get_by_client(self, client_id: int) -> List[GeneratedDocument]:
        """
        Obtiene todos los documentos generados de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de documentos generados del cliente
        """
        try:
            return self.db_session.query(GeneratedDocument).filter(GeneratedDocument.client_id == client_id).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_obligation(self, obligation_id: int) -> List[GeneratedDocument]:
        """
        Obtiene todos los documentos generados relacionados con una obligación específica.
        
        Args:
            obligation_id: ID de la obligación
            
        Returns:
            Lista de documentos generados relacionados con la obligación
        """
        try:
            return self.db_session.query(GeneratedDocument).filter(GeneratedDocument.obligation_id == obligation_id).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_document_type(self, doc_type: str) -> List[GeneratedDocument]:
        """
        Obtiene documentos generados por tipo de documento.
        
        Args:
            doc_type: Tipo de documento
            
        Returns:
            Lista de documentos generados del tipo especificado
        """
        try:
            return self.db_session.query(GeneratedDocument).filter(GeneratedDocument.document_type == doc_type).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_status(self, status: str) -> List[GeneratedDocument]:
        """
        Obtiene documentos generados por estado de envío.
        
        Args:
            status: Estado de envío del documento (is_sent)
            
        Returns:
            Lista de documentos generados con el estado especificado
        """
        try:
            # Convertimos el string a booleano para comparar con el campo is_sent
            is_sent = status.lower() == 'sent' or status.lower() == 'true'
            return self.db_session.query(GeneratedDocument).filter(GeneratedDocument.is_sent == is_sent).all()
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_date_range(self, start_date: str, end_date: str) -> List[GeneratedDocument]:
        """
        Obtiene documentos generados dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de documentos generados dentro del rango de fechas
        """
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            return (
                self.db_session.query(GeneratedDocument)
                .filter(GeneratedDocument.created_at >= start_dt)
                .filter(GeneratedDocument.created_at <= end_dt)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise

    def create_document(self, document_create: GeneratedDocumentCreate) -> GeneratedDocument:
        """
        Crea un nuevo documento generado.
        
        Args:
            document_create: Datos del documento a crear
            
        Returns:
            Documento generado creado
        """
        try:
            document = GeneratedDocument(
                filename=document_create.filename,
                document_type=document_create.document_type,
                tenant_id=document_create.tenant_id,
                process_id=document_create.process_id,
                template_id=document_create.template_id,
                client_id=document_create.client_id,
                obligation_id=document_create.obligation_id,
                file_path=document_create.file_path,
                file_size=document_create.file_size,
                variables_used=document_create.variables_used,
                resolution_number=document_create.resolution_number,
                radicado_number=document_create.radicado_number,
                created_by=document_create.created_by
            )
            self.db_session.add(document)
            self.db_session.commit()
            self.db_session.refresh(document)
            return document
        except Exception:
            self.db_session.rollback()
            raise

    def update_document(self, document_id: int, document_update: GeneratedDocumentResponse) -> Optional[GeneratedDocument]:
        """
        Actualiza un documento generado existente.
        
        Args:
            document_id: ID del documento a actualizar
            document_update: Datos actualizados del documento
            
        Returns:
            Documento actualizado o None si no se encuentra
        """
        try:
            document = self.get(document_id)
            if document:
                update_data = document_update.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(document, field, value)
                
                self.db_session.commit()
                self.db_session.refresh(document)
            return document
        except Exception:
            self.db_session.rollback()
            raise

    def get_documents_by_client_and_type(self, client_id: int, doc_type: str) -> List[GeneratedDocument]:
        """
        Obtiene documentos generados de un cliente específico por tipo.
        
        Args:
            client_id: ID del cliente
            doc_type: Tipo de documento
            
        Returns:
            Lista de documentos generados del cliente y tipo especificados
        """
        try:
            return (
                self.db_session.query(GeneratedDocument)
                .filter(GeneratedDocument.client_id == client_id)
                .filter(GeneratedDocument.document_type == doc_type)
                .all()
            )
        except Exception:
            self.db_session.rollback()
            raise