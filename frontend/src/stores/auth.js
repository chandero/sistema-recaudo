import { defineStore } from 'pinia'
import { authService } from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    currentUser: null,
    availableTenants: JSON.parse(localStorage.getItem('available_tenants') || '[]'),
    activeTenantId: parseInt(localStorage.getItem('active_tenant_id')) || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    getToken: (state) => state.token,
    getUserRole: (state) => state.currentUser?.role || null,
    activeTenant: (state) => state.availableTenants.find(t => t.tenant_id === state.activeTenantId) || null,
    hasMultipleTenants: (state) => state.availableTenants.length > 1,
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.login(email, password)
        this.token = response.access_token
        this.currentUser = response.user
        
        // Guardar tenants disponibles
        this.availableTenants = response.available_tenants || []
        this.activeTenantId = response.active_tenant_id || (this.availableTenants.length > 0 ? this.availableTenants[0].tenant_id : null)
        
        // Guardar token y tenant en localStorage
        localStorage.setItem('access_token', this.token)
        localStorage.setItem('user_role', response.user?.role || 'user')
        localStorage.setItem('available_tenants', JSON.stringify(this.availableTenants))
        if (this.activeTenantId) {
          localStorage.setItem('active_tenant_id', String(this.activeTenantId))
        }
        
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Credenciales inválidas'
        this.token = null
        this.currentUser = null
        
        // Limpiar cualquier dato de sesión anterior
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_role')
        localStorage.removeItem('active_tenant_id')
        localStorage.removeItem('available_tenants')
        
        return { 
          success: false, 
          error: this.error 
        }
      } finally {
        this.loading = false
      }
    },

    async switchTenant(tenantId) {
      this.activeTenantId = tenantId
      localStorage.setItem('active_tenant_id', String(tenantId))
      
      // Actualizar el currentUser con el nuevo tenant_id
      if (this.currentUser) {
        this.currentUser.tenant_id = tenantId
        // Actualizar el rol al rol correspondiente en este tenant
        const tenant = this.availableTenants.find(t => t.tenant_id === tenantId)
        if (tenant) {
          this.currentUser.role = tenant.role
        }
      }
    },

    async getCurrentUser() {
      if (!this.token) {
        throw new Error('No hay token disponible')
      }

      try {
        const response = await authService.getCurrentUser()
        this.currentUser = response.data
        return response.data
      } catch (error) {
        console.error('Error obteniendo usuario actual:', error)
        
        // Si el error es un 401 o 403, el token probablemente haya expirado
        if (error.response?.status === 401 || error.response?.status === 403) {
          this.logout(); // Limpiar sesión si el token no es válido
        }
        
        // Lanzar el error para que pueda ser manejado por el código que llama
        throw error
      }
    },

    // Alias para compatibilidad
    async fetchCurrentUser() {
      return this.getCurrentUser();
    },

    async logout() {
      try {
        // Llamar al endpoint de logout del backend
        await authService.logout();
      } catch (error) {
        console.error('Error during backend logout:', error);
        // Continuar con el logout local incluso si el backend falla
      } finally {
        // Limpiar estado local
        this.token = null
        this.currentUser = null
        this.availableTenants = []
        this.activeTenantId = null
        this.error = null
        
        // Remover del localStorage
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_role')
        localStorage.removeItem('active_tenant_id')
        localStorage.removeItem('available_tenants')
      }
    },

    clearToken() {
      this.token = null
      this.availableTenants = []
      this.activeTenantId = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_role')
      localStorage.removeItem('active_tenant_id')
      localStorage.removeItem('available_tenants')
    },

    setToken(token) {
      this.token = token
      localStorage.setItem('access_token', token)
    }
  }
})