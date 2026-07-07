import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Crear instancia de axios
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar token automáticamente
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_role')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Servicio de autenticación
export const authService = {
  async login(email, password) {
    const response = await apiClient.post('/auth/login', { email, password })
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user_role', response.data.user?.role || 'user')
    }
    return response.data
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_role')
  },

  getCurrentUser() {
    const token = localStorage.getItem('access_token')
    if (!token) return null
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload
    } catch (e) {
      return null
    }
  },

  isAuthenticated() {
    return !!localStorage.getItem('access_token')
  }
}

// Servicio de tenants (solo para admin de plataforma)
export const tenantService = {
  getAll() {
    return apiClient.get('/tenants/')
  },

  getById(id) {
    return apiClient.get(`/tenants/${id}`)
  },

  create(data) {
    return apiClient.post('/tenants/', data)
  },

  update(id, data) {
    return apiClient.put(`/tenants/${id}`, data)
  },

  delete(id) {
    return apiClient.delete(`/tenants/${id}`)
  }
}

// Servicio de clientes
export const clientService = {
  getAll(params = {}) {
    return apiClient.get('/clients/', { params })
  },

  getById(id) {
    return apiClient.get(`/clients/${id}`)
  },

  create(data) {
    return apiClient.post('/clients/', data)
  },

  update(id, data) {
    return apiClient.patch(`/clients/${id}`, data)
  },

  delete(id) {
    return apiClient.delete(`/clients/${id}`)
  },

  importExcel(file, columnMapping, saveTemplate = false, templateName = null) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('column_mapping', JSON.stringify(columnMapping))
    formData.append('save_template', saveTemplate.toString())
    if (templateName) {
      formData.append('template_name', templateName)
    }
    
    return apiClient.post('/import/excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }
}

// Servicio de obligaciones
export const obligationService = {
  getAll(params = {}) {
    return apiClient.get('/obligations/', { params })
  },

  getById(id) {
    return apiClient.get(`/obligations/${id}`)
  },

  create(data) {
    return apiClient.post('/obligations/', data)
  },

  update(id, data) {
    return apiClient.patch(`/obligations/${id}`, data)
  }
}

// Servicio de procesos de cobro
export const processService = {
  getAll(params = {}) {
    return apiClient.get('/processes/', { params })
  },

  getById(id) {
    return apiClient.get(`/processes/${id}`)
  },

  create(data) {
    return apiClient.post('/processes/', data)
  },

  updateState(processId, stateCode, observations = '') {
    return apiClient.post(`/processes/${processId}/transition`, { 
      state_code: stateCode, 
      observations 
    })
  },

  getHistory(processId) {
    return apiClient.get(`/processes/${processId}/history`)
  }
}

// Servicio de workflow
export const workflowService = {
  getStates() {
    return apiClient.get('/workflow/states/')
  },

  getTransitions() {
    return apiClient.get('/workflow/transitions/')
  },

  createState(data) {
    return apiClient.post('/workflow/states/', data)
  },

  createTransition(data) {
    return apiClient.post('/workflow/transitions/', data)
  }
}

// Servicio de documentos
export const documentService = {
  getTemplates(params = {}) {
    return apiClient.get('/documents/templates/', { params })
  },

  getTemplateById(id) {
    return apiClient.get(`/documents/templates/${id}`)
  },

  createTemplate(data) {
    return apiClient.post('/documents/templates/', data)
  },

  generateDocument(templateId, variables) {
    return apiClient.post(`/documents/templates/${templateId}/generate`, variables)
  },

  getGeneratedDocuments(params = {}) {
    return apiClient.get('/documents/generated/', { params })
  }
}

export default apiClient
