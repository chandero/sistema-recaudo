import { defineStore } from 'pinia'
import { authService } from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    role: localStorage.getItem('user_role') || null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    userRole: (state) => state.role,
    isPlatformAdmin: (state) => state.role === 'platform_admin',
  },

  actions: {
    async login(email, password) {
      try {
        const response = await authService.login(email, password)
        this.setToken(response.access_token)
        this.role = response.user?.role || 'user'
        this.user = response.user
        
        return { success: true }
      } catch (error) {
        console.error('Login error:', error)
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Error al iniciar sesión' 
        }
      }
    },

    logout() {
      authService.logout()
      this.token = null
      this.role = null
      this.user = null
    },

    setToken(token) {
      this.token = token
      localStorage.setItem('access_token', token)
    },

    clearToken() {
      this.token = null
      localStorage.removeItem('access_token')
    }
  }
})
