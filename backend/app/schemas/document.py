"""
Schemas para documentos y generación
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class DocumentTemplateBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    variables_schema: Dict[str, Any] = {}

class DocumentTemplateCreate(DocumentTemplateBase):
    tenant_id: int

class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    tenant_id: int
    version: int
    file_path: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentGenerationRequest(BaseModel):
    template_id: int
    process_id: int
    variables: Dict[str, Any]

class BatchGenerationRequest(BaseModel):
    template_id: int
    process_ids: List[int]
    variables_override: Optional[Dict[str, Any]] = None

class GeneratedDocumentResponse(BaseModel):
    id: int
    process_id: int
    template_id: int
    file_path: str
    generated_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True
