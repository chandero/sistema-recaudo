#!/usr/bin/env python3
"""
Script para limpiar los campos de resolución de todas las obligaciones en la base de datos.
Campos a limpiar:
- resolution_number (número de resolución)
- resolution_year (año de resolución)
- resolution_date (fecha de resolución)
- radicado_number (número de radicado)
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import engine, get_session
from app.models.obligation import Obligation
from app.repositories.obligation import ObligationRepository
from app.core.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_obligation_resolution_fields():
    """
    Limpia los campos de resolución de todas las obligaciones en la base de datos.
    """
    logger.info("Iniciando proceso de limpieza de campos de resolución en obligaciones...")
    
    try:
        # Obtener sesión de base de datos
        session_generator = get_session()
        session: Session = next(session_generator)
        
        try:
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
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error durante la limpieza de campos de resolución: {str(e)}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error general en el proceso de limpieza: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info(f"Configuración de base de datos: {settings.DATABASE_URL}")
    clean_obligation_resolution_fields()
    logger.info("Proceso de limpieza de campos de resolución finalizado.")