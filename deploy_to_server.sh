#!/bin/bash
# Script para desplegar la aplicación en el servidor remoto root@giron.tiksgroup.co
# El backend corre en Docker con volume mount (./backend:/app), por lo que
# los cambios de código se detectan automáticamente por uvicorn --reload.
# El frontend DEBE ser reconstruido (docker compose build frontend).
#
# IMPORTANTE:
#   - NO sobrescribe docker-compose.yml ni .env del servidor
#   - NO sobrescribe la configuración de nginx del servidor
#   - NO borra la base de datos (/opt/cyberrit/backend/test.db)
#   - Solo aplica migraciones incrementales (ALTER TABLE, CREATE TABLE IF NOT EXISTS)

set -e

REMOTE_HOST="root@giron.tiksgroup.co"
SSH_KEY="/home/chandero/.ssh/id_ed25519"
LOCAL_PROJECT_PATH="/home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo"
REMOTE_APP_PATH="/opt/cyberrit"

echo "🚀 Iniciando proceso de despliegue..."

# ── 1. Verificar conexión SSH ──
echo "🔗 Verificando conexión SSH..."
ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo '✅ Conexión OK'"

# ── 2. Backup de la base de datos antes de cualquier cambio ──
echo "💾 Haciendo backup de la base de datos..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "
    BACKUP_DIR=/opt/cyberrit/backups
    mkdir -p \$BACKUP_DIR
    BACKUP_FILE=\$BACKUP_DIR/test-db-pre-deploy-\$(date +%Y%m%d-%H%M%S).db
    cp /opt/cyberrit/backend/test.db \$BACKUP_FILE
    echo \"Backup creado: \$BACKUP_FILE\"
    ls -lh \$BACKUP_FILE
"

# ── 3. Sincronizar código (protegiendo configuración del servidor) ──
echo "📡 Copiando archivos actualizados..."
rsync -avz --delete \
    --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','.vscode','.idea','*.log','.venv'} \
    --exclude={'*.db','*.sqlite','*.sqlite3'} \
    --exclude={'docker-compose.yml','.env','.env.*'} \
    --exclude={'backend/app/uploads/generated/*','backend/logs/*','generados/*','backups/*'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

echo "✅ Archivos sincronizados"

# ── 4. Copiar script de migraciones ──
echo "📡 Copiando run_migrations.py..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/backend/run_migrations.py" "$REMOTE_HOST:$REMOTE_APP_PATH/backend/run_migrations.py"

# ── 5. Establecer permisos ──
echo "🔐 Configurando permisos..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_APP_PATH && chmod -R 755 $REMOTE_APP_PATH"

# ── 6. Ejecutar migraciones de base de datos ──
echo "🏃 Ejecutando migraciones..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && /usr/bin/python3.9 backend/run_migrations.py"

# ── 7. Reconstruir y reiniciar frontend (Docker) ──
echo "🐳 Reconstruyendo frontend Docker..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && docker compose build frontend"

# ── 8. Reiniciar contenedores ──
echo "🔄 Reiniciando contenedores..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && docker compose up -d --no-deps frontend"
# El backend tiene volume mount y --reload, pero reiniciamos para asegurar init_db()
ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && docker compose restart backend"

# Esperar a que el backend esté listo
echo "⏳ Esperando a que el backend inicie..."
sleep 5

# ── 9. Verificar que el backend responde ──
echo "🔍 Verificando backend..."
HEALTH=$(curl -s --max-time 10 http://127.0.0.1:8055/health 2>/dev/null || echo "FAIL")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Backend OK: $HEALTH"
else
    echo "⚠️  Backend no responde correctamente: $HEALTH"
    echo "   Revisar logs: docker logs cartera_backend --tail 30"
fi

# ── 10. Recargar nginx ──
echo "🔄 Recargando nginx..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -t && nginx -s reload"

# ── 11. Marcar despliegue ──
DEPLOYMENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i "$SSH_KEY" "$REMOTE_HOST" "echo '$DEPLOYMENT_TIMESTAMP' > $REMOTE_APP_PATH/.last_deployment"

echo ""
echo "============================================"
echo "✅ Despliegue completado!"
echo "   Aplicación: $REMOTE_APP_PATH"
echo "   Base de datos: /opt/cyberrit/backend/test.db"
echo "   Timestamp: $DEPLOYMENT_TIMESTAMP"
echo "   URL: https://giron.cyberrit.tiksgroup.co"
echo "============================================"
echo ""
echo "Pasos de verificación:"
echo "  1. docker logs cartera_backend --tail 20"
echo "  2. curl https://giron.cyberrit.tiksgroup.co/api/v1/dashboard/stats"
echo "  3. Verificar frontend en el navegador"
