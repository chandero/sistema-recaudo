from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Configuración de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Configuración de JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Configuración de la aplicación
    APP_NAME: str = os.getenv("APP_NAME", "Sistema de Recaudo")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Configuración del entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Configuración de CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]
    CORS_ORIGINS: list = BACKEND_CORS_ORIGINS
    
    # Configuración de logging
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/app/logs/sistema_recaudo.log")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json o text
    LOG_MAX_SIZE_MB: int = int(os.getenv("LOG_MAX_SIZE_MB", "100"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Configuración de auditoría
    AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    API_LOG_ENABLED: bool = os.getenv("API_LOG_ENABLED", "true").lower() == "true"
    DB_LOG_ENABLED: bool = os.getenv("DB_LOG_ENABLED", "true").lower() == "true"
    AUTH_LOG_ENABLED: bool = os.getenv("AUTH_LOG_ENABLED", "true").lower() == "true"
    
    # Configuración de servicios externos
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    USER_INVITATION_EXPIRE_HOURS: int = int(os.getenv("USER_INVITATION_EXPIRE_HOURS", "24"))
    
    # Configuración de almacenamiento de archivos
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16000000"))  # 16MB
    ALLOWED_EXTENSIONS: set = {"xlsx", "xls", "csv", "pdf", "docx", "doc", "jpg", "jpeg", "png"}
    
    # Configuración de seguridad
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL_CHARS", "true").lower() == "true"
    PASSWORD_REQUIRE_NUMBERS: bool = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
    PASSWORD_REQUIRE_UPPERCASE: bool = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"


settings = Settings()
