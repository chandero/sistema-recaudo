import { computed, ref } from 'vue'

/**
 * Composable para secciones colapsables cuyo estado de apertura se recuerda en
 * el navegador, de forma que cada panel se abre y cierra de manera independiente.
 */
export function useSeccionesColapsables(clave, porDefecto) {
  const nombreAlmacen = `secciones_${clave}`

  /**
   * Recupera lo guardado y lo fusiona sobre los defectos. Solo se aceptan las
   * claves conocidas con valor booleano, así un panel agregado después entra con
   * su estado por defecto y un almacenamiento viejo no rompe la vista.
   * @returns {Object} - Mapa nombre de sección -> abierto
   */
  const leerEstado = () => {
    const estado = { ...porDefecto }
    let guardado
    try {
      guardado = JSON.parse(localStorage.getItem(nombreAlmacen) || '{}')
    } catch (_) {
      // Almacenamiento no disponible o contenido corrupto: manda el defecto.
      return estado
    }
    if (!guardado || typeof guardado !== 'object') return estado
    Object.keys(porDefecto).forEach((nombre) => {
      if (typeof guardado[nombre] === 'boolean') {
        estado[nombre] = guardado[nombre]
      }
    })
    return estado
  }

  const abiertas = ref(leerEstado())

  const persistir = () => {
    try {
      localStorage.setItem(nombreAlmacen, JSON.stringify(abiertas.value))
    } catch (_) {
      // Safari en modo privado lanza al escribir; la vista sigue funcionando sin recuerdo.
    }
  }

  /**
   * Indica si una sección está abierta, para usar en v-show y en aria-expanded.
   * @param {string} nombre - Clave de la sección declarada en porDefecto
   * @returns {boolean} - Verdadero si el panel debe mostrarse
   */
  const estaAbierta = (nombre) => !!abiertas.value[nombre]

  /**
   * Abre o cierra una sección y guarda el resultado.
   * @param {string} nombre - Clave de la sección
   */
  const alternar = (nombre) => {
    abiertas.value[nombre] = !abiertas.value[nombre]
    persistir()
  }

  const todasAbiertas = computed(() =>
    Object.keys(porDefecto).every((nombre) => abiertas.value[nombre])
  )

  /**
   * Abre todas las secciones si había alguna cerrada; si ya estaban todas abiertas,
   * las cierra.
   */
  const alternarTodas = () => {
    const valor = !todasAbiertas.value
    Object.keys(porDefecto).forEach((nombre) => {
      abiertas.value[nombre] = valor
    })
    persistir()
  }

  return { abiertas, estaAbierta, alternar, alternarTodas, todasAbiertas }
}
