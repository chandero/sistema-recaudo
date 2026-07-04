from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    DOCX = "DOCX"
    PDF = "PDF"


class DocumentTemplateBase(BaseModel):
    name: str
    code: str
    template_type: TemplateType = TemplateType.DOCX
    description: Optional[str] = None
    version: int = 1
    is_active: bool = True
    variables_schema: Optional[Dict] = None


class DocumentTemplateCreate(DocumentTemplateBase):
    content: bytes


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    template_type: Optional[TemplateType] = None
    description: Optional[str] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    variables_schema: Optional[Dict] = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GeneratedDocumentBase(BaseModel):
    filename: str
    document_type: str
    variables_used: Optional[Dict] = None
    resolution_number: Optional[str] = None
    radicado_number: Optional[str] = None


class GeneratedDocumentCreate(GeneratedDocumentBase):
    process_id: Optional[int] = None
    template_id: Optional[int] = None
    client_id: Optional[int] = None
    obligation_id: Optional[int] = None
    file_path: str
    file_size: int = 0


class GeneratedDocumentResponse(GeneratedDocumentBase):
    id: int
    tenant_id: int
    process_id: Optional[int] = None
    template_id: Optional[int] = None
    client_id: Optional[int] = None
    obligation_id: Optional[int] = None
    file_path: str
    file_size: int
    created_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
