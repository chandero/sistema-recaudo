from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.import_map import ImportMappingTemplate
from app.models.import_batch import ImportBatch, ImportStatus
from app.schemas.import_map import ImportMappingCreate, ImportMappingResponse, ImportMappingUpdate
from app.schemas.import_batch import ImportBatchCreate, ImportBatchResponse, ImportBatchStatusResponse
from app.services.import_service import ImportService

router = APIRouter()

# Campos estándar del sistema para mapeo
STANDARD_FIELDS = {
    "cliente": [
        "identificacion", "nombre", "direccion", "telefono", "email", 
        "tipo_persona", "municipio", "departamento"
    ],
    "obligacion": [
        "numero_obligacion", "vigencia", "valor_total", "capital", 
        "intereses", "multas", "fecha_emision", "fecha_vencimiento",
        "concepto", "estado"
    ]
}

@router.get("/standard-fields", response_model=dict)
def get_standard_fields():
    """Obtiene los campos estándar del sistema disponibles para mapeo"""
    return STANDARD_FIELDS


@router.post("/mapping-templates", response_model=ImportMappingResponse)
def create_mapping_template(
    template: ImportMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva plantilla de mapeo de columnas"""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    # Validar que el mapping solo contenga campos válidos
    for source_col, target_field in template.mapping_config.items():
        valid_fields = STANDARD_FIELDS["cliente"] + STANDARD_FIELDS["obligacion"]
        if target_field not in valid_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Campo '{target_field}' no es un campo válido del sistema"
            )
    
    db_template = ImportMappingTemplate(
        tenant_id=current_user.tenant_id,
        name=template.name,
        description=template.description,
        mapping_config=template.mapping_config,
        supported_fields=template.supported_fields or list(STANDARD_FIELDS.keys()),
        is_active=True
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.get("/mapping-templates", response_model=List[ImportMappingResponse])
def list_mapping_templates(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista las plantillas de mapeo del tenant"""
    query = db.query(ImportMappingTemplate).filter(
        ImportMappingTemplate.tenant_id == current_user.tenant_id
    )
    
    if active_only:
        query = query.filter(ImportMappingTemplate.is_active == True)
    
    templates = query.offset(skip).limit(limit).all()
    return templates


@router.get("/mapping-templates/{template_id}", response_model=ImportMappingResponse)
def get_mapping_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene una plantilla de mapeo específica"""
    template = db.query(ImportMappingTemplate).filter(
        ImportMappingTemplate.id == template_id,
        ImportMappingTemplate.tenant_id == current_user.tenant_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    return template


@router.put("/mapping-templates/{template_id}", response_model=ImportMappingResponse)
def update_mapping_template(
    template_id: int,
    template_update: ImportMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza una plantilla de mapeo"""
    template = db.query(ImportMappingTemplate).filter(
        ImportMappingTemplate.id == template_id,
        ImportMappingTemplate.tenant_id == current_user.tenant_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/mapping-templates/{template_id}")
def delete_mapping_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina (desactiva) una plantilla de mapeo"""
    template = db.query(ImportMappingTemplate).filter(
        ImportMappingTemplate.id == template_id,
        ImportMappingTemplate.tenant_id == current_user.tenant_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Soft delete
    template.is_active = False
    db.commit()
    
    return {"message": "Plantilla desactivada exitosamente"}


@router.post("/upload", response_model=ImportBatchResponse)
async def upload_file(
    file: UploadFile = File(...),
    template_id: Optional[int] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sube un archivo Excel/CSV y crea un lote de importación"""
    # Validar extensión
    allowed_extensions = [".xlsx", ".xls", ".csv"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Archivo no válido. Extensiones permitidas: {', '.join(allowed_extensions)}"
        )
    
    # Crear directorio temporal si no existe
    temp_dir = "/tmp/imports"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Guardar archivo temporalmente
    temp_path = f"{temp_dir}/{current_user.tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Leer primeras filas para análisis
    try:
        if file_ext == ".csv":
            df = pd.read_csv(temp_path, nrows=5)
        else:
            df = pd.read_excel(temp_path, nrows=5)
        
        columns = df.columns.tolist()
        total_rows_estimate = len(pd.read_excel(temp_path) if file_ext != ".csv" else pd.read_csv(temp_path))
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Error al leer archivo: {str(e)}")
    
    # Crear lote de importación
    db_batch = ImportBatch(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        filename=temp_path,
        original_filename=file.filename,
        file_path=temp_path,
        total_rows=total_rows_estimate - 1,  # Restar header
        status=ImportStatus.MAPPING if not template_id else ImportStatus.PENDING,
        mapping_template_id=template_id,
        import_options={
            "skip_header": True,
            "delimiter": "," if file_ext == ".csv" else None,
            "encoding": "utf-8",
            "update_duplicates": False,
            "create_clients": True,
            "create_obligations": True
        }
    )
    
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    
    # Si hay plantilla, iniciar procesamiento en background
    if template_id and background_tasks:
        background_tasks.add_task(
            ImportService.process_import,
            db_batch.id,
            current_user.tenant_id
        )
    
    # Retornar columnas detectadas para mapeo
    result = ImportBatchResponse.from_orm(db_batch)
    result.detected_columns = columns
    
    return result


@router.post("/batches/{batch_id}/map-and-process")
def map_and_process_batch(
    batch_id: int,
    mapping: dict,
    save_as_template: bool = False,
    template_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aplica mapeo manual y procesa el lote"""
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.tenant_id == current_user.tenant_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    if batch.status != ImportStatus.MAPPING:
        raise HTTPException(
            status_code=400, 
            detail=f"El lote está en estado {batch.status}, no se puede mapear"
        )
    
    # Validar mapping
    valid_fields = STANDARD_FIELDS["cliente"] + STANDARD_FIELDS["obligacion"]
    for target_field in mapping.values():
        if target_field not in valid_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Campo '{target_field}' no es válido"
            )
    
    # Guardar mapeo personalizado
    batch.custom_mapping = mapping
    
    # Opcional: guardar como plantilla
    if save_as_template and template_name:
        new_template = ImportMappingTemplate(
            tenant_id=current_user.tenant_id,
            name=template_name,
            mapping_config=mapping,
            supported_fields=list(mapping.values()),
            is_active=True
        )
        db.add(new_template)
        batch.mapping_template_id = new_template.id
    
    # Cambiar estado y procesar
    batch.status = ImportStatus.PROCESSING
    db.commit()
    
    # Procesar en background
    ImportService.process_import(batch_id, current_user.tenant_id)
    
    return {"message": "Procesamiento iniciado", "batch_id": batch_id}


@router.get("/batches", response_model=List[ImportBatchResponse])
def list_import_batches(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ImportStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista los lotes de importación del tenant"""
    query = db.query(ImportBatch).filter(
        ImportBatch.tenant_id == current_user.tenant_id
    )
    
    if status:
        query = query.filter(ImportBatch.status == status)
    
    batches = query.order_by(ImportBatch.created_at.desc()).offset(skip).limit(limit).all()
    return batches


@router.get("/batches/{batch_id}", response_model=ImportBatchResponse)
def get_import_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene detalles de un lote de importación"""
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.tenant_id == current_user.tenant_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    return batch


@router.get("/batches/{batch_id}/status", response_model=ImportBatchStatusResponse)
def get_batch_status(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el estado actual del procesamiento del lote"""
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.tenant_id == current_user.tenant_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    return ImportBatchStatusResponse(
        id=batch.id,
        status=batch.status,
        total_rows=batch.total_rows,
        processed_rows=batch.processed_rows,
        success_rows=batch.success_rows,
        error_rows=batch.error_rows,
        errors_log=batch.errors_log,
        completed_at=batch.completed_at
    )
