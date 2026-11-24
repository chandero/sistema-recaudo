#!/bin/bash
# Script para desplegar la aplicación en el servidor remoto root@giron.tiksgroup.co
# El backend corre en Docker con volume mount (./backend:/app), por lo que tras
# copiar el código es necesario reiniciar el contenedor para recargar la aplicación.
# El frontend DEBE ser reconstruido (docker compose build frontend).
#
# IMPORTANTE:
#   - NO sobrescribe docker-compose.yml ni .env del servidor
#   - NO sobrescribe la configuración de nginx del servidor
#   - NO borra la base de datos (respalda todos los *.db antes de sincronizar)
#   - Solo aplica migraciones incrementales (ALTER TABLE, CREATE TABLE IF NOT EXISTS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_HOST="${REMOTE_HOST:-root@giron.tiksgroup.co}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_tmsoft}"
LOCAL_PROJECT_PATH="${LOCAL_PROJECT_PATH:-$SCRIPT_DIR}"
REMOTE_APP_PATH="${REMOTE_APP_PATH:-/opt/cyberrit}"
SSH="ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=10 $REMOTE_HOST"

echo "🚀 Iniciando proceso de despliegue en el servidor (frontend + backend)."
echo "   Origen : $LOCAL_PROJECT_PATH"
echo "   Destino: $REMOTE_HOST:$REMOTE_APP_PATH"

# ── 0. Version local que se despliega ──
if [ -d "$LOCAL_PROJECT_PATH/.git" ]; then
    cd "$LOCAL_PROJECT_PATH"
    GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    GIT_SHA="$(git rev-parse --short HEAD)"
    if [ -n "$(git status --porcelain)" ]; then
        echo "❌ Hay cambios sin commitear: el despliegue no sería reproducible."
        exit 1
    fi
    echo "🌿 Rama: $GIT_BRANCH @ $GIT_SHA"
else
    GIT_BRANCH="desconocida"
    GIT_SHA="desconocida"
fi

# ── 1. Verificar conexión SSH ──
echo "🔗 Verificando conexión SSH..."
$SSH "echo '✅ Conexión OK'"

# ── 2. Backup de la base de datos antes de cualquier cambio ──
echo "💾 Haciendo backup de la base de datos..."
$SSH "
    set -e
    BACKUP_DIR=$REMOTE_APP_PATH/backups
    mkdir -p \$BACKUP_DIR
    SELLOS=\$(date +%Y%m%d-%H%M%S)
    for db in $REMOTE_APP_PATH/backend/*.db $REMOTE_APP_PATH/*.db; do
        [ -f \"\$db\" ] || continue
        nombre=\$(basename \"\$db\")
        destino=\$BACKUP_DIR/\${nombre%.db}-deploy-\$SELLOS.db
        cp -a \"\$db\" \"\$destino\" && gzip -f \"\$destino\"
        echo \"  Backup: \$destino.gz\"
    done
    ls -1t \$BACKUP_DIR/*.db.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
    true
"

# ── 3. Sincronizar código (protegiendo configuración del servidor) ──
echo "📡 Copiando archivos actualizados..."
rsync -avz --delete \
    --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','.vscode','.idea','*.log','.venv','.qoder'} \
    --exclude={'*.db','*.db-journal','*.sqlite','*.sqlite3'} \
    --exclude={'docker-compose.yml','docker-compose.dev.yml','.env','.env.*'} \
    --exclude={'backend/app/uploads/generated/*','backend/logs/*','backend/test.db*','generados/*','backups/*','auditoria/*'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

echo "✅ Archivos sincronizados"

# ── 4. Copiar script de migraciones ──
echo "📡 Copiando run_migrations.py..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/backend/run_migrations.py" "$REMOTE_HOST:$REMOTE_APP_PATH/backend/run_migrations.py"

# ── 5. Establecer permisos (solo directorios y scripts ejecutables) ──
echo "🔐 Configurando permisos..."
$SSH "
    chown -R root:root $REMOTE_APP_PATH
    find $REMOTE_APP_PATH -type d -exec chmod 755 {} +
    find $REMOTE_APP_PATH -type f -not -path '*/uploads/*' -exec chmod 644 {} +
    find $REMOTE_APP_PATH -maxdepth 1 -name '*.sh' -exec chmod 755 {} +
    chmod 600 $REMOTE_APP_PATH/.env 2>/dev/null || true
"

# ── 6. Ejecutar migraciones de base de datos ──
echo "🏃 Ejecutando migraciones..."
$SSH "cd $REMOTE_APP_PATH && (docker compose exec -T backend python3 /app/run_migrations.py || /usr/bin/python3 backend/run_migrations.py)"

# ── 7. Reconstruir y reiniciar frontend (Docker) ──
echo "🐳 Reconstruyendo frontend Docker..."
$SSH "cd $REMOTE_APP_PATH && docker compose build frontend"

# ── 8. Reiniciar contenedores ──
echo "🔄 Reiniciando contenedores..."
$SSH "cd $REMOTE_APP_PATH && docker compose up -d --no-deps frontend"
$SSH "cd $REMOTE_APP_PATH && docker compose up -d backend && docker compose restart backend"

# ── 9. Verificar que el backend responde ──
echo "🔍 Verificando backend..."
HEALTH="FAIL"
for intento in 1 2 3 4 5 6; do
    sleep 5
    HEALTH="$(curl -s --max-time 10 http://127.0.0.1:8055/health 2>/dev/null || echo FAIL)"
    echo "$HEALTH" | grep -q "healthy" && break
    echo "   intento $intento: sin respuesta aún"
done

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Backend OK: $HEALTH"
else
    echo "❌ Backend no responde: $HEALTH"
    echo "   Revisar logs: ssh $REMOTE_HOST 'docker logs cartera_backend --tail 50'"
    echo "   Rollback: restaura el backup de $REMOTE_APP_PATH/backups y reinicia el backend"
    exit 1
fi

# ── 10. Recargar nginx ──
echo "🔄 Recargando nginx..."
$SSH "nginx -t && nginx -s reload"

# ── 11. Marcar despliegue con la version exacta ──
DEPLOYMENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REGISTRO="$DEPLOYMENT_TIMESTAMP | rama=$GIT_BRANCH | commit=$GIT_SHA | operador=$(whoami)@$(hostname)"
$SSH "echo '$REGISTRO' > $REMOTE_APP_PATH/.last_deployment"

echo ""
echo "============================================"
echo "✅ Despliegue completado!"
echo "   Aplicación: $REMOTE_APP_PATH"
echo "   Base de datos: revisa DATABASE_URL en $REMOTE_APP_PATH/.env"
echo "   Timestamp: $DEPLOYMENT_TIMESTAMP"
echo "   URL: https://giron.cyberrit.tiksgroup.co"
echo "============================================"
echo ""
echo "Pasos de verificación:"
echo "  1. docker logs cartera_backend --tail 20"
echo "  2. curl https://giron.cyberrit.tiksgroup.co/api/v1/dashboard/stats"
echo "  3. Verificar frontend en el navegador"
