#!/usr/bin/env python3
"""
Script para limpiar los campos de resolución de todas las obligaciones en la base de datos.
Este script está diseñado para ejecutarse en el servidor remoto después del despliegue.
Campos a limpiar:
- resolution_number (número de resolución)
- resolution_year (año de resolución)
- resolution_date (fecha de resolución)
- radicado_number (número de radicado)
- resolution_assigned_at (fecha de asignación de resolución)
- resolution_observations (observaciones de resolución)
"""

import sys
import os
from pathlib import Path

# Agregar el directorio de la aplicación al path para importar módulos
sys.path.insert(0, '/opt/cyberrit/backend')

from sqlalchemy.orm import Session
from sqlmodel import create_engine
from app.models.obligation import Obligation
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Usar la ubicación estándar de la base de datos en el servidor
DATABASE_URL = "sqlite:////opt/riap/db/cartera.db"


def clean_obligation_resolution_fields():
    """
    Limpia los campos de resolución de todas las obligaciones en la base de datos.
    """
    logger.info("Iniciando proceso de limpieza de campos de resolución en obligaciones...")
    logger.info(f"Conectando a la base de datos: {DATABASE_URL}")
    
    try:
        # Crear engine para la base de datos
        engine = create_engine(
            DATABASE_URL,
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # Aumentar timeout para operaciones de escritura
            }
        )
        
        # Obtener sesión de base de datos
        with Session(engine) as session:
            # Contar obligaciones antes de la limpieza
            total_obligations_before = session.query(Obligation).count()
            logger.info(f"Número total de obligaciones antes de la limpieza: {total_obligations_before}")
            
            # Contar obligaciones que tienen campos de resolución antes de la limpieza
            obligations_with_resolution = session.query(Obligation).filter(
                Obligation.resolution_number.isnot(None) |
                Obligation.resolution_year.isnot(None) |
                Obligation.resolution_date.isnot(None) |
                Obligation.radicado_number.isnot(None)
            ).count()
            logger.info(f"Número de obligaciones con campos de resolución antes de la limpieza: {obligations_with_resolution}")
            
            # Actualizar todos los registros de obligaciones para limpiar los campos de resolución
            updated_count = session.query(Obligation).update({
                Obligation.resolution_number: None,
                Obligation.resolution_year: None,
                Obligation.resolution_date: None,
                Obligation.radicado_number: None,
                Obligation.resolution_assigned_at: None,
                Obligation.resolution_observations: None
            })
            
            # Confirmar cambios
            session.commit()
            
            logger.info(f"Se han limpiado los campos de resolución de {updated_count} obligaciones.")
            
            # Contar obligaciones que tienen campos de resolución después de la limpieza
            obligations_with_resolution_after = session.query(Obligation).filter(
                Obligation.resolution_number.isnot(None) |
                Obligation.resolution_year.isnot(None) |
                Obligation.resolution_date.isnot(None) |
                Obligation.radicado_number.isnot(None)
            ).count()
            logger.info(f"Número de obligaciones con campos de resolución después de la limpieza: {obligations_with_resolution_after}")
            
            if obligations_with_resolution_after == 0:
                logger.info("✅ Todos los campos de resolución han sido limpiados exitosamente.")
            else:
                logger.warning(f"⚠️  Quedan {obligations_with_resolution_after} obligaciones con campos de resolución sin limpiar.")
                
            logger.info("✅ Proceso de limpieza completado exitosamente.")
                
    except Exception as e:
        logger.error(f"Error durante la limpieza de campos de resolución: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Ejecutando script de limpieza en el servidor remoto...")
    clean_obligation_resolution_fields()
    logger.info("Proceso de limpieza de campos de resolución finalizado.")