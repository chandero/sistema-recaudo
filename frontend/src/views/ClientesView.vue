<template>
  <div class="clientes-view">
      <div class="view-header">
        <div>
          <h1>Gestión de Clientes</h1>
          <p>Administre la información de contribuyentes y clientes</p>
        </div>
        <Button 
          label="Nuevo Cliente" 
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
              placeholder="Buscar por nombre o identificación..."
              class="w-full"
              @keyup.enter="loadClients"
            />
            <Button 
              label="Buscar" 
              icon="pi pi-search" 
              @click="loadClients"
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
            :rows="10"
            :rowsPerPageOptions="[5, 10, 25, 50]"
          >
            <Column field="identification" header="Identificación" style="width: 150px"></Column>
            <Column field="name" header="Nombre / Razón Social"></Column>
            <Column field="email" header="Email" style="width: 200px"></Column>
            <Column field="phone" header="Teléfono" style="width: 120px"></Column>
            <Column field="is_active" header="Estado" style="width: 100px">
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
                  text 
                  severity="info"
                  size="small"
                  @click="editClient(slotProps.data)"
                  v-tooltip="'Editar'"
                />
                <Button 
                  icon="pi pi-trash" 
                  text 
                  severity="danger"
                  size="small"
                  @click="deleteClient(slotProps.data)"
                  v-tooltip="'Eliminar'"
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
        header="Nuevo Cliente"
        :style="{ width: '500px' }"
        :closable="false"
      >
        <form @submit.prevent="saveClient">
          <div class="field mb-4">
            <label for="identification" class="block font-medium mb-2">Identificación</label>
            <InputText 
              id="identification" 
              v-model="clientForm.identification"
              class="w-full"
              required
            />
          </div>

          <div class="field mb-4">
            <label for="name" class="block font-medium mb-2">Nombre / Razón Social</label>
            <InputText 
              id="name" 
              v-model="clientForm.name"
              class="w-full"
              required
            />
          </div>

          <div class="field mb-4">
            <label for="email" class="block font-medium mb-2">Email</label>
            <InputText 
              id="email" 
              v-model="clientForm.email"
              type="email"
              class="w-full"
            />
          </div>

          <div class="field mb-4">
            <label for="phone" class="block font-medium mb-2">Teléfono</label>
            <InputText 
              id="phone" 
              v-model="clientForm.phone"
              class="w-full"
            />
          </div>

          <div class="field mb-4">
            <label for="address" class="block font-medium mb-2">Dirección</label>
            <InputText 
              id="address" 
              v-model="clientForm.address"
              class="w-full"
            />
          </div>

          <div class="flex justify-end gap-2">
            <Button 
              label="Cancelar" 
              severity="secondary" 
              @click="cancelForm"
              type="button"
            />
            <Button 
              label="Guardar" 
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

const toast = useToast()

const clients = ref([])
const loading = ref(false)
const saving = ref(false)
const showNewClientDialog = ref(false)
const editingClient = ref(null)

const filters = ref({
  search: ''
})

const clientForm = ref({
  identification: '',
  name: '',
  email: '',
  phone: '',
  address: ''
})

const loadClients = async () => {
  loading.value = true
  try {
    const response = await clientService.getAll({
      search: filters.value.search || undefined
    })
    clients.value = response.data || []
  } catch (error) {
    console.error('Error loading clients:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar los clientes',
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

const editClient = (client) => {
  editingClient.value = client
  clientForm.value = { ...client }
  showNewClientDialog.value = true
}

const saveClient = async () => {
  saving.value = true
  try {
    if (editingClient.value) {
      await clientService.update(editingClient.value.id, clientForm.value)
      toast.add({
        severity: 'success',
        summary: 'Éxito',
        detail: 'Cliente actualizado correctamente',
        life: 3000
      })
    } else {
      await clientService.create(clientForm.value)
      toast.add({
        severity: 'success',
        summary: 'Éxito',
        detail: 'Cliente creado correctamente',
        life: 3000
      })
    }
    
    showNewClientDialog.value = false
    cancelForm()
    loadClients()
  } catch (error) {
    console.error('Error saving client:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.detail || 'Error al guardar el cliente',
      life: 3000
    })
  } finally {
    saving.value = false
  }
}

const deleteClient = async (client) => {
  if (!confirm(`¿Está seguro de eliminar el cliente "${client.name}"?`)) {
    return
  }

  try {
    await clientService.delete(client.id)
    toast.add({
      severity: 'success',
      summary: 'Éxito',
      detail: 'Cliente eliminado correctamente',
      life: 3000
    })
    loadClients()
  } catch (error) {
    console.error('Error deleting client:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Error al eliminar el cliente',
      life: 3000
    })
  }
}

const cancelForm = () => {
  editingClient.value = null
  clientForm.value = {
    identification: '',
    name: '',
    email: '',
    phone: '',
    address: ''
  }
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
