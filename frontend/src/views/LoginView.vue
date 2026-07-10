<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <i class="pi pi-wallet login-icon"></i>
        <h1>Sistema de Gestión de Cartera</h1>
        <p>Inicie sesión para continuar</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="field">
          <label for="username">Usuario</label>
          <InputText 
            id="username" 
            v-model="username" 
            type="text" 
            placeholder="Ingrese su usuario"
            class="w-full"
            :disabled="loading"
            @input="clearError"
          />
        </div>

        <div class="field">
          <label for="password">Contraseña</label>
          <Password 
            id="password" 
            v-model="password" 
            placeholder="••••••••"
            toggleMask
            class="w-full"
            :disabled="loading"
            @input="clearError"
          />
        </div>

        <Message v-if="error" severity="error" :closable="false" class="mt-3">
          {{ error }}
        </Message>

        <Button 
          type="submit" 
          label="Iniciar sesión" 
          icon="pi pi-sign-in"
          class="w-full mt-4"
          :loading="loading"
          :disabled="!username || !password"
        />
      </form>

      <div class="login-footer">
        <p class="text-sm text-color-secondary">
          Sistema de Seguimiento y Control de Cobro de Cartera
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

// Clear any existing session data when login page loads
onMounted(() => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_role')
  authStore.clearToken()
})

const clearError = () => {
  error.value = ''
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  const result = await authStore.login(username.value, password.value)

  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%);
  padding: 2rem;
}

.login-card {
  background: var(--surface-ground);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  width: 100%;
  max-width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-icon {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
}

.login-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
}

.login-header p {
  color: var(--text-color-secondary);
  margin: 0;
}

.login-form .field {
  margin-bottom: 1.5rem;
}

.login-form label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-color);
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
  border-top: 1px solid var(--surface-border);
  padding-top: 1.5rem;
}
</style>
