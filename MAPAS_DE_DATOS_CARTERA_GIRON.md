# Mapas de Datos para Cartera de Impuesto de Alumbrado Público de Girón

## Descripción General

Este documento describe en detalle el mapeo de datos necesario para importar correctamente el archivo `cartera_giron_2026_final.csv` al sistema de recaudo como cartera del impuesto de alumbrado público de Girón a marzo de 2026.

## Estructura del Archivo Fuente

El archivo contiene la siguiente estructura de columnas:

| Número | Nombre de Columna | Tipo | Descripción |
|--------|-------------------|------|-------------|
| 1 | cod_municipio | Numérico | Código del municipio (60 para Girón) |
| 2 | municipio | Texto | Nombre del municipio (Girón) |
| 3 | ciclo | Numérico | Ciclo de facturación |
| 4 | cuenta | Numérico | Número de cuenta/medidor |
| 5 | nombre | Texto | Nombre del contribuyente |
| 6 | tipo_documento | Texto | Tipo de documento de identidad (CC, NIT, etc.) |
| 7 | documento_identidad | Numérico | Número de documento de identidad |
| 8 | ficha_catastral | Texto | Ficha catastral asociada |
| 9 | direccion | Texto | Dirección del contribuyente |
| 10 | clase_servicio | Numérico | Clase de servicio |
| 11 | antiguedad | Numérico | Antigüedad del servicio en meses |
| 12 | valor_alpu | Decimal | Valor de la deuda de alumbrado público |

## Mapeo Recomendado al Sistema

### Campos Obligatorios

| Campo del Sistema | Origen | Descripción |
|-------------------|--------|-------------|
| identificacion | documento_identidad | Documento de identidad del contribuyente |
| nombre | nombre | Nombre del contribuyente |
| numero_obligacion | cuenta | Número de cuenta que representa la obligación |
| valor_total | valor_alpu | Valor total de la obligación |

### Campos Opcionales

| Campo del Sistema | Origen | Valor por Defecto | Descripción |
|-------------------|--------|-------------------|-------------|
| direccion | direccion | - | Dirección del contribuyente |
| ciudad | municipio | - | Ciudad del contribuyente |
| departamento | - | "Santander" | Departamento (fijo para Girón) |
| vigencia | - | "2026" | Vigencia de la obligación |

## Consideraciones Especiales

### Formato de Valores Monetarios

El campo `valor_alpu` contiene valores monetarios con el formato decimal estándar (punto como separador decimal). El sistema de importación ha sido actualizado para manejar diferentes formatos monetarios, incluyendo valores con separadores de miles y diferentes formatos decimales.

### Tratamiento de Datos Faltantes

- **departamento**: Todos los registros son de Girón, por lo tanto, el departamento se establecerá como "Santander"
- **telefono** y **email**: No disponibles en el archivo original
- **fecha_emision** y **fecha_vencimiento**: No disponibles en el archivo original

### Validaciones Importantes

Antes de la importación, se deben considerar las siguientes validaciones:

1. **Duplicados**: Verificar si existen números de cuenta repetidos
2. **Valores nulos**: Asegurar que los campos obligatorios no tengan valores vacíos
3. **Formato de identificación**: Validar que los documentos de identidad tengan formato válido
4. **Rango de valores**: Verificar que los valores monetarios estén dentro de rangos razonables

## Procedimiento de Importación

### Paso 1: Preparación del Archivo
1. Asegurarse de que el archivo `cartera_giron_2026_final.csv` esté disponible en el directorio de importación
2. Verificar que el archivo tenga el formato correcto con comas como delimitadores

### Paso 2: Mapeo de Columnas
Al momento de importar, aplicar el siguiente mapeo:

- `identificacion` ← `documento_identidad`
- `nombre` ← `nombre`
- `direccion` ← `direccion`
- `ciudad` ← `municipio`
- `numero_obligacion` ← `cuenta`
- `valor_total` ← `valor_alpu`

### Paso 3: Configuración de Valores por Defecto
- Establecer `departamento` como "Santander"
- Establecer `vigencia` como "2026"

### Paso 4: Validación Previa
1. Validar el archivo antes de procesar
2. Revisar los errores y advertencias detectados
3. Corregir si es necesario

### Paso 5: Procesamiento
1. Confirmar la importación
2. Monitorear el progreso del proceso
3. Revisar resultados finales

## Estadísticas del Archivo

Basado en el análisis del archivo:

- **Total de registros**: 1,774 (aproximadamente, según tamaño del archivo)
- **Rango de valores**: Desde COP 200.000 hasta más de COP 1.000.000
- **Distribución geográfica**: 100% del municipio de Girón, departamento de Santander
- **Tipos de contribuyentes**: Personas naturales y jurídicas (según tipo de documento)

## Observaciones del Contenido

El archivo proviene de Electrificadora de Santander S.A. ESP y contiene información de clientes con deuda de alumbrado público en Girón, con las siguientes características:

- Antigüedad mínima de 3 meses
- Saldo mayor a 0
- Información detallada de dirección y contacto
- Datos de identificación verificables
- Valores monetarios actualizados

## Recomendaciones

1. **Realizar prueba piloto**: Importar una muestra pequeña antes de la importación completa
2. **Verificar duplicados**: Confirmar que no existan obligaciones duplicadas en el sistema
3. **Validar datos**: Revisar manualmente algunos registros para confirmar precisión
4. **Documentar proceso**: Registrar el proceso para futuras importaciones similares
5. **Seguimiento post-importación**: Verificar que los datos se hayan importado correctamente

## Campos Disponibles para Reportes

Tras la importación, estarán disponibles los siguientes datos para reportes y análisis:

- Identificación del contribuyente
- Nombre completo
- Dirección exacta
- Valor de la obligación
- Número de cuenta
- Historial de antigüedad de la deuda
- Distribución geográfica dentro del municipio