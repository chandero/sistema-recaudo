import { ref } from 'vue'
import api from '@/services/api'

/**
 * Composable para operaciones CRUD reutilizables
 * @param {string} endpoint - Endpoint base para las operaciones
 */
export function useApi(endpoint) {
  const loading = ref(false)
  const data = ref(null)
  const error = ref(null)

  /**
   * Obtiene todos los recursos
   * @param {Object} params - Parámetros de consulta
   * @returns {Promise<any>}
   */
  const getAll = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get(`/${endpoint}/`, { params })
      data.value = response.data
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Obtiene un recurso por ID
   * @param {number|string} id - ID del recurso
   * @returns {Promise<any>}
   */
  const getById = async (id) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get(`/${endpoint}/${id}`)
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Crea un nuevo recurso
   * @param {Object} itemData - Datos del nuevo recurso
   * @returns {Promise<any>}
   */
  const create = async (itemData) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post(`/${endpoint}/`, itemData)
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Actualiza un recurso existente
   * @param {number|string} id - ID del recurso
   * @param {Object} itemData - Datos actualizados
   * @returns {Promise<any>}
   */
  const update = async (id, itemData) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.patch(`/${endpoint}/${id}`, itemData)
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Elimina un recurso
   * @param {number|string} id - ID del recurso
   * @returns {Promise<any>}
   */
  const remove = async (id) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.delete(`/${endpoint}/${id}`)
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading: readonly(loading),
    data: readonly(data),
    error: readonly(error),
    getAll,
    getById,
    create,
    update,
    remove
  }
}

// Importar readonly para hacer las refs inmutables
import { readonly } from 'vue'