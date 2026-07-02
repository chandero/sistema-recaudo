# Cambios Realizados - Estado NOTIFICACION_WEB_PUBLICADA

## Resumen
Se agregó el estado `NOTIFICACION_WEB_PUBLICADA` al workflow de cobro de cartera para cubrir el escenario donde, después de fallar la entrega física de correspondencia, se realiza la notificación mediante publicación en la página web de la entidad (fijación en lista).

## Archivos Modificados

### 1. `/workspace/backend/app/models/workflow.py`
- **Cambio**: Agregado `NOTIFICACION_WEB_PUBLICADA = "NOTIFICACION_WEB_PUBLICADA"` al enum `WorkflowStateCode`
- **Ubicación**: Línea 20, entre `NOTIFICACION_DEVUELTA` y `REINTENTO_NOTIFICACION`

### 2. `/workspace/backend/app/schemas/workflow.py`
- **Cambio**: Agregado `NOTIFICACION_WEB_PUBLICADA = "NOTIFICACION_WEB_PUBLICADA"` al enum `WorkflowStateCode` del schema
- **Ubicación**: Línea 17, manteniendo consistencia con el modelo

### 3. `/workspace/backend/app/db/seed_workflow.py` (Nuevo Archivo)
- **Propósito**: Script de seed inicial para crear los estados y transiciones del workflow
- **Contenido**:
  - 21 estados del workflow incluyendo el nuevo `NOTIFICACION_WEB_PUBLICADA`
  - Transiciones configuradas con reglas automáticas
  - El nuevo estado tiene:
    - Orden: 10
    - Max días: 10
    - Descripción: "Notificación publicada en página web de la entidad (fijación en lista)"
  
- **Transiciones relacionadas con el nuevo estado**:
  - `ESPERANDO_RESULTADO_NOTIFICACION` → `NOTIFICACION_WEB_PUBLICADA` (condición: web_publication)
  - `NOTIFICACION_DEVUELTA` → `NOTIFICACION_WEB_PUBLICADA` (condición: web_after_return)
  - `NOTIFICACION_WEB_PUBLICADA` → `ESPERANDO_PAGO_VOLUNTARIO` (flujo normal)

### 4. Correcciones de Modelos Relacionados
Se corrigieron los campos de tipo `dict` en los siguientes modelos para usar correctamente SQLAlchemy JSON column:

- **`app/models/process.py`**: 
  - Campo `metadata` renombrado a `extra_data` (reservado en SQLAlchemy)
  - Uso correcto de `Column(SAJSON)` 

- **`app/models/document.py`**:
  - Campos `variables_schema` y `variables_used` corregidos

- **`app/models/import_template.py`**:
  - Campo `column_mapping` corregido

## Flujo Actualizado del Workflow

El flujo completo ahora incluye 21 estados:

1. CARTERA_CARGADA
2. OBLIGACION_VALIDADA
3. PENDIENTE_ASIGNACION_RESOLUCION
4. RESOLUCION_RADICADOS_ASIGNADOS
5. DOCUMENTO_NOTIFICACION_GENERADO
6. NOTIFICACION_ENVIADA
7. ESPERANDO_RESULTADO_NOTIFICACION
8. NOTIFICACION_ENTREGADA
9. NOTIFICACION_DEVUELTA
10. **NOTIFICACION_WEB_PUBLICADA** ← NUEVO
11. REINTENTO_NOTIFICACION
12. ESPERANDO_PAGO_VOLUNTARIO
13. COBRO_PERSUASIVO
14. ACUERDO_DE_PAGO
15. SEGUIMIENTO_ACUERDO
16. ACUERDO_INCUMPLIDO
17. COBRO_PREJURIDICO
18. COBRO_COACTIVO
19. PAGADO [FINAL]
20. ARCHIVADO [FINAL]
21. INCOBRABLE [FINAL]

## Próximos Pasos Sugeridos

1. Ejecutar migraciones de base de datos para agregar el nuevo estado
2. Actualizar el frontend Vue 3 para mostrar el nuevo estado en:
   - Dashboard del workflow
   - Vista Kanban
   - Selector de transiciones
3. Implementar endpoint para registrar la URL y fecha de publicación web
4. Agregar campo opcional `web_publication_url` y `web_publication_date` en el modelo de proceso o historial

## Comandos Útiles

```bash
# Ejecutar el seed del workflow
cd /workspace/backend
python app/db/seed_workflow.py

# Verificar que el modelo carga correctamente
python -c "from app.models.workflow import WorkflowStateCode; print(WorkflowStateCode.NOTIFICACION_WEB_PUBLICADA)"
```
