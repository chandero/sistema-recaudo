<template>
  <Layout>
    <div class="import-view">
      <Card class="w-full">
        <template #title>
          <div class="flex justify-between items-center">
            <span>Importación Masiva de Cartera</span>
            <Button 
              label="Nueva Importación" 
              icon="pi pi-plus" 
              @click="showUploadDialog = true"
              severity="primary"
            />
          </div>
        </template>
        <template #content>
          <!-- Filtros -->
          <div class="flex gap-3 mb-4">
            <Dropdown 
              v-model="filterStatus" 
              :options="statusOptions" 
              optionLabel="label" 
              optionValue="value"
              placeholder="Todos los estados"
              class="w-48"
            />
            <Button label="Filtrar" icon="pi pi-filter" @click="loadBatches" />
          </div>

          <!-- Tabla de lotes -->
          <DataTable 
            :value="batches" 
            :loading="loading"
            stripedRows
            paginator
            :rows="10"
            class="text-sm"
          >
            <Column field="id" header="ID" style="width: 60px"></Column>
            <Column field="original_filename" header="Archivo"></Column>
            <Column field="total_rows" header="Filas" style="width: 100px"></Column>
            <Column field="success_rows" header="Exitosas" style="width: 100px">
              <template #body="slotProps">
                <span class="text-green-600 font-medium">{{ slotProps.data.success_rows }}</span>
              </template>
            </Column>
            <Column field="error_rows" header="Errores" style="width: 100px">
              <template #body="slotProps">
                <span :class="slotProps.data.error_rows > 0 ? 'text-red-600 font-medium' : 'text-gray-400'">
                  {{ slotProps.data.error_rows }}
                </span>
              </template>
            </Column>
            <Column field="status" header="Estado" style="width: 150px">
              <template #body="slotProps">
                <Tag 
                  :value="getStatusLabel(slotProps.data.status)" 
                  :severity="getStatusSeverity(slotProps.data.status)"
                />
              </template>
            </Column>
            <Column field="created_at" header="Fecha" style="width: 150px">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column header="Acciones" style="width: 120px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-eye" 
                  text 
                  rounded 
                  size="small"
                  @click="viewBatchDetails(slotProps.data)"
                  v-tooltip="'Ver detalles'"
                />
                <Button 
                  v-if="slotProps.data.status === 'MAPPING'"
                  icon="pi pi-link" 
                  text 
                  rounded 
                  size="small"
                  @click="openMappingDialog(slotProps.data)"
                  v-tooltip="'Mapear columnas'"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Dialog de subida de archivo -->
      <Dialog 
        v-model:visible="showUploadDialog" 
        modal 
        header="Subir Archivo Excel/CSV"
        :style="{ width: '500px' }"
      >
        <div class="flex flex-col gap-4">
          <div class="field">
            <label for="fileInput" class="block mb-2 font-medium">Archivo</label>
            <input 
              id="fileInput"
              type="file" 
              @change="onFileSelect"
              accept=".xlsx,.xls,.csv"
              class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <small class="text-gray-500">Formatos permitidos: .xlsx, .xls, .csv</small>
          </div>

          <div class="field" v-if="selectedTemplate">
            <label class="block mb-2 font-medium">Plantilla de mapeo</label>
            <Dropdown 
              v-model="selectedTemplate" 
              :options="mappingTemplates" 
              optionLabel="name" 
              optionValue="id"
              placeholder="Seleccionar plantilla (opcional)"
              class="w-full"
            />
          </div>

          <div v-if="selectedFile" class="bg-blue-50 p-3 border-round">
            <p class="text-sm"><strong>Archivo:</strong> {{ selectedFile.name }}</p>
            <p class="text-sm text-gray-600 mt-1">
              Al subir el archivo, el sistema detectará las columnas disponibles para mapeo.
            </p>
          </div>
        </div>

        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="showUploadDialog = false" text />
          <Button 
            label="Subir Archivo" 
            icon="pi pi-upload" 
            @click="uploadFile" 
            :disabled="!selectedFile"
            :loading="uploading"
          />
        </template>
      </Dialog>

      <!-- Dialog de mapeo de columnas -->
      <Dialog 
        v-model:visible="showMappingDialog" 
        modal 
        header="Mapeo de Columnas"
        :style="{ width: '800px' }"
        :closable="false"
      >
        <div class="flex flex-col gap-4">
          <Message severity="info">
            Asigne cada columna del archivo a un campo del sistema. Las columnas sin mapeo serán ignoradas.
          </Message>

          <div class="grid grid-cols-2 gap-4">
            <div v-for="col in currentBatch?.detected_columns || []" :key="col" class="field">
              <label class="block mb-2 font-medium text-sm">{{ col }}</label>
              <Dropdown 
                v-model="columnMapping[col]" 
                :options="systemFields" 
                optionLabel="label" 
                optionValue="value"
                placeholder="-- Seleccionar campo --"
                class="w-full"
                showClear
              />
            </div>
          </div>

          <Divider />

          <div class="flex items-center gap-2">
            <Checkbox 
              v-model="saveAsTemplate" 
              inputId="saveTemplate" 
              :binary="true"
            />
            <label for="saveTemplate" class="cursor-pointer">Guardar este mapeo como plantilla reutilizable</label>
          </div>

          <div v-if="saveAsTemplate" class="field">
            <label for="templateName" class="block mb-2 font-medium">Nombre de la plantilla</label>
            <InputText 
              id="templateName"
              v-model="templateName" 
              placeholder="Ej: Importación Alumbrado 2024"
              class="w-full"
            />
          </div>
        </div>

        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="showMappingDialog = false" text />
          <Button 
            label="Procesar Importación" 
            icon="pi pi-check" 
            @click="processMapping"
            :loading="processing"
          />
        </template>
      </Dialog>

      <!-- Dialog de detalles del lote -->
      <Dialog 
        v-model:visible="showDetailsDialog" 
        modal 
        header="Detalles del Lote"
        :style="{ width: '600px' }"
      >
        <div v-if="selectedBatch" class="flex flex-col gap-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm text-gray-500">Archivo</label>
              <p class="font-medium">{{ selectedBatch.original_filename }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">Estado</label>
              <Tag 
                :value="getStatusLabel(selectedBatch.status)" 
                :severity="getStatusSeverity(selectedBatch.status)"
              />
            </div>
            <div>
              <label class="text-sm text-gray-500">Total filas</label>
              <p class="font-medium">{{ selectedBatch.total_rows }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">Fecha creación</label>
              <p class="font-medium">{{ formatDate(selectedBatch.created_at) }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">Exitosas</label>
              <p class="font-medium text-green-600">{{ selectedBatch.success_rows }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">Con errores</label>
              <p class="font-medium" :class="selectedBatch.error_rows > 0 ? 'text-red-600' : ''">
                {{ selectedBatch.error_rows }}
              </p>
            </div>
          </div>

          <Divider v-if="selectedBatch.errors_log && selectedBatch.errors_log.length > 0" />

          <div v-if="selectedBatch.errors_log && selectedBatch.errors_log.length > 0">
            <label class="block mb-2 font-medium">Errores (primeros 10)</label>
            <ScrollPanel style="max-height: 200px">
              <ul class="text-sm space-y-2">
                <li v-for="(error, idx) in selectedBatch.errors_log.slice(0, 10)" :key="idx" class="text-red-600 bg-red-50 p-2 border-round">
                  <strong>Fila {{ error.row }}:</strong> {{ error.error }}
                </li>
              </ul>
            </ScrollPanel>
          </div>

          <div v-else-if="selectedBatch.status === 'COMPLETED'" class="text-center py-4">
            <i class="pi pi-check-circle text-4xl text-green-500 mb-2"></i>
            <p class="text-green-600 font-medium">Importación completada exitosamente</p>
          </div>
        </div>

        <template #footer>
          <Button label="Cerrar" icon="pi pi-times" @click="showDetailsDialog = false" />
        </template>
      </Dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Layout from '../components/Layout.vue'
import api from '../services/api'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

// Estados
const loading = ref(false)
const uploading = ref(false)
const processing = ref(false)
const batches = ref([])
const mappingTemplates = ref([])
const filterStatus = ref(null)

// Dialogs
const showUploadDialog = ref(false)
const showMappingDialog = ref(false)
const showDetailsDialog = ref(false)

// Archivo y mapeo
const selectedFile = ref(null)
const selectedTemplate = ref(null)
const currentBatch = ref(null)
const selectedBatch = ref(null)
const columnMapping = ref({})
const saveAsTemplate = ref(false)
const templateName = ref('')

// Opciones de estado
const statusOptions = ref([
  { label: 'Todos', value: null },
  { label: 'Pendiente', value: 'PENDING' },
  { label: 'En mapeo', value: 'MAPPING' },
  { label: 'Procesando', value: 'PROCESSING' },
  { label: 'Completado', value: 'COMPLETED' },
  { label: 'Parcial', value: 'PARTIAL' },
  { label: 'Fallido', value: 'FAILED' }
])

// Campos del sistema para mapeo
const systemFields = ref([
  // Cliente
  { label: '--- CLIENTE ---', value: '', disabled: true },
  { label: 'Identificación', value: 'identificacion' },
  { label: 'Nombre', value: 'nombre' },
  { label: 'Dirección', value: 'direccion' },
  { label: 'Teléfono', value: 'telefono' },
  { label: 'Email', value: 'email' },
  { label: 'Tipo Persona', value: 'tipo_persona' },
  { label: 'Municipio', value: 'municipio' },
  { label: 'Departamento', value: 'departamento' },
  // Obligación
  { label: '--- OBLIGACIÓN ---', value: '', disabled: true },
  { label: 'Número Obligación', value: 'numero_obligacion' },
  { label: 'Vigencia', value: 'vigencia' },
  { label: 'Valor Total', value: 'valor_total' },
  { label: 'Capital', value: 'capital' },
  { label: 'Intereses', value: 'intereses' },
  { label: 'Multas', value: 'multas' },
  { label: 'Fecha Emisión', value: 'fecha_emision' },
  { label: 'Fecha Vencimiento', value: 'fecha_vencimiento' },
  { label: 'Concepto', value: 'concepto' },
  { label: 'Estado', value: 'estado' }
])

// Cargar lotes
const loadBatches = async () => {
  loading.value = true
  try {
    const params = filterStatus.value ? { status: filterStatus.value } : {}
    const response = await api.get('/importer/batches', { params })
    batches.value = response.data
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: 'No se pudieron cargar los lotes de importación' 
    })
  } finally {
    loading.value = false
  }
}

// Cargar plantillas de mapeo
const loadMappingTemplates = async () => {
  try {
    const response = await api.get('/importer/mapping-templates')
    mappingTemplates.value = response.data
  } catch (error) {
    console.error('Error cargando plantillas:', error)
  }
}

// Seleccionar archivo
const onFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

// Subir archivo
const uploadFile = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  if (selectedTemplate.value) {
    formData.append('template_id', selectedTemplate.value)
  }

  try {
    const response = await api.post('/importer/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    toast.add({ 
      severity: 'success', 
      summary: 'Archivo subido', 
      detail: `Se detectaron ${response.data.total_rows} filas` 
    })

    showUploadDialog.value = false
    selectedFile.value = null
    selectedTemplate.value = null

    // Si requiere mapeo, abrir dialog
    if (response.data.status === 'MAPPING' && response.data.detected_columns) {
      currentBatch.value = response.data
      columnMapping.value = {}
      openMappingDialog(response.data)
    } else {
      loadBatches()
    }
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'Error al subir archivo' 
    })
  } finally {
    uploading.value = false
  }
}

// Abrir dialog de mapeo
const openMappingDialog = (batch) => {
  currentBatch.value = batch
  columnMapping.value = {}
  showMappingDialog.value = true
}

// Procesar mapeo
const processMapping = async () => {
  // Validar que haya al menos un mapeo
  const hasMapping = Object.values(columnMapping.value).some(v => v && v !== '')
  if (!hasMapping) {
    toast.add({ 
      severity: 'warn', 
      summary: 'Advertencia', 
      detail: 'Debe mapear al menos una columna' 
    })
    return
  }

  processing.value = true

  try {
    // Convertir mapping a formato esperado (filtrar vacíos)
    const cleanMapping = {}
    for (const [col, field] of Object.entries(columnMapping.value)) {
      if (field && field !== '') {
        cleanMapping[col] = field
      }
    }

    await api.post(`/importer/batches/${currentBatch.value.id}/map-and-process`, {
      mapping: cleanMapping,
      save_as_template: saveAsTemplate.value,
      template_name: saveAsTemplate.value ? templateName.value : null
    })

    toast.add({ 
      severity: 'success', 
      summary: 'Procesamiento iniciado', 
      detail: 'La importación se está procesando en segundo plano' 
    })

    showMappingDialog.value = false
    saveAsTemplate.value = false
    templateName.value = ''
    currentBatch.value = null
    loadBatches()
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'Error al procesar mapeo' 
    })
  } finally {
    processing.value = false
  }
}

// Ver detalles
const viewBatchDetails = async (batch) => {
  selectedBatch.value = batch
  
  // Si el lote está procesando, obtener estado actualizado
  if (['PROCESSING', 'MAPPING'].includes(batch.status)) {
    try {
      const response = await api.get(`/importer/batches/${batch.id}/status`)
      selectedBatch.value = response.data
    } catch (error) {
      console.error('Error obteniendo estado:', error)
    }
  }
  
  showDetailsDialog.value = true
}

// Utilidades
const getStatusLabel = (status) => {
  const labels = {
    'PENDING': 'Pendiente',
    'PROCESSING': 'Procesando',
    'MAPPING': 'Requiere Mapeo',
    'VALIDATING': 'Validando',
    'COMPLETED': 'Completado',
    'PARTIAL': 'Completado con Errores',
    'FAILED': 'Fallido'
  }
  return labels[status] || status
}

const getStatusSeverity = (status) => {
  const severities = {
    'PENDING': 'secondary',
    'PROCESSING': 'info',
    'MAPPING': 'warn',
    'VALIDATING': 'info',
    'COMPLETED': 'success',
    'PARTIAL': 'warn',
    'FAILED': 'danger'
  }
  return severities[status] || 'secondary'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CO', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadBatches()
  loadMappingTemplates()
})
</script>

<style scoped>
.import-view {
  padding: 1.5rem;
}

.field {
  margin-bottom: 1rem;
}
</style>
