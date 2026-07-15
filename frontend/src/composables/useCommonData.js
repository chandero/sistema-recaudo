import { ref, readonly } from 'vue'
import api from '@/services/api'

/**
 * Composable para la gestión de datos comunes del sistema
 */
export function useCommonData() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * Carga los estados de proceso disponibles
   * @returns {Promise<Array>} - Lista de estados de proceso
   */
  const loadProcessStates = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/workflows/states/')
      return response.data || []
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga los tipos de documentos disponibles
   * @returns {Promise<Array>} - Lista de tipos de documentos
   */
  const loadDocumentTypes = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/documents/types')
      return response.data || []
    } catch (err) {
      error.value = err
      // Devolver tipos por defecto si falla la carga
      return [
        { name: 'Notificación de Cobro', value: 'notification' },
        { name: 'Acuerdo de Pago', value: 'agreement' },
        { name: 'Resolución', value: 'resolution' },
        { name: 'Carta de Recordatorio', value: 'reminder' },
        { name: 'Aviso Final', value: 'final_notice' }
      ]
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga las plantillas de documentos disponibles
   * @returns {Promise<Array>} - Lista de plantillas de documentos
   */
  const loadDocumentTemplates = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/documents/templates')
      return response.data || []
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga los clientes disponibles
   * @param {Object} params - Parámetros de filtrado
   * @returns {Promise<Array>} - Lista de clientes
   */
  const loadClients = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/clients/', { params })
      return response.data || []
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Carga las obligaciones disponibles
   * @param {Object} params - Parámetros de filtrado
   * @returns {Promise<Array>} - Lista de obligaciones
   */
  const loadObligations = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/obligations/', { params })
      return response.data || []
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading: readonly(loading),
    error: readonly(error),
    loadProcessStates,
    loadDocumentTypes,
    loadDocumentTemplates,
    loadClients,
    loadObligations
  }
}