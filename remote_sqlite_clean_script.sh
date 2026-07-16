#!/bin/bash

# Script para limpiar campos de resolución en la base de datos SQLite del servidor remoto
echo "$(date): Ejecutando script de limpieza en el servidor remoto..."

echo "$(date): Iniciando proceso de limpieza de campos de resolución en obligaciones..."

DB_PATH="/opt/riap/db/cartera.db"

if [ ! -f "$DB_PATH" ]; then
    echo "$(date): ERROR - No se encontró la base de datos en $DB_PATH"
    exit 1
fi

echo "$(date): Base de datos encontrada: $DB_PATH"

# Contar obligaciones antes de la limpieza
COUNT_BEFORE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM obligations;")
echo "$(date): Número total de obligaciones antes de la limpieza: $COUNT_BEFORE"

# Contar obligaciones con campos de resolución antes de la limpieza
COUNT_WITH_RESOLUTION_BEFORE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM obligations WHERE resolution_number IS NOT NULL OR resolution_year IS NOT NULL OR resolution_date IS NOT NULL OR radicado_number IS NOT NULL OR resolution_assigned_at IS NOT NULL OR resolution_observations IS NOT NULL;")
echo "$(date): Número de obligaciones con campos de resolución antes de la limpieza: $COUNT_WITH_RESOLUTION_BEFORE"

echo "$(date): Iniciando limpieza de campos de resolución..."

# Limpiar los campos de resolución: resolution_number, resolution_year, resolution_date, radicado_number, resolution_assigned_at, resolution_observations
sqlite3 "$DB_PATH" << EOF
BEGIN TRANSACTION;

UPDATE obligations 
SET 
    resolution_number = NULL,
    resolution_year = NULL,
    resolution_date = NULL,
    radicado_number = NULL,
    resolution_assigned_at = NULL,
    resolution_observations = NULL;

COMMIT;
EOF

if [ $? -eq 0 ]; then
    echo "$(date): Campos de resolución limpiados exitosamente."
else
    echo "$(date): ERROR - Falló la limpieza de campos de resolución."
    exit 1
fi

# Contar obligaciones con campos de resolución después de la limpieza
COUNT_WITH_RESOLUTION_AFTER=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM obligations WHERE resolution_number IS NOT NULL OR resolution_year IS NOT NULL OR resolution_date IS NOT NULL OR radicado_number IS NOT NULL OR resolution_assigned_at IS NOT NULL OR resolution_observations IS NOT NULL;")
echo "$(date): Número de obligaciones con campos de resolución después de la limpieza: $COUNT_WITH_RESOLUTION_AFTER"

# Validación adicional
if [ "$COUNT_WITH_RESOLUTION_AFTER" -eq 0 ]; then
    echo "$(date): ✅ ¡Éxito! Todos los campos de resolución han sido eliminados correctamente."
else
    echo "$(date): ⚠️ Advertencia: Aún hay $COUNT_WITH_RESOLUTION_AFTER obligaciones con campos de resolución."
fi

echo "$(date): Limpieza de campos de resolución completada exitosamente."
echo "$(date): Total de obligaciones: $COUNT_BEFORE"
echo "$(date): Script de limpieza finalizado."