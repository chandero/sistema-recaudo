"""Configuración del sistema de logging estructurado"""
import os
from enum import Enum
from typing import Optional


class LogFormat(str, Enum):
    """Formatos de log disponibles"""
    JSON = "json"
    TEXT = "text"


class LoggingConfig:
    """Clase de configuración para el sistema de logging"""
    
    def __init__(self):
        # Habilitar logging a archivo
        self.LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
        
        # Ruta del archivo de log
        self.LOG_FILE_PATH: str = os.getenv(
            "LOG_FILE_PATH", 
            "/app/logs/sistema_recaudo.log"
        )
        
        # Nivel mínimo de log
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Formato de log
        self.LOG_FORMAT: LogFormat = LogFormat(os.getenv("LOG_FORMAT", "json"))
        
        # Tamaño máximo del archivo de log (en MB)
        self.LOG_MAX_SIZE_MB: int = int(os.getenv("LOG_MAX_SIZE_MB", "100"))
        
        # Número de archivos de log rotados a mantener
        self.LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Habilitar logging de auditoría
        self.AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
        
        # Habilitar logging de solicitudes API
        self.API_LOG_ENABLED: bool = os.getenv("API_LOG_ENABLED", "true").lower() == "true"
        
        # Habilitar logging de operaciones de base de datos
        self.DB_LOG_ENABLED: bool = os.getenv("DB_LOG_ENABLED", "true").lower() == "true"
        
        # Habilitar logging de autenticación
        self.AUTH_LOG_ENABLED: bool = os.getenv("AUTH_LOG_ENABLED", "true").lower() == "true"


# Instancia global de la configuración
logging_config = LoggingConfig()