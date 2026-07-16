# Limpieza de Campos de Resolución y Despliegue

Este documento explica cómo usar los scripts para limpiar los campos de resolución de las obligaciones y desplegar la aplicación en el servidor remoto.

## Scripts incluidos

1. **[clean_obligations_resolution_fields.py](file:///home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo/backend/clean_obligations_resolution_fields.py)** - Limpia los campos de resolución de todas las obligaciones en la base de datos
2. **[deploy_to_server.sh](file:///home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo/deploy_to_server.sh)** - Despliega la aplicación en el servidor remoto e integra con el servicio nginx existente
3. **[clean_and_deploy.py](file:///home/chandero/Documentos/Desarrollo/Repositorios/tmtek/Qwen/sistema-recaudo/clean_and_deploy.py)** - Combina ambas operaciones en un solo flujo

## Campos que se limpian

Los siguientes campos se establecen en NULL para todas las obligaciones:
- `resolution_number` (número de resolución)
- `resolution_year` (año de resolución)
- `resolution_date` (fecha de resolución)
- `radicado_number` (número de radicado)
- `resolution_assigned_at` (fecha de asignación de resolución)
- `resolution_observations` (observaciones de resolución)

## Uso

### 1. Limpieza únicamente de la base de datos

```bash
cd backend
python clean_obligations_resolution_fields.py
```

### 2. Despliegue únicamente en el servidor

```bash
./deploy_to_server.sh
```

### 3. Limpieza y despliegue combinados

```bash
python clean_and_deploy.py
```

## Configuración previa

Antes de ejecutar los scripts, asegúrese de tener:

1. Acceso SSH al servidor `root@giron.tiksgroup.co` con la clave en `/home/chandero/.ssh/id_ed25519`
2. Python 3.8+ instalado para ejecutar los scripts de Python
3. rsync y scp disponibles para el despliegue
4. La configuración correcta de la base de datos en el entorno

## Destinos de despliegue

- Aplicación: `/opt/cyberrit`
- Base de datos: `/opt/riap/db`
- Configuración de nginx: `/etc/nginx/sites-available/sistema-recaudo.conf` (y enlazado en `/etc/nginx/sites-enabled/`)

## Integración con nginx existente

El script de despliegue:
1. Detecta si nginx está instalado en el servidor remoto
2. Crea un archivo de configuración para la aplicación en `/etc/nginx/sites-available/`
3. Crea un enlace simbólico en `/etc/nginx/sites-enabled/` para habilitar el sitio
4. Verifica la sintaxis de la configuración y recarga nginx
5. Configura el proxy inverso para enrutar solicitudes de `/api/` al backend en `http://127.0.0.1:8000`

## Notas importantes

- El script de limpieza respeta las transacciones de la base de datos y hará rollback en caso de error
- El script de despliegue excluye directorios innecesarios como `.git`, `__pycache__`, `node_modules`, etc.
- Se recomienda hacer backup de la base de datos antes de ejecutar la limpieza
- El script de despliegue mantiene la estructura de directorios original
- Al integrar con nginx existente, revise la configuración para evitar conflictos con sitios ya configurados