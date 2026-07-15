"""Middleware para logging de solicitudes API"""
import time
import uuid
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging.logger import log_api_request, log_api_response, get_logger
from app.core.logging.config import logging_config


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para registrar solicitudes y respuestas API"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("middleware")
    
    async def dispatch(self, request: Request, call_next):
        """Procesa la solicitud y registra información relevante"""
        if not logging_config.API_LOG_ENABLED:
            return await call_next(request)
        
        # Generar IDs únicos para la solicitud
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extraer información del usuario si está autenticado
        user_id = self._extract_user_id(request)
        
        # Registrar la solicitud entrante
        log_api_request(request, request.url.path, request.method, user_id)
        
        try:
            # Procesar la solicitud
            response: Response = await call_next(request)
            
            # Calcular tiempo de respuesta
            response_time = time.time() - start_time
            
            # Registrar la respuesta saliente
            log_api_response(request_id, response.status_code, response_time)
            
            # Agregar el ID de solicitud a la respuesta para seguimiento
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calcular tiempo de respuesta en caso de error
            response_time = time.time() - start_time
            
            # Registrar error en la solicitud
            self.logger.error(
                module="api",
                action="request_error",
                message=f"Error procesando solicitud: {str(e)}",
                user_id=user_id,
                request_id=request_id,
                data={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "response_time_ms": round(response_time * 1000, 2)
                }
            )
            
            # Agregar el ID de solicitud a la respuesta de error
            response = Response(
                content=f"Internal Server Error: {str(e)}",
                status_code=500,
                headers={"X-Request-ID": request_id}
            )
            
            return response
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extrae el ID de usuario de la solicitud si está disponible"""
        # En una implementación real, esto podría extraer el ID del usuario
        # desde el token JWT o de la sesión
        try:
            # Intentar obtener el ID del usuario desde el token JWT
            # (esto dependerá de cómo esté implementada la autenticación)
            token = request.headers.get("authorization", "").replace("Bearer ", "")
            if token:
                # Aquí iría la lógica para decodificar el token y obtener el user_id
                # Por ahora, retornamos None
                pass
        except Exception:
            pass
        
        return None


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de auditoría de operaciones sensibles"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("audit")
        
        # Operaciones que deben registrarse en el log de auditoría
        self.audit_operations = {
            "POST": ["/api/v1/auth/login", "/api/v1/auth/logout"],
            "PUT": ["/api/v1/users/", "/api/v1/clients/", "/api/v1/documents/"],
            "DELETE": ["/api/v1/users/", "/api/v1/clients/", "/api/v1/documents/"],
            "PATCH": ["/api/v1/users/", "/api/v1/clients/", "/api/v1/documents/"]
        }
    
    async def dispatch(self, request: Request, call_next):
        """Procesa la solicitud y registra operaciones de auditoría si es necesario"""
        if not logging_config.AUDIT_LOG_ENABLED:
            return await call_next(request)
        
        should_audit = self._should_audit_request(request)
        
        if should_audit:
            # Extraer información del usuario
            user_id = self._extract_user_id(request)
            
            # Registrar operación de auditoría antes de procesar
            self.logger.info(
                module="audit",
                action="operation_requested",
                message=f"Operación sensible solicitada: {request.method} {request.url.path}",
                user_id=user_id,
                data={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params)
                },
                source_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        
        response = await call_next(request)
        
        if should_audit:
            # Registrar resultado de la operación de auditoría
            user_id = self._extract_user_id(request)
            
            self.logger.info(
                module="audit",
                action="operation_completed",
                message=f"Operación sensible completada: {request.method} {request.url.path}",
                user_id=user_id,
                data={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": response.status_code
                }
            )
        
        return response
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determina si la solicitud debe registrarse en el log de auditoría"""
        path = request.url.path
        method = request.method.upper()
        
        # Verificar si la operación está en la lista de operaciones de auditoría
        if method in self.audit_operations:
            for audit_path in self.audit_operations[method]:
                if path.startswith(audit_path):
                    return True
        
        return False
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extrae el ID de usuario de la solicitud si está disponible"""
        # Misma lógica que en LoggingMiddleware
        try:
            token = request.headers.get("authorization", "").replace("Bearer ", "")
            if token:
                # Decodificar token y obtener user_id
                pass
        except Exception:
            pass
        
        return None