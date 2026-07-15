"""Middleware de seguridad HTTP para el sistema de recaudo."""
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.logging.logger import get_logger


class HttpSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para añadir cabeceras de seguridad HTTP."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("http_security")
    
    async def dispatch(self, request: Request, call_next):
        """Añade cabeceras de seguridad a las respuestas."""
        response: Response = await call_next(request)
        
        # Cabeceras de seguridad básicas
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.example.com; "
            "frame-ancestors 'none';"
        )
        
        # Prevenir MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Registrar acceso para propósitos de auditoría
        self.logger.info(
            module="http_security",
            action="request_processed",
            message="Solicitud procesada con cabeceras de seguridad",
            data={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code
            }
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para limitación de tasa."""
    
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window  # en segundos
        self.requests = {}  # Diccionario simple para almacenar conteos (usar Redis en producción)
        self.logger = get_logger("rate_limit")
    
    async def dispatch(self, request: Request, call_next):
        """Controla el número de solicitudes por IP."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Obtener marca de tiempo actual
        current_time = int(request.scope.get("start_time", 0)) or int(__import__('time').time())
        
        # Limpiar solicitudes antiguas
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if current_time - req_time < self.window
            ]
        else:
            self.requests[client_ip] = []
        
        # Añadir solicitud actual
        self.requests[client_ip].append(current_time)
        
        # Verificar límite
        if len(self.requests[client_ip]) > self.max_requests:
            self.logger.warning(
                module="rate_limit",
                action="rate_limit_exceeded",
                message=f"Límite de tasa excedido para IP {client_ip}",
                data={
                    "client_ip": client_ip,
                    "requests_count": len(self.requests[client_ip]),
                    "max_requests": self.max_requests
                }
            )
            return Response(
                content="Demasiadas solicitudes", 
                status_code=429,
                headers={"Retry-After": str(self.window)}
            )
        
        response = await call_next(request)
        return response