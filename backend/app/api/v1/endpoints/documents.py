"""
Endpoints para generación de documentos y gestión de correspondencia
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Optional
import os
import shutil
import json

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.document import DocumentTemplate, GeneratedDocument
from app.schemas.document import (
    DocumentTemplateCreate, 
    DocumentTemplateResponse, 
    DocumentGenerationRequest,
    BatchGenerationRequest,
    GeneratedDocumentResponse
)
from app.models.process import CobroProcess
from app.services.document_service import DocumentGenerationService

router = APIRouter()

UPLOAD_DIR = "app/uploads/templates"
OUTPUT_DIR = "app/uploads/generated"

# Asegurar directorios
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.get("/templates", response_model=List[DocumentTemplateResponse])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener plantillas del tenant"""
    statement = select(DocumentTemplate).where(
        DocumentTemplate.tenant_id == current_user.tenant_id,
        DocumentTemplate.is_active == True
    ).offset(skip).limit(limit)
    templates = session.exec(statement).all()
    return templates


@router.post("/templates", response_model=DocumentTemplateResponse)
def create_template(
    name: str = Form(...),
    code: str = Form(...),
    description: Optional[str] = Form(None),
    variables_schema: str = Form("{}"),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Subir nueva plantilla documental"""
    # Validar unicidad de código
    statement = select(DocumentTemplate).where(
        DocumentTemplate.code == code,
        DocumentTemplate.tenant_id == current_user.tenant_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de plantilla ya existe")
    
    # Guardar archivo
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.tenant_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Leer contenido del archivo
    file_content = open(file_path, "rb").read()
    
    # Parse variables_schema if it's a string
    if isinstance(variables_schema, str):
        try:
            variables_schema = json.loads(variables_schema)
        except (json.JSONDecodeError, TypeError):
            variables_schema = {}
    
    # Crear registro
    template = DocumentTemplate(
        name=name,
        code=code,
        description=description,
        content=file_content,
        file_path=file_path,
        variables_schema=variables_schema,
        tenant_id=current_user.tenant_id,
        version=1
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.get("/generated", response_model=List[GeneratedDocumentResponse])
def get_generated_documents(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener documentos generados del tenant"""
    statement = select(GeneratedDocument).where(
        GeneratedDocument.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit)
    documents = session.exec(statement).all()
    return documents


@router.post("/generate")
def generate_document(
    request: DocumentGenerationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Generar un documento individual"""
    statement = select(DocumentTemplate).where(
        DocumentTemplate.id == request.template_id,
        DocumentTemplate.tenant_id == current_user.tenant_id
    )
    template = session.exec(statement).first()
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    output_filename = f"doc_{request.process_id}_{template.code}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        # Crear archivo temporal DOCX
        temp_docx = output_path.replace(".pdf", ".docx")
        
        # Generar documento
        DocumentGenerationService.render_template(
            template.file_path, 
            request.variables, 
            temp_docx
        )
        
        # Convertir a PDF
        DocumentGenerationService.convert_to_pdf(
            temp_docx,
            output_path
        )
        
        # Registrar en BD
        doc_record = GeneratedDocument(
            process_id=request.process_id,
            template_id=template.id,
            file_path=output_path,
            filename=output_filename,
            document_type="PDF",
            tenant_id=current_user.tenant_id,
            created_by=current_user.id
        )
        session.add(doc_record)
        session.commit()
        
        # Limpieza
        if os.path.exists(temp_docx):
            os.remove(temp_docx)
        
        return {"message": "Documento generado", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/batch")
def generate_batch_documents(
    request: BatchGenerationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Generar lote masivo de documentos"""
    statement = select(DocumentTemplate).where(
        DocumentTemplate.id == request.template_id,
        DocumentTemplate.tenant_id == current_user.tenant_id
    )
    template = session.exec(statement).first()
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Obtener datos de los procesos
    statement = select(CobroProcess).where(
        CobroProcess.id.in_(request.process_ids),
        CobroProcess.tenant_id == current_user.tenant_id
    )
    processes = session.exec(statement).all()
    
    if len(processes) != len(request.process_ids):
        raise HTTPException(status_code=400, detail="Algunos procesos no existen o no pertenecen al tenant")
    
    # Preparar datos para generación
    proc_data = []
    for p in processes:
        proc_data.append({
            'cliente_nombre': p.client.name if p.client else 'N/A',
            'cliente_identificacion': p.client.identification if p.client else 'N/A',
            'obligacion_numero': p.obligation.numero_obligacion if p.obligation else 'N/A',
            'valor_total': p.obligation.valor_total if p.obligation else 0,
            'radicado': getattr(p, 'radicado_number', None) or 'PENDIENTE',
            'resolucion': getattr(p, 'resolution_number', None) or 'PENDIENTE',
            'fecha_emision': p.created_at.strftime('%Y-%m-%d'),
            'entidad_nombre': current_user.tenant.name
        })
    
    try:
        zip_path = DocumentGenerationService.generate_batch(
            templates=[{'path': template.file_path}],
            processes=proc_data,
            output_dir=OUTPUT_DIR
        )
        return {"message": f"Lote generado: {len(processes)} documentos", "zip_path": zip_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-to-correspondence")
def send_to_correspondence(
    document_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Enviar documento a correspondencia"""
    statement = select(GeneratedDocument).where(
        GeneratedDocument.id == document_id,
        GeneratedDocument.tenant_id == current_user.tenant_id
    )
    document = session.exec(statement).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Aquí se integraría con el sistema de correspondencia
    # Por ahora solo marcamos como enviado
    document.is_sent = True
    document.sent_at = datetime.utcnow()
    session.add(document)
    session.commit()
    session.refresh(document)
    
    return {"message": f"Documento #{document_id} enviado a correspondencia", "document": document}
