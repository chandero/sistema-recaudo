import { defineStore } from 'pinia'
import { authService } from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    currentUser: null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    getToken: (state) => state.token,
    getUserRole: (state) => state.currentUser?.role || null
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.login(email, password)
        this.token = response.access_token
        this.currentUser = response.user
        
        // Guardar token en localStorage
        localStorage.setItem('access_token', this.token)
        localStorage.setItem('user_role', response.user?.role || 'user')
        
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Credenciales inválidas'
        this.token = null
        this.currentUser = null
        
        // Limpiar cualquier dato de sesión anterior
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_role')
        
        return { 
          success: false, 
          error: this.error 
        }
      } finally {
        this.loading = false
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
        // Llamar al nuevo endpoint de logout del backend
        await apiClient.post('/api/v2/auth/logout');
      } catch (error) {
        console.error('Error during backend logout:', error);
        // Continuar con el logout local incluso si el backend falla
      } finally {
        // Limpiar estado local
        this.token = null
        this.currentUser = null
        this.error = null
        
        // Remover del localStorage
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_role')
      }
    },

    clearToken() {
      this.token = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_role')
    },

    setToken(token) {
      this.token = token
      localStorage.setItem('access_token', token)
    }
  }
})