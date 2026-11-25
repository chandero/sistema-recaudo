import { describe, expect, it } from 'vitest'
import {
  etiquetaAccion,
  etiquetaEntrega,
  fechasUsadas,
  formatFechaHora,
  parseFechaUTC,
  severidadAccion,
  severidadEntrega
} from '@/composables/historialGeneracion'

describe('marca de tiempo del histórico', () => {
  it('asume UTC cuando el backend manda la hora sin sufijo', () => {
    // Regresión: sin la Z, el navegador de Colombia mostraba la generación 5 horas antes.
    expect(parseFechaUTC('2026-11-25 17:29:04').getTime()).toBe(
      Date.UTC(2026, 10, 25, 17, 29, 4)
    )
  })

  it('respeta el offset cuando ya viene informado', () => {
    expect(parseFechaUTC('2026-11-25T17:29:04Z').getTime()).toBe(Date.UTC(2026, 10, 25, 17, 29, 4))
    expect(parseFechaUTC('2026-11-25T17:29:04-05:00').getTime()).toBe(
      Date.UTC(2026, 10, 25, 22, 29, 4)
    )
  })

  it('devuelve null cuando el texto no es una fecha', () => {
    expect(parseFechaUTC(null)).toBeNull()
    expect(parseFechaUTC('')).toBeNull()
    expect(parseFechaUTC('hoy')).toBeNull()
  })

  it('forma una fecha legible y marca guion cuando no hay dato', () => {
    const texto = formatFechaHora('2026-11-25 17:29:04')
    expect(texto).toContain('2026')
    expect(texto).not.toBe('-')
    expect(formatFechaHora(null)).toBe('-')
    expect(formatFechaHora('sin fecha')).toBe('-')
  })
})

describe('fechas impresas del documento', () => {
  it('toma solo las claves de fecha del contexto y las traduce', () => {
    const filas = fechasUsadas({
      variables_used: {
        nombre_usuario: 'MARLENY BARRERA BARON',
        fecha_pago: '2025-01-05',
        fecha_constancia: '08 de Mayo de 2025'
      }
    })
    expect(filas.map((fecha) => fecha.etiqueta)).toEqual(['Pago', 'Constancia'])
    expect(filas[0].valor).toBe('2025-01-05')
  })

  it('conserva la clave original cuando no está en el catálogo', () => {
    const filas = fechasUsadas({ variables_used: { fecha_limite: '2025-02-02' } })
    expect(filas).toEqual([{ clave: 'fecha_limite', etiqueta: 'fecha_limite', valor: '2025-02-02' }])
  })

  it('muestra guion cuando la fecha llegó vacía', () => {
    const filas = fechasUsadas({ variables_used: { fecha_pago: '' } })
    expect(filas).toEqual([{ clave: 'fecha_pago', etiqueta: 'Pago', valor: '-' }])
  })

  it('no falla si el histórico no trae contexto', () => {
    expect(fechasUsadas({})).toEqual([])
    expect(fechasUsadas()).toEqual([])
  })
})

describe('trazas de gestión y entrega', () => {
  it('distingue las gestiones que registró cada archivo', () => {
    expect(etiquetaAccion({ action: 'impresion_rango' })).toBe('Impresión por rango')
    expect(etiquetaAccion({ action: 'lote_correspondencia' })).toBe('Lote de correspondencia')
    expect(etiquetaAccion({ action: 'exportacion_excel' })).toBe('Exportación a Excel')
    expect(severidadAccion({ action: 'exportacion_excel' })).toBe('success')
  })

  it('asume documento oficial en las filas anteriores al cambio', () => {
    expect(etiquetaAccion({})).toBe('Documento oficial')
    expect(severidadAccion({ action: 'desconocida' })).toBe('info')
  })

  it('diferencia el correo que no salió según el motivo', () => {
    expect(etiquetaEntrega({ delivery_method: 'correo_fallido' })).toBe('Correo rechazado')
    expect(etiquetaEntrega({ delivery_method: 'correo_sin_destinatario' })).toBe('Sin correo de destino')
    expect(etiquetaEntrega({ delivery_method: 'correo_omitido' })).toBe('Correo omitido (SMTP)')
    expect(severidadEntrega({ delivery_method: 'correo_fallido' })).toBe('danger')
    expect(severidadEntrega({ delivery_method: 'correo_omitido' })).toBe('warn')
  })

  it('deja en guion la entrega desconocida en lugar de inventar un medio', () => {
    expect(etiquetaEntrega({})).toBe('-')
    expect(etiquetaEntrega({ delivery_method: 'otro' })).toBe('-')
    expect(severidadEntrega({})).toBe('secondary')
  })
})
