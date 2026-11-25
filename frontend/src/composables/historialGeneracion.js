/**
 * Utilidades de presentación del histórico de generación (/documents/generated).
 *
 * Son funciones puras sobre lo que responde el backend, así que viven fuera de la vista:
 * de esa forma se pueden probar sin montar el componente y la vista queda solo con el
 * marcado. La carga de datos y su estado siguen en cada pantalla.
 */

/**
 * Convierte una marca de tiempo del backend en Date.
 *
 * El backend guarda UTC sin sufijo y FastAPI la serializa tal cual ('2026-11-25 17:29:04');
 * sin la Z el navegador la leería como hora local y el histórico mostraría una hora
 * distinta a la de la generación.
 * @param {string|Date|null} valor - Marca de tiempo recibida
 * @returns {Date|null} - Fecha interpretable, o null si el texto no es una fecha
 */
export const parseFechaUTC = (valor) => {
  if (!valor) return null
  const texto = String(valor).trim()
  const normalizada = /Z$|[+-]\d{2}:?\d{2}$/.test(texto)
    ? texto
    : `${texto.replace(' ', 'T')}Z`
  const fecha = new Date(normalizada)
  return Number.isNaN(fecha.getTime()) ? null : fecha
}

/**
 * Formatea la fecha de generación en hora local del funcionario.
 * @param {string|Date|null} valor - Campo created_at de la fila
 * @returns {string} - Ejemplo: '25 de nov 2026, 12:29 p. m.'; '-' si no hay fecha
 */
export const formatFechaHora = (valor) => {
  const fecha = parseFechaUTC(valor)
  if (!fecha) return '-'
  return fecha.toLocaleString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Etiquetas cortas de las fechas del contexto impreso.
export const ETIQUETAS_FECHA = {
  fecha_pago: 'Pago',
  fecha_resolucion: 'Resolución',
  fecha_resolucion_larga: 'Resolución',
  fecha_constancia: 'Constancia',
  fecha_notificacion: 'Notificación',
  fecha_ejecutoria: 'Ejecutoria',
  fecha_ejecutoria_larga: 'Ejecutoria'
}

/**
 * Fechas que quedaron impresas en el documento, leídas de variables_used.
 * @param {Object} documento - Fila del histórico
 * @returns {Array<{clave: string, etiqueta: string, valor: string}>} - Una entrada por fecha
 */
export const fechasUsadas = (documento) => {
  const variables = documento?.variables_used || {}
  // Solo las fechas: es lo que se pudo corregir en el diálogo y lo que quedó impreso.
  return Object.keys(variables)
    .filter((clave) => clave.startsWith('fecha_'))
    .map((clave) => ({
      clave,
      etiqueta: ETIQUETAS_FECHA[clave] || clave,
      valor: variables[clave] || '-'
    }))
}

// Trazas que guarda el backend por cada archivo del histórico. Las filas anteriores a
// este cambio llegan sin traza y eran documentos oficiales, ese es el texto de reserva.
export const ETIQUETAS_ACCION = {
  documento: 'Documento oficial',
  impresion_rango: 'Impresión por rango',
  lote_correspondencia: 'Lote de correspondencia',
  exportacion_excel: 'Exportación a Excel'
}
export const SEVERIDADES_ACCION = {
  documento: 'info',
  impresion_rango: 'warn',
  lote_correspondencia: 'secondary',
  exportacion_excel: 'success'
}

/**
 * Nombre legible de la gestión que produjo el archivo.
 * @param {Object} documento - Fila del histórico
 * @returns {string} - Texto para mostrar en la tabla
 */
export const etiquetaAccion = (documento) => ETIQUETAS_ACCION[documento?.action] || 'Documento oficial'

/**
 * Severidad del tag de gestión.
 * @param {Object} documento - Fila del histórico
 * @returns {string} - Severidad de PrimeVue
 */
export const severidadAccion = (documento) => SEVERIDADES_ACCION[documento?.action] || 'info'

// Medios de entrega registrados por el backend. Se conservan los códigos de origen porque
// distinguen por qué no salió un correo, cosa que el simple "enviado" no cuenta.
export const ETIQUETAS_ENTREGA = {
  correo: 'Enviado por correo',
  correo_fallido: 'Correo rechazado',
  correo_sin_destinatario: 'Sin correo de destino',
  correo_omitido: 'Correo omitido (SMTP)',
  zip: 'Entregado en ZIP',
  impresion: 'Para impresión',
  descarga: 'Descarga'
}
export const SEVERIDADES_ENTREGA = {
  correo: 'success',
  correo_fallido: 'danger',
  correo_sin_destinatario: 'warn',
  correo_omitido: 'warn',
  zip: 'info',
  impresion: 'secondary',
  descarga: 'secondary'
}

/**
 * Nombre legible del medio por el que salió el archivo.
 * @param {Object} documento - Fila del histórico
 * @returns {string} - Texto para mostrar; '-' cuando la fila no trae la traza
 */
export const etiquetaEntrega = (documento) => ETIQUETAS_ENTREGA[documento?.delivery_method] || '-'

/**
 * Severidad del tag de entrega: lo que no llegó al destinatario debe saltar a la vista.
 * @param {Object} documento - Fila del histórico
 * @returns {string} - Severidad de PrimeVue
 */
export const severidadEntrega = (documento) => SEVERIDADES_ENTREGA[documento?.delivery_method] || 'secondary'
