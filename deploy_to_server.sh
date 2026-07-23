#!/bin/bash

# Script para desplegar la aplicación en el servidor remoto root@giron.tiksgroup.co
# Uso de Python 3.9 directo que tiene soporte SQLite

set -e

REMOTE_HOST="root@giron.tiksgroup.co"
SSH_KEY="/home/chandero/.ssh/id_ed25519"
LOCAL_PROJECT_PATH="/home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo"
REMOTE_APP_PATH="/opt/cyberrit"
REMOTE_DB_PATH="/opt/riap/db"
NGINX_CONFIG_FILE="nginx_cyberrit_config.conf"

echo "🚀 Iniciando proceso de despliegue..."

# Verificar conexión SSH
echo "🔗 Verificando conexión SSH..."
ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'OK'"

# Crear directorios
echo "📁 Creando directorios..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "mkdir -p $REMOTE_APP_PATH $REMOTE_DB_PATH"

# Copiar configuración de nginx
echo "📡 Copiando nginx config..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/$NGINX_CONFIG_FILE" "$REMOTE_HOST:/tmp/cyberrit.conf"

# Verificar base de datos existente
FIRST_DEPLOYMENT=false
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "ls $REMOTE_DB_PATH/*.db 2>/dev/null | head -n 1"; then
    echo "ℹ️  Base de datos existente. Este es un despliegue posterior."
    FIRST_DEPLOYMENT=false
else
    echo "🆕  Sin base de datos existente. Este es el primer despliegue."
    FIRST_DEPLOYMENT=true
fi

# Limpiar aplicación (excluyendo base de datos)
echo "🧹 Limpiando aplicación..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "find $REMOTE_APP_PATH -type f ! -name '*.db' -delete 2>/dev/null || true"

# Copiar archivos
echo "📡 Copiando archivos..."
rsync -avz --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','dist','build','.vscode','.idea','*.log','*.db','*.sqlite','.venv'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

# Copiar script de migraciones
echo "📡 Copiando run_migrations.py..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/backend/run_migrations.py" "$REMOTE_HOST:$REMOTE_APP_PATH/run_migrations.py"

# Establecer permisos
echo "🔐 Configurando permisos..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_APP_PATH $REMOTE_DB_PATH"

# Configurar nginx
echo "🌐 Configurando nginx..."
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx"; then
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "cp /tmp/cyberrit.conf /etc/nginx/sites-available/cyberrit.conf"
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "ln -sf /etc/nginx/sites-available/cyberrit.conf /etc/nginx/sites-enabled/cyberrit.conf"
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -t && nginx -s reload"
    echo "✅ Nginx configurado"
fi

# Ejecutar migraciones con Python 3.9 (que tiene soporte SQLite)
if [ "$FIRST_DEPLOYMENT" = false ]; then
    echo "🏃 Ejecutando migraciones..."
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "/usr/bin/python3.9 /opt/cyberrit/run_migrations.py"
fi

# Marcar despliegue
DEPLOYMENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i "$SSH_KEY" "$REMOTE_HOST" "echo '$DEPLOYMENT_TIMESTAMP' > $REMOTE_APP_PATH/.last_deployment"

echo ""
echo "✅ Despliegue completado!"
echo "   Aplicación: $REMOTE_APP_PATH"
echo "   Base de datos: $REMOTE_DB_PATH"
echo "   Python 3.9 usado para migraciones"
