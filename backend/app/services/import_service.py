"""
Servicio para importación de datos desde Excel/CSV.
Procesa archivos, mapea columnas y crea clientes y obligaciones.
"""

import io
from typing import Dict, List, Optional
from sqlmodel import Session, select
from fastapi import UploadFile, HTTPException
import pandas as pd
import re

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
        'IDENTIFICACION': ['identificacion', 'nit', 'cedula', 'id', 'documento'],
        'NOMBRE': ['nombre', 'razon_social', 'contribuyente', 'cliente', 'razon social'],
        'DIRECCION': ['direccion', 'dir_notificacion', 'dir', 'address', 'ubicacion'],
        'TELEFONO': ['telefono', 'celular', 'phone', 'movil', 'tel'],
        'EMAIL': ['email', 'correo', 'mail', 'e-mail', 'correo_electronico'],
        'CIUDAD': ['ciudad', 'municipio', 'localidad', 'town', 'city'],
        'DEPARTAMENTO': ['departamento', 'estado', 'provincia', 'state'],
        'NUMERO_OBLIGACION': ['numero_obligacion', 'factura', 'obligacion', 'cuenta', 'referencia', 'num obligacion'],
        'VIGENCIA': ['vigencia', 'periodo', 'ano', 'año', 'year', 'anio'],
        'VALOR_TOTAL': ['valor_total', 'valor', 'deuda', 'total', 'monto', 'importe'],
        'CAPITAL': ['capital', 'valor_capital', 'monto_capital'],
        'INTERESES': ['intereses', 'interes', 'valor_intereses', 'interes_corriente'],
        'MORA': ['mora', 'valor_mora', 'interes_mora', 'recargo'],
        'FECHA_EMISION': ['fecha_emision', 'fecha_expedicion', 'emision', 'fecha_inicio', 'inicio'],
        'FECHA_VENCIMIENTO': ['fecha_vencimiento', 'vencimiento', 'fecha_limite', 'fecha_fin', 'fin']
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


def convert_monetary_value(value) -> float:
    """
    Convierte un valor monetario a float, manejando diferentes formatos.
    Maneja casos como: '214.012', '214,012.50', '214.012,50', etc.
    """
    if pd.isna(value) or value == '' or value is None:
        return 0.0
    
    # Convertir a string si no lo es
    str_value = str(value).strip()
    
    # Si el valor ya es numérico, simplemente convertirlo
    try:
        return float(str_value)
    except ValueError:
        pass
    
    # Remover espacios en blanco
    str_value = str_value.replace(' ', '')
    
    # Caso 1: Formato con punto como separador de miles y coma como decimal (1.234,56)
    if ',' in str_value and '.' in str_value:
        # Determinar cuál es el separador decimal
        last_dot_pos = str_value.rfind('.')
        last_comma_pos = str_value.rfind(',')
        
        if last_comma_pos > last_dot_pos:
            # Coma es separador decimal
            str_value = str_value.replace('.', '')  # Remover puntos (separadores de miles)
            str_value = str_value.replace(',', '.')  # Reemplazar coma por punto decimal
        elif last_dot_pos > last_comma_pos:
            # Punto es separador decimal
            str_value = str_value.replace(',', '')  # Remover comas (separadores de miles)
    
    # Caso 2: Formato con solo comas (1,234.56 o 1234,56)
    elif ',' in str_value:
        # Si hay más de una aparición de coma o si hay punto después de la coma
        comma_count = str_value.count(',')
        if comma_count == 1:
            parts = str_value.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:  # Posible formato decimal
                # Suponer que es formato americano con coma como separador de miles
                str_value = str_value.replace(',', '')
    
    # Remover cualquier carácter no numérico excepto el punto decimal
    str_value = re.sub(r'[^\d.-]', '', str_value)
    
    try:
        return float(str_value)
    except ValueError:
        # Si todo falla, devolver 0.0
        return 0.0


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
    
    # Validar que los campos requeridos no tengan valores nulos
    for field in required_fields:
        if field in column_mapping:
            col_name = column_mapping[field]
            if df[col_name].isnull().any() or (df[col_name] == '').any():
                raise HTTPException(
                    status_code=400,
                    detail=f"La columna '{col_name}' (mapeada a '{field}') contiene valores vacíos o nulos"
                )
    
    # Validar que VALOR_TOTAL sea numérico
    if 'VALOR_TOTAL' in column_mapping:
        total_col = column_mapping['VALOR_TOTAL']
        # Validar valores monetarios
        for idx, value in enumerate(df[total_col]):
            try:
                converted_val = convert_monetary_value(value)
                if pd.isna(converted_val):
                    raise ValueError(f"Valor no convertible: {value}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Fila {idx + 2}: La columna '{total_col}' (mapeada a 'VALOR_TOTAL') contiene un valor no convertible: '{value}'"
                )
    
    # Validar fechas si están presentes
    date_fields = ['FECHA_EMISION', 'FECHA_VENCIMIENTO']
    for field in date_fields:
        if field in column_mapping:
            date_col = column_mapping[field]
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='raise')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"La columna '{date_col}' (mapeada a '{field}') contiene fechas con formato inválido"
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
                
                # Si no se especificó departamento, usar un valor por defecto
                if 'department' not in client_data:
                    client_data['department'] = 'Santander'  # Por defecto para Girón
                
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
                # Convertir valor total usando la función de conversión mejorada
                valor_total_raw = row[column_mapping['VALOR_TOTAL']]
                valor_total = convert_monetary_value(valor_total_raw)
                
                obligation_data = {
                    'numero_obligacion': numero_obligacion,
                    'vigencia': str(row.get(column_mapping.get('VIGENCIA'), '2026')),  # Valor por defecto para Girón
                    'valor_total': valor_total,
                    'client_id': client.id,
                    'tenant_id': tenant_id
                }
                
                # Campos opcionales de obligación
                if 'CAPITAL' in column_mapping and column_mapping['CAPITAL'] in df.columns:
                    val = row[column_mapping['CAPITAL']]
                    obligation_data['capital'] = convert_monetary_value(val) if pd.notna(val) else 0
                
                if 'INTERESES' in column_mapping and column_mapping['INTERESES'] in df.columns:
                    val = row[column_mapping['INTERESES']]
                    obligation_data['intereses'] = convert_monetary_value(val) if pd.notna(val) else 0
                
                if 'MORA' in column_mapping and column_mapping['MORA'] in df.columns:
                    val = row[column_mapping['MORA']]
                    obligation_data['mora'] = convert_monetary_value(val) if pd.notna(val) else 0
                
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


def get_template_preview(template: ImportTemplate) -> Dict:
    """Obtener una vista previa de la plantilla de importación."""
    return {
        'id': template.id,
        'name': template.name,
        'description': template.description,
        'is_default': template.is_default,
        'is_active': template.is_active,
        'column_mapping': template.column_mapping,
        'created_at': template.created_at,
        'updated_at': template.updated_at,
        'mapped_columns_count': len(template.column_mapping) if template.column_mapping else 0,
        'mapped_columns': list(template.column_mapping.keys()) if template.column_mapping else [],
        'mapped_system_fields': list(template.column_mapping.values()) if template.column_mapping else []
    }


def validate_import_file_content(df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict:
    """
    Valida el contenido del archivo de importación antes de procesarlo.
    
    Args:
        df: DataFrame con los datos del archivo
        column_mapping: Diccionario con el mapeo de columnas
        
    Returns:
        Dict con resultados de la validación
    """
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'summary': {
            'total_rows': len(df),
            'columns_count': len(df.columns),
            'mapped_columns_count': len(column_mapping)
        }
    }
    
    # Validar campos requeridos
    required_fields = ['IDENTIFICACION', 'NOMBRE', 'NUMERO_OBLIGACION', 'VALOR_TOTAL']
    
    for field in required_fields:
        if field not in column_mapping:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Campo requerido '{field}' no está mapeado")
        else:
            col_name = column_mapping[field]
            if col_name not in df.columns:
                validation_results['valid'] = False
                validation_results['errors'].append(f"La columna '{col_name}' (mapeada a '{field}') no existe en el archivo")
            else:
                # Verificar si hay valores nulos o vacíos en campos requeridos
                null_count = df[col_name].isnull().sum()
                empty_count = (df[col_name] == '').sum()
                
                if null_count > 0 or empty_count > 0:
                    validation_results['valid'] = False
                    validation_results['errors'].append(
                        f"La columna '{col_name}' (mapeada a '{field}') tiene {null_count} valores nulos y {empty_count} valores vacíos"
                    )
    
    # Validar tipos de datos
    if 'VALOR_TOTAL' in column_mapping:
        col_name = column_mapping['VALOR_TOTAL']
        # Validar cada valor individualmente usando la función convert_monetary_value
        for idx, value in enumerate(df[col_name]):
            try:
                converted_val = convert_monetary_value(value)
                if pd.isna(converted_val):
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Fila {idx + 2}: Valor no convertible en '{col_name}' (mapeada a 'VALOR_TOTAL'): '{value}'")
            except Exception:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Fila {idx + 2}: Error al convertir valor en '{col_name}' (mapeada a 'VALOR_TOTAL'): '{value}'")
    
    # Validar fechas si están presentes
    date_fields = ['FECHA_EMISION', 'FECHA_VENCIMIENTO']
    for field in date_fields:
        if field in column_mapping:
            col_name = column_mapping[field]
            invalid_dates = df[pd.to_datetime(df[col_name], errors='coerce').isna()].shape[0]
            if invalid_dates > 0:
                validation_results['warnings'].append(f"La columna '{col_name}' (mapeada a '{field}') tiene {invalid_dates} fechas inválidas")
    
    # Validar duplicados
    if 'IDENTIFICACION' in column_mapping and 'NUMERO_OBLIGACION' in column_mapping:
        id_col = column_mapping['IDENTIFICACION']
        obl_col = column_mapping['NUMERO_OBLIGACION']
        
        # Verificar duplicados de identificación
        duplicated_ids = df[df.duplicated(subset=[id_col], keep=False)][id_col].unique()
        if len(duplicated_ids) > 0:
            validation_results['warnings'].append(f"Se encontraron {len(duplicated_ids)} identificaciones duplicadas: {list(duplicated_ids[:5])}")  # Mostrar máximo 5
        
        # Verificar duplicados de obligación
        duplicated_obls = df[df.duplicated(subset=[obl_col], keep=False)][obl_col].unique()
        if len(duplicated_obls) > 0:
            validation_results['warnings'].append(f"Se encontraron {len(duplicated_obls)} números de obligación duplicados: {list(duplicated_obls[:5])}")  # Mostrar máximo 5
    
    return validation_results