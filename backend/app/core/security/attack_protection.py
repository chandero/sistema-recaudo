"""Módulo de protección contra ataques para el sistema de recaudo."""
import time
import hashlib
from typing import Optional, Dict, Any, List
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from app.core.logging.logger import get_logger


logger = get_logger(__name__)


class AttackProtection:
    """Clase para protección contra diversos tipos de ataques."""
    
    def __init__(self):
        # Almacenamiento para detección de ataques
        self.ip_request_counts = defaultdict(deque)  # Contador de solicitudes por IP
        self.ip_blocked = set()  # IPs bloqueadas temporalmente
        self.rate_limit_storage = {}  # Almacenamiento para rate limiting
        self.session_tokens = set()  # Tokens de sesión activos
        
        # Configuración de protección
        self.max_requests_per_minute = 60  # Límite de solicitudes por minuto
        self.max_request_size = 10 * 1024 * 1024  # 10MB máximo por solicitud
        self.block_duration = 300  # Duración del bloqueo en segundos (5 minutos)
        
    def check_rate_limit(self, request: Request) -> bool:
        """Verifica si una solicitud excede el límite de tasa."""
        client_ip = self._get_client_ip(request)
        
        if client_ip in self.ip_blocked:
            # Verificar si el bloqueo ha expirado
            block_time = self.rate_limit_storage.get(f"block_{client_ip}", 0)
            if time.time() - block_time > self.block_duration:
                self.ip_blocked.remove(client_ip)
                del self.rate_limit_storage[f"block_{client_ip}"]
            else:
                logger.warning(
                    module="attack_protection",
                    action="rate_limit_exceeded",
                    message=f"IP {client_ip} excedió el límite de tasa y está bloqueada",
                    data={"client_ip": client_ip, "blocked_until": block_time + self.block_duration}
                )
                return False
        
        now = time.time()
        minute_key = int(now // 60)
        
        # Limpiar solicitudes antiguas
        while self.ip_request_counts[client_ip] and self.ip_request_counts[client_ip][0] < now - 60:
            self.ip_request_counts[client_ip].popleft()
        
        # Verificar límite de solicitudes
        if len(self.ip_request_counts[client_ip]) >= self.max_requests_per_minute:
            # Bloquear IP
            self.ip_blocked.add(client_ip)
            self.rate_limit_storage[f"block_{client_ip}"] = now
            
            logger.warning(
                module="attack_protection",
                action="ip_blocked_rate_limit",
                message=f"IP {client_ip} bloqueada por exceder límite de tasa",
                data={"requests_per_minute": len(self.ip_request_counts[client_ip]), 
                      "max_allowed": self.max_requests_per_minute}
            )
            return False
        
        # Registrar solicitud
        self.ip_request_counts[client_ip].append(now)
        return True
    
    def check_request_size(self, request: Request) -> bool:
        """Verifica si el tamaño de la solicitud excede el límite."""
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(
                        module="attack_protection",
                        action="request_size_exceeded",
                        message=f"Solicitud excede el tamaño máximo permitido",
                        data={"size_bytes": size, "max_size_bytes": self.max_request_size}
                    )
                    return False
            return True
        except ValueError:
            # Si no se puede leer el content-length, dejar pasar
            return True
    
    def detect_sql_injection(self, data: str) -> bool:
        """Detecta posibles inyecciones SQL en los datos."""
        # Patrones comunes de inyección SQL
        sql_patterns = [
            r"(?i)(union\s+select|exec\s*\(|insert\s+into|drop\s+\w+|create\s+\w+|alter\s+\w+|delete\s+from)",
            r"(?i)(select\s+\*|from\s+\w+\s*;|--|/\*|\*/)",
            r"'(?:--|#|/\*|\*/)",
            r"(?i)(or\s+1\s*=\s*1|and\s+1\s*=\s*1)",
            r"(?i)(waitfor\s+delay|sleep\s*\()",
        ]
        
        for i, pattern in enumerate(sql_patterns):
            if data and re.search(pattern, data, re.IGNORECASE):
                logger.warning(
                    module="attack_protection",
                    action="sql_injection_detected",
                    message=f"Detectado posible intento de inyección SQL en patrón {i+1}",
                    data={"data_snippet": data[:50], "pattern_index": i}
                )
                return False
        
        return True
    
    def detect_xss_attack(self, data: str) -> bool:
        """Detecta posibles ataques XSS en los datos."""
        # Patrones comunes de XSS
        xss_patterns = [
            r"(?i)<script[^>]*>",
            r"(?i)</script>",
            r"(?i)<iframe[^>]*>",
            r"(?i)<object[^>]*>",
            r"(?i)<embed[^>]*>",
            r"(?i)<form[^>]*>",
            r"(?i)javascript:",
            r"(?i)vbscript:",
            r"(?i)on\w+\s*=",
            r"(?i)data:text/html",
        ]
        
        for i, pattern in enumerate(xss_patterns):
            if data and re.search(pattern, data, re.IGNORECASE):
                logger.warning(
                    module="attack_protection",
                    action="xss_attack_detected",
                    message=f"Detectado posible intento de XSS en patrón {i+1}",
                    data={"data_snippet": data[:50], "pattern_index": i}
                )
                return False
        
        return True
    
    def validate_input_data(self, data: Any) -> Dict[str, Any]:
        """Valida los datos de entrada para detectar posibles ataques."""
        validation_results = {
            "is_valid": True,
            "detected_attacks": [],
            "sanitized_data": data
        }
        
        if isinstance(data, str):
            # Verificar inyección SQL
            if not self.detect_sql_injection(data):
                validation_results["is_valid"] = False
                validation_results["detected_attacks"].append("SQL_INJECTION")
            
            # Verificar XSS
            if not self.detect_xss_attack(data):
                validation_results["is_valid"] = False
                validation_results["detected_attacks"].append("XSS")
            
            # Sanitizar si es necesario
            if not validation_results["is_valid"]:
                # Implementar sanitización básica
                import html
                sanitized = html.escape(data)
                validation_results["sanitized_data"] = sanitized
        
        elif isinstance(data, dict):
            # Recursivamente validar diccionarios
            sanitized_dict = {}
            for key, value in data.items():
                validated = self.validate_input_data(value)
                if not validated["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["detected_attacks"].extend(validated["detected_attacks"])
                sanitized_dict[key] = validated["sanitized_data"]
            validation_results["sanitized_data"] = sanitized_dict
        
        elif isinstance(data, list):
            # Recursivamente validar listas
            sanitized_list = []
            for item in data:
                validated = self.validate_input_data(item)
                if not validated["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["detected_attacks"].extend(validated["detected_attacks"])
                sanitized_list.append(validated["sanitized_data"])
            validation_results["sanitized_data"] = sanitized_list
        
        if not validation_results["is_valid"]:
            logger.warning(
                module="attack_protection",
                action="input_validation_failed",
                message="Detectadas posibles amenazas en los datos de entrada",
                data={"detected_attacks": validation_results["detected_attacks"]}
            )
        
        return validation_results
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP del cliente desde la solicitud."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        if hasattr(request, 'client') and request.client:
            return request.client.host or "unknown"
        
        return "unknown"
    
    def generate_csrf_token(self) -> str:
        """Genera un token CSRF seguro."""
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Almacenar token para validación posterior
        self.session_tokens.add(token)
        
        logger.info(
            module="attack_protection",
            action="csrf_token_generated",
            message="Token CSRF generado exitosamente",
            data={"token_length": len(token)}
        )
        
        return token
    
    def validate_csrf_token(self, token: str) -> bool:
        """Valida un token CSRF."""
        is_valid = token in self.session_tokens
        
        if is_valid:
            # Remover token después de usarlo (one-time use)
            self.session_tokens.discard(token)
        
        logger.info(
            module="attack_protection",
            action="csrf_token_validated",
            message=f"Token CSRF {'válido' if is_valid else 'inválido'}",
            data={"token_valid": is_valid}
        )
        
        return is_valid
    
    def detect_brute_force(self, identifier: str) -> bool:
        """Detecta posibles intentos de fuerza bruta."""
        # Esta es una implementación simple; en producción se debería usar Redis o DB
        key = f"bf_attempts_{identifier}"
        attempts = self.rate_limit_storage.get(key, 0)
        
        if attempts >= 5:  # 5 intentos fallidos
            logger.warning(
                module="attack_protection",
                action="brute_force_detected",
                message=f"Detectado posible intento de fuerza bruta para {identifier}",
                data={"attempts": attempts}
            )
            return True
        
        return False
    
    def record_failed_attempt(self, identifier: str):
        """Registra un intento fallido."""
        key = f"bf_attempts_{identifier}"
        current_attempts = self.rate_limit_storage.get(key, 0)
        self.rate_limit_storage[key] = current_attempts + 1
        
        logger.info(
            module="attack_protection",
            action="failed_attempt_recorded",
            message="Registrado intento fallido",
            data={"identifier": identifier, "current_attempts": current_attempts + 1}
        )
    
    def reset_failed_attempts(self, identifier: str):
        """Restablece los intentos fallidos."""
        key = f"bf_attempts_{identifier}"
        if key in self.rate_limit_storage:
            del self.rate_limit_storage[key]
        
        logger.info(
            module="attack_protection",
            action="failed_attempts_reset",
            message="Restablecidos intentos fallidos",
            data={"identifier": identifier}
        )


# Importar re acá para evitar problemas de importación circular
import re


# Instancia global de protección contra ataques
attack_protection = AttackProtection()