from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from datetime import datetime

class ImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    MAPPING = "MAPPING"  # Esperando mapeo del usuario
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"  # Completado con errores

class ImportBatch(Base):
    """Lote de importación de clientes/obligaciones desde Excel/CSV"""
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)  # Ruta temporal del archivo
    
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PENDING)
    
    # Mapeo usado (referencia a plantilla o mapeo manual)
    mapping_template_id = Column(Integer, ForeignKey("import_mapping_templates.id"), nullable=True)
    custom_mapping = Column(JSON, nullable=True)  # Si no usa plantilla
    
    # Configuración de importación
    import_options = Column(JSON, default={
        "skip_header": True,
        "delimiter": ",",
        "encoding": "utf-8",
        "update_duplicates": False,
        "create_clients": True,
        "create_obligations": True
    })
    
    # Errores detallados
    errors_log = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relaciones
    tenant = relationship("Tenant", back_populates="import_batches")
    user = relationship("User", back_populates="import_batches")
    mapping_template = relationship("ImportMappingTemplate", back_populates="batches")
