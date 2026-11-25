# Sistema de Seguimiento y Control de Cobro de Cartera

Plataforma multi-tenant para la gestión, seguimiento y control de procesos de cobranza de cartera pública y privada.

## Stack Tecnológico

- **Backend**: Python + FastAPI
- **Base de datos**: PostgreSQL
- **ORM**: SQLAlchemy + SQLModel
- **Migraciones**: Alembic
- **Frontend**: Vue 3 + PrimeVue + CSS
- **Reportes**: Excel y PDF
- **Automatización**: Celery + Redis
- **Infraestructura**: Docker + Nginx

## Estructura del Proyecto

```
/workspace
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       ├── views/
│       ├── router/
│       ├── stores/
│       └── assets/
├── docs/
└── docker-compose.yml
```

## Instalación y Ejecución

### Prerrequisitos

- Docker y Docker Compose
- Python 3.9+
- Node.js 18+

### Ejecución con Docker

```bash
docker-compose up -d
```

### Ejecución Local

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Workflow Inicial: Cobro de Alumbrado Público

El sistema incluye 20 estados predefinidos para el proceso de cobro:

1. CARTERA_CARGADA
2. OBLIGACION_VALIDADA
3. PENDIENTE_ASIGNACION_RESOLUCION
4. RESOLUCION_RADICADOS_ASIGNADOS
5. DOCUMENTO_NOTIFICACION_GENERADO
6. NOTIFICACION_ENVIADA
7. ESPERANDO_RESULTADO_NOTIFICACION
8. NOTIFICACION_ENTREGADA
9. NOTIFICACION_DEVUELTA
10. REINTENTO_NOTIFICACION
11. ESPERANDO_PAGO_VOLUNTARIO
12. COBRO_PERSUASIVO
13. ACUERDO_DE_PAGO
14. SEGUIMIENTO_ACUERDO
15. ACUERDO_INCUMPLIDO
16. COBRO_PREJURIDICO
17. COBRO_COACTIVO
18. PAGADO
19. ARCHIVADO
20. INCOBRABLE

## Características Principales

- Multi-tenant estricto con aislamiento de datos
- Gestión de usuarios, roles y permisos
- Importación masiva desde Excel/CSV con mapeo configurable
- Generación documental con plantillas DOCX/PDF
- Control de resolución y radicados
- Expediente digital completo
- Dashboard visual y Kanban operativo
- Automatización de cambios de estado por vencimiento
- Auditoría completa de operaciones

## Respaldo automático de datos

El script `backup_data.sh` respalda la información del servidor
`giron.tiksgroup.co`. En producción la base activa es SQLite
(`/opt/cyberrit/backend/test.db`), no PostgreSQL.

**Qué guarda**: la base de datos, las plantillas DOCX (`backend/app/uploads/templates`),
`plantillas_nuevas`, `auditoria`, `scripts`, `.env`, `docker-compose.yml`, las
configuraciones de nginx y `backend/run_migrations.py`. **No** guarda
`backend/app/uploads/generated`: los documentos generados vuelven a salir de la
base de datos y ya ocupan gigabytes.

**Cuándo y cuánto**: dos ejecuciones diarias por cron de root, 03:00 y 15:00, con
las 60 copias recientes conservadas (unos 300 MB).

**Dónde queda**:

| Copia | Ruta |
|---|---|
| Local | `/opt/siap/backups_cyberrit/cyberrit_<fecha>.tar.gz` |
| Remota | `84.247.164.191:/opt/giron/backups_cyberrit`, vía el `rsync` que ya ejecuta `/usr/bin/siap_backup.bash` sobre todo `/opt/siap` |
| Estado | `/opt/cyberrit/backups/.ultimo_respaldo` y `/var/log/cyberrit_backup.log` |

Vive dentro de `/opt/siap` para heredar la sincronización remota ya existente, pero
en un directorio propio: la rotación de SIAP elige «la más antigua» con un orden
numérico sobre nombres alfabéticos y borraría los archivos ajenos que aparezcan
antes.

**Alta en cron** (una sola vez, sin tocar las entradas existentes):

```bash
ssh root@giron.tiksgroup.co 'crontab <( { crontab -l 2>/dev/null | grep -v backup_data.sh; printf "0 3 * * * /opt/cyberrit/backup_data.sh >>/var/log/cyberrit_backup.log 2>&1\n0 15 * * * /opt/cyberrit/backup_data.sh >>/var/log/cyberrit_backup.log 2>&1\n"; } )'
```

**Restaurar**:

```bash
mkdir -p /restore
tar -xzf /opt/siap/backups_cyberrit/cyberrit_<fecha>.tar.gz -C /restore
sqlite3 /restore/opt/cyberrit/backend/test.db 'PRAGMA integrity_check;'   # debe decir ok
cd /opt/cyberrit && docker compose stop backend
cp /restore/opt/cyberrit/backend/test.db /opt/cyberrit/backend/test.db
docker compose up -d backend && curl -s localhost:8055/health
```

**Probar sin alterar la cadena de rotación**:

```bash
# En el servidor: una copia ahora mismo, sin enviarla al remoto
ssh root@giron.tiksgroup.co 'SEND_OFFSITE=0 /opt/cyberrit/backup_data.sh'

# Simulación: arma el archivo en /tmp, dice qué borraría y no toca el destino
ssh root@giron.tiksgroup.co 'DRY_RUN=1 KEEP=2 SEND_OFFSITE=0 /opt/cyberrit/backup_data.sh'
```

## Licencia

Propietario - Todos los derechos reservados
