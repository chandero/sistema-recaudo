"""Módulo de protección de datos para el sistema de recaudo."""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Union, Optional
from app.core.config import settings
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


class DataProtector:
    """Clase para la protección de datos sensibles."""
    
    def __init__(self):
        # Usar la clave secreta de la configuración para generar la clave de cifrado
        password = settings.SECRET_KEY.encode()
        salt = b'sistema_recaudo_salt'  # En producción, usar un salt aleatorio por cada clave
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Cifra datos sensibles."""
        try:
            if isinstance(data, str):
                data = data.encode()
            
            encrypted_data = self.cipher_suite.encrypt(data)
            encrypted_str = base64.urlsafe_b64encode(encrypted_data).decode()
            
            logger.info(
                module="data_protection",
                action="data_encrypted",
                message="Datos cifrados exitosamente",
                data={"data_type": type(data).__name__, "encrypted_length": len(encrypted_str)}
            )
            
            return encrypted_str
        except Exception as e:
            logger.error(
                module="data_protection",
                action="encryption_error",
                message=f"Error cifrando datos: {str(e)}",
                error_code="ENCRYPTION_ERROR"
            )
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Descifra datos sensibles."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            
            decrypted_str = decrypted_data.decode()
            
            logger.info(
                module="data_protection",
                action="data_decrypted",
                message="Datos descifrados exitosamente",
                data={"decrypted_length": len(decrypted_str)}
            )
            
            return decrypted_str
        except Exception as e:
            logger.error(
                module="data_protection",
                action="decryption_error",
                message=f"Error descifrando datos: {str(e)}",
                error_code="DECRYPTION_ERROR"
            )
            raise
    
    def hash_data(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """Hashea datos sensibles."""
        try:
            if isinstance(data, str):
                data = data.encode()
            
            if algorithm == 'sha256':
                import hashlib
                hashed = hashlib.sha256(data).hexdigest()
            else:
                raise ValueError(f"Algoritmo de hash no soportado: {algorithm}")
            
            logger.info(
                module="data_protection",
                action="data_hashed",
                message="Datos hasheados exitosamente",
                data={"algorithm": algorithm, "hash_length": len(hashed)}
            )
            
            return hashed
        except Exception as e:
            logger.error(
                module="data_protection",
                action="hash_error",
                message=f"Error hasheando datos: {str(e)}",
                error_code="HASH_ERROR"
            )
            raise
    
    def mask_sensitive_data(self, data: str, visible_chars: int = 2) -> str:
        """Enmascara datos sensibles como números de identificación o teléfonos."""
        if not data or len(data) <= visible_chars * 2:
            return '*' * len(data) if data else data
        
        visible_start = data[:visible_chars]
        visible_end = data[-visible_chars:] if visible_chars > 0 else ''
        masked_part = '*' * (len(data) - visible_chars * 2)
        
        masked_data = f"{visible_start}{masked_part}{visible_end}"
        
        logger.info(
            module="data_protection",
            action="data_masked",
            message="Datos sensibles enmascarados",
            data={"original_length": len(data), "masked_length": len(masked_data)}
        )
        
        return masked_data
    
    def validate_pii(self, data: str, data_type: str) -> bool:
        """Valida datos de identificación personal (PII)."""
        try:
            if data_type == 'email':
                import re
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                is_valid = re.match(pattern, data) is not None
            elif data_type == 'phone':
                import re
                pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
                is_valid = re.match(pattern, data) is not None
            elif data_type == 'identification':
                import re
                pattern = r'^\d{8,10}$'  # Para Colombia, cédula o NIT
                is_valid = re.match(pattern, data) is not None
            else:
                raise ValueError(f"Tipo de PII no soportado: {data_type}")
            
            logger.info(
                module="data_protection",
                action="pii_validated",
                message=f"PII de tipo {data_type} {'válida' if is_valid else 'inválida'}",
                data={"data_type": data_type, "is_valid": is_valid}
            )
            
            return is_valid
        except Exception as e:
            logger.error(
                module="data_protection",
                action="pii_validation_error",
                message=f"Error validando PII: {str(e)}",
                error_code="PII_VALIDATION_ERROR"
            )
            return False
    
    def sanitize_for_storage(self, data: dict, sensitive_fields: list) -> dict:
        """Sanitiza datos antes de almacenarlos."""
        sanitized = {}
        
        for key, value in data.items():
            if key in sensitive_fields:
                # Cifrar campos sensibles
                if isinstance(value, str):
                    sanitized[key] = self.encrypt_data(value)
                    sanitized[f"{key}_encrypted"] = True
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        logger.info(
            module="data_protection",
            action="data_sanitized_for_storage",
            message="Datos sanitizados para almacenamiento",
            data={"sensitive_fields_count": len(sensitive_fields), "total_fields": len(data)}
        )
        
        return sanitized
    
    def extract_from_storage(self, data: dict, sensitive_fields: list) -> dict:
        """Extrae y descifra datos sensibles desde almacenamiento."""
        extracted = {}
        
        for key, value in data.items():
            if key in sensitive_fields and data.get(f"{key}_encrypted"):
                # Descifrar campo sensible
                try:
                    extracted[key] = self.decrypt_data(value)
                except Exception:
                    # Si no se puede descifrar, dejar tal cual
                    extracted[key] = value
            else:
                extracted[key] = value
        
        logger.info(
            module="data_protection",
            action="data_extracted_from_storage",
            message="Datos extraídos y descifrados desde almacenamiento",
            data={"sensitive_fields_count": len(sensitive_fields), "total_fields": len(data)}
        )
        
        return extracted


# Instancia global del protector de datos
data_protector = DataProtector()