"""Módulo de sanitización de entradas para el sistema de recaudo."""
import re
import html
import urllib.parse
from typing import Union, Dict, List, Any
from bleach import clean
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


class InputSanitizer:
    """Clase para sanitizar entradas de usuario y prevenir ataques."""
    
    def __init__(self):
        # Tags y atributos permitidos para HTML seguro
        self.allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 
            'h4', 'h5', 'h6', 'blockquote', 'pre', 'code', 'hr', 'div', 'span'
        ]
        
        self.allowed_attributes = {
            '*': ['class', 'style'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        
        self.allowed_styles = [
            'color', 'background-color', 'font-weight', 'text-decoration', 
            'font-style', 'text-align', 'margin', 'padding'
        ]
    
    def sanitize_string(self, input_str: str, strip: bool = True) -> str:
        """Sanitiza una cadena de texto."""
        if not input_str:
            return input_str
        
        # Eliminar caracteres de control no imprimibles (excepto tab, newline, carriage return)
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        # Codificar caracteres especiales
        sanitized = html.escape(sanitized, quote=True)
        
        # Decodificar entidades HTML comunes para evitar doble codificación
        sanitized = html.unescape(sanitized)
        
        # Sanitizar con bleach si es HTML
        if '<' in sanitized and '>' in sanitized:
            sanitized = clean(
                sanitized,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                styles=self.allowed_styles,
                strip=strip
            )
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_string",
            message="Cadena sanitizada exitosamente",
            data={"original_length": len(input_str), "sanitized_length": len(sanitized)}
        )
        
        return sanitized
    
    def sanitize_html(self, html_content: str) -> str:
        """Sanitiza contenido HTML."""
        if not html_content:
            return html_content
        
        sanitized = clean(
            html_content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            styles=self.allowed_styles,
            strip=False
        )
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_html",
            message="HTML sanitizado exitosamente",
            data={"original_length": len(html_content), "sanitized_length": len(sanitized)}
        )
        
        return sanitized
    
    def sanitize_url(self, url: str) -> str:
        """Sanitiza una URL."""
        if not url:
            return url
        
        # Verificar que sea una URL válida
        try:
            parsed = urllib.parse.urlparse(url)
            # Solo permitir esquemas seguros
            if parsed.scheme not in ['http', 'https', 'mailto', 'ftp']:
                logger.warning(
                    module="input_sanitizer",
                    action="invalid_url_scheme",
                    message=f"Esquema de URL no permitido: {parsed.scheme}",
                    data={"url": url, "scheme": parsed.scheme}
                )
                return ""
            
            # Reensamblar la URL
            sanitized = urllib.parse.urlunparse(parsed)
        except Exception as e:
            logger.error(
                module="input_sanitizer",
                action="url_parse_error",
                message=f"Error parseando URL: {str(e)}",
                error_code="URL_PARSE_ERROR"
            )
            return ""
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_url",
            message="URL sanitizada exitosamente",
            data={"original_url": url, "sanitized_url": sanitized}
        )
        
        return sanitized
    
    def sanitize_sql_identifier(self, identifier: str) -> str:
        """Sanitiza un identificador SQL (nombre de tabla, columna, etc.)."""
        if not identifier:
            return identifier
        
        # Permitir solo caracteres alfanuméricos y guión bajo
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        
        # Verificar que no sea una palabra reservada
        reserved_words = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
            'TABLE', 'FROM', 'WHERE', 'JOIN', 'UNION', 'ORDER', 'GROUP', 
            'BY', 'HAVING', 'LIMIT', 'OFFSET', 'INTO', 'VALUES', 'SET'
        }
        
        if sanitized.upper() in reserved_words:
            logger.warning(
                module="input_sanitizer",
                action="sql_reserved_word",
                message=f"Palabra reservada SQL detectada: {identifier}",
                data={"identifier": identifier, "sanitized": sanitized}
            )
            return ""
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_sql_identifier",
            message="Identificador SQL sanitizado exitosamente",
            data={"original_identifier": identifier, "sanitized_identifier": sanitized}
        )
        
        return sanitized
    
    def sanitize_json_input(self, data: Union[str, Dict, List]) -> Union[Dict, List]:
        """Sanitiza entrada JSON."""
        if isinstance(data, str):
            try:
                import json
                parsed = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(
                    module="input_sanitizer",
                    action="json_decode_error",
                    message=f"Error decodificando JSON: {str(e)}",
                    error_code="JSON_DECODE_ERROR"
                )
                raise ValueError("JSON inválido")
        else:
            parsed = data
        
        if isinstance(parsed, dict):
            sanitized = {}
            for key, value in parsed.items():
                safe_key = self.sanitize_sql_identifier(str(key))
                if safe_key:  # Solo incluir claves válidas
                    if isinstance(value, (dict, list)):
                        sanitized[safe_key] = self.sanitize_json_input(value)
                    elif isinstance(value, str):
                        sanitized[safe_key] = self.sanitize_string(value)
                    else:
                        sanitized[safe_key] = value
            return sanitized
        elif isinstance(parsed, list):
            sanitized = []
            for item in parsed:
                if isinstance(item, (dict, list)):
                    sanitized.append(self.sanitize_json_input(item))
                elif isinstance(item, str):
                    sanitized.append(self.sanitize_string(item))
                else:
                    sanitized.append(item)
            return sanitized
        else:
            logger.error(
                module="input_sanitizer",
                action="invalid_json_type",
                message="Tipo de dato JSON no soportado",
                error_code="INVALID_JSON_TYPE"
            )
            raise ValueError("Tipo de dato JSON no soportado")
    
    def sanitize_file_name(self, filename: str) -> str:
        """Sanitiza un nombre de archivo."""
        if not filename:
            return filename
        
        # Eliminar caracteres peligrosos
        sanitized = re.sub(r'[^\w\-.]', '_', filename)
        
        # Prevenir traversals de directorio
        sanitized = sanitized.replace('../', '').replace('..\\', '')
        
        # Limitar longitud
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:250] + ('.' + ext if ext else '')
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_file_name",
            message="Nombre de archivo sanitizado exitosamente",
            data={"original_filename": filename, "sanitized_filename": sanitized}
        )
        
        return sanitized
    
    def sanitize_email(self, email: str) -> str:
        """Sanitiza un correo electrónico."""
        if not email:
            return email
        
        # Eliminar espacios en blanco al principio y al final
        email = email.strip()
        
        # Validar formato básico
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            logger.warning(
                module="input_sanitizer",
                action="invalid_email_format",
                message=f"Formato de correo electrónico inválido: {email}",
                data={"email": email}
            )
            return ""
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_email",
            message="Correo electrónico sanitizado exitosamente",
            data={"email": email}
        )
        
        return email
    
    def sanitize_phone(self, phone: str) -> str:
        """Sanitiza un número de teléfono."""
        if not phone:
            return phone
        
        # Conservar solo dígitos, signo más, guiones y paréntesis
        sanitized = re.sub(r'[^0-9+\-\(\)\s]', '', phone)
        
        # Eliminar espacios en blanco múltiples
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        logger.info(
            module="input_sanitizer",
            action="sanitize_phone",
            message="Número de teléfono sanitizado exitosamente",
            data={"original_phone": phone, "sanitized_phone": sanitized}
        )
        
        return sanitized
    
    def deep_sanitize(self, data: Any) -> Any:
        """Sanitiza recursivamente cualquier estructura de datos."""
        if isinstance(data, str):
            return self.sanitize_string(data)
        elif isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                safe_key = key if isinstance(key, str) else str(key)
                sanitized[self.sanitize_sql_identifier(safe_key)] = self.deep_sanitize(value)
            return sanitized
        elif isinstance(data, list):
            return [self.deep_sanitize(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self.deep_sanitize(item) for item in data)
        else:
            # Para tipos primitivos, devolver tal cual
            return data


# Instancia global del sanitizador de entradas
input_sanitizer = InputSanitizer()