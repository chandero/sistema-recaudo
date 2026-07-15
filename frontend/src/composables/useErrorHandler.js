import { useToast } from 'primevue/usetoast'

/**
 * Composable para manejo de errores reutilizable
 */
export function useErrorHandler() {
  const toast = useToast()

  /**
   * Muestra un mensaje de error usando PrimeVue Toast
   * @param {string|object} error - Mensaje de error o respuesta de error HTTP
   * @param {string} defaultMessage - Mensaje por defecto si no hay error específico
   */
  const handleError = (error, defaultMessage = 'Ha ocurrido un error inesperado') => {
    let errorMessage = defaultMessage
    
    if (error && typeof error === 'object') {
      // Si es una respuesta HTTP con detalle de error
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail
      } 
      // Si es un error con mensaje directo
      else if (error.message) {
        errorMessage = error.message
      }
      // Otros formatos de error
      else {
        errorMessage = error.toString()
      }
    } 
    else if (typeof error === 'string') {
      errorMessage = error
    }

    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: errorMessage,
      life: 5000
    })
  }

  /**
   * Ejecuta una función async con manejo de errores automático
   * @param {Function} asyncFn - Función async a ejecutar
   * @param {string} successMessage - Mensaje opcional de éxito
   * @param {string} errorMessage - Mensaje de error por defecto
   * @returns {Promise<any>} - Resultado de la función o null si hay error
   */
  const executeWithErrorHandling = async (asyncFn, successMessage = null, errorMessage = 'Ha ocurrido un error inesperado') => {
    try {
      const result = await asyncFn()
      
      if (successMessage) {
        toast.add({
          severity: 'success',
          summary: 'Éxito',
          detail: successMessage,
          life: 3000
        })
      }
      
      return result
    } catch (error) {
      handleError(error, errorMessage)
      return null
    }
  }

  return {
    handleError,
    executeWithErrorHandling
  }
}