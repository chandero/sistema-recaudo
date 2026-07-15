<template>
  <div class="users-page">
      <UserFeedback
        v-if="feedback"
        :key="feedback.key"
        :type="feedback.type"
        :title="feedback.title"
        :message="feedback.message"
        @close="feedback = null"
      />

      <div class="page-heading">
        <div>
          <h2>Gestión de usuarios</h2>
          <p>Administra el acceso, los roles y el estado de las cuentas.</p>
        </div>
        <div class="heading-actions">
          <Button label="Invitar usuario" icon="pi pi-send" outlined @click="openInvitation" />
          <Button label="Nuevo usuario" icon="pi pi-user-plus" @click="openCreate" />
        </div>
      </div>

      <Card class="filters-card">
        <template #content>
          <div class="filters">
            <span class="p-input-icon-left search-field">
              <i class="pi pi-search" />
              <InputText v-model="filters.search" placeholder="Buscar nombre, usuario o correo" @input="scheduleSearch" />
            </span>
            <Dropdown
              v-if="isPlatformAdmin"
              v-model="filters.tenant_id"
              :options="tenantOptions"
              optionLabel="name"
              optionValue="id"
              placeholder="Todos los tenants"
              showClear
              @change="applyFilters"
            />
            <Dropdown v-model="filters.role" :options="roleOptions" optionLabel="label" optionValue="value" placeholder="Todos los roles" showClear @change="applyFilters" />
            <Dropdown v-model="filters.is_active" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Todos los estados" showClear @change="applyFilters" />
            <Button icon="pi pi-refresh" label="Recargar" outlined @click="loadUsers" />
          </div>
        </template>
      </Card>

      <Card>
        <template #content>
          <Message v-if="loadError" severity="error" :closable="false">{{ loadError }}</Message>
          <DataTable
            :value="users"
            :loading="loading"
            :lazy="true"
            :paginator="true"
            :rows="pagination.pageSize"
            :totalRecords="pagination.total"
            :first="(pagination.page - 1) * pagination.pageSize"
            :rowsPerPageOptions="[10, 20, 50]"
            stripedRows
            responsiveLayout="scroll"
            @page="onPage"
          >
            <template #empty>No hay usuarios que coincidan con los filtros.</template>
            <Column field="full_name" header="Nombre" />
            <Column field="username" header="Usuario" />
            <Column field="email" header="Correo" />
            <Column v-if="isPlatformAdmin" header="Tenant">
              <template #body="{ data }">{{ tenantName(data.tenant_id) }}</template>
            </Column>
            <Column header="Rol">
              <template #body="{ data }"><Tag :value="roleLabel(data.role)" severity="info" /></template>
            </Column>
            <Column header="Estado">
              <template #body="{ data }"><Tag :value="data.is_active ? 'Activo' : 'Inactivo'" :severity="data.is_active ? 'success' : 'danger'" /></template>
            </Column>
            <Column header="Acciones" style="width: 190px">
              <template #body="{ data }">
                <div class="row-actions">
                  <Button icon="pi pi-pencil" text rounded v-tooltip="'Editar'" @click="openEdit(data)" />
                  <Button icon="pi pi-key" text rounded severity="warning" v-tooltip="'Restablecer contraseña'" @click="openPassword(data)" />
                  <Button
                    :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check-circle'"
                    text rounded
                    :severity="data.is_active ? 'danger' : 'success'"
                    :disabled="data.id === authStore.currentUser?.id"
                    v-tooltip="data.is_active ? 'Desactivar' : 'Activar'"
                    @click="askStatusChange(data)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <Dialog v-model:visible="formVisible" modal :header="editingUser ? 'Editar usuario' : 'Nuevo usuario'" :style="{ width: '540px' }">
        <form class="user-form" @submit.prevent="saveUser">
          <Message v-if="formError" severity="error" :closable="false">{{ formError }}</Message>
          <div class="field"><label for="fullName">Nombre completo *</label><InputText id="fullName" v-model.trim="form.full_name" /></div>
          <div class="field"><label for="username">Nombre de usuario *</label><InputText id="username" v-model.trim="form.username" /></div>
          <div class="field"><label for="email">Correo electrónico *</label><InputText id="email" v-model.trim="form.email" type="email" /></div>
          <div v-if="isPlatformAdmin" class="field">
            <label for="tenant">Tenant *</label>
            <Dropdown id="tenant" v-model="form.tenant_id" :options="tenantOptions" optionLabel="name" optionValue="id" placeholder="Seleccione un tenant" />
          </div>
          <div class="field">
            <label for="role">Rol *</label>
            <Dropdown id="role" v-model="form.role" :options="assignableRoles" optionLabel="label" optionValue="value" />
          </div>
          <div v-if="!editingUser" class="field">
            <label for="password">Contraseña temporal *</label>
            <Password id="password" v-model="form.password" toggleMask :feedback="true" />
            <small>Mínimo 8 caracteres, con mayúscula, minúscula y número.</small>
          </div>
          <div v-if="editingUser" class="field-checkbox"><Checkbox v-model="form.is_active" binary inputId="active" /><label for="active">Usuario activo</label></div>
        </form>
        <template #footer>
          <Button label="Cancelar" text @click="formVisible = false" />
          <Button label="Guardar" icon="pi pi-check" :loading="saving" @click="saveUser" />
        </template>
      </Dialog>

      <Dialog v-model:visible="passwordVisible" modal header="Restablecer contraseña" :style="{ width: '460px' }">
        <div class="user-form">
          <p>Define una nueva contraseña para <strong>{{ selectedUser?.full_name }}</strong>.</p>
          <Message v-if="passwordError" severity="error" :closable="false">{{ passwordError }}</Message>
          <div class="field"><label for="newPassword">Nueva contraseña *</label><Password id="newPassword" v-model="newPassword" toggleMask /></div>
          <small>Mínimo 8 caracteres, con mayúscula, minúscula y número.</small>
        </div>
        <template #footer>
          <Button label="Cancelar" text @click="passwordVisible = false" />
          <Button label="Restablecer" icon="pi pi-key" :loading="saving" @click="resetPassword" />
        </template>
      </Dialog>

      <Dialog v-model:visible="invitationVisible" modal header="Invitar usuario" :style="{ width: '540px' }">
        <div class="user-form">
          <Message v-if="invitationError" severity="error" :closable="false">{{ invitationError }}</Message>
          <div class="field"><label for="inviteName">Nombre completo *</label><InputText id="inviteName" v-model.trim="invitationForm.full_name" /></div>
          <div class="field"><label for="inviteUsername">Nombre de usuario *</label><InputText id="inviteUsername" v-model.trim="invitationForm.username" /></div>
          <div class="field"><label for="inviteEmail">Correo electrónico *</label><InputText id="inviteEmail" v-model.trim="invitationForm.email" type="email" /></div>
          <div v-if="isPlatformAdmin" class="field">
            <label for="inviteTenant">Tenant *</label>
            <Dropdown id="inviteTenant" v-model="invitationForm.tenant_id" :options="tenantOptions" optionLabel="name" optionValue="id" placeholder="Seleccione un tenant" />
          </div>
          <div class="field">
            <label for="inviteRole">Rol *</label>
            <Dropdown id="inviteRole" v-model="invitationForm.role" :options="assignableRoles" optionLabel="label" optionValue="value" />
          </div>
          <Message v-if="invitationResult" severity="success" :closable="false">
            {{ invitationResult.email_sent ? 'La invitación fue enviada por correo.' : 'Invitación creada. SMTP no está configurado; copia el enlace.' }}
          </Message>
          <div v-if="invitationResult" class="invitation-link">
            <InputText :modelValue="invitationResult.invitation_url" readonly />
            <Button icon="pi pi-copy" label="Copiar" outlined @click="copyInvitationLink" />
          </div>
        </div>
        <template #footer>
          <Button label="Cerrar" text @click="invitationVisible = false" />
          <Button v-if="!invitationResult" label="Crear invitación" icon="pi pi-send" :loading="saving" @click="sendInvitation" />
        </template>
      </Dialog>

      <ConfirmationDialog
        v-model:visible="statusConfirmation"
        :message="statusMessage"
        :acceptLabel="selectedUser?.is_active ? 'Desactivar' : 'Activar'"
        :acceptSeverity="selectedUser?.is_active ? 'danger' : 'success'"
        @accept="changeStatus"
      />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import UserFeedback from '@/components/UserFeedback.vue'
import { tenantService, userService } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { assignableRolesFor, isPlatformAdmin as hasPlatformRole, ROLE_OPTIONS, validateUserForm } from '@/utils/userManagement'

const authStore = useAuthStore()
const route = useRoute()
const isPlatformAdmin = computed(() => hasPlatformRole(authStore.currentUser?.role))
const users = ref([])
const tenants = ref([])
const loading = ref(false)
const saving = ref(false)
const loadError = ref('')
const formError = ref('')
const passwordError = ref('')
const feedback = ref(null)
const formVisible = ref(false)
const passwordVisible = ref(false)
const invitationVisible = ref(false)
const statusConfirmation = ref(false)
const editingUser = ref(null)
const selectedUser = ref(null)
const newPassword = ref('')
const invitationError = ref('')
const invitationResult = ref(null)
let searchTimer

const filters = reactive({ search: '', tenant_id: null, role: null, is_active: null })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const emptyForm = () => ({ full_name: '', username: '', email: '', password: '', role: 'OPERATOR', tenant_id: null, is_active: true })
const form = reactive(emptyForm())
const invitationForm = reactive({ full_name: '', username: '', email: '', role: 'OPERATOR', tenant_id: null })
const roleOptions = ROLE_OPTIONS
const assignableRoles = computed(() => assignableRolesFor(authStore.currentUser?.role))
const statusOptions = [{ label: 'Activos', value: true }, { label: 'Inactivos', value: false }]
const tenantOptions = computed(() => tenants.value.filter(tenant => tenant.is_active))
const statusMessage = computed(() => selectedUser.value?.is_active
  ? `¿Deseas desactivar a ${selectedUser.value.full_name}? No podrá iniciar sesión.`
  : `¿Deseas activar a ${selectedUser.value?.full_name}?`)

const apiError = (error, fallback) => error.response?.data?.detail || fallback
const notify = (type, title, message) => { feedback.value = { type, title, message, key: Date.now() } }
const roleLabel = role => roleOptions.find(option => option.value === role)?.label || role
const tenantName = id => tenants.value.find(tenant => tenant.id === id)?.name || (id ? `Tenant ${id}` : 'Plataforma')

async function loadTenants() {
  if (!isPlatformAdmin.value) return
  try { tenants.value = (await tenantService.getAll()).data } catch { tenants.value = [] }
}

async function loadUsers() {
  loading.value = true
  loadError.value = ''
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    Object.entries(filters).forEach(([key, value]) => { if (value !== null && value !== '') params[key] = value })
    const { data } = await userService.getAll(params)
    users.value = data.items
    pagination.total = data.total
  } catch (error) {
    loadError.value = apiError(error, 'No fue posible cargar los usuarios.')
  } finally { loading.value = false }
}

function scheduleSearch() { clearTimeout(searchTimer); searchTimer = setTimeout(applyFilters, 350) }
function applyFilters() { pagination.page = 1; loadUsers() }
function onPage(event) { pagination.page = event.page + 1; pagination.pageSize = event.rows; loadUsers() }
function resetForm() { Object.assign(form, emptyForm()); formError.value = '' }
function openCreate() { editingUser.value = null; resetForm(); formVisible.value = true }
function openInvitation() {
  Object.assign(invitationForm, { full_name: '', username: '', email: '', role: 'OPERATOR', tenant_id: filters.tenant_id || null })
  invitationError.value = ''
  invitationResult.value = null
  invitationVisible.value = true
}
function openEdit(user) {
  editingUser.value = user
  Object.assign(form, { full_name: user.full_name, username: user.username, email: user.email, password: '', role: user.role, tenant_id: user.tenant_id, is_active: user.is_active })
  formError.value = ''
  formVisible.value = true
}

function validateForm() {
  return validateUserForm(form, {
    editing: Boolean(editingUser.value),
    platformAdmin: isPlatformAdmin.value
  })
}

async function saveUser() {
  formError.value = validateForm()
  if (formError.value) return
  saving.value = true
  try {
    if (editingUser.value) {
      const { password, ...payload } = form
      await userService.update(editingUser.value.id, payload)
    } else await userService.create({ ...form })
    formVisible.value = false
    await loadUsers()
    notify('success', 'Usuario guardado', 'Los datos del usuario se actualizaron correctamente.')
  } catch (error) { formError.value = apiError(error, 'No fue posible guardar el usuario.') }
  finally { saving.value = false }
}

function openPassword(user) { selectedUser.value = user; newPassword.value = ''; passwordError.value = ''; passwordVisible.value = true }
async function resetPassword() {
  if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(newPassword.value)) { passwordError.value = 'La contraseña no cumple los requisitos de seguridad.'; return }
  saving.value = true
  try {
    await userService.resetPassword(selectedUser.value.id, newPassword.value)
    passwordVisible.value = false
    notify('success', 'Contraseña restablecida', 'La nueva contraseña fue guardada.')
  } catch (error) { passwordError.value = apiError(error, 'No fue posible restablecer la contraseña.') }
  finally { saving.value = false }
}

async function sendInvitation() {
  invitationError.value = validateUserForm(
    { ...invitationForm, password: 'Temporary1' },
    { platformAdmin: isPlatformAdmin.value }
  )
  if (invitationError.value) return
  saving.value = true
  try {
    const { data } = await userService.invite({ ...invitationForm })
    invitationResult.value = data
  } catch (error) { invitationError.value = apiError(error, 'No fue posible crear la invitación.') }
  finally { saving.value = false }
}

async function copyInvitationLink() {
  try {
    await navigator.clipboard.writeText(invitationResult.value.invitation_url)
    notify('success', 'Enlace copiado', 'El enlace de invitación está en el portapapeles.')
  } catch { notify('error', 'No se pudo copiar', 'Copia el enlace manualmente.') }
}

function askStatusChange(user) { selectedUser.value = user; statusConfirmation.value = true }
async function changeStatus() {
  try {
    await userService.changeStatus(selectedUser.value.id, !selectedUser.value.is_active)
    await loadUsers()
    notify('success', 'Estado actualizado', 'El estado del usuario fue actualizado.')
  } catch (error) { notify('error', 'No se actualizó el estado', apiError(error, 'Ocurrió un error.')) }
}

onMounted(async () => {
  if (isPlatformAdmin.value && route.query.tenant_id) {
    const tenantId = Number(route.query.tenant_id)
    filters.tenant_id = Number.isInteger(tenantId) ? tenantId : null
  }
  await loadTenants()
  await loadUsers()
})
</script>

<style scoped>
.users-page { display: flex; flex-direction: column; gap: 1rem; }
.page-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.page-heading h2 { margin: 0; }
.page-heading p { margin: .35rem 0 0; color: #6b7280; }
.heading-actions, .invitation-link { display: flex; gap: .75rem; align-items: center; }
.invitation-link .p-inputtext { flex: 1; }
.filters { display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; }
.search-field { flex: 1 1 280px; }
.search-field .p-inputtext { width: 100%; }
.row-actions { display: flex; gap: .15rem; }
.user-form { display: flex; flex-direction: column; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: .4rem; }
.field > .p-inputtext, .field > .p-dropdown { width: 100%; }
.field :deep(.p-password), .field :deep(.p-password-input) { width: 100%; }
.field-checkbox { display: flex; align-items: center; gap: .5rem; }
@media (max-width: 640px) { .page-heading { align-items: flex-start; flex-direction: column; } }
</style>
