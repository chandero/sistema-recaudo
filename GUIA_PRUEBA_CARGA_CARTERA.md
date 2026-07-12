# Guía Completa para Prueba de Carga de Cartera

## Descripción

Esta guía proporciona instrucciones detalladas para realizar una excelente prueba de la funcionalidad de carga de cartera en el sistema de recaudo.

## Datos de Ejemplo

Se ha creado un archivo de ejemplo con datos realistas de cartera que contiene:

- 10 registros de contribuyentes
- Información completa de clientes (identificación, nombre, dirección, teléfono, correo electrónico, ciudad y departamento)
- Información completa de obligaciones (número de obligación, vigencia, valor total, capital, intereses, mora, fechas de emisión y vencimiento)

## Estructura del Archivo de Ejemplo

El archivo `examples/cartera_ejemplo.csv` contiene las siguientes columnas:

| Columna | Tipo | Descripción |
|--------|------|-------------|
| identificacion | Texto | Identificación del contribuyente (cédula o NIT) |
| nombre | Texto | Nombre completo o razón social del contribuyente |
| direccion | Texto | Dirección del contribuyente |
| telefono | Texto | Número de teléfono del contribuyente |
| email | Texto | Correo electrónico del contribuyente |
| ciudad | Texto | Ciudad del contribuyente |
| departamento | Texto | Departamento del contribuyente |
| numero_obligacion | Texto | Número de la obligación fiscal |
| vigencia | Texto | Vigencia de la obligación |
| valor_total | Numérico | Valor total de la obligación |
| capital | Numérico | Valor del capital adeudado |
| intereses | Numérico | Valor de intereses |
| mora | Numérico | Valor por concepto de mora |
| fecha_emision | Fecha | Fecha de emisión de la obligación |
| fecha_vencimiento | Fecha | Fecha de vencimiento de la obligación |

## Pasos para Realizar la Prueba

### 1. Acceder al Sistema
- Iniciar sesión en el sistema de recaudo
- Navegar a la sección de "Importar Cartera"

### 2. Cargar el Archivo de Ejemplo
- Hacer clic en el botón "Nueva Importación"
- Seleccionar el archivo `examples/cartera_ejemplo.csv` o `examples/cartera_ejemplo.xlsx`
- Esperar a que el sistema detecte las columnas

### 3. Verificar el Mapeo Automático
- Observar cómo el sistema sugiere automáticamente el mapeo de columnas
- Confirmar que las columnas se han asociado correctamente a los campos del sistema:
  - identificacion → identificacion
  - nombre → nombre
  - direccion → direccion
  - telefono → telefono
  - email → email
  - ciudad → ciudad
  - departamento → departamento
  - numero_obligacion → numero_obligacion
  - vigencia → vigencia
  - valor_total → valor_total
  - capital → capital
  - intereses → intereses
  - mora → mora
  - fecha_emision → fecha_emision
  - fecha_vencimiento → fecha_vencimiento

### 4. Procesar la Importación
- Hacer clic en "Procesar Importación"
- Monitorear el progreso de la importación
- Verificar que se completen todos los pasos sin errores

### 5. Validar Resultados
- Revisar el resumen de la importación
- Confirmar que se hayan procesado las 10 filas correctamente
- Verificar que se hayan creado 10 clientes y 10 obligaciones
- Comprobar que los datos se hayan almacenado correctamente en la base de datos

### 6. Probar Funcionalidades Adicionales
- Probar la creación de una plantilla de mapeo
- Guardar la configuración actual como plantilla reutilizable
- Probar la vista previa de la plantilla guardada
- Probar la funcionalidad de edición y eliminación de plantillas

## Escenarios de Prueba Adicionales

### Prueba con Errores Controlados
- Modificar el archivo de ejemplo introduciendo valores inválidos (ej. caracteres en campos numéricos)
- Verificar que el sistema detecte y reporte adecuadamente los errores

### Prueba con Campos Faltantes
- Eliminar algunos campos opcionales del archivo
- Confirmar que la importación continúa funcionando correctamente

### Prueba de Rendimiento
- Generar un archivo más grande con cientos de registros
- Medir el tiempo de procesamiento y uso de recursos

## Consideraciones Técnicas

### Validaciones del Sistema
- El sistema verifica que estén presentes los campos requeridos: identificación, nombre, número de obligación y valor total
- Se valida que los campos numéricos contengan valores válidos
- Se verifica que las fechas tengan formato correcto

### Manejo de Registros Duplicados
- El sistema debe detectar clientes existentes y actualizar la información
- Las obligaciones deben verificarse para evitar duplicados

### Seguridad y Permisos
- Verificar que solo usuarios autorizados puedan acceder a la funcionalidad
- Confirmar que los datos se importan solo para el tenant correcto

## Resultados Esperados

- Importación exitosa de todos los registros
- Creación de clientes y obligaciones en la base de datos
- Registro de la operación en el historial de importaciones
- Disponibilidad de la plantilla de mapeo para usos futuros

## Reporte de la Prueba

Para cada ejecución de prueba, documentar:
- Fecha y hora de la prueba
- Usuario que realizó la prueba
- Archivo utilizado
- Número de registros procesados
- Errores detectados (si aplica)
- Tiempo de procesamiento
- Observaciones generales