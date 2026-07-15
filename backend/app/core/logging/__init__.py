"""Paquete de logging estructurado para el sistema de recaudo"""

import logging

from .logger import (
    StructuredLogger, 
    get_logger, 
    log_api_request, 
    log_api_response, 
    log_database_operation,
    log_authentication_event,
    log_error_occurred
)
from .config import logging_config
from .middleware import LoggingMiddleware, AuditLoggingMiddleware
from .utils import (
    sanitize_sensitive_data,
    create_correlation_id,
    format_log_timestamp,
    extract_user_info_from_token,
    log_exception_details,
    get_client_ip,
    mask_sensitive_headers
)

logger = logging.getLogger("sistema-recaudo")

__all__ = [
    # Logger
    "StructuredLogger",
    "get_logger",
    "log_api_request",
    "log_api_response",
    "log_database_operation",
    "log_authentication_event",
    "log_error_occurred",
    "logger",
    
    # Configuración
    "logging_config",
    
    # Middleware
    "LoggingMiddleware",
    "AuditLoggingMiddleware",
    
    # Utilidades
    "sanitize_sensitive_data",
    "create_correlation_id",
    "format_log_timestamp",
    "extract_user_info_from_token",
    "log_exception_details",
    "get_client_ip",
    "mask_sensitive_headers"
]