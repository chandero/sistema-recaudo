import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useSeccionesColapsables } from '@/composables/useSeccionesColapsables'

const porDefecto = {
  datos: true,
  impresion: false,
  excel: false,
  filtros: true,
  tabla: true
}

const leerGuardado = () => JSON.parse(localStorage.getItem('secciones_resoluciones') || '{}')

describe('estado de las secciones colapsables', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('arranca con los valores por defecto cuando no hay nada guardado', () => {
    const { estaAbierta } = useSeccionesColapsables('resoluciones', porDefecto)

    expect(estaAbierta('datos')).toBe(true)
    expect(estaAbierta('impresion')).toBe(false)
    expect(estaAbierta('tabla')).toBe(true)
  })

  it('alterna una sección y persiste el mapa completo', () => {
    const { alternar, estaAbierta } = useSeccionesColapsables('resoluciones', porDefecto)

    alternar('excel')

    expect(estaAbierta('excel')).toBe(true)
    expect(leerGuardado()).toEqual({ ...porDefecto, excel: true })
  })

  it('recupera lo guardado en lugar de los defectos al recrear el composable', () => {
    localStorage.setItem('secciones_resoluciones', JSON.stringify({ ...porDefecto, datos: false }))

    const { estaAbierta } = useSeccionesColapsables('resoluciones', porDefecto)

    expect(estaAbierta('datos')).toBe(false)
  })

  it('ignora contenido corrupto y valores que no son booleanos', () => {
    localStorage.setItem('secciones_resoluciones', 'no-es-json')
    expect(useSeccionesColapsables('resoluciones', porDefecto).estaAbierta('datos')).toBe(true)

    localStorage.setItem('secciones_resoluciones', JSON.stringify({ datos: 'si', excel: 1 }))
    const { estaAbierta } = useSeccionesColapsables('resoluciones', porDefecto)

    expect(estaAbierta('datos')).toBe(true)
    expect(estaAbierta('excel')).toBe(false)
  })

  it('descarta las claves que ya no existen en la configuración', () => {
    localStorage.setItem('secciones_resoluciones', JSON.stringify({ fantasma: true }))

    const { alternar } = useSeccionesColapsables('resoluciones', porDefecto)
    alternar('datos')

    expect(leerGuardado()).not.toHaveProperty('fantasma')
    expect(leerGuardado()).toHaveProperty('datos', false)
  })

  it('abre o cierra todo según cómo estuvieran las secciones', () => {
    const { alternarTodas, estaAbierta, todasAbiertas } = useSeccionesColapsables('resoluciones', porDefecto)

    alternarTodas()

    expect(todasAbiertas.value).toBe(true)
    expect(estaAbierta('impresion')).toBe(true)
    expect(estaAbierta('excel')).toBe(true)

    alternarTodas()

    expect(todasAbiertas.value).toBe(false)
    expect(estaAbierta('datos')).toBe(false)
    expect(estaAbierta('tabla')).toBe(false)
  })

  it('sigue funcionando si el almacenamiento no permite escribir', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('cuota superada')
    })

    const { alternar, estaAbierta } = useSeccionesColapsables('resoluciones', porDefecto)
    alternar('tabla')

    expect(estaAbierta('tabla')).toBe(false)
  })
})
