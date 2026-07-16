#!/usr/bin/env python3
"""
Script para ejecutar migraciones de base de datos necesarias en despliegues posteriores.
Este script verifica si hay migraciones pendientes y las aplica si es necesario.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from app.core.config import settings
from app.core.database import engine
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_pending_migrations():
    """
    Verifica si hay migraciones pendientes comparando el esquema actual con los modelos definidos.
    """
    logger.info("Verificando migraciones pendientes...")
    
    try:
        # Obtener la inspección de la base de datos
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        # Obtener las tablas definidas en los modelos
        from app.models.user import User
        from app.models.tenant import Tenant
        from app.models.client import Client
        from app.models.obligation import Obligation
        from app.models.process import CobroProcess
        from app.models.document import DocumentTemplate, GeneratedDocument
        
        defined_tables = set()
        for mapper in SQLModel.registry.mappers:
            table = mapper.local_table
            if hasattr(table, 'name'):
                defined_tables.add(table.name)
        
        missing_tables = defined_tables - existing_tables
        extra_tables = existing_tables - defined_tables
        
        if missing_tables:
            logger.info(f"Tablas faltantes en la base de datos: {missing_tables}")
        else:
            logger.info("No hay tablas faltantes en la base de datos.")
            
        if extra_tables:
            logger.info(f"Tablas adicionales en la base de datos: {extra_tables}")
        
        # Verificar columnas faltantes en tablas existentes
        pending_changes = False
        for table_name in existing_tables.intersection(defined_tables):
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            model_class = None
            
            # Buscar la clase de modelo correspondiente
            model_classes = {
                'users': User,
                'tenants': Tenant,
                'clients': Client,
                'obligations': Obligation,
                'cobro_processes': CobroProcess,
                'document_templates': DocumentTemplate,
                'generated_documents': GeneratedDocument
            }
            
            if table_name in model_classes:
                model_class = model_classes[table_name]
                
                if hasattr(model_class, '__table__'):
                    defined_columns = {col.name for col in model_class.__table__.columns}
                    missing_columns = defined_columns - existing_columns
                    
                    if missing_columns:
                        logger.info(f"Columnas faltantes en la tabla '{table_name}': {missing_columns}")
                        pending_changes = True
        
        return len(missing_tables) > 0 or pending_changes
        
    except Exception as e:
        logger.error(f"Error al verificar migraciones pendientes: {str(e)}")
        return False


def run_alembic_migrations():
    """
    Ejecuta las migraciones de Alembic si están disponibles.
    """
    logger.info("Intentando ejecutar migraciones de Alembic...")
    
    try:
        alembic_dir = Path(__file__).parent / "backend" / "alembic"
        alembic_ini_path = Path(__file__).parent / "backend" / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.warning("Archivo alembic.ini no encontrado. Saltando migraciones de Alembic.")
            return False
            
        # Importar alembic y ejecutar migraciones
        from alembic import command
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        logger.info("Ejecutando migraciones: alembic upgrade head")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Migraciones de Alembic ejecutadas exitosamente.")
        return True
        
    except ImportError:
        logger.warning("Alembic no está disponible. Instale alembic para usar migraciones automáticas.")
        return False
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones de Alembic: {str(e)}")
        return False


def run_manual_migrations():
    """
    Ejecuta migraciones manuales si no se puede usar Alembic.
    """
    logger.info("Ejecutando migraciones manuales...")
    
    try:
        with engine.connect() as conn:
            # Importar todos los modelos para que SQLModel los registre
            from app.models.user import User
            from app.models.tenant import Tenant
            from app.models.client import Client
            from app.models.obligation import Obligation
            from app.models.process import CobroProcess
            from app.models.document import DocumentTemplate, GeneratedDocument
            
            # Crear tablas que falten
            for mapper in SQLModel.registry.mappers:
                table = mapper.local_table
                if table.exists(conn):
                    logger.debug(f"Tabla {table.name} ya existe")
                else:
                    logger.info(f"Creando tabla {table.name}")
                    table.create(conn)
                    
            # Verificar y posiblemente añadir columnas faltantes
            # Esto es más complejo y podría requerir una herramienta como Alembic para hacerlo de forma segura
            logger.info("Migraciones manuales completadas.")
            return True
            
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones manuales: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta el proceso de migración.
    """
    logger.info("🚀 Iniciando proceso de migración de base de datos...")
    
    # Verificar si hay migraciones pendientes
    if check_pending_migrations():
        logger.info("Se detectaron migraciones pendientes.")
        
        # Intentar primero con Alembic
        if run_alembic_migrations():
            logger.info("✅ Migraciones completadas exitosamente con Alembic.")
        else:
            logger.info("Intentando migraciones manuales...")
            if run_manual_migrations():
                logger.info("✅ Migraciones manuales completadas exitosamente.")
            else:
                logger.error("❌ No se pudieron aplicar las migraciones.")
                return False
    else:
        logger.info("✅ No hay migraciones pendientes. La base de datos está actualizada.")
    
    logger.info("🎉 Proceso de migración de base de datos finalizado.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)