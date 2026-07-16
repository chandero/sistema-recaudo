#!/usr/bin/env python3
"""
Script temporal para limpiar los campos de resolución de todas las obligaciones en la base de datos.
Este script modifica la configuración para permitir escritura en la base de datos SQLite.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio backend al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.models.obligation import Obligation
from sqlmodel import create_engine, SQLModel
import logging

# Configurar logging básico para evitar problemas
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar configuración para obtener la URL de la base de datos
from app.core.config import settings


def clean_obligation_resolution_fields():
    """
    Limpia los campos de resolución de todas las obligaciones en la base de datos.
    """
    # Modificar temporalmente la configuración para permitir escritura
    db_url = settings.DATABASE_URL
    
    # Si es SQLite, intentar abrir con permisos de escritura
    if db_url.startswith("sqlite:///"):
        # Extraer la ruta del archivo
        db_path = db_url.replace("sqlite:///", "")
        logger.info(f"Intentando abrir base de datos SQLite: {db_path}")
        
        # Crear engine con configuración específica para SQLite
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={
                "check_same_thread": False,
                "timeout": 20  # Aumentar timeout para operaciones de escritura
            }
        )
    else:
        engine = create_engine(db_url)
    
    logger.info("Iniciando proceso de limpieza de campos de resolución en obligaciones...")
    logger.info(f"Conectando a la base de datos: {db_url}")
    
    try:
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
            
            # Realizar la actualización campo por campo para evitar problemas de permisos
            # Primero seleccionamos los IDs para evitar mantener el cursor abierto durante la actualización
            obligation_ids = [ob.id for ob in session.query(Obligation.id).all()]
            total_to_update = len(obligation_ids)
            
            logger.info(f"Identificados {total_to_update} registros para actualizar...")
            
            # Actualizar cada registro individualmente
            updated_count = 0
            for i, obl_id in enumerate(obligation_ids):
                try:
                    obligation = session.get(Obligation, obl_id)
                    if obligation:
                        # Guardar valores anteriores para verificar si había datos
                        had_resolution_data = (
                            obligation.resolution_number is not None or
                            obligation.resolution_year is not None or
                            obligation.resolution_date is not None or
                            obligation.radicado_number is not None
                        )
                        
                        # Limpiar los campos
                        obligation.resolution_number = None
                        obligation.resolution_year = None
                        obligation.resolution_date = None
                        obligation.radicado_number = None
                        obligation.resolution_assigned_at = None
                        obligation.resolution_observations = None
                        
                        if had_resolution_data:
                            updated_count += 1
                            
                        # Commit cada cierto número de registros para evitar locks prolongados
                        if (i + 1) % 100 == 0:
                            session.commit()
                            logger.info(f"Progreso: {i + 1}/{total_to_update} registros procesados...")
                            
                except Exception as e:
                    logger.error(f"Error actualizando obligación ID {obl_id}: {str(e)}")
                    session.rollback()
                    continue
            
            # Hacer commit final
            try:
                session.commit()
                logger.info(f"Commit final realizado. Total actualizados: {updated_count}")
            except Exception as e:
                logger.error(f"Error en commit final: {str(e)}")
                session.rollback()
                raise
                
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
        logger.error(f"Error durante la limpieza de campos de resolución: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Ejecutando script de limpieza temporal...")
    clean_obligation_resolution_fields()
    logger.info("Proceso de limpieza de campos de resolución finalizado.")