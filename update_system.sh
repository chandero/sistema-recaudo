#!/bin/bash

# Script simplificado para actualizar el sistema remoto
# Útil para despliegues rápidos de actualizaciones de código

# Temporarily disable exit on error for the whole script to prevent interruption during rsync
set +e

# Variables de configuración
REMOTE_HOST="root@giron.tiksgroup.co"
SSH_KEY="/home/chandero/.ssh/id_ed25519"
LOCAL_PROJECT_PATH="/home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo"
REMOTE_APP_PATH="/opt/cyberrit"

echo "🚀 Iniciando proceso de actualización del sistema remoto..."

# Verificar conexión SSH
echo "🔗 Verificando conexión SSH con $REMOTE_HOST..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'Conexión exitosa'" > /dev/null 2>&1; then
    echo "✅ Conexión SSH exitosa"
else
    echo "❌ No se pudo conectar al servidor remoto. Por favor, verifique la conexión y credenciales."
    exit 1
fi

# Construir el frontend localmente antes de subirlo
echo "🔨 Construyendo el frontend para producción..."
cd "$LOCAL_PROJECT_PATH/frontend"
npm install --silent
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Error al construir el frontend. Abortando actualización."
    exit 1
fi
echo "✅ Frontend construido exitosamente"

# Copiar archivos del proyecto al servidor remoto (excluyendo directorios innecesarios)
# Nota: Ya no excluimos 'dist' porque necesitamos el dist del frontend
echo "📡 Copiando archivos actualizados al servidor remoto..."
rsync -avz --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','.vscode','.idea','*.log','*.db','backend/app/uploads/generated/*','backend/logs/*','generados/*'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"
    
# Check the rsync exit code and report
RSYNC_EXIT_CODE=$?
if [ $RSYNC_EXIT_CODE -eq 0 ] || [ $RSYNC_EXIT_CODE -eq 23 ]; then
    echo "✅ Transferencia de archivos completada (con posibles advertencias manejables)"
else
    echo "❌ Error en la transferencia de archivos: código $RSYNC_EXIT_CODE"
    exit $RSYNC_EXIT_CODE
fi

# Establecer permisos adecuados en el servidor
echo "🔐 Configurando permisos en el servidor..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_APP_PATH && chmod -R 755 $REMOTE_APP_PATH"

# Ir al directorio remoto y ejecutar migraciones si es necesario
echo "🔄 Ejecutando migraciones en el servidor remoto..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && python run_migrations.py"

# Reiniciar servicios si es necesario (esto dependerá de la configuración específica del servidor)
echo "🔄 Reiniciando servicios si es necesario..."
# ssh -i "$SSH_KEY" "$REMOTE_HOST" "systemctl restart cyberrit-backend || true"
# ssh -i "$SSH_KEY" "$REMOTE_HOST" "systemctl restart cyberrit-frontend || true"

# Recargar configuración de nginx
echo "🔄 Recargando configuración de nginx..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -s reload || systemctl reload nginx || service nginx reload"

# Marcar que la actualización se completó
UPDATE_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i "$SSH_KEY" "$REMOTE_HOST" "echo '$UPDATE_TIMESTAMP' > $REMOTE_APP_PATH/.last_update"

echo ""
echo "✅ Actualización del sistema remoto completada exitosamente!"
echo "Ubicación de la aplicación: $REMOTE_APP_PATH"
echo "Última actualización: $UPDATE_TIMESTAMP"
echo ""
echo "Sugerencias para post-actualización:"
echo "1. Verificar que el servicio backend esté corriendo (puerto 8000)"
echo "2. Probar la conectividad a la aplicación en cyberrit.tiksgroup.co"
echo "3. Verificar que todas las funcionalidades críticas estén operativas"
echo ""

echo "🎉 ¡Actualización finalizada!"

# Re-enable exit on error if needed for subsequent operations
set -e