#!/usr/bin/env python3
"""
Script para ejecutar migraciones de base de datos necesarias en despliegues posteriores.
Este script verifica si hay migraciones pendientes y las aplica si es necesario.
"""

import os
import sys
from pathlib import Path
import logging
import sqlite3

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_sqlite_migrations(db_path: str) -> bool:
    """
    Ejecuta migraciones manuales para SQLite usando SQL directo.
    """
    logger.info(f"Verificando base de datos: {db_path}")
    
    try:
        # Verificar si la base de datos existe
        if not os.path.exists(db_path):
            logger.error(f"La base de datos no existe: {db_path}")
            return False
            
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla tenants tiene las columnas nuevas
        cursor.execute("PRAGMA table_info(tenants)")
        columns = {col[1] for col in cursor.fetchall()}
        
        logger.info(f"Columnas actuales en tabla tenants: {columns}")
        
        # Agregar columna city si no existe
        if 'city' not in columns:
            logger.info("Agregando columna 'city' a la tabla tenants...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN city VARCHAR(100)")
            conn.commit()
            logger.info("✅ Columna 'city' agregada exitosamente")
        else:
            logger.info("Columna 'city' ya existe")
        
        # Agregar columna department si no existe
        if 'department' not in columns:
            logger.info("Agregando columna 'department' a la tabla tenants...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN department VARCHAR(100)")
            conn.commit()
            logger.info("✅ Columna 'department' agregada exitosamente")
        else:
            logger.info("Columna 'department' ya existe")
        
        # Verificar tabla alembic_version
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if not cursor.fetchone():
            logger.info("Creando tabla alembic_version...")
            cursor.execute("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL
                )
            """)
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('d6276b05fcf1')")
            conn.commit()
            logger.info("✅ Tabla alembic_version creada y actualizada")
        else:
            # Verificar versión actual
            cursor.execute("SELECT * FROM alembic_version")
            current_version = cursor.fetchone()
            logger.info(f"Versión actual de alembic_version: {current_version}")
            
            if current_version and current_version[0] != 'd6276b05fcf1':
                logger.info("Actualizando versión de alembic_version...")
                cursor.execute("UPDATE alembic_version SET version_num = 'd6276b05fcf1'")
                conn.commit()
                logger.info("✅ Versión de alembic_version actualizada")
            else:
                logger.info("Versión de alembic_version correcta")
        
        # Verificar las columnas finales
        cursor.execute("PRAGMA table_info(tenants)")
        columns = {col[1] for col in cursor.fetchall()}
        logger.info(f"Columnas finales en tabla tenants: {columns}")
        
        conn.close()
        logger.info("✅ Migraciones SQLite completadas exitosamente.")
        return True
        
    except sqlite3.OperationalError as e:
        logger.error(f"Error de SQLite: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta el proceso de migración.
    """
    logger.info("🚀 Iniciando proceso de migración de base de datos...")
    
    # Determinar la ruta de la base de datos
    # Primero intentar desde variables de entorno
    db_path = os.getenv("DATABASE_PATH", "/opt/riap/db/cartera.db")
    
    # Si no existe, buscar en directorios comunes
    if not os.path.exists(db_path):
        possible_paths = [
            "/opt/riap/db/cartera.db",
            "/opt/cyberrit/backend/test.db",
            "test.db",
            "./test.db"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                logger.info(f"Base de datos encontrada en: {db_path}")
                break
        else:
            logger.error("No se encontró ninguna base de datos. Rutas intentadas:")
            for path in possible_paths:
                logger.error(f"  - {path}")
            return False
    
    # Ejecutar migraciones SQLite
    return run_sqlite_migrations(db_path)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
