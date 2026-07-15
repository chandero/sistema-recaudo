"""Módulo de protección de endpoints para el sistema de recaudo."""
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security.auth import auth_security, TokenData
from app.core.security.attack_protection import attack_protection
from app.core.security.validation import SecurityValidator
from app.core.security.input_sanitizer import input_sanitizer
from app.core.security.token_validation import token_validator
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


security = HTTPBearer()


class EndpointProtector:
    """Clase para proteger endpoints con diversas medidas de seguridad."""
    
    def __init__(self):
        self.security_validator = SecurityValidator()
        self.input_sanitizer = input_sanitizer
        self.token_validator = token_validator
    
    def protect_endpoint(
        self, 
        required_permissions: Optional[list] = None,
        validate_inputs: bool = True,
        check_rate_limit: bool = True,
        validate_request_size: bool = True
    ):
        """Decorador para proteger endpoints."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Obtener la solicitud si está presente
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                # Verificar límite de tasa
                if check_rate_limit and request and not attack_protection.check_rate_limit(request):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Demasiadas solicitudes"
                    )
                
                # Verificar tamaño de solicitud
                if validate_request_size and request and not attack_protection.check_request_size(request):
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Solicitud demasiado grande"
                    )
                
                # Validar y sanear entradas
                if validate_inputs:
                    # Sanear argumentos de entrada
                    for key, value in kwargs.items():
                        if isinstance(value, str):
                            kwargs[key] = self.input_sanitizer.sanitize_string(value)
                        elif isinstance(value, dict):
                            kwargs[key] = self.input_sanitizer.deep_sanitize(value)
                
                # Ejecutar la función original
                result = await func(*args, **kwargs) if func.__name__.startswith('async') else func(*args, **kwargs)
                
                return result
            return wrapper
        return decorator
    
    def require_authentication(self):
        """Requiere autenticación para acceder al endpoint."""
        async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
            token = credentials.credentials
            
            # Verificar si el token ha sido revocado
            if auth_security.is_token_revoked(token):
                logger.warning(
                    module="endpoint_protection",
                    action="token_revoked_access_attempt",
                    message="Intento de acceso con token revocado",
                    data={"token_revoked": True}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token ha sido revocado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = auth_security.decode_token(token)
            if token_data is None:
                logger.warning(
                    module="endpoint_protection",
                    action="invalid_token_access_attempt",
                    message="Intento de acceso con token inválido",
                    data={"token_valid": False}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudo validar las credenciales",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info(
                module="endpoint_protection",
                action="user_authenticated",
                message="Usuario autenticado exitosamente",
                user_id=token_data.user_id,
                data={"username": token_data.username, "role": token_data.role}
            )
            return token_data
        
        return get_current_user
    
    def require_permission(self, permission: str):
        """Requiere un permiso específico para acceder al endpoint."""
        def permission_checker(current_user: TokenData = Depends(self.require_authentication())):
            # En una implementación real, esto verificaría permisos específicos
            # Por ahora, simplemente verificamos el rol
            if permission == "admin" and current_user.role != "admin":
                logger.warning(
                    module="endpoint_protection",
                    action="insufficient_permissions",
                    message=f"Usuario {current_user.username} no tiene permiso {permission}",
                    user_id=current_user.user_id,
                    data={"user_role": current_user.role, "required_permission": permission}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos suficientes"
                )
            
            logger.info(
                module="endpoint_protection",
                action="permission_granted",
                message=f"Permiso {permission} concedido a usuario {current_user.username}",
                user_id=current_user.user_id,
                data={"username": current_user.username, "permission": permission}
            )
            return current_user
        return permission_checker
    
    def validate_input_data(self, data: Any):
        """Valida datos de entrada para proteger contra ataques."""
        validation_result = attack_protection.validate_input_data(data)
        
        if not validation_result["is_valid"]:
            logger.warning(
                module="endpoint_protection",
                action="input_validation_failed",
                message="Datos de entrada no válidos",
                data={"detected_attacks": validation_result["detected_attacks"]}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datos de entrada inválidos: {', '.join(validation_result['detected_attacks'])}"
            )
        
        return validation_result["sanitized_data"]
    
    def validate_file_upload(self, filename: str, file_size: int, allowed_extensions: list):
        """Valida subida de archivos."""
        # Validar tipo de archivo
        if not self.security_validator.validate_file_type(filename, allowed_extensions):
            logger.warning(
                module="endpoint_protection",
                action="invalid_file_type",
                message=f"Tipo de archivo no permitido: {filename}",
                data={"filename": filename, "allowed_extensions": allowed_extensions}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo no permitido"
            )
        
        # Validar tamaño de archivo
        max_size = 10 * 1024 * 1024  # 10MB
        if not self.security_validator.validate_file_size(file_size, max_size):
            logger.warning(
                module="endpoint_protection",
                action="file_too_large",
                message=f"Archivo demasiado grande: {file_size} bytes",
                data={"file_size": file_size, "max_size": max_size}
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Archivo demasiado grande"
            )
        
        logger.info(
            module="endpoint_protection",
            action="file_upload_validated",
            message="Archivo subido validado exitosamente",
            data={"filename": filename, "file_size": file_size}
        )
    
    def prevent_sql_injection(self, input_str: str):
        """Prevención de inyección SQL."""
        if not self.security_validator.validate_sql_injection_risk(input_str):
            logger.warning(
                module="endpoint_protection",
                action="sql_injection_attempt",
                message="Detectado posible intento de inyección SQL",
                data={"input_snippet": input_str[:50]}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solicitud contiene posibles intentos de inyección SQL"
            )
    
    def prevent_xss_attack(self, input_str: str):
        """Prevención de ataques XSS."""
        if not self.security_validator.validate_xss_risk(input_str):
            logger.warning(
                module="endpoint_protection",
                action="xss_attack_attempt",
                message="Detectado posible intento de XSS",
                data={"input_snippet": input_str[:50]}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solicitud contiene posibles intentos de XSS"
            )


# Importar aquí para evitar importaciones circulares
def validate_xss_risk(input_str: str) -> bool:
    """Función auxiliar para validar riesgo XSS."""
    # Patrones comunes de XSS
    xss_patterns = [
        r"(?i)<script[^>]*>",
        r"(?i)</script>",
        r"(?i)<iframe[^>]*>",
        r"(?i)<object[^>]*>",
        r"(?i)<embed[^>]*>",
        r"(?i)<form[^>]*>",
        r"(?i)javascript:",
        r"(?i)vbscript:",
        r"(?i)on\w+\s*=",
        r"(?i)data:text/html",
    ]
    
    for pattern in xss_patterns:
        if input_str and re.search(pattern, input_str, re.IGNORECASE):
            return False
    
    return True


# Agregar la función al validador de seguridad
SecurityValidator.validate_xss_risk = staticmethod(validate_xss_risk)


# Instancia global del protector de endpoints
endpoint_protector = EndpointProtector()