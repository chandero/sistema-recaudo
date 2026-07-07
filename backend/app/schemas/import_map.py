from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ImportMappingBase(BaseModel):
    name: str = Field(..., description="Nombre de la plantilla")
    description: Optional[str] = None
    mapping_config: Dict[str, str] = Field(..., description="Mapeo columna archivo -> campo sistema")
    supported_fields: Optional[List[str]] = None

class ImportMappingCreate(ImportMappingBase):
    pass

class ImportMappingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mapping_config: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

class ImportMappingResponse(ImportMappingBase):
    id: int
    tenant_id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ImportBatchBase(BaseModel):
    filename: str
    original_filename: str
    total_rows: int = 0
    import_options: Optional[Dict[str, Any]] = None

class ImportBatchCreate(ImportBatchBase):
    pass

class ImportBatchResponse(ImportBatchBase):
    id: int
    tenant_id: int
    user_id: int
    status: str
    processed_rows: int = 0
    success_rows: int = 0
    error_rows: int = 0
    mapping_template_id: Optional[int] = None
    custom_mapping: Optional[Dict[str, str]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    detected_columns: Optional[List[str]] = None  # Solo para respuesta después de upload
    
    class Config:
        from_attributes = True

class ImportBatchStatusResponse(BaseModel):
    id: int
    status: str
    total_rows: int
    processed_rows: int
    success_rows: int
    error_rows: int
    errors_log: Optional[List[Dict[str, Any]]] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
