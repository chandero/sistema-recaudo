# Sistema de Seguimiento y Control de Cobro de Cartera
## Resumen de Implementación - Versión 0.1

### ✅ Componentes Implementados

#### Backend (FastAPI + PostgreSQL)

**Modelos de Datos:**
- `Tenant` - Multi-tenancy estricto
- `User` - Usuarios con roles (PLATFORM_ADMIN, TENANT_ADMIN, MANAGER, OPERATOR, VIEWER)
- `Client` - Contribuyentes/clientes
- `Obligation` - Obligaciones de cartera
- `CollectionProcess` - Procesos de cobro con workflow
- `WorkflowState` - Estados configurables del workflow
- `WorkflowTransition` - Transiciones y reglas automáticas
- `DocumentTemplate` - Plantillas DOCX/PDF con variables
- `GeneratedDocument` - Documentos generados
- `ImportBatch` - Lotes de importación Excel/CSV
- `ImportMappingTemplate` - Plantillas de mapeo de columnas

**Endpoints API:**
- `/api/v1/auth/*` - Autenticación JWT (login, refresh, logout)
- `/api/v1/tenants/*` - CRUD de tenants (solo platform_admin)
- `/api/v1/clients/*` - Gestión de clientes
- `/api/v1/processes/*` - Gestión de procesos de cobro
- `/api/v1/workflows/*` - Configuración de workflows
- `/api/v1/documents/*` - Plantillas y generación documental
- `/api/v1/importer/*` - Importación masiva con mapeo

**Servicios:**
- `auth_service.py` - JWT y seguridad
- `document_service.py` - Generación DOCX→PDF (docxtpl + LibreOffice)
- `email_service.py` - Envío de correos con plantillas Jinja2
- `import_service.py` - Procesamiento Excel/CSV con mapeo dinámico

**Workflow Inicial (20 estados):**
CARTERA_CARGADA → OBLIGACION_VALIDADA → PENDIENTE_ASIGNACION_RESOLUCION → 
RESOLUCION_RADICADOS_ASIGNADOS → DOCUMENTO_NOTIFICACION_GENERADO → 
NOTIFICACION_ENVIADA → ESPERANDO_RESULTADO_NOTIFICACION → 
NOTIFICACION_ENTREGADA/NOTIFICACION_DEVUELTA → REINTENTO_NOTIFICACION → 
ESPERANDO_PAGO_VOLUNTARIO → COBRO_PERSUASIVO → ACUERDO_DE_PAGO → 
SEGUIMIENTO_ACUERDO → COBRO_PREJURIDICO → COBRO_COACTIVO → PAGADO/ARCHIVADO/INCOBRABLE

#### Frontend (Vue 3 + PrimeVue)

**Vistas Implementadas:**
- `LoginView.vue` - Autenticación JWT
- `DashboardView.vue` - Panel principal con indicadores
- `AdminView.vue` - Gestión de tenants y usuarios
- `ClientesView.vue` - CRUD de clientes/contribuyentes
- `ResolucionesView.vue` - Asignación de resoluciones y radicados
- `WorkflowView.vue` - Editor visual Kanban del flujo de cobro
- `EmailTemplatesView.vue` - Plantillas de correos electrónicos
- `ImportarView.vue` - Carga Excel/CSV con mapeo de columnas
- `DocumentosView.vue` - Gestión de plantillas y generación PDF/ZIP

**Características Frontend:**
- Router con guardias de autenticación
- Layout responsive con menú lateral
- Store Pinia para estado global
- Componentes PrimeVue (DataTable, Dialog, Dropdown, Toast, etc.)
- Cliente Axios con interceptores JWT

### 📁 Estructura del Proyecto

```
/workspace
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── tenants.py
│   │   │   ├── clients.py
│   │   │   ├── processes.py
│   │   │   ├── workflows.py
│   │   │   ├── documents.py
│   │   │   └── importer.py
│   │   ├── models/
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── process.py
│   │   │   ├── workflow.py
│   │   │   └── document.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── email_service.py
│   │   │   └── import_service.py
│   │   └── db/
│   │       ├── session.py
│   │       └── seed_workflow.py
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── services/
│   │   ├── stores/
│   │   └── router/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

### 🚀 Cómo Ejecutar

**Con Docker (Recomendado):**
```bash
cd /workspace
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed_workflow
```

Acceder a:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

**Credenciales por defecto:**
- Usuario: admin@platform.com
- Contraseña: admin123

### 🔑 Funcionalidades Clave

1. **Multi-tenant estricto**: Todas las consultas filtran por tenant_id
2. **Importación Excel/CSV**: Mapeo configurable de columnas, plantillas reutilizables
3. **Generación documental**: Plantillas DOCX con variables, salida PDF individual o ZIP masivo
4. **Workflow configurable**: Estados, transiciones, tiempos máximos, cambios automáticos
5. **Resoluciones/Radicados**: Control de consecutivos, reserva, generación masiva
6. **Email templates**: Plantillas Jinja2 para notificaciones
7. **Seguridad RBAC**: Roles, permisos individuales, auditoría

### 📋 Próximos Pasos Sugeridos

1. **Pruebas unitarias**: Implementar tests para endpoints críticos
2. **Celery/Redis**: Configurar tareas en segundo plano para generaciones masivas
3. **OCR**: Integrar Tesseract/pytesseract para lectura de guías escaneadas
4. **Reportes**: Dashboards ejecutivos con indicadores de gestión
5. **Expediente digital**: Historial completo de actuaciones por proceso
6. **IA/ML**: Sugerencia de mapeo, predicción de pago, detección de riesgo

### 📞 Soporte

Para problemas de instalación o configuración, revisar el archivo `GUIA_INSTALACION.md` 
o la documentación Swagger en `/docs`.
