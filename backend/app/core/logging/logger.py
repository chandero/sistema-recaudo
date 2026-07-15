import json
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from app.core.config import settings


class LogLevel(str, Enum):
    """Niveles de log disponibles"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEvent(BaseModel):
    """Modelo para eventos de log estructurados"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: LogLevel
    service: str
    module: str
    action: str
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    error_code: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


class StructuredLogger:
    """Logger estructurado para el sistema de recaudo"""
    
    def __init__(self, service_name: str = "sistema-recaudo"):
        self.service_name = service_name
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura el logger con formato estructurado"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.DEBUG)
        
        # Evitar duplicados si ya está configurado
        if logger.handlers:
            return logger
            
        # Formateador JSON
        formatter = JsonFormatter()
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo si está habilitado
        if settings.LOG_TO_FILE:
            log_dir = Path(settings.LOG_FILE_PATH).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _log(self, level: LogLevel, module: str, action: str, message: str, 
             user_id: Optional[int] = None, request_id: Optional[str] = None,
             correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
             error_code: Optional[str] = None, source_ip: Optional[str] = None,
             user_agent: Optional[str] = None, trace_id: Optional[str] = None,
             span_id: Optional[str] = None):
        """Método privado para registrar eventos de log"""
        log_event = LogEvent(
            level=level,
            service=self.service_name,
            module=module,
            action=action,
            message=message,
            user_id=user_id,
            request_id=request_id,
            correlation_id=correlation_id,
            data=data or {},
            error_code=error_code,
            source_ip=source_ip,
            user_agent=user_agent,
            trace_id=trace_id,
            span_id=span_id
        )
        
        # Registrar el evento
        if level == LogLevel.DEBUG:
            self.logger.debug(log_event.model_dump_json())
        elif level == LogLevel.INFO:
            self.logger.info(log_event.model_dump_json())
        elif level == LogLevel.WARNING:
            self.logger.warning(log_event.model_dump_json())
        elif level == LogLevel.ERROR:
            self.logger.error(log_event.model_dump_json())
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_event.model_dump_json())
    
    def debug(self, module: str, action: str, message: str, 
              user_id: Optional[int] = None, request_id: Optional[str] = None,
              correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
              source_ip: Optional[str] = None, user_agent: Optional[str] = None,
              trace_id: Optional[str] = None, span_id: Optional[str] = None):
        """Registra un evento de nivel DEBUG"""
        self._log(LogLevel.DEBUG, module, action, message, user_id, request_id,
                  correlation_id, data, None, source_ip, user_agent, trace_id, span_id)
    
    def info(self, module: str, action: str, message: str, 
             user_id: Optional[int] = None, request_id: Optional[str] = None,
             correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
             source_ip: Optional[str] = None, user_agent: Optional[str] = None,
             trace_id: Optional[str] = None, span_id: Optional[str] = None):
        """Registra un evento de nivel INFO"""
        self._log(LogLevel.INFO, module, action, message, user_id, request_id,
                  correlation_id, data, None, source_ip, user_agent, trace_id, span_id)
    
    def warning(self, module: str, action: str, message: str, 
                user_id: Optional[int] = None, request_id: Optional[str] = None,
                correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
                error_code: Optional[str] = None, source_ip: Optional[str] = None,
                user_agent: Optional[str] = None, trace_id: Optional[str] = None,
                span_id: Optional[str] = None):
        """Registra un evento de nivel WARNING"""
        self._log(LogLevel.WARNING, module, action, message, user_id, request_id,
                  correlation_id, data, error_code, source_ip, user_agent, trace_id, span_id)
    
    def error(self, module: str, action: str, message: str, 
              user_id: Optional[int] = None, request_id: Optional[str] = None,
              correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
              error_code: Optional[str] = None, source_ip: Optional[str] = None,
              user_agent: Optional[str] = None, trace_id: Optional[str] = None,
              span_id: Optional[str] = None):
        """Registra un evento de nivel ERROR"""
        self._log(LogLevel.ERROR, module, action, message, user_id, request_id,
                  correlation_id, data, error_code, source_ip, user_agent, trace_id, span_id)
    
    def critical(self, module: str, action: str, message: str, 
                 user_id: Optional[int] = None, request_id: Optional[str] = None,
                 correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None,
                 error_code: Optional[str] = None, source_ip: Optional[str] = None,
                 user_agent: Optional[str] = None, trace_id: Optional[str] = None,
                 span_id: Optional[str] = None):
        """Registra un evento de nivel CRITICAL"""
        self._log(LogLevel.CRITICAL, module, action, message, user_id, request_id,
                  correlation_id, data, error_code, source_ip, user_agent, trace_id, span_id)


class JsonFormatter(logging.Formatter):
    """Formateador de logs en formato JSON"""
    
    def format(self, record):
        """Formatea el registro como JSON"""
        # Parsear el mensaje si es JSON válido
        try:
            log_data = json.loads(record.getMessage())
            if isinstance(log_data, dict):
                return json.dumps(log_data)
        except json.JSONDecodeError:
            pass
        
        # Si no es JSON, crear un objeto de log estándar
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'module'):
            log_entry['module'] = record.module
        if hasattr(record, 'funcName'):
            log_entry['function'] = record.funcName
        if hasattr(record, 'lineno'):
            log_entry['line'] = record.lineno
        
        return json.dumps(log_entry)


# Instancia global del logger
logger_instance = StructuredLogger()


def get_logger(module_name: str) -> StructuredLogger:
    """Obtiene una instancia del logger estructurado"""
    return StructuredLogger(service_name=f"sistema-recaudo.{module_name}")


def log_api_request(request, endpoint: str, method: str, user_id: Optional[int] = None):
    """Registra una solicitud API"""
    from uuid import uuid4
    
    request_id = str(uuid4())
    logger_instance.info(
        module="api",
        action="request_received",
        message=f"Solicitud {method} recibida para {endpoint}",
        user_id=user_id,
        request_id=request_id,
        data={
            "method": method,
            "endpoint": endpoint,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        },
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return request_id


def log_api_response(request_id: str, status_code: int, response_time: float):
    """Registra una respuesta API"""
    logger_instance.info(
        module="api",
        action="response_sent",
        message=f"Respuesta enviada con código {status_code}",
        request_id=request_id,
        data={
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2)
        }
    )


def log_database_operation(operation: str, table: str, user_id: Optional[int] = None, 
                          record_id: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
    """Registra una operación de base de datos"""
    logger_instance.info(
        module="database",
        action=operation,
        message=f"Operación {operation} en tabla {table}",
        user_id=user_id,
        data={
            "table": table,
            "record_id": record_id,
            **(data or {})
        }
    )


def log_authentication_event(event: str, username: str, success: bool, 
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """Registra un evento de autenticación"""
    logger_instance.info(
        module="authentication",
        action=event,
        message=f"Evento de autenticación: {event} para usuario {username}",
        data={
            "username": username,
            "success": success
        },
        source_ip=ip_address,
        user_agent=user_agent
    )


def log_error_occurred(error: Exception, module: str, action: str, 
                      user_id: Optional[int] = None, request_id: Optional[str] = None,
                      error_code: Optional[str] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Registra la ocurrencia de un error"""
    logger_instance.error(
        module=module,
        action=action,
        message=str(error),
        user_id=user_id,
        request_id=request_id,
        error_code=error_code,
        data={
            "error_type": type(error).__name__,
            "error_traceback": str(error.__traceback__) if error.__traceback__ else None,
            **(additional_data or {})
        }
    )