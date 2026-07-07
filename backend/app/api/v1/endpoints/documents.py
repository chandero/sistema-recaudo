"""
Endpoints para generación de documentos y gestión de correspondencia
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.document import DocumentTemplate, GeneratedDocument
from app.schemas.document import (
    DocumentTemplateCreate, 
    DocumentTemplateResponse, 
    DocumentGenerationRequest,
    BatchGenerationRequest
)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener plantillas del tenant"""
    templates = db.query(DocumentTemplate).filter(
        DocumentTemplate.tenant_id == current_user.tenant_id,
        DocumentTemplate.is_active == True
    ).offset(skip).limit(limit).all()
    return templates

@router.post("/templates", response_model=DocumentTemplateResponse)
def create_template(
    name: str = Form(...),
    code: str = Form(...),
    description: Optional[str] = Form(None),
    variables_schema: str = Form("{}"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subir nueva plantilla documental"""
    # Validar unicidad de código
    existing = db.query(DocumentTemplate).filter(
        DocumentTemplate.code == code,
        DocumentTemplate.tenant_id == current_user.tenant_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de plantilla ya existe")
    
    # Guardar archivo
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.tenant_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Crear registro
    template = DocumentTemplate(
        name=name,
        code=code,
        description=description,
        file_path=file_path,
        variables_schema=variables_schema,
        tenant_id=current_user.tenant_id,
        version=1
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.post("/generate")
def generate_document(
    request: DocumentGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar un documento individual"""
    template = db.query(DocumentTemplate).filter(
        DocumentTemplate.id == request.template_id,
        DocumentTemplate.tenant_id == current_user.tenant_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    output_filename = f"doc_{request.process_id}_{template.code}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        # Generar documento
        DocumentGenerationService.render_template(
            template.file_path, 
            request.variables, 
            output_path.replace(".pdf", ".docx") # Temporal DOCX
        )
        
        # Convertir a PDF
        DocumentGenerationService.convert_to_pdf(
            output_path.replace(".pdf", ".docx"),
            output_path
        )
        
        # Registrar en BD
        doc_record = GeneratedDocument(
            process_id=request.process_id,
            template_id=template.id,
            file_path=output_path,
            generated_by=current_user.id,
            tenant_id=current_user.tenant_id
        )
        db.add(doc_record)
        db.commit()
        
        return {"message": "Documento generado", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/batch")
def generate_batch_documents(
    request: BatchGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar lote masivo de documentos"""
    template = db.query(DocumentTemplate).filter(
        DocumentTemplate.id == request.template_id,
        DocumentTemplate.tenant_id == current_user.tenant_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Obtener datos de los procesos
    from app.models.process import CollectionProcess
    processes = db.query(CollectionProcess).filter(
        CollectionProcess.id.in_(request.process_ids),
        CollectionProcess.tenant_id == current_user.tenant_id
    ).all()
    
    if len(processes) != len(request.process_ids):
        raise HTTPException(status_code=400, detail="Algunos procesos no existen o no pertenecen al tenant")
    
    # Preparar datos para generación
    proc_data = []
    for p in processes:
        proc_data.append({
            'cliente_nombre': p.client.name if p.client else 'N/A',
            'cliente_identificacion': p.client.identification if p.client else 'N/A',
            'obligacion_numero': p.obligation.number if p.obligation else 'N/A',
            'valor_total': p.obligation.total_amount if p.obligation else 0,
            'radicado': p.radicado_number or 'PENDIENTE',
            'resolucion': p.resolution_number or 'PENDIENTE',
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
