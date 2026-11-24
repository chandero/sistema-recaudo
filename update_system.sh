#!/bin/bash
# Actualización rápida del sistema en giron.tiksgroup.co (proyecto cyberrit).
#
#   ./update_system.sh              # despliegue interactivo (pide confirmación)
#   ./update_system.sh --dry-run    # muestra qué se enviaría, sin tocar el servidor
#   ./update_system.sh --yes        # sin preguntas (para automatizar)
#
# Diferencias con deploy_to_server.sh:
#   - deploy_to_server.sh: despliegue completo (backup, migraciones, rebuild del frontend)
#   - update_system.sh:    actualización de código + migraciones, sin reconstruir frontend
#
# Configuración por variables de entorno (tienen prioridad sobre los valores por defecto):
#   REMOTE_HOST, SSH_KEY, REMOTE_APP_PATH, LOCAL_PROJECT_PATH, CARTERA_DATA_DIR
#
# NOTA: el frontend corre en Docker y su dist va embebido en la imagen. Si cambiaste
# archivos de frontend, reconstruye:
#   ssh "$REMOTE_HOST" "cd $REMOTE_APP_PATH && docker compose build frontend && docker compose up -d frontend"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REMOTE_HOST="${REMOTE_HOST:-root@giron.tiksgroup.co}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_tmsoft}"
REMOTE_APP_PATH="${REMOTE_APP_PATH:-/opt/cyberrit}"
LOCAL_PROJECT_PATH="${LOCAL_PROJECT_PATH:-$SCRIPT_DIR}"
# Directorio de datos del servidor, fuera del árbol de código (ver docker-compose.yml)
CARTERA_DATA_DIR="${CARTERA_DATA_DIR:-/var/lib/cyberrit}"

DRY_RUN=0
ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --yes|-y)  ASSUME_YES=1 ;;
        *) echo "⚠️  Argumento desconocido: $arg"; exit 2 ;;
    esac
done

run_remote() {
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "  [dry-run] ssh ... $*"
    else
        ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE_HOST" "$@"
    fi
}

echo "🚀 Iniciando actualización rápida del sistema"
echo "   Origen : $LOCAL_PROJECT_PATH"
echo "   Destino: $REMOTE_HOST:$REMOTE_APP_PATH"
echo ""

# ── 1. Estado del árbol local que se va a desplegar ──
if [ -d "$LOCAL_PROJECT_PATH/.git" ]; then
    cd "$LOCAL_PROJECT_PATH"
    GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    GIT_SHA="$(git rev-parse --short HEAD)"
    GIT_DIRTY="$(git status --porcelain | wc -l)"
    echo "🌿 Rama: $GIT_BRANCH @ $GIT_SHA ($( [ "$GIT_DIRTY" -gt 0 ] && echo "$GIT_DIRTY archivos sin commitear" || echo 'árbol limpio' ))"
    if [ "$GIT_DIRTY" -gt 0 ]; then
        echo "❌ Hay cambios sin commitear: el despliegue no sería reproducible."
        echo "   Commitéalos (o guarda con 'git stash') y vuelve a intentar."
        exit 1
    fi
else
    GIT_BRANCH="desconocida"
    GIT_SHA="desconocida"
    echo "⚠️  $LOCAL_PROJECT_PATH no es un repositorio git: no se podrá registrar la versión desplegada."
fi

if [ "$DRY_RUN" -eq 0 ] && [ "$ASSUME_YES" -eq 0 ]; then
    printf "¿Continuar con el despliegue en producción? [s/N] "
    read -r respuesta
    case "$respuesta" in
        [sS]*) : ;;
        *) echo "Cancelado."; exit 1 ;;
    esac
fi

# ── 2. Conexión SSH ──
echo "🔗 Verificando conexión SSH..."
if ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE_HOST" "echo ok" >/dev/null 2>&1; then
    echo "✅ Conexión SSH exitosa"
else
    echo "❌ No se pudo conectar a $REMOTE_HOST con la clave $SSH_KEY"
    exit 1
fi

# ── 3. Backup de las bases de datos ANTES de tocar nada ──
# El servidor tiene la base activa dentro del árbol de código; sin este respaldo,
# un rsync mal dirigido o una migración incorrecta son irreversibles.
echo "💾 Respaldando bases de datos del servidor..."
run_remote "
    set -e
    BACKUP_DIR=$REMOTE_APP_PATH/backups
    mkdir -p \$BACKUP_DIR
    SELLOS=\$(date +%Y%m%d-%H%M%S)
    respaldados=0
    for db in $REMOTE_APP_PATH/backend/*.db $REMOTE_APP_PATH/*.db $CARTERA_DATA_DIR/*.db; do
        [ -f \"\$db\" ] || continue
        nombre=\$(basename \"\$db\")
        destino=\$BACKUP_DIR/\${nombre%.db}-\$SELLOS.db
        # .backup produce una copia consistente aunque haya conexiones activas
        if command -v sqlite3 >/dev/null 2>&1; then
            sqlite3 \"\$db\" \".backup '\$destino'\"
        else
            cp -a \"\$db\" \"\$destino\"
        fi
        gzip -f \"\$destino\"
        echo \"  backup: \$destino.gz\"
        respaldados=\$((respaldados + 1))
    done
    if [ \"\$respaldados\" -eq 0 ]; then
        echo '  ⚠️  No se encontró ningún .db que respaldar'
    fi
    # Retención: conserva los 10 backups más recientes por base
    ls -1t \$BACKUP_DIR/*.db.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
"
echo "✅ Respaldo listo (o nada que respaldar)"

# ── 4. Sincronizar código (protegiendo configuración y datos del servidor) ──
echo "📡 Copiando archivos actualizados..."
RSYNC_FLAGS=(-avz --delete)
[ "$DRY_RUN" -eq 1 ] && RSYNC_FLAGS+=(--dry-run)
rsync "${RSYNC_FLAGS[@]}" \
    --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','.vscode','.idea','*.log','.venv','.qoder'} \
    --exclude={'*.db','*.db-journal','*.sqlite','*.sqlite3'} \
    --exclude={'docker-compose.yml','docker-compose.dev.yml','.env','.env.*'} \
    --exclude={'backend/app/uploads/generated/*','backend/logs/*','backend/test.db*','generados/*','backups/*','auditoria/*'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

RSYNC_EXIT_CODE=$?
if [ "$RSYNC_EXIT_CODE" -eq 0 ] || [ "$RSYNC_EXIT_CODE" -eq 23 ]; then
    echo "✅ Transferencia completada"
else
    echo "❌ Error en la transferencia: código $RSYNC_EXIT_CODE"
    exit "$RSYNC_EXIT_CODE"
fi

# ── 5. Permisos: solo ejecutable en scripts, no un 755 general ──
# Un chmod -R 755 sobre todo el proyecto marca como ejecutables archivos que no lo son
# y rompe la comparación de modos con git.
echo "🔐 Configurando permisos..."
run_remote "
    chown -R root:root $REMOTE_APP_PATH
    find $REMOTE_APP_PATH -type d -exec chmod 755 {} +
    find $REMOTE_APP_PATH -type f -not -path '*/uploads/*' -exec chmod 644 {} +
    find $REMOTE_APP_PATH -maxdepth 1 -name '*.sh' -exec chmod 755 {} +
    find $REMOTE_APP_PATH/scripts -name '*.sh' -exec chmod 755 {} + 2>/dev/null || true
    chmod 600 $REMOTE_APP_PATH/.env 2>/dev/null || true
"

if [ "$DRY_RUN" -eq 1 ]; then
    echo ""
    echo "Dry-run terminado: no se aplicaron cambios."
    exit 0
fi

# ── 6. Migraciones ──
# run_migrations.py aplica el esquema pendiente con Alembic; si falla, se interrumpe
# el despliegue en lugar de reiniciar con un esquema a medias.
echo "🏃 Ejecutando migraciones..."
run_remote "cd $REMOTE_APP_PATH && (docker compose exec -T backend python3 /app/run_migrations.py || /usr/bin/python3 backend/run_migrations.py)"

# ── 7. Reiniciar backend ──
echo "🔄 Reiniciando backend..."
run_remote "cd $REMOTE_APP_PATH && docker compose up -d backend && docker compose restart backend"

# ── 8. Verificar que responde ──
echo "⏳ Esperando al backend..."
SALUD="FAIL"
for intento in 1 2 3 4 5 6; do
    sleep 5
    SALUD="$(run_remote "curl -s --max-time 5 http://127.0.0.1:8055/health" || echo FAIL)"
    echo "$SALUD" | grep -q "healthy" && break
    echo "  intento $intento: sin respuesta aún"
done

if echo "$SALUD" | grep -q "healthy"; then
    echo "✅ Backend OK: $SALUD"
else
    echo "❌ El backend no respondió. Último estado: $SALUD"
    echo "   Revisa: ssh $REMOTE_HOST 'docker logs cartera_backend --tail 50'"
    echo "   Rollback: restaura el backup de $REMOTE_APP_PATH/backups y docker compose restart backend"
    exit 1
fi

# ── 9. Recargar nginx ──
echo "🔄 Recargando nginx..."
run_remote "nginx -t && nginx -s reload"

# ── 10. Registrar la versión desplegada ──
# Sin el commit no se puede saber qué código está corriendo: fue la causa de fondo
# de la auditoría de noviembre de 2026.
UPDATE_TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
REGISTRO="$UPDATE_TIMESTAMP | rama=$GIT_BRANCH | commit=$GIT_SHA | operador=$(whoami)@$(hostname)"
run_remote "echo '$REGISTRO' > $REMOTE_APP_PATH/.last_update"

echo ""
echo "✅ Actualización completada"
echo "   $REGISTRO"
echo ""
echo "⚠️  Si cambiaste archivos del frontend, reconstruye el contenedor:"
echo "   ssh $REMOTE_HOST 'cd $REMOTE_APP_PATH && docker compose build frontend && docker compose up -d frontend'"
