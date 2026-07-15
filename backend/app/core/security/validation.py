"""Módulo de validación de seguridad para el sistema de recaudo."""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import constr
import re
from datetime import datetime
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


class SecurityValidator:
    """Clase para validaciones de seguridad de datos."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida un correo electrónico."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = re.match(pattern, email) is not None
        logger.info(
            module="security_validation",
            action="validate_email",
            message=f"Correo electrónico {'válido' if is_valid else 'inválido'}: {email}",
            data={"email": email, "is_valid": is_valid}
        )
        return is_valid

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida un número de teléfono."""
        # Permitir números de teléfono con formato internacional
        pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
        is_valid = re.match(pattern, phone) is not None
        logger.info(
            module="security_validation",
            action="validate_phone",
            message=f"Número de teléfono {'válido' if is_valid else 'inválido'}: {phone}",
            data={"phone": phone, "is_valid": is_valid}
        )
        return is_valid

    @staticmethod
    def validate_identification(identificacion: str) -> bool:
        """Valida una identificación (cédula, NIT, etc.)."""
        # Para Colombia, validar cédula (8-10 dígitos) o NIT (9 dígitos con dígito de verificación)
        pattern = r'^\d{8,10}$'
        is_valid = re.match(pattern, identificacion) is not None
        logger.info(
            module="security_validation",
            action="validate_identification",
            message=f"Identificación {'válida' if is_valid else 'inválida'}: {identificacion}",
            data={"identification": identificacion, "is_valid": is_valid}
        )
        return is_valid

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Union[bool, List[str]]]:
        """Valida la fortaleza de una contraseña."""
        errors = []
        
        # Longitud mínima
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        # Contiene mayúsculas
        if not re.search(r'[A-Z]', password):
            errors.append("La contraseña debe contener al menos una letra mayúscula")
        
        # Contiene minúsculas
        if not re.search(r'[a-z]', password):
            errors.append("La contraseña debe contener al menos una letra minúscula")
        
        # Contiene números
        if not re.search(r'\d', password):
            errors.append("La contraseña debe contener al menos un número")
        
        # Contiene caracteres especiales
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("La contraseña debe contener al menos un carácter especial")
        
        is_valid = len(errors) == 0
        
        logger.info(
            module="security_validation",
            action="validate_password_strength",
            message=f"Contraseña {'válida' if is_valid else 'inválida'}",
            data={"password_length": len(password), "errors_count": len(errors), "is_valid": is_valid}
        )
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitiza una cadena de entrada para prevenir XSS e inyecciones."""
        # Eliminar etiquetas HTML
        sanitized = re.sub(r'<[^>]*>', '', input_str)
        
        # Codificar caracteres potencialmente peligrosos
        sanitized = sanitized.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
        
        logger.info(
            module="security_validation",
            action="sanitize_input",
            message="Entrada sanitizada correctamente",
            data={"original_length": len(input_str), "sanitized_length": len(sanitized)}
        )
        
        return sanitized

    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """Valida el tipo de archivo según la extensión."""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        is_valid = extension in allowed_extensions
        
        logger.info(
            module="security_validation",
            action="validate_file_type",
            message=f"Tipo de archivo {'permitido' if is_valid else 'no permitido'}: {extension}",
            data={"filename": filename, "extension": extension, "is_valid": is_valid}
        )
        
        return is_valid

    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Valida el tamaño del archivo."""
        is_valid = file_size <= max_size
        logger.info(
            module="security_validation",
            action="validate_file_size",
            message=f"Tamaño de archivo {'válido' if is_valid else 'excede límite'}: {file_size}/{max_size}",
            data={"file_size": file_size, "max_size": max_size, "is_valid": is_valid}
        )
        return is_valid

    @staticmethod
    def validate_sql_injection_risk(input_str: str) -> bool:
        """Detecta posibles intentos de inyección SQL."""
        sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b',
            r'(--)',
            r'(\bOR\b|\bAND\b)\s+[\'"][^\'"]*[\'"]\s*=\s*[\'"][^\'"]*[\'"]',
            r'[\'"][^\'"]*(--|#|/\*|\*/)',
        ]
        
        for i, pattern in enumerate(sql_patterns):
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False


class ClientSecurityValidator:
    """Validador específico para datos de clientes."""
    
    @staticmethod
    def validate_client_data(data: Dict[str, Any]) -> Dict[str, Union[bool, List[str]]]:
        """Valida los datos de un cliente."""
        errors = []
        
        # Validar identificación
        if 'identification' in data:
            if not data['identification']:
                errors.append("La identificación es requerida")
            elif not SecurityValidator.validate_identification(data['identification']):
                errors.append("La identificación no tiene un formato válido")
        
        # Validar nombre
        if 'name' in data:
            if not data['name']:
                errors.append("El nombre es requerido")
            elif len(data['name']) < 2:
                errors.append("El nombre debe tener al menos 2 caracteres")
            elif len(data['name']) > 100:
                errors.append("El nombre no debe exceder los 100 caracteres")
        
        # Validar correo
        if 'email' in data:
            if data['email'] and not SecurityValidator.validate_email(data['email']):
                errors.append("El correo electrónico no tiene un formato válido")
        
        # Validar teléfono
        if 'phone' in data and data['phone']:
            if not SecurityValidator.validate_phone(data['phone']):
                errors.append("El número de teléfono no tiene un formato válido")
        
        # Validar dirección
        if 'address' in data and data['address']:
            if len(data['address']) > 255:
                errors.append("La dirección no debe exceder los 255 caracteres")
        
        is_valid = len(errors) == 0
        
        logger.info(
            module="security_validation",
            action="validate_client_data",
            message=f"Datos de cliente {'válidos' if is_valid else 'inválidos'}",
            data={"errors_count": len(errors), "is_valid": is_valid}
        )
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }


class ObligationSecurityValidator:
    """Validador específico para datos de obligaciones."""
    
    @staticmethod
    def validate_obligation_data(data: Dict[str, Any]) -> Dict[str, Union[bool, List[str]]]:
        """Valida los datos de una obligación."""
        errors = []
        
        # Validar ID de cliente
        if 'client_id' in data:
            if not isinstance(data['client_id'], int) or data['client_id'] <= 0:
                errors.append("El ID de cliente debe ser un número entero positivo")
        
        # Validar número de obligación
        if 'number' in data:
            if not data['number']:
                errors.append("El número de obligación es requerido")
            elif len(data['number']) < 3:
                errors.append("El número de obligación debe tener al menos 3 caracteres")
            elif len(data['number']) > 50:
                errors.append("El número de obligación no debe exceder los 50 caracteres")
        
        # Validar concepto
        if 'concept' in data:
            if not data['concept']:
                errors.append("El concepto es requerido")
            elif len(data['concept']) > 255:
                errors.append("El concepto no debe exceder los 255 caracteres")
        
        # Validar monto
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append("El monto debe ser un número positivo")
            except (ValueError, TypeError):
                errors.append("El monto debe ser un número válido")
        
        # Validar fechas
        if 'issue_date' in data:
            try:
                datetime.fromisoformat(data['issue_date'].replace('Z', '+00:00'))
            except ValueError:
                errors.append("La fecha de expedición no tiene un formato válido")
        
        if 'due_date' in data:
            try:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                if 'issue_date' in data:
                    issue_date = datetime.fromisoformat(data['issue_date'].replace('Z', '+00:00'))
                    if due_date < issue_date:
                        errors.append("La fecha de vencimiento no puede ser anterior a la fecha de expedición")
            except ValueError:
                errors.append("La fecha de vencimiento no tiene un formato válido")
        
        # Validar estado
        if 'status' in data:
            valid_statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED']
            if data['status'] not in valid_statuses:
                errors.append(f"El estado debe ser uno de los siguientes: {', '.join(valid_statuses)}")
        
        # Validar descripción
        if 'description' in data and data['description']:
            if len(data['description']) > 1000:
                errors.append("La descripción no debe exceder los 1000 caracteres")
        
        is_valid = len(errors) == 0
        
        logger.info(
            module="security_validation",
            action="validate_obligation_data",
            message=f"Datos de obligación {'válidos' if is_valid else 'inválidos'}",
            data={"errors_count": len(errors), "is_valid": is_valid}
        )
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }


class DocumentSecurityValidator:
    """Validador específico para datos de documentos."""
    
    @staticmethod
    def validate_document_data(data: Dict[str, Any]) -> Dict[str, Union[bool, List[str]]]:
        """Valida los datos de un documento."""
        errors = []
        
        # Validar ID de cliente
        if 'client_id' in data:
            if not isinstance(data['client_id'], int) or data['client_id'] <= 0:
                errors.append("El ID de cliente debe ser un número entero positivo")
        
        # Validar ID de obligación
        if 'obligation_id' in data:
            if not isinstance(data['obligation_id'], int) or data['obligation_id'] <= 0:
                errors.append("El ID de obligación debe ser un número entero positivo")
        
        # Validar tipo de documento
        if 'type' in data:
            if not data['type']:
                errors.append("El tipo de documento es requerido")
            elif len(data['type']) < 2:
                errors.append("El tipo de documento debe tener al menos 2 caracteres")
            elif len(data['type']) > 50:
                errors.append("El tipo de documento no debe exceder los 50 caracteres")
        
        # Validar estado
        if 'status' in data:
            valid_statuses = ['DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'ARCHIVED']
            if data['status'] not in valid_statuses:
                errors.append(f"El estado debe ser uno de los siguientes: {', '.join(valid_statuses)}")
        
        # Validar contenido
        if 'content' in data and data['content']:
            if len(data['content']) > 10000:  # 10KB máximo
                errors.append("El contenido no debe exceder los 10000 caracteres")
        
        # Validar nombre de archivo
        if 'file_name' in data and data['file_name']:
            if len(data['file_name']) > 255:
                errors.append("El nombre de archivo no debe exceder los 255 caracteres")
        
        # Validar ruta de archivo
        if 'file_path' in data and data['file_path']:
            if len(data['file_path']) > 500:
                errors.append("La ruta de archivo no debe exceder los 500 caracteres")
        
        # Validar metadatos
        if 'metadata' in data and data['metadata']:
            if isinstance(data['metadata'], str):
                try:
                    # Si es una cadena, verificar que sea un JSON válido
                    import json
                    parsed = json.loads(data['metadata'])
                    if not isinstance(parsed, dict):
                        errors.append("Los metadatos deben ser un objeto JSON válido")
                except json.JSONDecodeError:
                    errors.append("Los metadatos deben ser un JSON válido")
            elif not isinstance(data['metadata'], dict):
                errors.append("Los metadatos deben ser un objeto o una cadena JSON válida")
        
        is_valid = len(errors) == 0
        
        logger.info(
            module="security_validation",
            action="validate_document_data",
            message=f"Datos de documento {'válidos' if is_valid else 'inválidos'}",
            data={"errors_count": len(errors), "is_valid": is_valid}
        )
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }


class UserSecurityValidator:
    """Validador específico para datos de usuarios."""
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any]) -> Dict[str, Union[bool, List[str]]]:
        """Valida los datos de un usuario."""
        errors = []
        
        # Validar nombre de usuario
        if 'username' in data:
            if not data['username']:
                errors.append("El nombre de usuario es requerido")
            elif len(data['username']) < 3:
                errors.append("El nombre de usuario debe tener al menos 3 caracteres")
            elif len(data['username']) > 50:
                errors.append("El nombre de usuario no debe exceder los 50 caracteres")
            elif not re.match(r'^[a-zA-Z0-9_-]+$', data['username']):
                errors.append("El nombre de usuario solo puede contener letras, números, guiones bajos y guiones medios")
        
        # Validar correo
        if 'email' in data:
            if not data['email']:
                errors.append("El correo electrónico es requerido")
            elif not SecurityValidator.validate_email(data['email']):
                errors.append("El correo electrónico no tiene un formato válido")
        
        # Validar contraseña
        if 'password' in data:
            if not data['password']:
                errors.append("La contraseña es requerida")
            else:
                password_validation = SecurityValidator.validate_password_strength(data['password'])
                if not password_validation['is_valid']:
                    errors.extend(password_validation['errors'])
        
        # Validar nombre completo
        if 'full_name' in data:
            if not data['full_name']:
                errors.append("El nombre completo es requerido")
            elif len(data['full_name']) < 2:
                errors.append("El nombre completo debe tener al menos 2 caracteres")
            elif len(data['full_name']) > 100:
                errors.append("El nombre completo no debe exceder los 100 caracteres")
        
        # Validar rol
        if 'role' in data:
            valid_roles = ['admin', 'user', 'viewer', 'operator']
            if data['role'] not in valid_roles:
                errors.append(f"El rol debe ser uno de los siguientes: {', '.join(valid_roles)}")
        
        is_valid = len(errors) == 0
        
        logger.info(
            module="security_validation",
            action="validate_user_data",
            message=f"Datos de usuario {'válidos' if is_valid else 'inválidos'}",
            data={"errors_count": len(errors), "is_valid": is_valid}
        )
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }