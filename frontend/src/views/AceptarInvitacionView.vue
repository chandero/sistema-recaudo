<template>
  <div class="invitation-page">
    <Card class="invitation-card">
      <template #title>Activar cuenta</template>
      <template #subtitle>Define una contraseña segura para completar tu invitación.</template>
      <template #content>
        <div v-if="completed" class="completed-state">
          <i class="pi pi-check-circle"></i>
          <h3>Cuenta activada</h3>
          <p>Ya puedes iniciar sesión con tu correo y la contraseña definida.</p>
          <Button label="Ir al inicio de sesión" icon="pi pi-sign-in" @click="router.push('/login')" />
        </div>
        <form v-else class="invitation-form" @submit.prevent="acceptInvitation">
          <Message v-if="!token" severity="error" :closable="false">El enlace de invitación no contiene un token válido.</Message>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <div class="field">
            <label for="password">Nueva contraseña</label>
            <Password id="password" v-model="password" toggleMask :feedback="true" />
            <small>Mínimo 8 caracteres, con mayúscula, minúscula y número.</small>
          </div>
          <div class="field">
            <label for="confirmation">Confirmar contraseña</label>
            <Password id="confirmation" v-model="confirmation" toggleMask :feedback="false" />
          </div>
          <Button type="submit" label="Activar cuenta" icon="pi pi-check" :loading="loading" :disabled="!token" />
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userService } from '@/services/api'

const route = useRoute()
const router = useRouter()
const token = typeof route.query.token === 'string' ? route.query.token : ''
const password = ref('')
const confirmation = ref('')
const loading = ref(false)
const completed = ref(false)
const error = ref('')

async function acceptInvitation() {
  error.value = ''
  if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(password.value)) {
    error.value = 'La contraseña no cumple los requisitos de seguridad.'
    return
  }
  if (password.value !== confirmation.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }
  loading.value = true
  try {
    await userService.acceptInvitation(token, password.value)
    completed.value = true
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No fue posible aceptar la invitación.'
  } finally { loading.value = false }
}
</script>

<style scoped>
.invitation-page { min-height: 100vh; display: grid; place-items: center; padding: 1.5rem; background: linear-gradient(135deg, var(--primary-50), var(--primary-100)); }
.invitation-card { width: min(100%, 480px); }
.invitation-form { display: flex; flex-direction: column; gap: 1.25rem; }
.field { display: flex; flex-direction: column; gap: .45rem; }
.field :deep(.p-password), .field :deep(.p-password-input) { width: 100%; }
.completed-state { text-align: center; }
.completed-state .pi { color: var(--green-500); font-size: 3rem; }
</style>
