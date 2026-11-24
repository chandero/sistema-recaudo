#!/usr/bin/env python3
"""
Script de migración para despliegues en producción (SQLite).
Target: /opt/cyberrit/backend/test.db (base de datos activa del backend).

Este script:
1. Agrega columnas faltantes en tablas existentes (ALTER TABLE ADD COLUMN).
2. Crea tablas nuevas si no existen (CREATE TABLE IF NOT EXISTS).
3. NO borra datos existentes.
4. NO modifica la tabla alembic_version (el backend usa init_db/create_all).
"""

import os
import sys
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ruta de la base de datos activa en el servidor de producción
DEFAULT_DB_PATH = "/opt/cyberrit/backend/test.db"

# ─────────────────────────────────────────────────────────────
# Definición de columnas esperadas por tabla
# (solo tablas que ya existían antes de esta actualización)
# ─────────────────────────────────────────────────────────────
EXPECTED_COLUMNS = {
    "tenants": [
        ("address", "VARCHAR(500)"),
        ("city", "VARCHAR(100)"),
        ("department", "VARCHAR(100)"),
    ],
    # Las demás tablas existentes ya tienen todas sus columnas correctas.
    # Si en el futuro se agregan columnas a modelos existentes, añadir aquí.
}

# ─────────────────────────────────────────────────────────────
# Tablas nuevas que podrían no existir aún.
# init_db() del backend las crea automáticamente con create_all(),
# pero las creamos aquí por seguridad antes del restart.
# ─────────────────────────────────────────────────────────────
NEW_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS process_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        process_id INTEGER NOT NULL REFERENCES cobro_processes(id),
        user_id INTEGER REFERENCES users(id),
        content TEXT NOT NULL,
        is_pinned BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS process_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        process_number_prefix VARCHAR(10),
        process_number_padding INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payment_agreements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        process_id INTEGER NOT NULL REFERENCES cobro_processes(id),
        client_id INTEGER NOT NULL REFERENCES clients(id),
        total_amount FLOAT NOT NULL,
        number_of_installments INTEGER NOT NULL DEFAULT 1,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        start_date DATETIME,
        end_date DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agreement_installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agreement_id INTEGER NOT NULL REFERENCES payment_agreements(id),
        installment_number INTEGER NOT NULL,
        amount FLOAT NOT NULL,
        due_date DATETIME NOT NULL,
        paid_amount FLOAT DEFAULT 0,
        paid_at DATETIME,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        notification_type VARCHAR(50) DEFAULT 'info',
        is_read BOOLEAN DEFAULT 0,
        link VARCHAR(500),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


def get_existing_columns(cursor, table_name):
    """Retorna un set con los nombres de columnas de una tabla."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def get_existing_tables(cursor):
    """Retorna un set con los nombres de tablas existentes."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return {row[0] for row in cursor.fetchall()}


def run_migrations(db_path: str) -> bool:
    """Ejecuta las migraciones pendientes sobre la base de datos SQLite."""
    logger.info(f"Base de datos objetivo: {db_path}")

    if not os.path.exists(db_path):
        logger.error(f"La base de datos NO existe: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        existing_tables = get_existing_tables(cursor)
        logger.info(f"Tablas existentes: {sorted(existing_tables)}")

        changes_made = 0

        # ── 1. Agregar columnas faltantes en tablas existentes ──
        for table_name, columns in EXPECTED_COLUMNS.items():
            if table_name not in existing_tables:
                logger.warning(f"Tabla '{table_name}' no existe, saltando columnas")
                continue

            existing_cols = get_existing_columns(cursor, table_name)
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    logger.info(f"  + Columna '{col_name}' en '{table_name}': {sql}")
                    cursor.execute(sql)
                    changes_made += 1
                else:
                    logger.debug(f"  = Columna '{col_name}' ya existe en '{table_name}'")

        if changes_made > 0:
            conn.commit()
            logger.info(f"✅ {changes_made} columna(s) agregada(s)")
        else:
            logger.info("✅ No faltan columnas en tablas existentes")

        # ── 2. Crear tablas nuevas ──
        new_tables_created = 0
        for sql in NEW_TABLES:
            # Extraer nombre de tabla del SQL
            table_name = sql.split("IF NOT EXISTS")[1].strip().split("(")[0].strip()
            if table_name not in existing_tables:
                logger.info(f"  + Creando tabla '{table_name}'...")
                cursor.execute(sql)
                new_tables_created += 1
            else:
                logger.debug(f"  = Tabla '{table_name}' ya existe")

        if new_tables_created > 0:
            conn.commit()
            logger.info(f"✅ {new_tables_created} tabla(s) nueva(s) creada(s)")
        else:
            logger.info("✅ No faltan tablas nuevas")

        # ── 3. Verificación final ──
        final_tables = get_existing_tables(cursor)
        logger.info(f"Tablas finales: {sorted(final_tables)}")

        for table_name in EXPECTED_COLUMNS:
            if table_name in final_tables:
                cols = get_existing_columns(cursor, table_name)
                expected = {c[0] for c in EXPECTED_COLUMNS[table_name]}
                missing = expected - cols
                if missing:
                    logger.error(f"⚠️  Columnas aún faltantes en '{table_name}': {missing}")

        conn.close()
        total_changes = changes_made + new_tables_created
        if total_changes > 0:
            logger.info(f"🎉 Migración completada: {total_changes} cambio(s) aplicado(s)")
        else:
            logger.info("🎉 Base de datos ya estaba actualizada, no se requirieron cambios")
        return True

    except sqlite3.OperationalError as e:
        logger.error(f"Error de SQLite: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False


def main():
    logger.info("🚀 Iniciando migración de base de datos para producción...")

    # Determinar ruta de la BD
    db_path = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

    # Si la ruta por defecto no existe, buscar alternativas
    if not os.path.exists(db_path):
        alternatives = [
            "/opt/cyberrit/backend/test.db",
            "/opt/riap/db/cartera.db",
        ]
        for alt in alternatives:
            if os.path.exists(alt):
                db_path = alt
                logger.info(f"Usando base de datos alternativa: {db_path}")
                break
        else:
            logger.error("No se encontró ninguna base de datos")
            return False

    return run_migrations(db_path)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
