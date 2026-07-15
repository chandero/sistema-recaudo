from sqlmodel import SQLModel
from app.core.logging.logger import get_logger

# Logger para modelos
model_logger = get_logger("models")

class Base(SQLModel):
    """Clase base para todos los modelos de la aplicación."""
    
    @classmethod
    def create_tables(cls, engine):
        """Crear todas las tablas asociadas a los modelos."""
        try:
            SQLModel.metadata.create_all(bind=engine)
            model_logger.info(
                module="models",
                action="tables_created",
                message="Tablas de base de datos creadas exitosamente"
            )
        except Exception as e:
            model_logger.error(
                module="models",
                action="tables_creation_failed",
                message=f"Error creando tablas de base de datos: {str(e)}",
                error_code="TABLES_CREATION_ERROR"
            )
            raise
    
    def dict(self):
        """Convierte el modelo a un diccionario excluyendo campos nulos."""
        result = {}
        for attr, value in self.__dict__.items():
            if not attr.startswith('_'):  # Excluir atributos privados
                if value is not None:  # Excluir valores nulos
                    result[attr] = value
        return result