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

## Licencia

Propietario - Todos los derechos reservados
