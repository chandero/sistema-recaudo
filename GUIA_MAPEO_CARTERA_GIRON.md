# Guía de Mapeo para Cartera de Impuesto de Alumbrado Público de Girón

## Descripción

Este documento describe cómo mapear los datos del archivo `cartera_giron_2026_final.csv` para importarlos al sistema de recaudo como cartera del impuesto de alumbrado público de Girón a marzo de 2026.

## Estructura del Archivo

El archivo `cartera_giron_2026_final.csv` contiene la siguiente estructura:

| Columna | Nombre Original | Descripción | Mapeo Recomendado |
|---------|----------------|-------------|-------------------|
| 1 | cod_municipio | Código del municipio | No mapear directamente |
| 2 | municipio | Nombre del municipio | ciudad |
| 3 | ciclo | Ciclo de facturación | No mapear directamente |
| 4 | cuenta | Número de cuenta | numero_obligacion |
| 5 | nombre | Nombre del contribuyente | nombre |
| 6 | tipo_documento | Tipo de documento de identidad | No mapear directamente (pero útil para referencia) |
| 7 | documento_identidad | Número de documento de identidad | identificacion |
| 8 | ficha_catastral | Ficha catastral | No mapear directamente |
| 9 | direccion | Dirección del contribuyente | direccion |
| 10 | clase_servicio | Clase de servicio | No mapear directamente |
| 11 | antiguedad | Antigüedad del servicio | No mapear directamente |
| 12 | valor_alpu | Valor de la deuda de alumbrado público | valor_total |

## Mapeo Recomendado

Para importar correctamente los datos al sistema, se recomienda el siguiente mapeo:

- **identificacion** ← documento_identidad
- **nombre** ← nombre
- **direccion** ← direccion
- **ciudad** ← municipio
- **numero_obligacion** ← cuenta
- **valor_total** ← valor_alpu

## Consideraciones Especiales

1. El campo `valor_alpu` contiene valores monetarios que pueden requerir tratamiento especial para asegurar que el separador decimal sea compatible (usando punto en lugar de coma).

2. El campo `direccion` puede contener direcciones muy largas o con caracteres especiales que deben ser manejados adecuadamente.

3. El campo `nombre` puede contener nombres de personas naturales o jurídicas, por lo que podría ser necesario determinar el tipo de contribuyente según el `tipo_documento`.

4. El año de vigencia para todas las obligaciones debería ser 2026 según el nombre del archivo.

## Datos Complementarios

Dado que el sistema requiere algunos campos que no están en el archivo original, se recomienda:

- **departamento**: Todos los registros son de Girón, por lo tanto, el departamento es "Santander"
- **vigencia**: Establecer como "2026" para todas las obligaciones
- **telefono**, **email**: No disponibles en el archivo original, dejar vacíos o solicitar en otro proceso

## Procedimiento de Importación

1. Acceder al sistema de recaudo
2. Navegar a la sección de importación
3. Cargar el archivo `cartera_giron_2026_final.csv`
4. Aplicar el mapeo recomendado anterior
5. Establecer valores predeterminados:
   - Departamento: "Santander"
   - Vigencia: "2026"
6. Validar el archivo antes de procesar
7. Confirmar e iniciar la importación

## Validación de Datos

Antes de la importación, se recomienda validar:

- Que todos los documentos de identidad tengan formato válido
- Que los valores monetarios no contengan caracteres no numéricos
- Que no haya duplicados en los números de cuenta
- Que las direcciones no excedan la longitud máxima permitida

## Notas Adicionales

Este archivo proviene de Electrificadora de Santander S.A. ESP y contiene información de clientes con deuda de alumbrado público en Girón, con antigüedad mínima de 3 meses y saldo mayor a 0.