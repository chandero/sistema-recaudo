<template>
  <div class="clientes-view">
      <div class="view-header">
        <div>
          <h1>{{ t('components.client_view.title') }}</h1>
          <p>{{ t('components.client_view.subtitle') }}</p>
        </div>
        <Button 
          :label="t('components.client_view.new_client')" 
          icon="pi pi-plus" 
          @click="showNewClientDialog = true"
        />
      </div>

      <!-- Filtros -->
      <Card class="filters-card mb-4">
        <template #content>
          <div class="filters-grid">
            <InputText 
              v-model="filters.search" 
              :placeholder="t('components.client_view.search_placeholder')"
              class="w-full"
              @keyup.enter="loadClients(true)"
            />
            <Button 
              :label="t('common.search')" 
              icon="pi pi-search" 
              @click="loadClients(true)"
            />
          </div>
        </template>
      </Card>

      <!-- Tabla de clientes -->
      <Card>
        <template #content>
          <DataTable 
            :value="clients" 
            :loading="loading"
            stripedRows
            paginator
            lazy
            :first="first"
            :rows="rows"
            :totalRecords="totalRecords"
            :rowsPerPageOptions="[5, 10, 25, 50]"
            :currentPageReportTemplate="t('components.client_view.page_report')"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            @page="onPage"
          >
            <Column field="identification" :header="t('forms.identification')" style="width: 150px"></Column>
            <Column field="name" :header="t('components.client_view.full_name')"></Column>
            <Column field="email" :header="t('forms.email')" style="width: 200px"></Column>
            <Column field="phone" :header="t('components.client_view.phone')" style="width: 120px"></Column>
            <Column field="is_active" :header="t('forms.status')" style="width: 100px">
              <template #body="slotProps">
                <Tag 
                  :value="slotProps.data.is_active ? t('components.client_view.active') : t('components.client_view.inactive')" 
                  :severity="slotProps.data.is_active ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column :header="t('common.actions')" style="width: 150px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-pencil" 
                  text 
                  severity="info"
                  size="small"
                  @click="editClient(slotProps.data)"
                  v-tooltip="t('common.edit')"
                />
                <Button 
                  icon="pi pi-trash" 
                  text 
                  severity="danger"
                  size="small"
                  @click="deleteClient(slotProps.data)"
                  v-tooltip="t('components.client_view.remove')"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Diálogo Nuevo/Editar Cliente -->
      <Dialog 
        v-model:visible="showNewClientDialog" 
        modal 
        :header="t('components.client_view.new_client_dialog')"
        :style="{ width: '500px' }"
        :closable="false"
      >
        <form @submit.prevent="saveClient">
          <div class="field mb-4">
            <label for="identification" class="block font-medium mb-2">{{ t('forms.identification') }}</label>
            <InputText 
              id="identification" 
              v-model="form.identification"
              class="w-full"
              required
            />
          </div>

          <div class="field mb-4">
            <label for="name" class="block font-medium mb-2">{{ t('forms.name') }}</label>
            <InputText 
              id="name" 
              v-model="form.name"
              class="w-full"
              required
            />
          </div>

          <div class="field mb-4">
            <label for="email" class="block font-medium mb-2">{{ t('forms.email') }}</label>
            <InputText 
              id="email" 
              v-model="form.email"
              type="email"
              class="w-full"
            />
          </div>

          <div class="field mb-4">
            <label for="phone" class="block font-medium mb-2">{{ t('components.client_view.phone') }}</label>
            <InputText 
              id="phone" 
              v-model="form.phone"
              class="w-full"
            />
          </div>

          <div class="field mb-4">
            <label for="address" class="block font-medium mb-2">{{ t('forms.address') }}</label>
            <InputText 
              id="address" 
              v-model="form.address"
              class="w-full"
            />
          </div>

          <div class="flex justify-end gap-2">
            <Button 
              :label="t('common.cancel')" 
              severity="secondary" 
              @click="cancelForm"
              type="button"
            />
            <Button 
              :label="t('common.save')" 
              icon="pi pi-check" 
              type="submit"
              :loading="saving"
            />
          </div>
        </form>
      </Dialog>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { clientService } from '../services/api'
import { useToast } from 'primevue/usetoast'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useForm } from '@/composables/useForm'
import { useI18n } from '@/composables/useI18n'

const toast = useToast()
const { handleError } = useErrorHandler()
const { t } = useI18n() // Usar la función de traducción

// Inicializar el composable de formulario con los campos de cliente
const { form, resetForm: resetClientForm } = useForm({
  identification: '',
  name: '',
  email: '',
  phone: '',
  address: ''
})

const clients = ref([])
const totalRecords = ref(0)
const first = ref(0)
const rows = ref(10)
const loading = ref(false)
const saving = ref(false)
const showNewClientDialog = ref(false)
const editingClient = ref(null)

const filters = ref({
  search: ''
})

const loadClients = async (resetPage = false) => {
  if (resetPage) first.value = 0
  loading.value = true
  try {
    const response = await clientService.getAll({
      skip: first.value,
      limit: rows.value,
      search: filters.value.search || undefined
    })
    clients.value = response.data || []
    totalRecords.value = Number(response.headers['x-total-count']) || 0
  } catch (error) {
    console.error('Error loading clients:', error)
    handleError(error, t('messages.errors.generic'))
  } finally {
    loading.value = false
  }
}

const onPage = (event) => {
  first.value = event.first
  rows.value = event.rows
  loadClients()
}

const editClient = (client) => {
  editingClient.value = client
  // Actualizar el formulario con los datos del cliente
  Object.assign(form, { ...client })
  showNewClientDialog.value = true
}

const saveClient = async () => {
  saving.value = true
  try {
    if (editingClient.value) {
      await clientService.update(editingClient.value.id, form)
      toast.add({
        severity: 'success',
        summary: t('common.success'),
        detail: t('messages.success.updated'),
        life: 3000
      })
    } else {
      await clientService.create(form)
      toast.add({
        severity: 'success',
        summary: t('common.success'),
        detail: t('messages.success.created'),
        life: 3000
      })
    }
    
    showNewClientDialog.value = false
    cancelForm()
    loadClients()
  } catch (error) {
    console.error('Error saving client:', error)
    handleError(error, 'Error al guardar el cliente')
  } finally {
    saving.value = false
  }
}

const deleteClient = async (client) => {
  if (!confirm(t('messages.confirm.delete'))) {
    return
  }

  try {
    await clientService.delete(client.id)
    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('messages.success.deleted'),
      life: 3000
    })
    if (clients.value.length === 1 && first.value > 0) {
      first.value = Math.max(0, first.value - rows.value)
    }
    loadClients()
  } catch (error) {
    console.error('Error deleting client:', error)
    handleError(error, 'Error al eliminar el cliente')
  }
}

const cancelForm = () => {
  editingClient.value = null
  resetClientForm()
}

onMounted(() => {
  loadClients()
})
</script>

<style scoped>
.clientes-view {
  padding: 2rem;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
}

.view-header p {
  color: var(--text-color-secondary);
  margin: 0;
}

.filters-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 1rem;
}
</style>
