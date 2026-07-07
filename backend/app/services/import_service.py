"""
Servicio para importación de datos desde Excel/CSV.
Procesa archivos, mapea columnas y crea clientes y obligaciones.
"""

import io
from typing import Dict, List, Optional
from sqlmodel import Session, select
from fastapi import UploadFile, HTTPException
import pandas as pd

from app.models.client import Client, Obligation
from app.models.import_template import ImportTemplate


def detect_file_type(file: UploadFile) -> str:
    """Detectar el tipo de archivo (Excel o CSV)."""
    filename = file.filename.lower()
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        return 'excel'
    elif filename.endswith('.csv'):
        return 'csv'
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Use .xlsx o .csv")


async def read_file(file: UploadFile, file_type: str) -> pd.DataFrame:
    """Leer archivo Excel o CSV y retornar DataFrame."""
    content = await file.read()
    
    if file_type == 'excel':
        df = pd.read_excel(io.BytesIO(content))
    else:  # csv
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
    
    return df


def normalize_column_name(col_name: str) -> str:
    """Normalizar nombre de columna para facilitar matching."""
    normalized = col_name.strip().upper().replace('_', ' ').replace('-', ' ')
    return normalized


def suggest_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """Sugerir mapeo inteligente de columnas basado en nombres similares."""
    # Mapeo interno del sistema
    system_fields = {
        'IDENTIFICACION': ['identificacion', 'nit', 'cedula', 'id'],
        'NOMBRE': ['nombre', 'razon_social', 'contribuyente', 'cliente'],
        'DIRECCION': ['direccion', 'dir_notificacion', 'dir', 'address'],
        'TELEFONO': ['telefono', 'celular', 'phone', 'movil'],
        'EMAIL': ['email', 'correo', 'mail', 'e-mail'],
        'CIUDAD': ['ciudad', 'municipio', 'localidad'],
        'DEPARTAMENTO': ['departamento', 'estado', 'provincia'],
        'NUMERO_OBLIGACION': ['numero_obligacion', 'factura', 'obligacion', 'cuenta', 'referencia'],
        'VIGENCIA': ['vigencia', 'periodo', 'ano', 'año', 'year'],
        'VALOR_TOTAL': ['valor_total', 'valor', 'deuda', 'total', 'monto'],
        'CAPITAL': ['capital', 'valor_capital'],
        'INTERESES': ['intereses', 'valor_intereses'],
        'MORA': ['mora', 'valor_mora'],
        'FECHA_EMISION': ['fecha_emision', 'fecha_expedicion', 'emision'],
        'FECHA_VENCIMIENTO': ['fecha_vencimiento', 'vencimiento', 'fecha_limite']
    }
    
    suggested_mapping = {}
    
    for df_col in df_columns:
        normalized = normalize_column_name(df_col)
        
        for system_field, possible_names in system_fields.items():
            for possible_name in possible_names:
                if possible_name in normalized:
                    suggested_mapping[system_field] = df_col
                    break
    
    return suggested_mapping


async def process_import_file(
    file: UploadFile,
    column_mapping: Dict[str, str],
    tenant_id: int,
    user_id: int,
    save_template: bool = False,
    template_name: Optional[str] = None,
    session: Session = None
) -> Dict:
    """
    Procesar archivo de importación y crear clientes/obligaciones.
    
    Args:
        file: Archivo subido
        column_mapping: Diccionario con mapeo de columnas
        tenant_id: ID del tenant
        user_id: ID del usuario que importa
        save_template: Si guardar el mapeo como plantilla
        template_name: Nombre de la plantilla si se guarda
        session: Sesión de base de datos
    
    Returns:
        Dict con resultados de la importación
    """
    # Detectar tipo de archivo
    file_type = detect_file_type(file)
    
    # Leer archivo
    df = await read_file(file, file_type)
    
    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    
    # Validar columnas requeridas
    required_fields = ['IDENTIFICACION', 'NOMBRE', 'NUMERO_OBLIGACION', 'VALOR_TOTAL']
    missing_fields = []
    
    for field in required_fields:
        if field not in column_mapping or column_mapping[field] not in df.columns:
            missing_fields.append(field)
    
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Columnas requeridas faltantes: {', '.join(missing_fields)}"
        )
    
    # Guardar plantilla si se solicita
    if save_template and template_name:
        template = ImportTemplate(
            name=template_name,
            tenant_id=tenant_id,
            column_mapping=column_mapping,
            created_by=user_id,
            is_default=False,
            is_active=True
        )
        session.add(template)
        session.commit()
    
    # Procesar filas
    stats = {
        'total_rows': len(df),
        'clients_created': 0,
        'clients_updated': 0,
        'obligations_created': 0,
        'errors': []
    }
    
    clients_cache = {}  # Cache para evitar duplicados en memoria
    
    for index, row in df.iterrows():
        try:
            # Extraer datos del cliente
            identificacion = str(row[column_mapping['IDENTIFICACION']]).strip()
            nombre = str(row[column_mapping['NOMBRE']]).strip()
            
            # Verificar si cliente ya existe
            client = clients_cache.get(identificacion)
            if not client:
                statement = select(Client).where(
                    Client.identification == identificacion,
                    Client.tenant_id == tenant_id
                )
                client = session.exec(statement).first()
            
            if not client:
                # Crear nuevo cliente
                client_data = {
                    'identification': identificacion,
                    'name': nombre,
                    'tenant_id': tenant_id
                }
                
                # Campos opcionales
                optional_mappings = {
                    'address': 'DIRECCION',
                    'phone': 'TELEFONO',
                    'email': 'EMAIL',
                    'city': 'CIUDAD',
                    'department': 'DEPARTAMENTO'
                }
                
                for field, map_key in optional_mappings.items():
                    if map_key in column_mapping and column_mapping[map_key] in df.columns:
                        value = row[column_mapping[map_key]]
                        if pd.notna(value):
                            client_data[field] = str(value).strip()
                
                client = Client(**client_data)
                session.add(client)
                session.commit()
                session.refresh(client)
                stats['clients_created'] += 1
                clients_cache[identificacion] = client
            else:
                stats['clients_updated'] += 1
                clients_cache[identificacion] = client
            
            # Crear obligación
            numero_obligacion = str(row[column_mapping['NUMERO_OBLIGACION']]).strip()
            
            # Verificar si obligación ya existe
            statement = select(Obligation).where(
                Obligation.numero_obligacion == numero_obligacion,
                Obligation.tenant_id == tenant_id
            )
            existing_obligation = session.exec(statement).first()
            
            if not existing_obligation:
                obligation_data = {
                    'numero_obligacion': numero_obligacion,
                    'vigencia': str(row.get(column_mapping.get('VIGENCIA'), '2024')),
                    'valor_total': float(row[column_mapping['VALOR_TOTAL']]),
                    'client_id': client.id,
                    'tenant_id': tenant_id
                }
                
                # Campos opcionales de obligación
                if 'CAPITAL' in column_mapping and column_mapping['CAPITAL'] in df.columns:
                    val = row[column_mapping['CAPITAL']]
                    obligation_data['capital'] = float(val) if pd.notna(val) else 0
                
                if 'INTERESES' in column_mapping and column_mapping['INTERESES'] in df.columns:
                    val = row[column_mapping['INTERESES']]
                    obligation_data['intereses'] = float(val) if pd.notna(val) else 0
                
                if 'MORA' in column_mapping and column_mapping['MORA'] in df.columns:
                    val = row[column_mapping['MORA']]
                    obligation_data['mora'] = float(val) if pd.notna(val) else 0
                
                # Fechas
                if 'FECHA_EMISION' in column_mapping and column_mapping['FECHA_EMISION'] in df.columns:
                    val = row[column_mapping['FECHA_EMISION']]
                    if pd.notna(val):
                        try:
                            obligation_data['fecha_emision'] = pd.to_datetime(val)
                        except:
                            pass
                
                if 'FECHA_VENCIMIENTO' in column_mapping and column_mapping['FECHA_VENCIMIENTO'] in df.columns:
                    val = row[column_mapping['FECHA_VENCIMIENTO']]
                    if pd.notna(val):
                        try:
                            obligation_data['fecha_vencimiento'] = pd.to_datetime(val)
                        except:
                            pass
                
                obligation = Obligation(**obligation_data)
                session.add(obligation)
                session.commit()
                stats['obligations_created'] += 1
            
        except Exception as e:
            stats['errors'].append({
                'row': index + 1,
                'error': str(e)
            })
    
    return {
        'message': 'Importación completada',
        'stats': stats,
        'success': len(stats['errors']) == 0
    }


async def get_import_templates(tenant_id: int, session: Session) -> List[ImportTemplate]:
    """Obtener plantillas de importación de un tenant."""
    statement = select(ImportTemplate).where(
        ImportTemplate.tenant_id == tenant_id,
        ImportTemplate.is_active == True
    )
    templates = session.exec(statement).all()
    return templates


async def save_import_template(
    name: str,
    column_mapping: Dict[str, str],
    tenant_id: int,
    user_id: int,
    is_default: bool = False,
    session: Session = None
) -> ImportTemplate:
    """Guardar una nueva plantilla de importación."""
    # Si es default, desactivar las demás
    if is_default:
        statement = select(ImportTemplate).where(
            ImportTemplate.tenant_id == tenant_id,
            ImportTemplate.is_default == True
        )
        templates = session.exec(statement).all()
        for template in templates:
            template.is_default = False
            session.add(template)
    
    template = ImportTemplate(
        name=name,
        tenant_id=tenant_id,
        column_mapping=column_mapping,
        created_by=user_id,
        is_default=is_default,
        is_active=True
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return template
