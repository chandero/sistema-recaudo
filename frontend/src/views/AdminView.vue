<template>
  <Layout>
    <div class="admin-panel">
      <h2 class="section-title">Administración de Tenants</h2>
      
      <!-- Toolbar -->
      <div class="toolbar mb-4 flex justify-content-between align-items-center">
        <div class="flex gap-2">
          <Button 
            label="Nuevo Tenant" 
            icon="pi pi-plus" 
            @click="openNewTenantDialog"
            class="p-button-success"
          />
          <Button 
            label="Recargar" 
            icon="pi pi-refresh" 
            @click="loadTenants"
            outlined
          />
        </div>
        <IconField>
          <InputIcon>
            <i class="pi pi-search" />
          </InputIcon>
          <InputText 
            v-model="searchTerm" 
            placeholder="Buscar tenant..." 
            @input="filterTenants"
          />
        </IconField>
      </div>

      <!-- Tabla de Tenants -->
      <Card class="mb-4">
        <template #content>
          <DataTable 
            :value="filteredTenants" 
            :paginator="true" 
            :rows="10"
            :loading="loading"
            stripedRows
            responsiveLayout="scroll"
          >
            <Column field="id" header="ID" style="width: 80px"></Column>
            <Column field="name" header="Nombre" sortable></Column>
            <Column field="code" header="Código" sortable></Column>
            <Column field="is_active" header="Estado" sortable style="width: 120px">
              <template #body="slotProps">
                <Tag 
                  :value="slotProps.data.is_active ? 'Activo' : 'Inactivo'" 
                  :severity="slotProps.data.is_active ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column field="created_at" header="Fecha Creación" sortable style="width: 150px">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column header="Acciones" style="width: 200px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-pencil" 
                  class="p-button-rounded p-button-info p-button-sm mr-2"
                  @click="editTenant(slotProps.data)"
                  v-tooltip="'Editar'"
                />
                <Button 
                  icon="pi pi-users" 
                  class="p-button-rounded p-button-warning p-button-sm mr-2"
                  @click="manageUsers(slotProps.data)"
                  v-tooltip="'Gestionar Usuarios'"
                />
                <Button 
                  icon="pi pi-file" 
                  class="p-button-rounded p-button-success p-button-sm mr-2"
                  @click="manageTemplates(slotProps.data)"
                  v-tooltip="'Plantillas'"
                />
                <Button 
                  icon="pi pi-trash" 
                  class="p-button-rounded p-button-danger p-button-sm"
                  @click="confirmDeleteTenant(slotProps.data)"
                  v-tooltip="'Eliminar'"
                  :disabled="!current_user?.is_platform_admin"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Dialog Nuevo/Editar Tenant -->
      <Dialog 
        v-model:visible="tenantDialogVisible" 
        modal 
        :header="editingTenant ? 'Editar Tenant' : 'Nuevo Tenant'"
        :style="{ width: '500px' }"
        :closable="false"
      >
        <div class="flex flex-column gap-4">
          <div class="field">
            <label for="name" class="font-semibold mb-2 block">Nombre *</label>
            <InputText 
              id="name" 
              v-model="tenantForm.name" 
              class="w-full" 
              :class="{ 'p-invalid': submitted && !tenantForm.name }"
              required
            />
            <small v-if="submitted && !tenantForm.name" class="p-error">El nombre es requerido</small>
          </div>
          
          <div class="field">
            <label for="code" class="font-semibold mb-2 block">Código *</label>
            <InputText 
              id="code" 
              v-model="tenantForm.code" 
              class="w-full" 
              :class="{ 'p-invalid': submitted && !tenantForm.code }"
              required
            />
            <small v-if="submitted && !tenantForm.code" class="p-error">El código es requerido</small>
          </div>
          
          <div class="field-checkbox">
            <Checkbox 
              v-model="tenantForm.is_active" 
              :binary="true" 
              inputId="is_active"
            />
            <label for="is_active" class="ml-2">Activo</label>
          </div>
        </div>
        
        <template #footer>
          <Button 
            label="Cancelar" 
            icon="pi pi-times" 
            @click="closeTenantDialog" 
            class="p-button-text"
          />
          <Button 
            label="Guardar" 
            icon="pi pi-check" 
            @click="saveTenant" 
            :loading="saving"
          />
        </template>
      </Dialog>

      <!-- Dialog Gestionar Usuarios -->
      <Dialog 
        v-model:visible="usersDialogVisible" 
        modal 
        header="Gestión de Usuarios"
        :style="{ width: '800px' }"
        :maximizable="true"
      >
        <div v-if="selectedTenant">
          <div class="flex justify-content-between align-items-center mb-4">
            <h4 class="m-0">Usuarios de {{ selectedTenant.name }}</h4>
            <Button 
              label="Nuevo Usuario" 
              icon="pi pi-user-plus" 
              @click="openNewUserDialog"
              class="p-button-success"
            />
          </div>
          
          <DataTable 
            :value="tenantUsers" 
            :paginator="true" 
            :rows="5"
            stripedRows
          >
            <Column field="username" header="Usuario"></Column>
            <Column field="email" header="Email"></Column>
            <Column field="full_name" header="Nombre Completo"></Column>
            <Column field="role" header="Rol">
              <template #body="slotProps">
                <Tag :value="formatRole(slotProps.data.role)" />
              </template>
            </Column>
            <Column field="is_active" header="Estado">
              <template #body="slotProps">
                <Tag 
                  :value="slotProps.data.is_active ? 'Activo' : 'Inactivo'" 
                  :severity="slotProps.data.is_active ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column header="Acciones" style="width: 150px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-pencil" 
                  class="p-button-rounded p-button-info p-button-sm mr-2"
                  @click="editUser(slotProps.data)"
                />
                <Button 
                  icon="pi pi-trash" 
                  class="p-button-rounded p-button-danger p-button-sm"
                  @click="confirmDeleteUser(slotProps.data)"
                />
              </template>
            </Column>
          </DataTable>
        </div>
      </Dialog>

      <!-- Dialog Nuevo/Editar Usuario -->
      <Dialog 
        v-model:visible="userDialogVisible" 
        modal 
        :header="editingUser ? 'Editar Usuario' : 'Nuevo Usuario'"
        :style="{ width: '500px' }"
        :closable="false"
      >
        <div class="flex flex-column gap-3">
          <div class="field">
            <label class="font-semibold mb-2 block">Username *</label>
            <InputText v-model="userForm.username" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Email *</label>
            <InputText v-model="userForm.email" type="email" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Nombre Completo *</label>
            <InputText v-model="userForm.full_name" class="w-full" />
          </div>
          
          <div class="field" v-if="!editingUser">
            <label class="font-semibold mb-2 block">Contraseña *</label>
            <Password v-model="userForm.password" class="w-full" toggleMask />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Rol *</label>
            <Dropdown 
              v-model="userForm.role" 
              :options="roles" 
              optionLabel="label"
              optionValue="value"
              class="w-full"
              placeholder="Seleccione un rol"
            />
          </div>
          
          <div class="field-checkbox">
            <Checkbox v-model="userForm.is_active" :binary="true" inputId="user_active" />
            <label for="user_active" class="ml-2">Activo</label>
          </div>
        </div>
        
        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="closeUserDialog" class="p-button-text" />
          <Button label="Guardar" icon="pi pi-check" @click="saveUser" :loading="saving" />
        </template>
      </Dialog>

      <!-- Dialog Plantillas Documentales -->
      <Dialog 
        v-model:visible="templatesDialogVisible" 
        modal 
        header="Plantillas Documentales"
        :style="{ width: '900px' }"
        :maximizable="true"
      >
        <div v-if="selectedTenant">
          <div class="flex justify-content-between align-items-center mb-4">
            <h4 class="m-0">Plantillas de {{ selectedTenant.name }}</h4>
            <Button 
              label="Nueva Plantilla" 
              icon="pi pi-file-plus" 
              @click="openNewTemplateDialog"
              class="p-button-success"
            />
          </div>
          
          <DataTable 
            :value="tenantTemplates" 
            :paginator="true" 
            :rows="5"
            stripedRows
          >
            <Column field="name" header="Nombre"></Column>
            <Column field="code" header="Código"></Column>
            <Column field="template_type" header="Tipo">
              <template #body="slotProps">
                <Tag :value="slotProps.data.template_type" />
              </template>
            </Column>
            <Column field="version" header="Versión"></Column>
            <Column field="is_active" header="Estado">
              <template #body="slotProps">
                <Tag 
                  :value="slotProps.data.is_active ? 'Activa' : 'Inactiva'" 
                  :severity="slotProps.data.is_active ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column header="Acciones" style="width: 200px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-download" 
                  class="p-button-rounded p-button-info p-button-sm mr-2"
                  @click="downloadTemplate(slotProps.data)"
                  v-tooltip="'Descargar'"
                />
                <Button 
                  icon="pi pi-eye" 
                  class="p-button-rounded p-button-warning p-button-sm mr-2"
                  @click="viewTemplate(slotProps.data)"
                  v-tooltip="'Ver Variables'"
                />
                <Button 
                  icon="pi pi-trash" 
                  class="p-button-rounded p-button-danger p-button-sm"
                  @click="confirmDeleteTemplate(slotProps.data)"
                  v-tooltip="'Eliminar'"
                />
              </template>
            </Column>
          </DataTable>
        </div>
      </Dialog>

      <!-- Dialog Nueva Plantilla -->
      <Dialog 
        v-model:visible="templateDialogVisible" 
        modal 
        header="Nueva Plantilla"
        :style="{ width: '600px' }"
        :closable="false"
      >
        <div class="flex flex-column gap-3">
          <div class="field">
            <label class="font-semibold mb-2 block">Nombre *</label>
            <InputText v-model="templateForm.name" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Código *</label>
            <InputText v-model="templateForm.code" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Descripción</label>
            <Textarea v-model="templateForm.description" class="w-full" rows="3" />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Tipo *</label>
            <Dropdown 
              v-model="templateForm.template_type" 
              :options="templateTypes" 
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Archivo de Plantilla *</label>
            <FileUpload 
              name="file"
              @select="onFileSelect"
              accept=".docx,.pdf"
              :maxFileSize="5000000"
              customUpload
              :auto="false"
            />
            <small v-if="selectedFile" class="text-success">
              Archivo seleccionado: {{ selectedFile.name }}
            </small>
          </div>
          
          <div class="field">
            <label class="font-semibold mb-2 block">Esquema de Variables (JSON)</label>
            <Textarea 
              v-model="templateForm.variables_schema_str" 
              class="w-full" 
              rows="5"
              placeholder='{"cliente": "string", "obligacion": "string", "valor": "number"}'
            />
          </div>
          
          <div class="field-checkbox">
            <Checkbox v-model="templateForm.is_active" :binary="true" inputId="template_active" />
            <label for="template_active" class="ml-2">Activa</label>
          </div>
        </div>
        
        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="closeTemplateDialog" class="p-button-text" />
          <Button label="Guardar" icon="pi pi-check" @click="saveTemplate" :loading="saving" />
        </template>
      </Dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const authStore = useAuthStore()
const current_user = computed(() => authStore.user)

// Estados
const loading = ref(false)
const saving = ref(false)
const searchTerm = ref('')
const tenants = ref([])
const filteredTenants = ref([])
const tenantUsers = ref([])
const tenantTemplates = ref([])
const selectedTenant = ref(null)

// Diálogos
const tenantDialogVisible = ref(false)
const usersDialogVisible = ref(false)
const userDialogVisible = ref(false)
const templatesDialogVisible = ref(false)
const templateDialogVisible = ref(false)

// Formularios
const editingTenant = ref(null)
const editingUser = ref(null)
const tenantForm = ref({ name: '', code: '', is_active: true })
const userForm = ref({ username: '', email: '', full_name: '', password: '', role: 'OPERATOR', is_active: true })
const templateForm = ref({ 
  name: '', 
  code: '', 
  description: '', 
  template_type: 'DOCX', 
  is_active: true,
  variables_schema_str: ''
})
const selectedFile = ref(null)
const submitted = ref(false)

// Opciones
const roles = [
  { label: 'Administrador de Tenant', value: 'TENANT_ADMIN' },
  { label: 'Gerente', value: 'MANAGER' },
  { label: 'Operador', value: 'OPERATOR' },
  { label: 'Visualizador', value: 'VIEWER' }
]

const templateTypes = [
  { label: 'Word (DOCX)', value: 'DOCX' },
  { label: 'PDF', value: 'PDF' }
]

// Cargar tenants
const loadTenants = async () => {
  loading.value = true
  try {
    const response = await api.get('/tenants/')
    tenants.value = response.data
    filterTenants()
  } catch (error) {
    console.error('Error cargando tenants:', error)
  } finally {
    loading.value = false
  }
}

// Filtrar tenants
const filterTenants = () => {
  if (!searchTerm.value) {
    filteredTenants.value = tenants.value
  } else {
    filteredTenants.value = tenants.value.filter(t => 
      t.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      t.code.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  }
}

// Formatear fecha
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CO')
}

// Formatear rol
const formatRole = (role) => {
  const roleNames = {
    'PLATFORM_ADMIN': 'Admin Plataforma',
    'TENANT_ADMIN': 'Admin Tenant',
    'MANAGER': 'Gerente',
    'OPERATOR': 'Operador',
    'VIEWER': 'Visualizador'
  }
  return roleNames[role] || role
}

// Gestión de Tenants
const openNewTenantDialog = () => {
  editingTenant.value = null
  tenantForm.value = { name: '', code: '', is_active: true }
  submitted.value = false
  tenantDialogVisible.value = true
}

const editTenant = (tenant) => {
  editingTenant.value = tenant
  tenantForm.value = { ...tenant }
  tenantDialogVisible.value = true
}

const closeTenantDialog = () => {
  tenantDialogVisible.value = false
  editingTenant.value = null
}

const saveTenant = async () => {
  submitted.value = true
  if (!tenantForm.value.name || !tenantForm.value.code) return
  
  saving.value = true
  try {
    if (editingTenant.value) {
      await api.patch(`/tenants/${editingTenant.value.id}`, tenantForm.value)
    } else {
      await api.post('/tenants/', tenantForm.value)
    }
    await loadTenants()
    closeTenantDialog()
  } catch (error) {
    console.error('Error guardando tenant:', error)
  } finally {
    saving.value = false
  }
}

const confirmDeleteTenant = (tenant) => {
  // Implementar confirmación
  console.log('Eliminar tenant:', tenant)
}

// Gestión de Usuarios
const manageUsers = async (tenant) => {
  selectedTenant.value = tenant
  usersDialogVisible.value = true
  // Cargar usuarios del tenant
  try {
    const response = await api.get(`/tenants/${tenant.id}/users`)
    tenantUsers.value = response.data || []
  } catch (error) {
    tenantUsers.value = []
  }
}

const openNewUserDialog = () => {
  editingUser.value = null
  userForm.value = { username: '', email: '', full_name: '', password: '', role: 'OPERATOR', is_active: true }
  userDialogVisible.value = true
}

const editUser = (user) => {
  editingUser.value = user
  userForm.value = { ...user, password: '' }
  userDialogVisible.value = true
}

const closeUserDialog = () => {
  userDialogVisible.value = false
  editingUser.value = null
}

const saveUser = async () => {
  saving.value = true
  try {
    if (editingUser.value) {
      await api.put(`/users/${editingUser.value.id}`, userForm.value)
    } else {
      await api.post('/users/', { ...userForm.value, tenant_id: selectedTenant.value.id })
    }
    await manageUsers(selectedTenant.value)
    closeUserDialog()
  } catch (error) {
    console.error('Error guardando usuario:', error)
  } finally {
    saving.value = false
  }
}

const confirmDeleteUser = (user) => {
  console.log('Eliminar usuario:', user)
}

// Gestión de Plantillas
const manageTemplates = async (tenant) => {
  selectedTenant.value = tenant
  templatesDialogVisible.value = true
  // Cargar plantillas del tenant
  try {
    const response = await api.get(`/documents/templates/?tenant_id=${tenant.id}`)
    tenantTemplates.value = response.data || []
  } catch (error) {
    tenantTemplates.value = []
  }
}

const openNewTemplateDialog = () => {
  templateForm.value = { 
    name: '', 
    code: '', 
    description: '', 
    template_type: 'DOCX', 
    is_active: true,
    variables_schema_str: ''
  }
  selectedFile.value = null
  templateDialogVisible.value = true
}

const closeTemplateDialog = () => {
  templateDialogVisible.value = false
}

const onFileSelect = (event) => {
  selectedFile.value = event.files[0]
}

const extractVariablesFromTemplate = async () => {
  if (!selectedFile.value) {
    alert('Por favor seleccione un archivo de plantilla primero');
    return;
  }

  // Mostrar mensaje de carga
  console.log('Analizando plantilla para extraer variables...');
  
  // Subir temporalmente el archivo para análisis
  const formData = new FormData();
  formData.append('file', selectedFile.value);
  
  try {
    // Primero, subir el archivo a un endpoint temporal para análisis
    // En lugar de eso, primero debemos guardar la plantilla y luego analizarla
    // Pero para análisis previo al guardado, podríamos tener un endpoint especial
    
    // Alternativa: mostrar instrucciones al usuario
    alert('Para extraer variables automáticamente, guarde la plantilla primero y luego use la opción de análisis en la lista de plantillas.');
  } catch (error) {
    console.error('Error extrayendo variables de la plantilla:', error);
    alert('Hubo un error al intentar extraer las variables de la plantilla.');
  }
}

const viewTemplate = (template) => {
  console.log('Ver plantilla:', template)
}

const downloadTemplate = (template) => {
  console.log('Descargar plantilla:', template)
}

const confirmDeleteTemplate = (template) => {
  console.log('Eliminar plantilla:', template)
}

const saveTemplate = async () => {
  saving.value = true
  try {
    // Implementar subida de archivo con FormData
    const formData = new FormData()
    formData.append('name', templateForm.value.name)
    formData.append('code', templateForm.value.code)
    formData.append('description', templateForm.value.description || '')
    formData.append('template_type', templateForm.value.template_type)
    formData.append('is_active', templateForm.value.is_active)
    if (templateForm.value.variables_schema_str) {
      formData.append('variables_schema', JSON.parse(templateForm.value.variables_schema_str))
    }
    if (selectedFile.value) {
      formData.append('file', selectedFile.value)
    }
    
    await api.post('/documents/templates/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    await manageTemplates(selectedTenant.value)
    closeTemplateDialog()
  } catch (error) {
    console.error('Error guardando plantilla:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTenants()
})
</script>

<style scoped>
.admin-panel {
  padding: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--text-color);
}

.toolbar {
  background: var(--surface-card);
  padding: 1rem;
  border-radius: 8px;
}

.field-checkbox {
  display: flex;
  align-items: center;
}

.text-success {
  color: var(--green-500);
}
</style>
