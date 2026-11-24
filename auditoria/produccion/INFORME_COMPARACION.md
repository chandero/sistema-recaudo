# Informe de comparación: código local vs despliegue en el servidor Girón

Fecha de auditoría: 2026-11-24 (UTC-5)
Servidor auditado: `root@giron.tiksgroup.co` (hostname `siap`), aplicación en `/opt/cyberrit`
Referencia real del sistema de recaudo: **https://giron.cyberrit.tiksgroup.co** (título "Sistema de Gestión de Cartera")

> Aclaración importante sobre la URL. El sitio nginx activo `giron.tiksgroup.co` sirve otro
> producto (CyberSIAP, desde `/var/www/cybersiapv2/frontend/dist`, proxy a `127.0.0.1:9095`).
> El sistema de recaudo desplegado en ese mismo servidor está montado sobre el sitio nginx
> `cyberrit`, cuyo `server_name` es `giron.cyberrit.tiksgroup.co` y hace proxy a los contenedores
> `cartera_frontend` (5055) y `cartera_backend` (8055). Toda esta auditoría corresponde a ese
> sistema, no a CyberSIAP.

## 1. Veredicto

**El código local NO es igual al remoto.** Ninguna rama del repositorio reproduce lo desplegado.

- `main` (HEAD local, `1984fd4`) coincide en **101 de 204** archivos de código (49,5 %).
- `origin/refactor/ajuste-global-reglas` (`4997a0f`, el commit publicado más reciente) coincide en
  **144 de 204** (70,6 %).
- El árbol de producción es **superador** del repositorio: ningún archivo versionado falta en el
  servidor (0 "solo en referencia"), mientras que **28 archivos de código existen únicamente en el
  servidor** y **32 archivos versionados tienen contenido distinto** en producción.
- Brecha temporal: último commit publicado el 2026-07-23; último despliegue por rsync el
  2026-08-28 14:19:10 (`.last_update`), con archivos editados directamente el 27 y 28 de agosto.
  Es decir, aproximadamente un mes de trabajo nunca llegó a GitHub.

## 2. Método y evidencia

Auditoría 100 % en solo lectura sobre el servidor (ninguna orden escribió, reinició o reconstruyó
contenedores). Reproducible con los scripts de `auditoria/scripts/`:

| Script | Propósito |
|---|---|
| `captura_remoto.sh` | Hashes del código, configs, build servido, `openapi.json` vivo, inventario de datos |
| `hashes.sh` / `hashes_locales.sh` | Mismo filtro de hashing aplicado a `main`, a la rama y al árbol de trabajo (vía worktrees) |
| `comparar.sh` | Clasificación idéntico / distinto / solo-servidor / solo-referencia (`11_*.txt`, `11_resumen_comparacion.csv`) |
| `generar_diffs.sh` | 72 diffs unificados en `auditoria/produccion/diffs/` |
| `rutas_api.py` | Rutas que responde el backend en producción frente a las que declara cada referencia |
| `crear_baseline.sh`, `normalizar_permisos.sh` | Construcción de la rama de línea base |

Recuento de archivos de código comparados (`.py`, `.vue`, `.js`, `.json`, `.yml`, `.conf`, `.md`,
`.ini`, `.txt`, `Dockerfile`; excluyendo `node_modules`, `__pycache__`, `.venv`, `frontend/dist`,
`generados`, `.qoder`, logs, subidas generadas y `package-lock.json`):

| Referencia | Archivos | Idénticos | Distintos | Solo en servidor | Solo en referencia | Coincidencia |
|---|---|---|---|---|---|---|
| `main` | 141 | 101 | 40 | 63 | 0 | 49,5 % |
| `origin/refactor/ajuste-global-reglas` | 176 | 144 | 32 | 28 | 0 | 70,6 % |
| árbol de trabajo previo a esta auditoría | 141 | 101 | 40 | 63 | 0 | 49,5 % |

## 3. Funcionalidad que solo existe en producción

### Backend (módulos ausentes del repositorio)

| Ruta | Contenido |
|---|---|
| `backend/app/api/v1/endpoints/payment_agreements.py` | Acuerdos de pago: crear, aceptar, cancelar, pagar cuota |
| `backend/app/api/v1/endpoints/reports.py` | Reportes: aging, desempeño, por operador, exportación de procesos a Excel |
| `backend/app/api/v1/endpoints/dashboard.py` | `/api/v1/dashboard/stats` |
| `backend/app/api/v1/endpoints/notifications.py` | Notificaciones, contador, marcar leída, marcar todas, búsqueda |
| `backend/app/models/payment_agreement.py`, `notification.py`, `process_config.py`, `process_note.py` | Modelos de acuerdo, notificación, configuración de flujo y notas de proceso |
| `backend/app/schemas/payment_agreement.py` | Esquemas de acuerdo e installment |
| `backend/app/tasks/` (`document_tasks.py`, `state_expiration.py`) | Tareas asíncronas con `backend/app/celery_app.py` |
| `backend/app/core/db_utils.py` | Utilidades de acceso a datos |
| `backend/tests/test_processes_dashboard.py` | Pruebas de procesos y dashboard |
| `scripts/seed_transitions.py` | Semilla de transiciones de flujo |
| 5 migraciones Alembic | `004_tenant_process_configs`, `005_process_notes`, `005_user_tenants`, `006_payment_agreements`, `007_notifications` |

### Frontend (vistas y componentes ausentes del repositorio)

`frontend/src/views/AcuerdosView.vue`, `ExpedienteView.vue`, `ReportesView.vue`,
`WorkflowDesignerView.vue`, `frontend/src/components/GlobalSearch.vue`,
`frontend/src/components/NotificationBell.vue`.

### Contrato de API verificado contra el backend vivo

Producción expone **84 rutas**; la rama `refactor/ajuste-global-reglas` solo declara 51. Las 33
rutas restantes no existen en ninguna rama (listado completo en `12_rutas_api_prod_vs_local.txt`),
entre ellas:

```
/api/v1/payment-agreements/            /api/v1/payment-agreements/{id}/accept
/api/v1/payment-agreements/{id}/cancel /api/v1/payment-agreements/{id}/installments/{iid}/pay
/api/v1/processes/{id}/expedient       /api/v1/processes/{id}/notes
/api/v1/processes/{id}/timeline        /api/v1/processes/{id}/transition
/api/v1/reports/aging                  /api/v1/reports/performance
/api/v1/reports/operator/{user_id}     /api/v1/reports/export/processes-excel
/api/v1/notifications/*                /api/v1/workflows/designer
/api/v1/workflows/bulk-transition      /api/v1/dashboard/stats
```

Detectada también una ruta que solo existe en `main` y ya fue eliminada en producción:
`/api/v1/auth/users` (migró a `/api/v1/users/*`).

### Archivos versionados cuyo contenido difiere en producción (32 frente a la rama)

Los cambios más pesados, por líneas de diff:

| Archivo | Líneas de diff |
|---|---|
| `frontend/src/views/ProcesosView.vue` | 1233 |
| `frontend/src/views/WorkflowView.vue` | 993 |
| `backend/app/api/v1/endpoints/processes.py` | 869 |
| `frontend/src/views/DashboardView.vue` | 735 |
| `backend/app/api/v1/endpoints/workflows.py` | 666 |
| `backend/run_migrations.py` | 333 |
| `frontend/src/views/LoginView.vue` | 288 |
| `frontend/src/services/api.js` | 266 |
| `frontend/src/components/Layout.vue` | 187 |
| `backend/app/schemas/process.py` | 172 |

Completan la lista `api.py`, `auth.py`, `users.py`, `config.py`, `database.py`, `dependencies.py`,
`main.py`, `models/__init__.py`, `models/user.py`, `repositories/user.py`, `schemas/auth.py`,
`schemas/workflow.py`, `document_generation_service.py`, `docker-compose.yml`,
`frontend/package.json`, `AppMenu.vue`, `main.js`, `router/index.js`, `stores/auth.js`,
`DocumentosView.vue` y dos migraciones Alembic. Cada diff está guardado en
`auditoria/produccion/diffs/rama__*.diff`.

## 4. Cómo está desplegado (condiciones que afectan el trabajo diario)

- **Sin repositorio en el servidor**: `/opt/cyberrit` no tiene `.git`; la única trazabilidad era el
  archivo `.last_update`. Los scripts de despliegue versionados apuntan a rutas de otra máquina
  (`/home/chandero/...`) y a una clave `/home/chandero/.ssh/id_ed25519`, que no coinciden con este
  equipo (`~/.ssh/id_ed25519_tmsoft`).
- **El backend se ejecuta desde el código en disco**: `cartera_backend` monta `./backend:/app` y
  corre `uvicorn --reload`. Editar en el servidor cambia la aplicación en caliente, que es justo lo
  que produjo la deriva de agosto.
- **El frontend se sirve desde la imagen**: `cartera_frontend` no tiene volúmenes; su `index.html`
  (27-ago 19:12) es idéntico al `dist` en disco, con `/assets/index-C-vhG3i0.js` y
  `/assets/index-CUMNJegx.css`. Los 56 chunks del build incluyen `AcuerdosView`, `ExpedienteView`,
  `ReportesView` y `WorkflowDesignerView`, pruebas definitivas de que el build en línea no proviene
  de ninguna rama publicada. La rama fija en cambio `index-D6YcdXdU.js`.
- **Base de datos real**: el compose declara `DB_PATH=/opt/riap/db/cartera.db`, pero el `.env` del
  servidor dirige la aplicación a `backend/test.db`, que es la base activa: 25 tablas, 1309 clients,
  1417 obligations, 30 payment_agreements, 0 notifications. `/opt/riap/db/cartera.db` tiene solo 16
  tablas y `alembic_version = d6276b05fcf1`: es una base abandonada que no refleja el esquema real.
- **Estado de imágenes**: `cyberrit-backend` creada hace 3 meses, `cyberrit-frontend` hace 2; los
  contenedores llevan 3 semanas en ejecución. El backend no necesita reconstruir imagen por el bind
  mount, pero el frontend sí: cambiar vistas exige `docker compose build frontend`.
- Exposición pública del API: `/docs` y `/openapi.json` respondiendo en producción sin autenticación.

## 5. Riesgos y deuda técnica detectados

1. Meses de funcionalidad productiva fuera de control de versiones (28 archivos y 33 rutas).
2. Migraciones Alembic duplicadas en el servidor: conviven `005_process_notes.py` y
   `005_user_tenants.py` con prefijo de revisión repetido, lo que puede romper `alembic upgrade`.
3. Producción corre con `ENVIRONMENT=development`, `DEBUG=True` y `--reload`; `SECRET_KEY` admite un
   valor de respaldo codificado en el compose.
4. La base de datos de trabajo (`backend/test.db`) vive dentro del árbol de código y viaja con los
   rsync de despliegue: riesgo de sobrescritura en el siguiente despliegue.
5. Artefactos contaminando el repositorio: `ResolucionesView.vue.bak` (1036 líneas), `.pyc` y
   `__pycache__` versionados en la rama, `frontend/index.prod.html` con hashes de build fijados a
   mano.
6. Copias duplicadas del build (`frontend/dist` en disco y dentro de la imagen) y dos hosts activos
   (`giron.tiksgroup.co` vs `giron.cyberrit.tiksgroup.co`) que prestan a desplegar sobre el sitio
   equivocado.
7. En `/opt/cyberrit` se observó `examples/examples/` con CSVs duplicados (subproducto de un rsync
   con ruta anidada); no se incorporó a la línea base.
8. Deuda preexistente del repositorio, no introducida por esta auditoría: `.env` está versionado
   desde antes en `main` y en la rama (con `SECRET_KEY` y credenciales de base de datos reales), y
   hay 40 archivos `__pycache__/*.pyc` bajo control de versiones. El vuelco de producción **no tocó
   ninguno de esos archivos** (`git diff 4997a0f HEAD` no los incluye), pero deberían retirarse del
   índice con `git rm --cached` y la clave debería rotarse, porque ya está publicada en GitHub.
9. `/docs` y `/openapi.json` del backend de producción son accesibles sin autenticación: exponen el
   mapa completo del API, incluidos los módulos de acuerdos de pago y reportes.

## 6. Línea base creada

- Rama `baseline/produccion-20261124`, construida desde `origin/refactor/ajuste-global-reglas` y
  ajustada para quedar **byte a byte igual** al código del servidor.
- Validación: `hashes_baseline.txt` frente a `hashes_remoto.txt` → **0 diferencias** en los 204
  archivos de código (`13_diff_hash_baseline_vs_prod.txt` vacío).
- Sin datos ni secretos versionados: se excluyeron `*.db`, `.env`, `frontend/dist`, `node_modules`,
  `logs`, `backups`, `generados` y `.qoder`. Se añadieron esas entradas a `.gitignore`.
- Las plantillas subidas (`backend/app/uploads/templates`) se sincronizaron solo añadiendo, sin
  borrar las locales.
- Etiqueta `prod-20261124` sobre ese commit.

## 8. Validación de la línea base

| Comprobación | Resultado |
|---|---|
| Hashes md5 de la rama frente al árbol del servidor | **204/204 idénticos, 0 diferencias** (`13_diff_hash_baseline_vs_prod.txt` vacío) |
| Falsos cambios de modo (755 heredados del servidor) | 0 tras `normalizar_permisos.sh` |
| Sintaxis de los 95 módulos `backend/app/**/*.py` | 0 errores de análisis |
| `docker compose config` local | válido |
| Arranque local de la línea base (`docker compose up -d --build`) | contenedores `cartera_*` creados y en ejecución; `GET :8055/health` devolvió `{"status":"healthy"}` |
| Contrato del backend local vs producción | **84 rutas locales / 84 rutas en producción, 0 diferencias** |
| Build local del frontend a partir del código recuperado | `index.html` sirve `/assets/index-C-vhG3i0.js`, **el mismo hash del bundle desplegado** |
| Datos o artefactos versionados por error | ninguno nuevo: `*.db`, `.env`, `frontend/dist`, `node_modules`, `generados` y `.qoder` quedaron excluidos |
| Estado del servidor tras la auditoría | intacto: solo órdenes de lectura, sin escrituras, reinicios ni reconstrucciones |

Los contenedores locales se detuvieron con `docker compose down` al terminar la validación. Para
volver a levantar el entorno: `docker compose up -d --build` (backend en `:8055`, frontend en `:5055`).

## 9. Recomendaciones para arrancar la nueva tarea

1. Trabajar desde `baseline/produccion-20261124`, no desde `main`. `main` queda a 4 commits de la
   rama y a 63 archivos de producción.
2. Antes de tocar nada, reconstruir el frontend en el servidor (`docker compose build frontend`)
   solo cuando haya cambios de vistas, porque el contenedor no monta el `dist`.
3. Unificar el destino de la base de datos: mover la base activa fuera del árbol de código y hacer
   que compose y `.env` apunten a la misma ruta; hoy `cartera.db` y `test.db` cuentan historias
   distintas.
4. Eliminar del repo los `.bak` y `__pycache__` versionados, y normalizar los prefijos de revisión
   Alembic antes de generar la siguiente migración.
5. Definir cómo se promoverá código al servidor (rsync con `--delete` es peligroso con bases en el
   árbol) y registrar el commit desplegado en `.last_update` para que el próximo inventario sea
   inmediato.

## 10. Índice de anexos

| Archivo | Contenido |
|---|---|
| `hashes_remoto.txt`, `hashes_main.txt`, `hashes_rama.txt`, `hashes_working_tree.txt`, `hashes_baseline.txt` | Árboles de md5 por referencia |
| `11_resumen_comparacion.csv` | Matriz de conteos |
| `11_distintos_*`, `11_solo_servidor_*`, `11_solo_referencia_*` | Listados por categoría |
| `diffs/` | 72 diffs unificados (rama y main contra producción) |
| `12_rutas_api_prod_vs_local.txt` | Rutas del API en producción vs cada referencia |
| `13_diff_hash_baseline_vs_prod.txt` | Verificación de la línea base (vacío = idéntico) |
| `15_arranque_docker_local.log`, `16_validacion_runtime.txt` | Arranque y validación de contrato del entorno local |
| `01_metadata.txt`, `02_listado_mtimes.txt`, `03_frontend_dist.txt`, `04_openapi_prod.json`, `05_datos_inventario.txt`, `06_inventario_modulos.txt`, `07_health_y_frontend_contenedor.txt` | Capturas del servidor |
| `config/` | compose, nginx activo, Dockerfiles, nombres de variables `.env`, hallazgos de configuración |
