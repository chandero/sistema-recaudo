# Auto de Archivo (GD-F.03) y Constancia Secretarial (GD-F.01)

Generación manual, individual o por selección múltiple, de dos documentos nuevos
sobre las plantillas oficiales recibidas. No sustituye ni modifica el acto
administrativo GD-F.03 que hoy se produce en producción: conviven los tres.

Salidas: DOCX, PDF o ambos. Cada archivo se empaqueta en un ZIP
(`correspondencia_<tipo>_<marca>.zip`) y, si se marca la opción, se envía al
correo del cliente con los documentos adjuntos.

## Endpoints

| Método | Ruta | Cuerpo |
| --- | --- | --- |
| POST | `/api/v1/documents/auto-archivo/preview` | `{obligation_ids}` |
| POST | `/api/v1/documents/constancia/preview` | `{obligation_ids}` |
| POST | `/api/v1/documents/auto-archivo/generate` | ver abajo |
| POST | `/api/v1/documents/constancia/generate` | ver abajo |
| PUT | `/api/v1/documents/templates/{code}/content` | multipart `file` (DOCX) |

Cuerpo de `generate`:

```json
{
  "obligation_ids": [1, 2],
  "formato": "docx | pdf | ambos",
  "fechas": { "1": { "fecha_pago": "2024-12-19" } },
  "persistir_fechas": true,
  "enviar_correo": false,
  "destinatarios": { "1": "deudor@example.com" }
}
```

El `preview` devuelve por fila el contexto resuelto, las fechas derivadas, los
`problemas` (bloqueantes: sin resolución, sin fecha de pago, sin fecha de
ejecutoria) y las `advertencias` (informativas: cliente sin correo). El botón
**Generar** del diálogo queda deshabilitado mientras exista un bloqueante.

Respuesta de `generate`: ZIP con cabeceras `X-Document-Count`, `X-File-Count`,
`X-Email-Sent` y `X-Email-Failed`.

## Plantillas y variables

Archivos versionados en `backend/app/uploads/templates/`:

- `1_auto_de_archivo.docx` — código `AUTO_ARCHIVO`
  `numero_resolucion`, `fecha_resolucion`, `cuenta_usuario`, `direccion_usuario`,
  `nombre_usuario`, `documento_usuario`, `fecha_pago`
- `1_constancia_secretarial.docx` — código `CONSTANCIA_SECRETARIAL`
  `fecha_constancia`, `numero_resolucion`, `fecha_resolucion_larga`,
  `cuenta_usuario`, `direccion_usuario`, `nombre_usuario`, `documento_usuario`,
  `fecha_ejecutoria_larga` (el formato repite el bloque dos veces en el mismo
  archivo; ambos se resuelven con el mismo contexto)

Origen de los datos:

| Variable | Fuente |
| --- | --- |
| `numero_resolucion`, `fecha_resolucion` | `obligation.resolution_number` / `resolution_date` |
| `nombre_usuario`, `documento_usuario`, `direccion_usuario` | `Client.name`, `identification`, `address` |
| `cuenta_usuario` | `obligation.description` (mismo criterio del acto administrativo) |
| `fecha_pago` | `obligation.paid_date`; si es nula, el último paso del proceso a `PAGADO`/`ARCHIVADO` |
| `fecha_ejecutoria_larga` | `obligation.executory_date` |
| `fecha_constancia` | `notification_date` o la fecha del día |

Los firmantes y el texto normativo quedan impresos en la plantilla, tal como
llegaron los formatos. Las fechas largas se emiten como `09 de Abril de 2025`.

Los DOCX originales traían datos reales de deudores, por eso **no se versionan**:
viven en `plantillas_nuevas/` (excluido en `.gitignore`) y solo entran al
repositorio las plantillas convertidas. Para regenerarlas:

```bash
cd backend
python3 scripts/convierte_plantillas.py ../plantillas_nuevas
```

El script verifica el número exacto de apariciones de cada valor; si la
plantilla oficial cambia, falla en vez de generar un documento a medias.

### Reemplazar una plantilla existente

La generación siempre lee el binario guardado en `document_templates.content`, no
el archivo de disco: el cambio surte efecto en la petición siguiente, sin
reiniciar el servicio.

**Desde la interfaz** — Documentos → pestaña *Plantillas* → botón *Reemplazar* de
la fila. Llama a `PUT /api/v1/documents/templates/{code}/content` (multipart,
`file`) y devuelve la plantilla con su nueva `version` y el `variables_schema`
recalculado. Rechaza con 400 cuando:

- la extensión no es `.docx`/`.dotx`, el archivo está vacío o pasa de 10 MB;
- el DOCX no tiene variables `{{...}}`: imprimiría lo mismo para todos los casos
  y conservaría los datos del archivo original (error típico al subir el formato
  oficial ya diligenciado);
- falta alguna variable obligatoria del código, según
  `VARIABLES_OBLIGATORIAS` en `backend/app/services/template_utils.py`.

Las variables no reconocidas no bloquean: se guardan en
`variables_schema.desconocidas` y la interfaz las muestra como advertencia
(docxtpl las resuelve vacías).

El reemplazo también sobrescribe el archivo espejo de la plantilla
(`1_auto_de_archivo.docx` / `1_constancia_secretarial.docx`) para que
`registrar_plantillas.py` no revierta el binario la próxima vez que se ejecute.
Si esa escritura en disco falla, la plantilla queda aplicada igualmente en la
base de datos y se avisa con la cabecera `X-Template-Warning`.

**Por consola** — sustituir el archivo en `backend/app/uploads/templates/` con el
mismo nombre y ejecutar `python scripts/registrar_plantillas.py`: compara bytes,
informa `IGUAL` si no cambió y `ACTUALIZA` (subiendo `version`) si cambió.

Si el cambio de formato agrega un dato variable nuevo, hay que declararlo en
`_contexto_documento` y en `ETIQUETAS_PLACEHOLDER`. Si solo cambia el diseño
(logos, firmas, texto normativo), basta con subir el DOCX con las mismas
variables.

## Columnas nuevas

`obligations.paid_date`, `obligations.notification_date`,
`obligations.executory_date` (todas `DATE` nullable).

- Migración: `backend/alembic/versions/009_fechas_documentos.py`
  (`down_revision = 008_merge_cabeceras`).
- `backend/run_migrations.py` las declara en `EXPECTED_COLUMNS`, así que la ruta
  de despliegue sin alembic también las valida.
- Editables en el formulario de Obligaciones y corrigibles en el diálogo de
  generación. Si se marca «Guardar las fechas en la obligación», lo digitado se
  persiste; si no, la corrección aplica solo a ese documento.

## Despliegue en giron.cyberrit.tiksgroup.co

```bash
# 1. Sincronizar código de la rama (incluye las dos plantillas convertidas)
rsync -av --delete backend/app/uploads/templates/ \
  /opt/cyberrit/backend/app/uploads/templates/

# 2. Aplicar la migración 009 dentro del contenedor
docker compose exec backend alembic current      # debe mostrar 008_merge_cabeceras
docker compose exec backend alembic upgrade head # agrega las tres columnas DATE

# 3. Registrar las plantillas en document_templates (idempotente, un registro por tenant)
docker compose exec backend python scripts/registrar_plantillas.py --dry-run
docker compose exec backend python scripts/registrar_plantillas.py

# 4. Correo: verificar SMTP en .env antes de usar «Enviar al correo del cliente»
#    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL
docker compose exec backend python -c "from app.core.config import settings; \
  print(bool(settings.SMTP_SERVER and settings.SMTP_USER))"

# 5. Reiniciar backend y frontend
docker compose up -d --build backend frontend
```

Si el paso 2 falla por deriva de esquema (la base activa no está stampada),
primero `alembic stamp 008_merge_cabeceras` y luego `upgrade head`; el procedimiento
está en `auditoria/produccion/RUNBOOK_RIESGOS.md`, sección 6.

El paso 3 puede repetirse cada vez que el funcionario actualice un DOCX: si el
binario no cambió, el script informa `IGUAL` y no toca la fila; si cambió,
incrementa `version`.

## Pruebas

```bash
docker compose run --rm backend pip install -r requirements-dev.txt
docker compose run --rm backend python3 -m pytest tests -q
```

`backend/tests/test_correspondencia_documentos.py` cubre formatos de fecha,
derivación de la fecha de pago desde el historial, overrides, persistencia,
aislamiento por tenant, ZIP DOCX/PDF/ambos, conteos de correo y adjuntos del
`EmailService`. Además renderiza las dos plantillas oficiales convertidas y
exige que no quede ningún `{{ }}` sin resolver.

La conversión real a PDF requiere LibreOffice dentro del contenedor (ya se usa
para la impresión por rango del acto administrativo).

## Limits and notes

- No se generan automáticamente al cambiar el estado a pagado: la orden fue
  generación manual.
- El reemplazo de plantilla usa el mismo permiso que la subida
  (`get_current_active_user`), es decir cualquier usuario activo del tenant; la
  ruta está pensada para el funcionario que mantiene los formatos.
- Los códigos `AUTO_ARCHIVO` y `CONSTANCIA_SECRETARIAL` son distintos de
  `GD-F.03` para no chocar con el glob `{tenant}_*GD-F.03*` del endpoint
  genérico de plantillas.
- La vista `ResolucionesView.vue` (y `ObligacionesView.vue`) no usan i18n: los
  textos nuevos van en español, como el resto del archivo. Los catálogos en
  `frontend/src/locales` siguen sin emplearse en estas vistas.
- Detectado durante la implementación, **no corregido aquí**:
  `PUT/POST /api/v1/obligations/` falla porque `ObligationService` llama
  `repository.update_obligation` / `create_obligation`, métodos que no existen
  en `ObligationRepository` ni en `BaseRepository` (solo hay `create`/`update`).
  Hasta repararlo, los tres campos nuevos del formulario de Obligaciones no
  pueden guardarse por esa ruta; el diálogo de generación sí los persiste
  porque escribe la obligación directamente.
