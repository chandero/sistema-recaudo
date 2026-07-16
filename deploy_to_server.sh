#!/bin/bash

# Script para desplegar la aplicación en el servidor remoto root@giron.tiksgroup.co
# La aplicación se desplegará en la carpeta /opt/cyberrit
# La base de datos se copiará en la carpeta /opt/riap/db
# Se integrará con el servicio nginx existente en el servidor usando el dominio cyberrit.tiksgroup.co
# Para el primer despliegue se copia la base de datos de desarrollo, para posteriores solo se realizan migraciones

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

echo "🚀 Iniciando proceso de despliegue..."

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

# Verificar si es el primer despliegue o uno posterior
FIRST_DEPLOYMENT=false
DB_FILE=$(find "$LOCAL_PROJECT_PATH" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | head -n 1)

# Verificar si ya existe una base de datos en el servidor remoto
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "ls $REMOTE_DB_PATH/*.db $REMOTE_DB_PATH/*.sqlite $REMOTE_DB_PATH/*.sqlite3 2>/dev/null | head -n 1"; then
    echo "ℹ️  Se detectó una base de datos existente en el servidor remoto. Este es un despliegue posterior."
    FIRST_DEPLOYMENT=false
else
    echo "🆕  No se detectaron bases de datos en el servidor remoto. Este es el primer despliegue."
    FIRST_DEPLOYMENT=true
fi

if [ "$FIRST_DEPLOYMENT" = true ]; then
    echo "📦 Primer despliegue: Copiando base de datos de desarrollo al servidor remoto..."
    
    if [ -n "$DB_FILE" ]; then
        echo "🗄️ Copiando base de datos de desarrollo al servidor remoto..."
        DB_FILENAME=$(basename "$DB_FILE")
        scp -i "$SSH_KEY" "$DB_FILE" "$REMOTE_HOST:$REMOTE_DB_PATH/$DB_FILENAME"
        echo "✅ Base de datos de desarrollo copiada: $DB_FILENAME"
    else
        echo "⚠️ No se encontró archivo de base de datos en el directorio del proyecto"
        echo "💡 Considera crear una base de datos vacía o con datos de ejemplo para el primer despliegue"
    fi
else
    echo "🔄 Despliegue posterior: No se copia la base de datos, solo se aplicarán migraciones si es necesario..."
    echo "💡 Asegúrate de que las migraciones necesarias se apliquen en el servidor remoto"
    
    # Crear un archivo de control de migración si no existe
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "[ ! -f $REMOTE_DB_PATH/.migration_control ] && touch $REMOTE_DB_PATH/.migration_control"
    
    # Crear un archivo de control de migración si no existe
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "[ ! -f $REMOTE_DB_PATH/.migration_control ] && touch $REMOTE_DB_PATH/.migration_control"
fi

# Limpiar directorio de aplicación remota
echo "🧹 Limpiando directorio de aplicación remota..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "rm -rf $REMOTE_APP_PATH/*"

# Copiar archivos del proyecto al servidor remoto (excluyendo directorios innecesarios)
echo "📡 Copiando archivos del proyecto al servidor remoto..."
rsync -avz --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','dist','build','.vscode','.idea','*.log'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

# Copiar también el script de migraciones
echo "📡 Copiando script de migraciones al servidor remoto..."
rsync -avz -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/run_migrations.py" "$REMOTE_HOST:$REMOTE_APP_PATH/run_migrations.py"

# Establecer permisos adecuados en el servidor
```

deploy_to_server.sh
```bash
<<<<<<< SEARCH
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
echo "✅ Despliegue completado exitosamente!"
echo ""
echo "Tipo de despliegue: $(if [ "$FIRST_DEPLOYMENT" = true ]; then echo "Primera instalación"; else echo "Actualización"; fi)"
echo "Ubicación de la aplicación: $REMOTE_APP_PATH"
echo "Ubicación de la base de datos: $REMOTE_DB_PATH"
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx" > /dev/null 2>&1; then
    echo "Dominio configurado: cyberrit.tiksgroup.co"
    echo "Configuración de nginx: $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf"
    echo "Sitio habilitado: $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"
fi
echo ""
echo "Sugerencias para post-despliegue:"
if [ "$FIRST_DEPLOYMENT" = true ]; then
    echo "1. Revisar la base de datos copiada en el servidor remoto"
else
    echo "1. Verificar que las migraciones necesarias se hayan aplicado correctamente"
    echo "2. Revisar que la base de datos existente sea compatible con la nueva versión del código"
fi
echo "2. Ajustar variables de entorno si es necesario"
echo "3. Verificar que el servicio backend esté corriendo (puerto 8000)"
echo "4. Asegurarse de tener certificados SSL válidos para cyberrit.tiksgroup.co (si se va a usar HTTPS)"
echo "5. Validar la configuración de nginx para evitar conflictos con sitios existentes"
echo "6. Probar la conectividad a la aplicación en cyberrit.tiksgroup.co"
echo ""

echo "🎉 ¡Despliegue finalizado!"
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

# Si es un despliegue posterior, ejecutar migraciones
if [ "$FIRST_DEPLOYMENT" = false ]; then
    echo "🏃 Ejecutando migraciones necesarias en el servidor remoto..."
    ssh -i "$SSH_KEY" "$REMOTE_HOST" "cd $REMOTE_APP_PATH && python run_migrations.py"
    echo "✅ Migraciones ejecutadas en el servidor remoto."
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
echo "✅ Despliegue completado exitosamente!"
echo ""
echo "Tipo de despliegue: $(if [ "$FIRST_DEPLOYMENT" = true ]; then echo "Primera instalación"; else echo "Actualización"; fi)"
echo "Ubicación de la aplicación: $REMOTE_APP_PATH"
echo "Ubicación de la base de datos: $REMOTE_DB_PATH"
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx" > /dev/null 2>&1; then
    echo "Dominio configurado: cyberrit.tiksgroup.co"
    echo "Configuración de nginx: $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf"
    echo "Sitio habilitado: $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"
fi
echo ""
echo "Sugerencias para post-despliegue:"
if [ "$FIRST_DEPLOYMENT" = true ]; then
    echo "1. Revisar la base de datos copiada en el servidor remoto"
else
    echo "1. Verificar que las migraciones se hayan aplicado correctamente"
    echo "2. Revisar que la base de datos existente sea compatible con la nueva versión del código"
    echo "3. Probar las nuevas funcionalidades que requieran cambios en la base de datos"
fi
echo "2. Ajustar variables de entorno si es necesario"
echo "3. Verificar que el servicio backend esté corriendo (puerto 8000)"
echo "4. Asegurarse de tener certificados SSL válidos para cyberrit.tiksgroup.co (si se va a usar HTTPS)"
echo "5. Validar la configuración de nginx para evitar conflictos con sitios existentes"
echo "6. Probar la conectividad a la aplicación en cyberrit.tiksgroup.co"
echo ""

echo "🎉 ¡Despliegue finalizado!"
fi

# Limpiar directorio de aplicación remota
echo "🧹 Limpiando directorio de aplicación remota..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "rm -rf $REMOTE_APP_PATH/*"

# Copiar archivos del proyecto al servidor remoto (excluyendo directorios innecesarios)
echo "📡 Copiando archivos del proyecto al servidor remoto..."
rsync -avz --exclude={'__pycache__','.git','.gitignore','*.pyc','.pytest_cache','node_modules','dist','build','.vscode','.idea','*.log'} \
    -e "ssh -i $SSH_KEY" "$LOCAL_PROJECT_PATH/" "$REMOTE_HOST:$REMOTE_APP_PATH/"

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
echo "✅ Despliegue completado exitosamente!"
echo ""
echo "Tipo de despliegue: $(if [ "$FIRST_DEPLOYMENT" = true ]; then echo "Primera instalación"; else echo "Actualización"; fi)"
echo "Ubicación de la aplicación: $REMOTE_APP_PATH"
echo "Ubicación de la base de datos: $REMOTE_DB_PATH"
if ssh -i "$SSH_KEY" "$REMOTE_HOST" "command -v nginx" > /dev/null 2>&1; then
    echo "Dominio configurado: cyberrit.tiksgroup.co"
    echo "Configuración de nginx: $REMOTE_NGINX_SITES_AVAILABLE/cyberrit.conf"
    echo "Sitio habilitado: $REMOTE_NGINX_SITES_ENABLED/cyberrit.conf"
fi
echo ""
echo "Sugerencias para post-despliegue:"
if [ "$FIRST_DEPLOYMENT" = true ]; then
    echo "1. Revisar la base de datos copiada en el servidor remoto"
else
    echo "1. Verificar que las migraciones necesarias se hayan aplicado correctamente"
    echo "2. Revisar que la base de datos existente sea compatible con la nueva versión del código"
fi
echo "2. Ajustar variables de entorno si es necesario"
echo "3. Verificar que el servicio backend esté corriendo (puerto 8000)"
echo "4. Asegurarse de tener certificados SSL válidos para cyberrit.tiksgroup.co (si se va a usar HTTPS)"
echo "5. Validar la configuración de nginx para evitar conflictos con sitios existentes"
echo "6. Probar la conectividad a la aplicación en cyberrit.tiksgroup.co"
echo ""

echo "🎉 ¡Despliegue finalizado!"