"""Módulo de seguridad de autenticación para el sistema de recaudo."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import redis
import os
from app.core.config import settings
from app.core.logging.logger import get_logger, log_authentication_event


logger = get_logger(__name__)


# Contexto de hashing de contraseñas
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "sha256_crypt"], deprecated="auto")

# Esquema de seguridad para la autenticación
security = HTTPBearer()


class TokenData(BaseModel):
    """Datos del token JWT."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class AuthSecurity:
    """Clase para la seguridad de autenticación."""
    
    def __init__(self):
        # Conectar a Redis para almacenamiento de tokens revocados
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()  # Verificar conexión
        except Exception as e:
            logger.error(
                module="auth_security",
                action="redis_connection_failed",
                message=f"Error conectando a Redis: {str(e)}",
                error_code="REDIS_CONNECTION_ERROR"
            )
            self.redis_client = None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña coincide con el hash."""
        try:
            is_valid = pwd_context.verify(plain_password, hashed_password)
            logger.info(
                module="auth_security",
                action="verify_password",
                message="Contraseña verificada",
                data={"verification_result": is_valid}
            )
            return is_valid
        except Exception as e:
            logger.error(
                module="auth_security",
                action="verify_password_error",
                message=f"Error verificando contraseña: {str(e)}",
                error_code="PASSWORD_VERIFICATION_ERROR"
            )
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Genera un hash de la contraseña."""
        try:
            hashed = pwd_context.hash(password)
            logger.info(
                module="auth_security",
                action="hash_password",
                message="Contraseña hasheada exitosamente",
                data={"password_length": len(password)}
            )
            return hashed
        except Exception as e:
            logger.error(
                module="auth_security",
                action="hash_password_error",
                message=f"Error hasheando contraseña: {str(e)}",
                error_code="PASSWORD_HASH_ERROR"
            )
            raise
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token de acceso JWT."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.info(
                module="auth_security",
                action="create_access_token",
                message="Token JWT creado exitosamente",
                data={"username": data.get("sub"), "expires_at": expire.isoformat()}
            )
            return encoded_jwt
        except Exception as e:
            logger.error(
                module="auth_security",
                action="create_access_token_error",
                message=f"Error creando token JWT: {str(e)}",
                error_code="JWT_CREATION_ERROR"
            )
            raise
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decodifica un token JWT."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            role: str = payload.get("role")
            
            if username is None:
                logger.warning(
                    module="auth_security",
                    action="decode_token_no_username",
                    message="Token JWT no contiene nombre de usuario",
                    data={"token_present": token is not None}
                )
                return None
            
            token_data = TokenData(username=username, user_id=user_id, role=role)
            logger.info(
                module="auth_security",
                action="decode_token_success",
                message="Token JWT decodificado exitosamente",
                data={"username": username, "user_id": user_id, "role": role}
            )
            return token_data
        except JWTError as e:
            logger.error(
                module="auth_security",
                action="decode_token_error",
                message=f"Error decodificando token JWT: {str(e)}",
                error_code="JWT_DECODE_ERROR"
            )
            return None
        except Exception as e:
            logger.error(
                module="auth_security",
                action="decode_token_general_error",
                message=f"Error general decodificando token: {str(e)}",
                error_code="GENERAL_JWT_ERROR"
            )
            return None
    
    def is_token_revoked(self, token: str) -> bool:
        """Verifica si un token ha sido revocado."""
        if not self.redis_client:
            logger.warning(
                module="auth_security",
                action="check_revoked_token_redis_unavailable",
                message="Redis no disponible para verificación de tokens revocados",
                error_code="REDIS_UNAVAILABLE"
            )
            return False
        
        try:
            # Usar el hash del token como clave
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            revoked = self.redis_client.exists(f"revoked_token:{token_hash}")
            logger.info(
                module="auth_security",
                action="check_revoked_token",
                message=f"Token {'revocado' if revoked else 'activo'}",
                data={"token_revoked": revoked}
            )
            return bool(revoked)
        except Exception as e:
            logger.error(
                module="auth_security",
                action="check_revoked_token_error",
                message=f"Error verificando token revocado: {str(e)}",
                error_code="TOKEN_REVOCATION_CHECK_ERROR"
            )
            return False
    
    def revoke_token(self, token: str) -> bool:
        """Revoca un token JWT."""
        if not self.redis_client:
            logger.warning(
                module="auth_security",
                action="revoke_token_redis_unavailable",
                message="Redis no disponible para revocación de tokens",
                error_code="REDIS_UNAVAILABLE"
            )
            return False
        
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            # Establecer el token como revocado con un TTL basado en el tiempo de expiración original
            # Por simplicidad, usar el mismo tiempo de expiración
            self.redis_client.setex(
                f"revoked_token:{token_hash}",
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convertir a segundos
                "revoked"
            )
            logger.info(
                module="auth_security",
                action="revoke_token",
                message="Token JWT revocado exitosamente",
                data={"token_hash": token_hash}
            )
            return True
        except Exception as e:
            logger.error(
                module="auth_security",
                action="revoke_token_error",
                message=f"Error revocando token JWT: {str(e)}",
                error_code="TOKEN_REVOCATION_ERROR"
            )
            return False
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Obtiene el usuario actual a partir del token JWT."""
        token = credentials.credentials
        
        # Verificar si el token ha sido revocado
        if self.is_token_revoked(token):
            logger.warning(
                module="auth_security",
                action="get_current_user_token_revoked",
                message="Intento de acceso con token revocado",
                data={"token_revoked": True}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token ha sido revocado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = self.decode_token(token)
        if token_data is None:
            logger.warning(
                module="auth_security",
                action="get_current_user_invalid_token",
                message="Token JWT inválido o expirado",
                data={"token_valid": False}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar las credenciales",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(
            module="auth_security",
            action="get_current_user_success",
            message="Usuario autenticado exitosamente",
            user_id=token_data.user_id,
            data={"username": token_data.username, "role": token_data.role}
        )
        return token_data
    
    def get_current_active_user(self, current_user: TokenData = Depends(get_current_user)):
        """Obtiene el usuario activo actual."""
        # Aquí podrías verificar si el usuario está activo en la base de datos
        # Por ahora, simplemente retornamos el usuario
        return current_user
    
    def verify_brute_force_attempt(self, identifier: str, request: Request) -> bool:
        """Verifica si hay intentos de fuerza bruta."""
        if not self.redis_client:
            logger.warning(
                module="auth_security",
                action="brute_force_check_redis_unavailable",
                message="Redis no disponible para verificación de fuerza bruta",
                error_code="REDIS_UNAVAILABLE"
            )
            return True  # Permitir si no hay Redis
        
        try:
            # Llave para contar intentos fallidos
            key = f"login_attempts:{identifier}"
            attempts = self.redis_client.get(key)
            
            if attempts and int(attempts) >= 5:  # 5 intentos fallidos
                # Bloquear temporalmente
                ttl = self.redis_client.ttl(key)
                logger.warning(
                    module="auth_security",
                    action="brute_force_detected",
                    message=f"Detectado intento de fuerza bruta para {identifier}",
                    data={"attempts": attempts, "ttl_seconds": ttl}
                )
                return False
            
            return True
        except Exception as e:
            logger.error(
                module="auth_security",
                action="brute_force_check_error",
                message=f"Error verificando intentos de fuerza bruta: {str(e)}",
                error_code="BRUTE_FORCE_CHECK_ERROR"
            )
            return True  # Permitir si hay error
    
    def record_failed_login_attempt(self, identifier: str):
        """Registra un intento de inicio de sesión fallido."""
        if not self.redis_client:
            return
        
        try:
            key = f"login_attempts:{identifier}"
            # Incrementar contador y establecer TTL de 15 minutos
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 900)  # 15 minutos
            pipe.execute()
            
            logger.info(
                module="auth_security",
                action="record_failed_login",
                message="Registrado intento de inicio de sesión fallido",
                data={"identifier": identifier}
            )
        except Exception as e:
            logger.error(
                module="auth_security",
                action="record_failed_login_error",
                message=f"Error registrando intento de inicio de sesión fallido: {str(e)}",
                error_code="FAILED_LOGIN_RECORD_ERROR"
            )
    
    def clear_failed_login_attempts(self, identifier: str):
        """Limpia los intentos de inicio de sesión fallidos."""
        if not self.redis_client:
            return
        
        try:
            key = f"login_attempts:{identifier}"
            self.redis_client.delete(key)
            
            logger.info(
                module="auth_security",
                action="clear_failed_login_attempts",
                message="Limpiados intentos de inicio de sesión fallidos",
                data={"identifier": identifier}
            )
        except Exception as e:
            logger.error(
                module="auth_security",
                action="clear_failed_login_attempts_error",
                message=f"Error limpiando intentos de inicio de sesión fallidos: {str(e)}",
                error_code="CLEAR_FAILED_LOGIN_ERROR"
            )


# Instancia global de seguridad de autenticación
auth_security = AuthSecurity()


def get_auth_security():
    """Obtiene la instancia de seguridad de autenticación."""
    return auth_security


def verify_current_user_role(required_role: str):
    """Verifica que el usuario tenga el rol requerido."""
    async def role_checker(current_user: TokenData = Depends(auth_security.get_current_active_user)):
        if current_user.role != required_role:
            logger.warning(
                module="auth_security",
                action="role_verification_failed",
                message=f"Usuario no tiene el rol requerido {required_role}",
                user_id=current_user.user_id,
                data={"user_role": current_user.role, "required_role": required_role}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes"
            )
        
        logger.info(
            module="auth_security",
            action="role_verification_success",
            message=f"Usuario verificado con rol {required_role}",
            user_id=current_user.user_id,
            data={"user_role": current_user.role, "required_role": required_role}
        )
        return current_user
    
    return role_checker


def log_auth_event(event: str, username: str, success: bool, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """Registra un evento de autenticación."""
    log_authentication_event(event, username, success, ip_address, user_agent)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Función auxiliar para crear un token de acceso JWT usando el singleton auth_security."""
    return auth_security.create_access_token(data, expires_delta)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Función auxiliar para verificar una contraseña usando el singleton auth_security."""
    return auth_security.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Función auxiliar para hashear una contraseña usando el singleton auth_security."""
    return auth_security.get_password_hash(password)
