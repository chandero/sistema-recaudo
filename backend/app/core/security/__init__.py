"""Paquete de seguridad para el sistema de recaudo."""

from .validation import (
    SecurityValidator,
    ClientSecurityValidator,
    ObligationSecurityValidator,
    DocumentSecurityValidator,
    UserSecurityValidator
)
from .auth import (
    AuthSecurity,
    TokenData,
    auth_security,
    get_auth_security,
    verify_current_user_role,
    log_auth_event,
    create_access_token,
    verify_password,
    get_password_hash
)
from .attack_protection import (
    AttackProtection,
    attack_protection
)
from .input_sanitizer import (
    InputSanitizer,
    input_sanitizer
)
from .token_validation import (
    TokenValidator,
    token_validator
)
from .endpoint_protection import (
    EndpointProtector,
    endpoint_protector
)
from .data_protection import (
    DataProtector,
    data_protector
)

__all__ = [
    # Validación
    "SecurityValidator",
    "ClientSecurityValidator",
    "ObligationSecurityValidator",
    "DocumentSecurityValidator",
    "UserSecurityValidator",
    
    # Autenticación
    "AuthSecurity",
    "TokenData",
    "auth_security",
    "get_auth_security",
    "verify_current_user_role",
    "log_auth_event",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    
    # Protección contra ataques
    "AttackProtection",
    "attack_protection",
    
    # Sanitización de entradas
    "InputSanitizer",
    "input_sanitizer",
    
    # Validación de tokens
    "TokenValidator",
    "token_validator",
    
    # Protección de endpoints
    "EndpointProtector",
    "endpoint_protector",
    
    # Protección de datos
    "DataProtector",
    "data_protector"
]