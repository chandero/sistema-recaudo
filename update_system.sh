#!/bin/bash
# Script simplificado para actualizar el sistema remoto
# Útil para despliegues rápidos de actualizaciones de código
#
# Diferencias con deploy_to_server.sh:
#   - deploy_to_server.sh: despliegue completo (backup, migraciones, rebuild frontend Docker)
#   - update_system.sh: actualización rápida (solo código + migraciones, sin rebuild frontend)
#
# NOTA: El frontend corre en Docker y debe ser reconstruido con:
#   ssh root@giron.tiksgroup.co "cd /opt/cyberrit && docker compose build frontend && docker compose up -d frontend"

set +e

REMOTE_HOST="root@giron.tiksgroup.co"
SSH_KEY="/home/chandero/.ssh/id_ed25519"
LOCAL_PROJECT_PATH="/home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo"
REMOTE_APP_PATH="/opt/cyberrit"

echo "🚀 Iniciando actualización rápida del sistema..."

# Verificar conexión SSH
echo "🔗 Verificando conexión SSH..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'Conexión exitosa'" > /dev/null 2>&1; then
    echo "✅ Conexión SSH exitosa"
else
    echo "❌ No se pudo conectar al servidor remoto."
    exit 1
fi

# Copiar archivos (protegiendo configuración del servidor)
echo "📡 Copiando archivos actualizados..."
rsync -avz --delete \
    --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','.vscode','.idea','*.log','.venv'} \
    --exclude={'*.db','*.sqlite','*.sqlite3'} \
    --exclude={'docker-compose.yml','.env','.env.*'} \
    --exclude={'backend/app/uploads/generated/*','backend/logs/*','generados/*','backups/*'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

RSYNC_EXIT_CODE=$?
if [ $RSYNC_EXIT_CODE -eq 0 ] || [ $RSYNC_EXIT_CODE -eq 23 ]; then
    echo "✅ Transferencia completada"
else
    echo "❌ Error en la transferencia: código $RSYNC_EXIT_CODE"
    exit $RSYNC_EXIT_CODE
fi

# Establecer permisos
echo "🔐 Configurando permisos..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_APP_PATH && chmod -R 755 $REMOTE_APP_PATH"

# Ejecutar migraciones
echo "🏃 Ejecutando migraciones..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && /usr/bin/python3.9 backend/run_migrations.py"

# Reiniciar backend (el volume mount detecta cambios, pero reiniciamos para init_db)
echo "🔄 Reiniciando backend..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && docker compose restart backend"

# Recargar nginx
echo "🔄 Recargando nginx..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -t && nginx -s reload"

# Marcar actualización
UPDATE_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i "$SSH_KEY" "$REMOTE_HOST" "echo '$UPDATE_TIMESTAMP' > $REMOTE_APP_PATH/.last_update"

echo ""
echo "✅ Actualización completada!"
echo "   Última actualización: $UPDATE_TIMESTAMP"
echo ""
echo "⚠️  Si cambiaste archivos del frontend, recuerda reconstruir el contenedor:"
echo "   ssh root@giron.tiksgroup.co 'cd /opt/cyberrit && docker compose build frontend && docker compose up -d frontend'"

set -e
