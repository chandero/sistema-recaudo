import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// Crear instancia de axios
const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

// Interceptor para agregar token y tenant automáticamente
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      console.warn('No access_token found in localStorage for request:', config.url)
    }
    
    // Agregar tenant activo como header
    const activeTenantId = localStorage.getItem('active_tenant_id')
    if (activeTenantId) {
      config.headers['X-Tenant-Id'] = activeTenantId
    }
    
    // Si el body es FormData, no establecer Content-Type para que axios lo genere automáticamente
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Rutas cuyo 401 NO significa sesión caducada: son las que negocian la sesión.
// Tratarlas como expiración recargaba /login y borraba el mensaje de credenciales
// antes de que el usuario pudiera leerlo.
const RUTAS_DE_AUTENTICACION = ['/auth/login', '/auth/token', '/auth/logout', '/auth/switch-tenant']

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config?.url || ''
      const esIntentoDeSesion = RUTAS_DE_AUTENTICACION.some((ruta) => url.includes(ruta))
      // Token expirado o inválido: se limpia la sesión y se vuelve al login, pero
      // solo si la página no es ya el login (evita recargar sobre el propio error).
      if (!esIntentoDeSesion && window.location.pathname !== '/login') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_role')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Servicio de autenticación
export const authService = {
  async login(email, password) {
    // El backend ahora espera JSON
    const response = await apiClient.post('/auth/login', {
      email,
      password
    })
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user_role', response.data.user?.role || 'user')
      // Also set token in memory for immediate use
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
    }
    return response.data
  },

  async logout() {
    try {
      // Llamar al endpoint de logout del backend
      await apiClient.post('/auth/logout')
    } catch (error) {
      console.error('Error during logout:', error);
      // Continuar con el logout local incluso si el backend falla
    } finally {
      // Limpiar datos locales
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_role')
      localStorage.removeItem('active_tenant_id')
      // Limpiar el token de la instancia de axios
      delete apiClient.defaults.headers.common['Authorization']
    }
  },
  
  // Cambiar de tenant activo
  async switchTenant(tenantId) {
    const response = await apiClient.post('/auth/switch-tenant', { tenant_id: tenantId })
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('active_tenant_id', String(tenantId))
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
    }
    return response.data
  },
  
  // Método para obtener el usuario actual desde el backend
  getCurrentUser() {
    return apiClient.get('/auth/me')
  },

  // Método para decodificar el token (mantenido para compatibilidad)
  decodeToken() {
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

// Servicio de administración de usuarios
export const userService = {
  getAll(params = {}) {
    return apiClient.get('/users/', { params })
  },

  getById(id) {
    return apiClient.get(`/users/${id}`)
  },

  create(data) {
    return apiClient.post('/users/', data)
  },

  update(id, data) {
    return apiClient.patch(`/users/${id}`, data)
  },

  changeStatus(id, isActive) {
    return apiClient.patch(`/users/${id}/status`, { is_active: isActive })
  },

  resetPassword(id, password) {
    return apiClient.post(`/users/${id}/reset-password`, { password })
  },

  invite(data) {
    return apiClient.post('/users/invitations', data)
  },

  acceptInvitation(token, password) {
    return apiClient.post('/users/invitations/accept', { token, password })
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
    return apiClient.put(`/clients/${id}`, data)
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

  getCount() {
    return apiClient.get('/obligations/stats/count')
  },

  create(data) {
    return apiClient.post('/obligations/', data)
  },

  update(id, data) {
    return apiClient.put(`/obligations/${id}`, data)
  },

  delete(id) {
    return apiClient.delete(`/obligations/${id}`)
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

  getDetail(id) {
    return apiClient.get(`/processes/${id}/detail`)
  },

  create(data) {
    return apiClient.post('/processes/', data)
  },

  transition(processId, targetStateId, observations = '') {
    return apiClient.post(`/processes/${processId}/transition`, {
      target_state_id: targetStateId,
      observations
    })
  },

  getHistory(processId) {
    return apiClient.get(`/processes/${processId}/history`)
  },

  getTimeline(processId) {
    return apiClient.get(`/processes/${processId}/timeline`)
  },

  getStats() {
    return apiClient.get('/processes/stats')
  },

  getExpedient(processId) {
    return apiClient.get(`/processes/${processId}/expedient`)
  },

  getNotes(processId) {
    return apiClient.get(`/processes/${processId}/notes`)
  },

  createNote(processId, data) {
    return apiClient.post(`/processes/${processId}/notes`, data)
  },

  getDocuments(processId) {
    return apiClient.get(`/processes/${processId}/documents`)
  }
}

// Servicio de workflow
export const workflowService = {
  getStates(includeInactive = false) {
    return apiClient.get('/workflows/states/', { params: { include_inactive: includeInactive } })
  },

  getState(id) {
    return apiClient.get(`/workflows/states/${id}`)
  },

  createState(data) {
    return apiClient.post('/workflows/states/', data)
  },

  updateState(id, data) {
    return apiClient.put(`/workflows/states/${id}`, data)
  },

  deleteState(id) {
    return apiClient.delete(`/workflows/states/${id}`)
  },

  getTransitions(stateId = null, includeInactive = false) {
    const params = { include_inactive: includeInactive }
    if (stateId) params.state_id = stateId
    return apiClient.get('/workflows/transitions/', { params })
  },

  createTransition(data) {
    return apiClient.post('/workflows/transitions/', data)
  },

  updateTransition(id, data) {
    return apiClient.put(`/workflows/transitions/${id}`, data)
  },

  deleteTransition(id) {
    return apiClient.delete(`/workflows/transitions/${id}`)
  },

  getTransitionRules() {
    return apiClient.get('/workflows/transitions/rules')
  },

  getDesigner() {
    return apiClient.get('/workflows/designer')
  },

  seed(overwrite = false) {
    return apiClient.post('/workflows/seed', null, { params: { overwrite } })
  },

  getKanban() {
    return apiClient.get('/workflows/kanban')
  },

  bulkTransition(processIds, targetStateId, observations = null) {
    return apiClient.post('/workflows/bulk-transition', {
      process_ids: processIds,
      target_state_id: targetStateId,
      observations
    })
  }
}

// Servicio de documentos
export const documentService = {
  getTemplates(params = {}) {
    return apiClient.get('/documents/templates', { params })
  },

  getTemplateById(id) {
    return apiClient.get(`/documents/templates/${id}`)
  },

  createTemplate(data) {
    // No especificar Content-Type para que axios lo genere automáticamente si es FormData
    const config = {}
    return apiClient.post('/documents/templates', data, config)
  },

  reemplazarPlantilla(code, file) {
    // Sustituye el DOCX de una plantilla registrada por su código (sube la versión)
    const data = new FormData()
    data.append('file', file)
    return apiClient.put(`/documents/templates/${encodeURIComponent(code)}/content`, data)
  },

  generateDocument(templateId, variables) {
    return apiClient.post(`/documents/generate`, { template_id: templateId, ...variables })
  },

  getGeneratedDocuments(params = {}) {
    return apiClient.get('/documents/generated', { params })
  },

  downloadTemplate: async (templateId) => {
    const response = await apiClient.get(`/documents/templates/${templateId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  },

  generateDocumentFromTemplate: async (templateId, clientData) => {
    const response = await apiClient.post(`/documents/templates/${templateId}/generate`, clientData, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Auto de Archivo (GD-F.03) y Constancia Secretarial (GD-F.01)
  previewAutoArchivo(obligationIds) {
    return apiClient.post('/documents/auto-archivo/preview', { obligation_ids: obligationIds })
  },

  previewConstancia(obligationIds) {
    return apiClient.post('/documents/constancia/preview', { obligation_ids: obligationIds })
  },

  generarAutoArchivo(payload) {
    return apiClient.post('/documents/auto-archivo/generate', payload, { responseType: 'blob' })
  },

  generarConstancia(payload) {
    return apiClient.post('/documents/constancia/generate', payload, { responseType: 'blob' })
  }
};

// Servicio de dashboard
export const dashboardService = {
  getStats() {
    return apiClient.get('/dashboard/stats')
  }
}

// Servicio de acuerdos de pago
export const agreementService = {
  getAll(params = {}) {
    return apiClient.get('/payment-agreements/', { params })
  },

  getById(id) {
    return apiClient.get(`/payment-agreements/${id}`)
  },

  create(data) {
    return apiClient.post('/payment-agreements/', data)
  },

  accept(id, data = {}) {
    return apiClient.post(`/payment-agreements/${id}/accept`, data)
  },

  payInstallment(agreementId, installmentId, data) {
    return apiClient.post(`/payment-agreements/${agreementId}/installments/${installmentId}/pay`, data)
  },

  cancel(id) {
    return apiClient.post(`/payment-agreements/${id}/cancel`)
  }
}

// Servicio de notificaciones
export const notificationService = {
  getAll(unreadOnly = false) {
    return apiClient.get('/notifications/notifications', { params: { unread_only: unreadOnly } })
  },

  getCount() {
    return apiClient.get('/notifications/notifications/count')
  },

  markRead(id) {
    return apiClient.post(`/notifications/notifications/${id}/read`)
  },

  markAllRead() {
    return apiClient.post('/notifications/notifications/read-all')
  }
}

// Servicio de búsqueda global
export const searchService = {
  search(query, limit = 20) {
    return apiClient.get('/notifications/search', { params: { q: query, limit } })
  }
}

// Servicio de reportes
export const reportService = {
  getAging() {
    return apiClient.get('/reports/aging')
  },

  getPerformance(startDate, endDate) {
    return apiClient.get('/reports/performance', {
      params: { start_date: startDate, end_date: endDate }
    })
  },

  getOperatorReport(userId) {
    return apiClient.get(`/reports/operator/${userId}`)
  },

  exportProcessesExcel(params = {}) {
    return apiClient.get('/reports/export/processes-excel', {
      params,
      responseType: 'blob'
    })
  }
}

export default apiClient
