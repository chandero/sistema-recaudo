from pydantic import BaseModel, validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum
import json


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
    variables_schema: Optional[Union[str, Dict[str, Any]]] = None
    
    @validator('variables_schema', pre=True, always=True)
    def normalize_variables_schema(cls, v):
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        if isinstance(v, dict):
            return v
        return {}


class DocumentTemplateCreate(DocumentTemplateBase):
    content: Optional[bytes] = None


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    template_type: Optional[TemplateType] = None
    description: Optional[str] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    variables_schema: Optional[Union[str, Dict[str, Any]]] = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            dict: lambda v: json.dumps(v) if isinstance(v, dict) else v
        }


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
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Request schemas for document generation
class DocumentGenerationRequest(BaseModel):
    template_id: int
    process_id: int
    variables: Dict[str, str]


class BatchGenerationRequest(BaseModel):
    template_id: int
    process_ids: List[int]
