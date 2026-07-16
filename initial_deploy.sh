#!/bin/bash

# Script para desplegar la aplicación en el servidor remoto root@giron.tiksgroup.co
# Versión para primer despliegue - fuerza la copia de la base de datos de desarrollo
# La aplicación se desplegará en la carpeta /opt/cyberrit
# La base de datos de desarrollo se copiará en la carpeta /opt/riap/db
# Se integrará con el servicio nginx existente en el servidor usando el dominio cyberrit.tiksgroup.co

set -e  # Salir inmediatamente si algún comando falla

# Variables de configuración
REMOTE_HOST="root@giron.tiksgroup.co"
SSH_KEY="/home/chandero/.ssh/id_ed25519"
LOCAL_PROJECT_PATH="/home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo"
REMOTE_APP_PATH="/opt/cyberrit"
REMOTE_DB_PATH="/opt/riap/db"
REMOTE_NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
REMOTE_NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
NGINX_CONFIG_FILE="nginx_cyberrit_config.conf"

echo "🚀 Iniciando proceso de despliegue inicial..."

# Verificar conexión SSH
echo "🔗 Verificando conexión SSH con $REMOTE_HOST..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'Conexión exitosa'" > /dev/null 2>&1; then
    echo "✅ Conexión SSH exitosa"
else
    echo "❌ No se pudo conectar al servidor remoto. Por favor, verifique la conexión y credenciales."
    exit 1
fi

# Crear directorios remotos
echo "📁 Creando directorios remotos..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "mkdir -p $REMOTE_APP_PATH $REMOTE_DB_PATH && chmod 755 $REMOTE_APP_PATH $REMOTE_DB_PATH"

# Copiar archivo de configuración de nginx al servidor remoto
echo "📡 Copiando archivo de configuración de nginx al servidor remoto..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/$NGINX_CONFIG_FILE" "$REMOTE_HOST:/tmp/cyberrit.conf"

# Encontrar archivo de base de datos de desarrollo
DB_FILE=$(find "$LOCAL_PROJECT_PATH" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | head -n 1)

if [ -n "$DB_FILE" ]; then
    echo "📦 Este es un despliegue inicial: Copiando base de datos de desarrollo al servidor remoto..."
    
    echo "🗄️ Copiando base de datos de desarrollo al servidor remoto..."
    DB_FILENAME=$(basename "$DB_FILE")
    scp -i "$SSH_KEY" "$DB_FILE" "$REMOTE_HOST:$REMOTE_DB_PATH/$DB_FILENAME"
    echo "✅ Base de datos de desarrollo copiada: $DB_FILENAME"
    
    # Cambiar nombre a cartera.db para seguir la convención del sistema
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_DB_PATH && mv $DB_FILENAME cartera.db"
    echo "✅ Base de datos renombrada a cartera.db"
else
    echo "❌ No se encontró archivo de base de datos en el directorio del proyecto"
    echo "💡 Debe proporcionar un archivo de base de datos para el primer despliegue"
    exit 1
fi

# Limpiar directorio de aplicación remota
echo "🧹 Limpiando directorio de aplicación remota..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "rm -rf $REMOTE_APP_PATH/*"

# Copiar archivos del proyecto al servidor remoto (excluyendo directorios innecesarios)
echo "📡 Copiando archivos del proyecto al servidor remoto..."
rsync -avz --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','dist','build','.vscode','.idea','*.log'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

# Copiar también el script de limpieza remota
echo "📡 Copiando script de limpieza remota al servidor..."
scp -i "$SSH_KEY" "$LOCAL_PROJECT_PATH/remote_clean_script.py" "$REMOTE_HOST:$REMOTE_APP_PATH/remote_clean_script.py"

# Establecer permisos adecuados en el servidor
echo "🔐 Configurando permisos en el servidor..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_APP_PATH && chmod -R 755 $REMOTE_APP_PATH"
ssh -i "$SSH_KEY" "$REMOTE_HOST" "chown -R root:root $REMOTE_DB_PATH && chmod -R 755 $REMOTE_DB_PATH"

# Verificar si nginx está instalado en el servidor remoto
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx"; then
    echo "✅ Nginx está instalado en el servidor remoto"
    
    # Copiar configuración de nginx a sites-available
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "cp /tmp/cyberrit.conf $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf"
    
    # Enlazar configuración a sites-enabled si no existe
    if ! ssh -i "$SSH_KEY" "$REMOTE_HOST" "test -f $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"; then
        ssh -i "$SSH_KEY" "$REMOTE_HOST" "ln -s $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"
        echo "🔗 Configuración de nginx enlazada a sites-enabled para cyberrit.tiksgroup.co"
    else
        echo "ℹ️ Configuración de nginx ya existe en sites-enabled para cyberrit.tiksgroup.co"
    fi
    
    # Verificar sintaxis de configuración de nginx
    if ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -t"; then
        echo "✅ Sintaxis de configuración de nginx correcta"
        
        # Recargar configuración de nginx
        ssh -i "$SSH_KEY" "$REMOTE_HOST" "nginx -s reload || systemctl reload nginx || service nginx reload"
        echo "🔄 Configuración de nginx recargada para el dominio cyberrit.tiksgroup.co"
    else
        echo "❌ Error en la sintaxis de configuración de nginx. Por favor, verifique la configuración."
        echo "💡 Puede necesitar ajustar la configuración de nginx para que no entre en conflicto con sitios existentes"
        exit 1
    fi
else
    echo "⚠️ Nginx no está instalado en el servidor remoto. La aplicación se desplegará pero no se configurará automáticamente con nginx."
    echo "💡 Puede necesitar configurar nginx manualmente para servir la aplicación."
fi

# Marcar que el despliegue se completó
DEPLOYMENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ssh -i "$SSH_KEY" "$REMOTE_HOST" "echo '$DEPLOYMENT_TIMESTAMP' > $REMOTE_APP_PATH/.last_deployment"

# Verificar que los archivos se hayan copiado correctamente
echo "🔍 Verificando archivos copiados..."
REMOTE_FILE_COUNT=$(ssh -i "$SSH_KEY" "$REMOTE_HOST" "find $REMOTE_APP_PATH -type f | wc -l")
echo "📁 Número de archivos en $REMOTE_APP_PATH: $REMOTE_FILE_COUNT"

# Mostrar información del despliegue
echo ""
echo "✅ Despliegue inicial completado exitosamente!"
echo ""
echo "Tipo de despliegue: Primera instalación"
echo "Ubicación de la aplicación: $REMOTE_APP_PATH"
echo "Ubicación de la base de datos: $REMOTE_DB_PATH/cartera.db"
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx" > /dev/null 2>&1; then
    echo "Dominio configurado: cyberrit.tiksgroup.co"
    echo "Configuración de nginx: $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf"
    echo "Sitio habilitado: $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"
fi
echo ""
echo "Sugerencias para post-despliegue:"
echo "1. Ejecutar el script de limpieza de campos de resolución en el servidor remoto:"
echo "   ssh -i $SSH_KEY $REMOTE_HOST 'cd $REMOTE_APP_PATH && python remote_clean_script.py'"
echo "2. Revisar la base de datos copiada en el servidor remoto"
echo "3. Ajustar variables de entorno si es necesario"
echo "4. Verificar que el servicio backend esté corriendo (puerto 8000)"
echo "5. Asegurarse de tener certificados SSL válidos para cyberrit.tiksgroup.co (si se va a usar HTTPS)"
echo "6. Validar la configuración de nginx para evitar conflictos con sitios existentes"
echo "7. Probar la conectividad a la aplicación en cyberrit.tiksgroup.co"
echo ""

echo "🎉 ¡Despliegue inicial finalizado!"