from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.models.document import Document


class DocumentService:
    """
    Servicio para operaciones relacionadas con documentos.
    Este servicio actúa como intermediario entre las capas de presentación y persistencia,
    utilizando el repositorio correspondiente para las operaciones de base de datos.
    """
    
    def __init__(self, db: Session):
        self.repository = DocumentRepository(db)

    def get_document(self, document_id: int) -> Optional[Document]:
        """
        Obtiene un documento por su ID.
        
        Args:
            document_id: ID del documento
            
        Returns:
            Documento con el ID especificado o None si no se encuentra
        """
        return self.repository.get(document_id)

    def get_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Obtiene una lista de documentos con opción de paginación.
        
        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Límite de registros a devolver
            
        Returns:
            Lista de documentos
        """
        return self.repository.get_all(skip, limit)

    def get_documents_by_client(self, client_id: int) -> List[Document]:
        """
        Obtiene todos los documentos de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de documentos del cliente
        """
        return self.repository.get_by_client(client_id)

    def get_documents_by_obligation(self, obligation_id: int) -> List[Document]:
        """
        Obtiene todos los documentos relacionados con una obligación específica.
        
        Args:
            obligation_id: ID de la obligación
            
        Returns:
            Lista de documentos relacionados con la obligación
        """
        return self.repository.get_by_obligation(obligation_id)

    def get_documents_by_type(self, doc_type: str) -> List[Document]:
        """
        Obtiene documentos por tipo.
        
        Args:
            doc_type: Tipo de documento
            
        Returns:
            Lista de documentos del tipo especificado
        """
        return self.repository.get_by_type(doc_type)

    def get_documents_by_status(self, status: str) -> List[Document]:
        """
        Obtiene documentos por estado.
        
        Args:
            status: Estado del documento
            
        Returns:
            Lista de documentos con el estado especificado
        """
        return self.repository.get_by_status(status)

    def get_documents_by_date_range(self, start_date: str, end_date: str) -> List[Document]:
        """
        Obtiene documentos dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de documentos dentro del rango de fechas
        """
        return self.repository.get_by_date_range(start_date, end_date)

    def create_document(self, document_create: DocumentCreate) -> Document:
        """
        Crea un nuevo documento.
        
        Args:
            document_create: Datos del documento a crear
            
        Returns:
            Documento creado
        """
        return self.repository.create_document(document_create)

    def update_document(self, document_id: int, document_update: DocumentUpdate) -> Optional[Document]:
        """
        Actualiza un documento existente.
        
        Args:
            document_id: ID del documento a actualizar
            document_update: Datos actualizados del documento
            
        Returns:
            Documento actualizado o None si no se encuentra
        """
        return self.repository.update_document(document_id, document_update)

    def delete_document(self, document_id: int) -> bool:
        """
        Elimina un documento por su ID.
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        return self.repository.delete(document_id)

    def get_documents_by_client_and_type(self, client_id: int, doc_type: str) -> List[Document]:
        """
        Obtiene documentos de un cliente específico por tipo.
        
        Args:
            client_id: ID del cliente
            doc_type: Tipo de documento
            
        Returns:
            Lista de documentos del cliente y tipo especificados
        """
        return self.repository.get_documents_by_client_and_type(client_id, doc_type)

    def count_documents(self) -> int:
        """
        Cuenta el número total de documentos.
        
        Returns:
            Número total de documentos
        """
        return self.repository.count()