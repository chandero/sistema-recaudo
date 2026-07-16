#!/usr/bin/env python3
"""
Script para limpiar los campos de resolución de las obligaciones y desplegar la aplicación en el servidor remoto.
Este script combina ambas operaciones en un solo flujo.
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rutas importantes
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
CLEAN_SCRIPT = BACKEND_DIR / "clean_obligations_resolution_fields.py"
DEPLOY_SCRIPT = PROJECT_ROOT / "deploy_to_server.sh"


def run_clean_database():
    """
    Ejecuta el script para limpiar los campos de resolución en la base de datos.
    """
    logger.info("🔄 Iniciando limpieza de campos de resolución en la base de datos...")
    
    try:
        # Ejecutar el script de limpieza
        result = subprocess.run([
            sys.executable, str(CLEAN_SCRIPT)
        ], capture_output=True, text=True, cwd=BACKEND_DIR)
        
        if result.returncode == 0:
            logger.info("✅ Limpieza de campos de resolución completada exitosamente.")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"❌ Error en la limpieza de campos de resolución:")
            logger.error(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al ejecutar el script de limpieza: {str(e)}")
        return False


def run_deployment():
    """
    Ejecuta el script de despliegue al servidor remoto.
    """
    logger.info("🔄 Iniciando despliegue en el servidor remoto...")
    
    try:
        # Ejecutar el script de despliegue
        result = subprocess.run([
            str(DEPLOY_SCRIPT)
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logger.info("✅ Despliegue en servidor remoto completado exitosamente.")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"❌ Error en el despliegue:")
            logger.error(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al ejecutar el script de despliegue: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta la limpieza y el despliegue.
    """
    logger.info("🚀 Iniciando proceso de limpieza y despliegue...")
    
    # Verificar que los scripts existen
    if not CLEAN_SCRIPT.exists():
        logger.error(f"❌ El script de limpieza no existe: {CLEAN_SCRIPT}")
        return False
        
    if not DEPLOY_SCRIPT.exists():
        logger.error(f"❌ El script de despliegue no existe: {DEPLOY_SCRIPT}")
        return False
    
    # Hacer el script de despliegue ejecutable
    os.chmod(DEPLOY_SCRIPT, 0o755)
    
    # Ejecutar limpieza de base de datos
    if not run_clean_database():
        logger.error("❌ Se detuvo el proceso debido a un error en la limpieza de la base de datos.")
        return False
    
    logger.info("✅ Limpieza de base de datos completada. Continuando con el despliegue...")
    
    # Ejecutar despliegue
    if not run_deployment():
        logger.error("❌ Se detuvo el proceso debido a un error en el despliegue.")
        return False
    
    logger.info("🎉 ¡Proceso de limpieza y despliegue completado exitosamente!")
    logger.info("")
    logger.info("📋 Resumen:")
    logger.info("   1. Campos de resolución limpiados de todas las obligaciones")
    logger.info("   2. Aplicación desplegada en: /opt/cyberrit")
    logger.info("   3. Base de datos copiada en: /opt/riap/db")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)