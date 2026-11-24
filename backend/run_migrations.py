#!/usr/bin/env python3
"""
Script de migración para despliegues en producción (SQLite).

La base objetivo se resuelve en este orden:
  1. DATABASE_PATH (compatibilidad con despliegues anteriores)
  2. DATABASE_URL (la variable que realmente lee app/core/config.py)
  3. La configuración de la propia aplicación (app.core.config.settings)
  4. /opt/cyberrit/backend/test.db

El punto 3 existe porque dentro del contenedor el código está montado en /app:
las rutas del servidor (/opt/cyberrit/...) no existen allí, y solo la aplicación
sabe qué base está usando de verdad.

Este script:
1. Agrega columnas faltantes en tablas existentes (ALTER TABLE ADD COLUMN).
2. Crea tablas nuevas si no existen (CREATE TABLE IF NOT EXISTS).
3. NO borra datos existentes.
4. NO modifica la tabla alembic_version: convive con Alembic pero no la reemplaza.
"""

import os
import sys
import sqlite3
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ruta histórica de la base activa en el servidor de producción
DEFAULT_DB_PATH = "/opt/cyberrit/backend/test.db"

# Alternativas conocidas, usadas solo si la ruta resuelta no existe
RUTAS_ALTERNATIVAS = [
    DEFAULT_DB_PATH,
    "/opt/riap/db/cartera.db",
]


def _ruta_desde_url(url: str) -> Optional[str]:
    """Extrae la ruta de archivo de una URL sqlite (relativa o absoluta)."""
    for prefijo in ("sqlite+aiosqlite:///", "sqlite:///"):
        if url.startswith(prefijo):
            return url[len(prefijo):] or None
    return None


def _ruta_desde_aplicacion() -> Optional[str]:
    """Lee la base que va a usar el backend importando su propia configuración.

    Dentro del contenedor no se exporta DATABASE_URL y el working directory es
    /app, por lo que la aplicación resuelve sqlite:///./test.db. Sin este paso el
    script caía en la ruta por defecto del servidor (inexistente dentro del contenedor)
    y terminaba aplicando el ALTER TABLE sobre /opt/riap/db/cartera.db, una base que
    ya no se monta: la base activa se quedaba sin esquema nuevo.
    """
    try:
        from app.core.config import settings
    except Exception:
        # Se ejecuta fuera del entorno de la aplicación (host): no hay configuración
        # que consultar, así que se sigue el orden histórico.
        return None
    return _ruta_desde_url(str(settings.DATABASE_URL))


def resolver_ruta_bd() -> Tuple[str, str, bool]:
    """Devuelve (ruta, origen, estricta) de la base que se va a migrar.

    estricta=True indica que la ruta salió de la configuración de la aplicación: no
    se buscan rutas alternativas, porque migrar otra base dejaría la activa sin las
    columnas que el código nuevo espera.
    """
    explicita = os.environ.get("DATABASE_PATH")
    if explicita:
        return explicita, "DATABASE_PATH", False

    en_ruta = _ruta_desde_url(os.environ.get("DATABASE_URL", ""))
    if en_ruta:
        return en_ruta, "DATABASE_URL", False

    desde_aplicacion = _ruta_desde_aplicacion()
    if desde_aplicacion:
        return desde_aplicacion, "configuración de la aplicación", True

    return DEFAULT_DB_PATH, "ruta por defecto", False

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
    # Fechas del Auto de Archivo y la Constancia Secretarial.
    # Equivale a la migración Alembic 009_fechas_documentos.
    "obligations": [
        ("paid_date", "DATE"),
        ("notification_date", "DATE"),
        ("executory_date", "DATE"),
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

        # Alembic y este script conviven: si la base nunca se stampó, "alembic upgrade"
        # desde cero chocaría contra las tablas que create_all ya generó.
        if "alembic_version" not in existing_tables:
            logger.warning(
                "La base no tiene tabla alembic_version: su esquema viene de "
                "init_db()/create_all y de este script, no de las revisiones de Alembic. "
                "Antes de usar 'alembic upgrade head' hay que stampar la versión alcanzada."
            )

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

    db_path, origen, estricta = resolver_ruta_bd()
    db_path = os.path.abspath(db_path)
    logger.info(f"Ruta resuelta desde {origen}: {db_path}")

    # Si la ruta no existe, solo se buscan alternativas cuando la fuente fue una
    # variable de entorno o el valor por defecto del servidor.
    if not os.path.exists(db_path):
        if estricta:
            logger.error(
                f"La base que usa la aplicación no existe en {db_path}. Se aborta sin "
                "probar rutas alternativas: migrar una base distinta dejaría la activa "
                "sin esquema nuevo y el backend fallaría al leer las columnas nuevas."
            )
            return False
        for alt in RUTAS_ALTERNATIVAS:
            if os.path.exists(alt):
                logger.warning(
                    f"{db_path} no existe; se usará la alternativa {alt}. "
                    "Verifica DATABASE_URL antes de continuar: migrar la base equivocada "
                    "deja la base activa sin esquema nuevo."
                )
                db_path = alt
                break
        else:
            logger.error("No se encontró ninguna base de datos")
            return False

    return run_migrations(db_path)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
