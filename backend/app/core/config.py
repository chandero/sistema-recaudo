from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

# Valor de desarrollo histórico: nunca aceptable en un entorno expuesto.
SQLITE_URL_POR_DEFECTO = "sqlite:///./test.db"
CLAVES_NO_SEGURAS = {
    "your-secret-key-here",
    "supersecretkeychangeinproduction1234567890",
    "cambiar_en_produccion",
    "secret",
    "changeme",
}


def _origenes_perm():
    """Orígenes CORS: los locales de siempre más los que aporte BACKEND_CORS_ORIGINS."""
    base = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]
    extras = [o.strip() for o in os.getenv("BACKEND_CORS_ORIGINS", "").split(",") if o.strip()]
    frontend = os.getenv("FRONTEND_URL", "").strip()
    if frontend:
        extras.append(frontend.rstrip("/"))
    return list(dict.fromkeys(base + extras))


class Settings(BaseSettings):
    # Configuración de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", SQLITE_URL_POR_DEFECTO)
    
    # Configuración de JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    
    # Configuración de la aplicación
    APP_NAME: str = os.getenv("APP_NAME", "Sistema de Recaudo")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Configuración del entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    
    # Superficie expuesta del API: documentación y semilla de datos de prueba
    EXPOSE_API_DOCS: bool = os.getenv(
        "EXPOSE_API_DOCS", "true" if ENVIRONMENT == "development" else "false"
    ).lower() == "true"
    SEED_DEMO_DATA: bool = os.getenv(
        "SEED_DEMO_DATA", "true" if ENVIRONMENT == "development" else "false"
    ).lower() == "true"
    BOOTSTRAP_ADMIN_PASSWORD: Optional[str] = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    
    # Configuración de CORS
    BACKEND_CORS_ORIGINS: List[str] = _origenes_perm()
    CORS_ORIGINS: List[str] = _origenes_perm()
    
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

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @model_validator(mode="after")
    def _validar_configuracion_de_produccion(self) -> "Settings":
        """Bloquea el arranque si un entorno expuesto queda con valores de desarrollo.

        En desarrollo no se aplica ninguna restricción: el comportamiento histórico
        (SQLite local, docs activas, semilla de datos) se conserva intacto.
        """
        if not self.ENVIRONMENT.startswith("prod"):
            return self

        errores: List[str] = []
        if self.SECRET_KEY in CLAVES_NO_SEGURAS or len(self.SECRET_KEY) < 32:
            errores.append("SECRET_KEY: define un valor único de mínimo 32 caracteres")
        if self.DATABASE_URL == SQLITE_URL_POR_DEFECTO:
            errores.append("DATABASE_URL: apunta a la base del servidor, no a sqlite:///./test.db")
        if self.DEBUG:
            errores.append("DEBUG: debe ser false en producción")
        if self.SEED_DEMO_DATA:
            errores.append("SEED_DEMO_DATA: debe ser false para no crear Demo Tenant ni estados de prueba")
        if self.EXPOSE_API_DOCS:
            errores.append("EXPOSE_API_DOCS: la documentación del API no debe estar pública")
        if errores:
            raise ValueError("Configuración insegura en producción -> " + " | ".join(errores))
        return self


settings = Settings()
