"""Utilidades para el sistema de logging estructurado"""
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime


def sanitize_sensitive_data(data: Dict[str, Any], fields_to_mask: Optional[list] = None) -> Dict[str, Any]:
    """
    Sanitiza datos sensibles antes de registrarlos.
    
    Args:
        data: Diccionario con datos a sanitizar
        fields_to_mask: Lista de campos que deben ser enmascarados
    
    Returns:
        Diccionario con datos sensibles enmascarados
    """
    if fields_to_mask is None:
        fields_to_mask = ["password", "secret", "token", "key", "authorization", "auth"]
    
    sanitized_data = {}
    
    for key, value in data.items():
        if key.lower() in fields_to_mask:
            # Enmascara el valor con asteriscos o hash
            if isinstance(value, str) and len(value) > 4:
                sanitized_data[key] = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
            else:
                sanitized_data[key] = "***"
        elif isinstance(value, dict):
            # Recursivamente sanitizar diccionarios anidados
            sanitized_data[key] = sanitize_sensitive_data(value, fields_to_mask)
        elif isinstance(value, list):
            # Sanitizar listas que contienen diccionarios
            sanitized_value = []
            for item in value:
                if isinstance(item, dict):
                    sanitized_value.append(sanitize_sensitive_data(item, fields_to_mask))
                else:
                    sanitized_value.append(item)
            sanitized_data[key] = sanitized_value
        else:
            sanitized_data[key] = value
    
    return sanitized_data


def create_correlation_id(request_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Crea un ID de correlación único para seguir una solicitud a través del sistema.
    
    Args:
        request_data: Opcionalmente, datos de la solicitud para generar un ID más específico
    
    Returns:
        ID de correlación único
    """
    if request_data:
        # Crear un hash basado en los datos de la solicitud
        data_str = json.dumps(request_data, sort_keys=True, default=str)
        hash_obj = hashlib.sha256(data_str.encode())
        return hash_obj.hexdigest()[:16]  # Tomar solo los primeros 16 caracteres
    else:
        # Generar un ID aleatorio
        import uuid
        return str(uuid.uuid4()).replace("-", "")[:16]


def format_log_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Formatea un timestamp para el log.
    
    Args:
        timestamp: Objeto datetime a formatear (usa el actual si es None)
    
    Returns:
        Timestamp en formato ISO 8601
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    return timestamp.isoformat()


def extract_user_info_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extrae información del usuario desde un token JWT.
    
    Args:
        token: Token JWT codificado
    
    Returns:
        Información del usuario o None si no se puede decodificar
    """
    try:
        import jwt
        from app.core.config import settings
        
        # Decodificar el token sin verificar firma (solo para extracción de info)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Extraer información común del payload
        user_info = {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        
        return {k: v for k, v in user_info.items() if v is not None}
    except Exception:
        # Si no se puede decodificar, retornar None
        return None


def log_exception_details(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extrae detalles detallados de una excepción para logging.
    
    Args:
        exception: Excepción a analizar
        context: Contexto adicional para el log
    
    Returns:
        Diccionario con detalles de la excepción
    """
    import traceback
    
    exception_details = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "traceback": traceback.format_exc(),
        "context": context or {}
    }
    
    # Si la excepción tiene atributos específicos, incluirlos
    if hasattr(exception, '__cause__') and exception.__cause__:
        exception_details["cause"] = str(exception.__cause__)
    
    if hasattr(exception, 'args') and len(exception.args) > 1:
        exception_details["additional_args"] = exception.args[1:]
    
    return exception_details


def get_client_ip(request) -> Optional[str]:
    """
    Extrae la IP del cliente desde la solicitud.
    
    Args:
        request: Objeto de solicitud FastAPI
    
    Returns:
        IP del cliente o None si no se puede determinar
    """
    # Intentar obtener la IP desde diferentes cabeceras
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # La primera IP en X-Forwarded-For es la original
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Usar la IP directa del cliente si está disponible
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return None


def mask_sensitive_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Enmascara cabeceras sensibles.
    
    Args:
        headers: Diccionario de cabeceras HTTP
    
    Returns:
        Cabeceras con valores sensibles enmascarados
    """
    sensitive_headers = [
        "authorization", "x-api-key", "x-auth-token", "cookie",
        "set-cookie", "proxy-authorization", "www-authenticate"
    ]
    
    masked_headers = {}
    for key, value in headers.items():
        if key.lower() in sensitive_headers:
            # Enmascarar el valor
            if len(value) > 8:
                masked_headers[key] = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
            else:
                masked_headers[key] = "***"
        else:
            masked_headers[key] = value
    
    return masked_headers