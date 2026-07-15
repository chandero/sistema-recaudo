"""Módulo de validación de tokens para el sistema de recaudo."""
import jwt
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security.auth import auth_security
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


class TokenValidator:
    """Clase para validar tokens JWT y otros tipos de tokens."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida un token de acceso JWT."""
        try:
            # Verificar si el token ha sido revocado
            if auth_security.is_token_revoked(token):
                logger.warning(
                    module="token_validation",
                    action="access_token_revoked",
                    message="Token de acceso ha sido revocado",
                    data={"token_revoked": True}
                )
                return None
            
            # Decodificar el token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")
            
            # Verificar expiración
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                logger.warning(
                    module="token_validation",
                    action="access_token_expired",
                    message="Token de acceso ha expirado",
                    data={"exp_time": datetime.utcfromtimestamp(exp).isoformat()}
                )
                return None
            
            # Construir datos del token
            token_data = {
                "username": username,
                "user_id": user_id,
                "role": role,
                "exp": exp,
                "iat": iat
            }
            
            logger.info(
                module="token_validation",
                action="access_token_validated",
                message="Token de acceso validado exitosamente",
                user_id=user_id,
                data={"username": username, "role": role}
            )
            
            return token_data
        except jwt.ExpiredSignatureError:
            logger.error(
                module="token_validation",
                action="access_token_expired_error",
                message="Firma del token ha expirado",
                error_code="TOKEN_EXPIRED"
            )
            return None
        except jwt.JWTError as e:
            logger.error(
                module="token_validation",
                action="access_token_invalid",
                message=f"Token de acceso inválido: {str(e)}",
                error_code="TOKEN_INVALID"
            )
            return None
        except Exception as e:
            logger.error(
                module="token_validation",
                action="access_token_validation_error",
                message=f"Error general validando token: {str(e)}",
                error_code="TOKEN_VALIDATION_ERROR"
            )
            return None
    
    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida un token de actualización."""
        try:
            # En una implementación completa, los tokens de actualización tendrían
            # una lógica diferente y posiblemente una clave diferente
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            exp: int = payload.get("exp")
            
            # Verificar expiración (los refresh tokens suelen durar más)
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                logger.warning(
                    module="token_validation",
                    action="refresh_token_expired",
                    message="Token de actualización ha expirado",
                    data={"exp_time": datetime.utcfromtimestamp(exp).isoformat()}
                )
                return None
            
            token_data = {
                "username": username,
                "user_id": user_id,
                "exp": exp
            }
            
            logger.info(
                module="token_validation",
                action="refresh_token_validated",
                message="Token de actualización validado exitosamente",
                user_id=user_id,
                data={"username": username}
            )
            
            return token_data
        except jwt.ExpiredSignatureError:
            logger.error(
                module="token_validation",
                action="refresh_token_expired_error",
                message="Firma del token de actualización ha expirado",
                error_code="REFRESH_TOKEN_EXPIRED"
            )
            return None
        except jwt.JWTError as e:
            logger.error(
                module="token_validation",
                action="refresh_token_invalid",
                message=f"Token de actualización inválido: {str(e)}",
                error_code="REFRESH_TOKEN_INVALID"
            )
            return None
        except Exception as e:
            logger.error(
                module="token_validation",
                action="refresh_token_validation_error",
                message=f"Error general validando refresh token: {str(e)}",
                error_code="REFRESH_TOKEN_VALIDATION_ERROR"
            )
            return None
    
    def validate_api_key(self, api_key: str) -> bool:
        """Valida una clave de API."""
        # En una implementación real, esto verificaría la clave de API
        # contra una base de datos o un servicio de autenticación
        if not api_key:
            logger.warning(
                module="token_validation",
                action="api_key_missing",
                message="Clave de API ausente",
                data={"api_key_present": bool(api_key)}
            )
            return False
        
        # Validación simple para demostración
        # En producción, esto debería verificar la clave contra una base de datos
        is_valid = len(api_key) >= 32 and api_key.startswith("sk-")
        
        logger.info(
            module="token_validation",
            action="api_key_validated",
            message=f"Clave de API {'válida' if is_valid else 'inválida'}",
            data={"api_key_length": len(api_key), "api_key_valid": is_valid}
        )
        
        return is_valid
    
    def validate_csrf_token(self, token: str, expected_token: str) -> bool:
        """Valida un token CSRF."""
        if not token or not expected_token:
            logger.warning(
                module="token_validation",
                action="csrf_token_missing",
                message="Token CSRF ausente",
                data={"token_present": bool(token), "expected_token_present": bool(expected_token)}
            )
            return False
        
        # Comparar tokens usando comparación segura
        is_valid = jwt.decode(token, self.secret_key, algorithms=[self.algorithm]) == \
                   jwt.decode(expected_token, self.secret_key, algorithms=[self.algorithm]) if token and expected_token else False
        
        # Alternativa más simple para comparación de strings
        import hmac
        is_valid = hmac.compare_digest(token, expected_token)
        
        logger.info(
            module="token_validation",
            action="csrf_token_validated",
            message=f"Token CSRF {'válido' if is_valid else 'inválido'}",
            data={"token_valid": is_valid}
        )
        
        return is_valid
    
    def validate_bearer_token(self, authorization_header: str) -> Optional[Dict[str, Any]]:
        """Valida un token Bearer desde el header de autorización."""
        if not authorization_header:
            logger.warning(
                module="token_validation",
                action="authorization_header_missing",
                message="Header de autorización ausente",
                data={"header_present": bool(authorization_header)}
            )
            return None
        
        # Verificar el formato "Bearer <token>"
        parts = authorization_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(
                module="token_validation",
                action="invalid_authorization_format",
                message="Formato de header de autorización inválido",
                data={"parts_count": len(parts), "prefix": parts[0] if parts else None}
            )
            return None
        
        token = parts[1]
        return self.validate_access_token(token)
    
    def extract_permissions_from_token(self, token_data: Dict[str, Any]) -> List[str]:
        """Extrae permisos del token."""
        # En una implementación real, los permisos vendrían en el token
        # Por ahora, asignaremos permisos basados en el rol
        role = token_data.get("role", "user")
        
        permissions = {
            "admin": ["read", "write", "delete", "manage_users", "manage_system"],
            "operator": ["read", "write", "process_documents"],
            "viewer": ["read"],
            "user": ["read", "write_own"]
        }
        
        perms = permissions.get(role, ["read"])
        
        logger.info(
            module="token_validation",
            action="permissions_extracted",
            message=f"Permisos extraídos para rol {role}",
            data={"role": role, "permissions": perms}
        )
        
        return perms
    
    def validate_token_scopes(self, token_data: Dict[str, Any], required_scopes: List[str]) -> bool:
        """Valida que el token tenga los scopes requeridos."""
        permissions = self.extract_permissions_from_token(token_data)
        
        # Verificar si todos los scopes requeridos están en los permisos
        has_required_scopes = all(scope in permissions for scope in required_scopes)
        
        logger.info(
            module="token_validation",
            action="scopes_validated",
            message=f"Scopes requeridos {'válidos' if has_required_scopes else 'inválidos'}",
            data={"required_scopes": required_scopes, "user_permissions": permissions, "valid": has_required_scopes}
        )
        
        return has_required_scopes


# Instancia global del validador de tokens
token_validator = TokenValidator()