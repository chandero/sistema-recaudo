import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

/**
 * Composable para la gestión de autenticación
 */
export function useAuth() {
  const authStore = useAuthStore()

  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const currentUser = computed(() => authStore.currentUser)
  const token = computed(() => authStore.token)
  const userRole = computed(() => authStore.getUserRole)
  const isLoading = computed(() => authStore.loading)
  const error = computed(() => authStore.error)

  /**
   * Iniciar sesión
   * @param {string} email - Correo electrónico
   * @param {string} password - Contraseña
   * @returns {Promise<Object>} - Resultado de la operación de inicio de sesión
   */
  const login = async (email, password) => {
    return await authStore.login(email, password)
  }

  /**
   * Cerrar sesión
   */
  const logout = () => {
    authStore.logout()
  }

  /**
   * Obtener el usuario actual
   * @returns {Promise<Object>} - Información del usuario actual
   */
  const getCurrentUser = async () => {
    return await authStore.getCurrentUser()
  }

  /**
   * Verifica si el usuario tiene un rol específico
   * @param {string} role - Rol a verificar
   * @returns {boolean} - True si el usuario tiene el rol
   */
  const hasRole = (role) => {
    return userRole.value === role
  }

  /**
   * Verifica si el usuario tiene permisos de administrador
   * @returns {boolean} - True si el usuario es administrador
   */
  const isAdmin = () => {
    return hasRole('admin') || hasRole('platform_admin')
  }

  /**
   * Verifica si el usuario tiene permisos de cliente
   * @returns {boolean} - True si el usuario es cliente
   */
  const isClient = () => {
    return hasRole('client')
  }

  return {
    isAuthenticated,
    currentUser,
    token,
    userRole,
    isLoading,
    error,
    login,
    logout,
    getCurrentUser,
    hasRole,
    isAdmin,
    isClient
  }
}