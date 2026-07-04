from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.document import DocumentTemplate, GeneratedDocument, TemplateType
from app.models.user import User
from app.schemas.document import DocumentTemplateResponse, DocumentTemplateCreate, GeneratedDocumentResponse

router = APIRouter()


@router.get("/templates/", response_model=List[DocumentTemplateResponse])
async def get_templates(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener plantillas documentales del tenant."""
    statement = select(DocumentTemplate).where(
        DocumentTemplate.tenant_id == current_user.tenant_id,
        DocumentTemplate.is_active == is_active
    )
    templates = session.exec(statement.offset(skip).limit(limit)).all()
    return templates


@router.get("/templates/{template_id}", response_model=DocumentTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener una plantilla específica."""
    template = session.get(DocumentTemplate, template_id)
    if not template or template.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.post("/templates/", response_model=DocumentTemplateResponse)
async def create_template(
    name: str,
    code: str,
    description: Optional[str] = None,
    template_type: TemplateType = TemplateType.DOCX,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Crear una nueva plantilla documental."""
    # Verificar código único
    statement = select(DocumentTemplate).where(
        DocumentTemplate.code == code,
        DocumentTemplate.tenant_id == current_user.tenant_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una plantilla con este código")
    
    content = await file.read()
    
    template = DocumentTemplate(
        name=name,
        code=code,
        description=description,
        template_type=template_type,
        tenant_id=current_user.tenant_id,
        content=content,
        variables_schema={},
        version=1,
        is_active=True
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.post("/generate/")
async def generate_document(
    template_id: int,
    variables: dict,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Generar documento desde plantilla."""
    from app.services.document_service import generate_document_from_template
    
    template = session.get(DocumentTemplate, template_id)
    if not template or template.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    result = await generate_document_from_template(
        template=template,
        variables=variables,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        session=session
    )
    
    return result


@router.get("/generated/", response_model=List[GeneratedDocumentResponse])
async def get_generated_documents(
    skip: int = 0,
    limit: int = 100,
    process_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Obtener documentos generados."""
    statement = select(GeneratedDocument).where(
        GeneratedDocument.tenant_id == current_user.tenant_id
    )
    
    if process_id:
        statement = statement.where(GeneratedDocument.process_id == process_id)
    
    documents = session.exec(statement.offset(skip).limit(limit)).all()
    return documents
