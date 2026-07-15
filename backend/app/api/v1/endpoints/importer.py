from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
import pandas as pd
import json
import os
from datetime import datetime
import uuid

from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.import_map import ImportMappingTemplate
from app.models.import_batch import ImportBatch, ImportStatus
from app.models.workflow import WorkflowState
from app.schemas.import_map import ImportMappingCreate, ImportMappingResponse, ImportMappingUpdate
from app.schemas.import_batch import ImportBatchCreate, ImportBatchResponse, ImportBatchStatusResponse
from app.services import import_service

router = APIRouter()

# Campos estándar del sistema para mapeo
STANDARD_FIELDS = {
    "cliente": [
        "identificacion", "nombre", "direccion", "telefono", "email", 
        "tipo_persona", "municipio", "departamento"
    ],
    "obligacion": [
        "numero_obligacion", "vigencia", "valor_total", "capital", 
        "intereses", "mora", "fecha_emision", "fecha_vencimiento",
        "concepto", "estado"
    ]
}

FRONTEND_STANDARD_FIELDS = {
    "cliente": [
        "client.identification", "client.name", "client.address", "client.phone",
        "client.email", "client.additional_attributes.custom_field_1",
        "client.additional_attributes.custom_field_2", "client.additional_attributes.custom_field_3",
        "client.additional_attributes.document_type", "client.additional_attributes.municipality",
        "client.additional_attributes.cycle", "client.additional_attributes.account_number",
        "client.additional_attributes.cadastral_record", "client.additional_attributes.service_class",
        "client.additional_attributes.aging", "client.additional_attributes.apu_value"
    ],
    "obligacion": [
        "obligation.number", "obligation.amount", "obligation.issue_date",
        "obligation.due_date", "obligation.concept", "obligation.status",
        "obligation.additional_attributes.custom_field_1",
        "obligation.additional_attributes.custom_field_2",
        "obligation.additional_attributes.custom_field_3"
    ]
}


def get_valid_mapping_fields() -> List[str]:
    return (
        STANDARD_FIELDS["cliente"] +
        STANDARD_FIELDS["obligacion"] +
        FRONTEND_STANDARD_FIELDS["cliente"] +
        FRONTEND_STANDARD_FIELDS["obligacion"]
    )


@router.get("/standard-fields", response_model=dict)
def get_standard_fields():
    """Obtiene los campos estándar del sistema disponibles para mapeo"""
    try:
        return STANDARD_FIELDS
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo campos estándar: {str(e)}")


@router.post("/mapping-templates", response_model=ImportMappingResponse)
def create_mapping_template(
    template: ImportMappingCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Crea una nueva plantilla de mapeo de columnas"""
    try:
        # Validar que el mapping solo contenga campos válidos
        for target_field in template.mapping_config.values():
            valid_fields = get_valid_mapping_fields()
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
        
        session.add(db_template)
        session.commit()
        session.refresh(db_template)
        
        return db_template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando plantilla de mapeo: {str(e)}")


@router.get("/mapping-templates", response_model=List[ImportMappingResponse])
def list_mapping_templates(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Lista las plantillas de mapeo del tenant"""
    try:
        statement = select(ImportMappingTemplate).where(
            ImportMappingTemplate.tenant_id == current_user.tenant_id
        )
        
        if active_only:
            statement = statement.where(ImportMappingTemplate.is_active == True)
        
        statement = statement.offset(skip).limit(limit)
        templates = session.exec(statement).all()
        return templates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando plantillas de mapeo: {str(e)}")


@router.get("/mapping-templates/{template_id}", response_model=ImportMappingResponse)
def get_mapping_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene una plantilla de mapeo específica"""
    try:
        statement = select(ImportMappingTemplate).where(
            ImportMappingTemplate.id == template_id,
            ImportMappingTemplate.tenant_id == current_user.tenant_id
        )
        template = session.exec(statement).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo plantilla de mapeo: {str(e)}")


@router.put("/mapping-templates/{template_id}", response_model=ImportMappingResponse)
def update_mapping_template(
    template_id: int,
    template_update: ImportMappingUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza una plantilla de mapeo"""
    try:
        statement = select(ImportMappingTemplate).where(
            ImportMappingTemplate.id == template_id,
            ImportMappingTemplate.tenant_id == current_user.tenant_id
        )
        template = session.exec(statement).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        update_data = template_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        session.add(template)
        session.commit()
        session.refresh(template)
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando plantilla de mapeo: {str(e)}")


@router.delete("/mapping-templates/{template_id}")
def delete_mapping_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Elimina (desactiva) una plantilla de mapeo"""
    try:
        statement = select(ImportMappingTemplate).where(
            ImportMappingTemplate.id == template_id,
            ImportMappingTemplate.tenant_id == current_user.tenant_id
        )
        template = session.exec(statement).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Soft delete
        template.is_active = False
        session.add(template)
        session.commit()
        
        return {"message": "Plantilla desactivada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando plantilla de mapeo: {str(e)}")


@router.get("/mapping-templates/{template_id}/preview")
def get_template_preview(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene una vista previa detallada de una plantilla de mapeo"""
    try:
        statement = select(ImportMappingTemplate).where(
            ImportMappingTemplate.id == template_id,
            ImportMappingTemplate.tenant_id == current_user.tenant_id
        )
        template = session.exec(statement).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Convertir el objeto de plantilla al formato de vista previa
        preview_data = {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'is_active': template.is_active,
            'created_at': template.created_at,
            'mapping_config': template.mapping_config,
            'supported_fields': template.supported_fields,
            'mapped_columns_count': len(template.mapping_config) if template.mapping_config else 0,
            'mapped_columns': list(template.mapping_config.keys()) if template.mapping_config else [],
            'mapped_system_fields': list(template.mapping_config.values()) if template.mapping_config else []
        }
        
        return preview_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo vista previa de plantilla: {str(e)}")


@router.post("/validate-file")
async def validate_import_file(
    file: UploadFile = File(...),
    mapping_config: str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Valida un archivo de importación antes de procesarlo"""
    try:
        import tempfile
        import os
        
        # Validar extensión
        allowed_extensions = [".xlsx", ".xls", ".csv"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Archivo no válido. Extensiones permitidas: {', '.join(allowed_extensions)}"
            )
        
        # Obtener el mapping config del formulario
        try:
            column_mapping = json.loads(mapping_config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Configuración de mapeo inválida")
        
        # Crear un directorio temporal único por usuario y sesión
        temp_dir = f"/tmp/imports/{current_user.id}_{uuid.uuid4().hex}"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = f"{temp_dir}/{current_user.tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Leer archivo
            if file_ext == ".csv":
                df = pd.read_csv(temp_path, encoding='utf-8')
            else:
                df = pd.read_excel(temp_path)
            
            # Validar contenido
            validation_result = import_service.validate_import_file_content(df, column_mapping)
            
            # Borrar archivo temporal
            os.remove(temp_path)
            # Borrar directorio temporal si está vacío
            os.rmdir(os.path.dirname(temp_path))
            
            return validation_result
        except Exception as e:
            # Borrar archivo temporal en caso de error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            # Borrar directorio temporal si existe
            temp_parent_dir = os.path.dirname(temp_path)
            if os.path.exists(temp_parent_dir):
                os.rmdir(temp_parent_dir)
            raise HTTPException(status_code=400, detail=f"Error al validar archivo: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando archivo: {str(e)}")


@router.post("/upload", response_model=ImportBatchResponse)
async def upload_file(
    file: UploadFile = File(...),
    template_id: Optional[int] = Form(None),
    column_mapping: Optional[str] = Form(None),
    initial_process_state: Optional[int] = Form(None),
    save_template: bool = Form(False),
    template_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Sube un archivo Excel/CSV y crea un lote de importación"""
    try:
        # Validar extensión
        allowed_extensions = [".xlsx", ".xls", ".csv"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Archivo no válido. Extensiones permitidas: {', '.join(allowed_extensions)}"
            )
        
        # Crear un directorio temporal único por usuario y sesión
        temp_dir = f"/tmp/imports/{current_user.id}_{uuid.uuid4().hex}"
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
            total_rows_df = pd.read_excel(temp_path) if file_ext != ".csv" else pd.read_csv(temp_path)
            total_rows_estimate = len(total_rows_df)
        except Exception as e:
            os.remove(temp_path)
            os.rmdir(temp_dir)
            raise HTTPException(status_code=400, detail=f"Error al leer archivo: {str(e)}")

        parsed_mapping = None
        if column_mapping:
            try:
                parsed_mapping = json.loads(column_mapping)
            except json.JSONDecodeError:
                os.remove(temp_path)
                os.rmdir(temp_dir)
                raise HTTPException(status_code=400, detail="Configuración de mapeo inválida")

            valid_fields = get_valid_mapping_fields()
            for target_field in parsed_mapping.values():
                if target_field and target_field not in valid_fields:
                    os.remove(temp_path)
                    os.rmdir(temp_dir)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo '{target_field}' no es válido"
                    )

        selected_state = None
        if initial_process_state:
            selected_state = session.get(WorkflowState, initial_process_state)
            if (
                not selected_state
                or selected_state.tenant_id != current_user.tenant_id
                or not selected_state.is_active
            ):
                os.remove(temp_path)
                os.rmdir(temp_dir)
                raise HTTPException(status_code=400, detail="Estado inicial no válido")

        selected_template = None
        if template_id:
            selected_template = session.get(ImportMappingTemplate, template_id)
            if (
                not selected_template
                or selected_template.tenant_id != current_user.tenant_id
                or not selected_template.is_active
            ):
                os.remove(temp_path)
                os.rmdir(temp_dir)
                raise HTTPException(status_code=400, detail="Plantilla de mapeo no válida")

        if parsed_mapping is None and selected_template:
            parsed_mapping = selected_template.mapping_config

        new_template = None
        if save_template and template_name and parsed_mapping:
            new_template = ImportMappingTemplate(
                tenant_id=current_user.tenant_id,
                name=template_name,
                mapping_config=parsed_mapping,
                supported_fields=list(parsed_mapping.values()),
                is_active=True
            )
            session.add(new_template)
            session.flush()

        import_options = {
            "skip_header": True,
            "delimiter": "," if file_ext == ".csv" else None,
            "encoding": "utf-8",
            "update_duplicates": False,
            "create_clients": True,
            "create_obligations": True
        }

        if selected_state:
            import_options["initial_process_state_id"] = selected_state.id
            import_options["initial_process_state_code"] = selected_state.code.value
            import_options["initial_process_state_name"] = selected_state.name
        
        # Crear lote de importación
        initial_status = ImportStatus.PENDING if parsed_mapping else ImportStatus.MAPPING
        db_batch = ImportBatch(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            filename=temp_path,
            original_filename=file.filename,
            file_path=temp_path,
            total_rows=total_rows_estimate - 1,  # Restar header
            status=initial_status,
            mapping_template_id=new_template.id if new_template else template_id,
            custom_mapping=parsed_mapping,
            import_options=import_options
        )
        
        session.add(db_batch)
        session.commit()
        session.refresh(db_batch)
        
        # Retornar columnas detectadas para mapeo
        result = ImportBatchResponse.from_orm(db_batch)
        result.detected_columns = columns

        if initial_status == ImportStatus.PENDING and background_tasks:
            background_tasks.add_task(import_service.process_import_batch, db_batch.id, current_user.tenant_id)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")


@router.post("/batches/{batch_id}/map-and-process")
def map_and_process_batch(
    batch_id: int,
    mapping: dict,
    save_as_template: bool = False,
    template_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Aplica mapeo manual y procesa el lote"""
    try:
        statement = select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.tenant_id == current_user.tenant_id
        )
        batch = session.exec(statement).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        
        if batch.status != ImportStatus.MAPPING:
            raise HTTPException(
                status_code=400, 
                detail=f"El lote está en estado {batch.status}, no se puede mapear"
            )
        
        # Validar mapping
        valid_fields = get_valid_mapping_fields()
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
            session.add(new_template)
            batch.mapping_template_id = new_template.id
        
        # Cambiar estado y procesar
        batch.status = ImportStatus.PROCESSING
        session.add(batch)
        session.commit()
        session.refresh(batch)
        
        if background_tasks:
            background_tasks.add_task(import_service.process_import_batch, batch_id, current_user.tenant_id)
        
        return {"message": "Procesamiento iniciado", "batch_id": batch_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando lote: {str(e)}")


@router.get("/batches", response_model=List[ImportBatchResponse])
def list_import_batches(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[ImportStatus] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Lista los lotes de importación del tenant"""
    try:
        statement = select(ImportBatch).where(
            ImportBatch.tenant_id == current_user.tenant_id
        )
        
        if status_filter:
            statement = statement.where(ImportBatch.status == status_filter)
        
        statement = statement.offset(skip).limit(limit).order_by(ImportBatch.created_at.desc())
        batches = session.exec(statement).all()
        return batches
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando lotes de importación: {str(e)}")


@router.get("/batches/{batch_id}", response_model=ImportBatchResponse)
def get_import_batch(
    batch_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene detalles de un lote de importación"""
    try:
        statement = select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.tenant_id == current_user.tenant_id
        )
        batch = session.exec(statement).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo lote de importación: {str(e)}")


@router.get("/batches/{batch_id}/status", response_model=ImportBatchStatusResponse)
def get_batch_status(
    batch_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene el estado actual del procesamiento del lote"""
    try:
        statement = select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.tenant_id == current_user.tenant_id
        )
        batch = session.exec(statement).first()
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de lote: {str(e)}")