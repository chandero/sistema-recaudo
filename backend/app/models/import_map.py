from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.tenant import Tenant

class ImportMappingTemplate(Base):
    """Plantilla de mapeo de columnas para importaciones Excel/CSV"""
    __tablename__ = "import_mapping_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, index=True, nullable=False)  # Ej: "Importación Alumbrado 2024"
    description = Column(String, nullable=True)
    
    # Estructura JSON: {"columna_archivo": "campo_sistema", ...}
    mapping_config = Column(JSON, nullable=False)
    
    # Campos estándar del sistema que soporta esta plantilla
    supported_fields = Column(JSON, nullable=False, default=list) 
    
    is_active = Column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="import_templates")
