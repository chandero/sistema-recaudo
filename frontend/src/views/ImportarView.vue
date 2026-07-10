<template>
  <Layout>
    <div class="import-view">
      <!-- Header -->
      <div class="view-header mb-4">
        <div class="flex align-items-center gap-3">
          <i class="pi pi-upload text-3xl text-blue-600"></i>
          <div>
            <h2 class="text-2xl font-bold text-gray-800 m-0">Importación de Cartera</h2>
            <p class="text-gray-500 m-0">Cargar archivos Excel o CSV con datos de cartera</p>
          </div>
        </div>
        <Button 
          label="Nueva Importación" 
          icon="pi pi-plus-circle" 
          severity="success"
          raised
          @click="showUploadDialog = true"
        />
      </div>

      <!-- Filtros -->
      <Card class="mb-4 shadow-1">
        <template #content>
          <div class="flex flex-column sm:flex-row gap-3">
            <Dropdown 
              v-model="filterStatus" 
              :options="statusOptions" 
              optionLabel="label" 
              optionValue="value"
              placeholder="Todos los estados"
              class="w-full sm:w-200px"
            />
            <Button label="Filtrar" icon="pi pi-filter-fill" severity="primary" @click="loadBatches" />
            <Button label="Recargar" icon="pi pi-refresh" severity="secondary" outlined @click="loadBatches" />
          </div>
        </template>
      </Card>

      <!-- Tabla de lotes -->
      <Card class="shadow-1">
        <template #header>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-database"></i>
            <h3 class="m-0">Historial de Importaciones</h3>
          </div>
        </template>
        <template #content>
          <DataTable 
            :value="batches" 
            :loading="loading"
            stripedRows
            responsiveLayout="scroll"
            paginator
            :rows="10"
            :rowsPerPageOptions="[5, 10, 20, 50]"
            class="p-datatable-gridlines"
          >
            <Column field="id" header="ID" style="width: 60px"></Column>
            <Column field="original_filename" header="Archivo" sortable>
              <template #body="slotProps">
                <div class="flex align-items-center gap-2">
                  <i class="pi pi-file-excel text-green-600"></i>
                  <span>{{ slotProps.data.original_filename }}</span>
                </div>
              </template>
            </Column>
            <Column field="total_rows" header="Filas" sortable style="width: 100px">
              <template #body="slotProps">
                <span class="font-medium">{{ slotProps.data.total_rows }}</span>
              </template>
            </Column>
            <Column field="success_rows" header="Éxito" sortable style="width: 100px">
              <template #body="slotProps">
                <span class="text-green-600 font-medium">{{ slotProps.data.success_rows }}</span>
              </template>
            </Column>
            <Column field="error_rows" header="Errores" sortable style="width: 100px">
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
            <Column field="created_at" header="Fecha" sortable style="width: 150px">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column header="Acciones" style="width: 120px">
              <template #body="slotProps">
                <div class="flex gap-1">
                  <Button 
                    icon="pi pi-eye" 
                    class="p-button-rounded p-button-outlined p-button-info p-button-sm"
                    title="Ver detalles"
                    @click="viewBatchDetails(slotProps.data)"
                  />
                  <Button 
                    v-if="slotProps.data.status === 'MAPPING'" 
                    icon="pi pi-link" 
                    class="p-button-rounded p-button-outlined p-button-warning p-button-sm"
                    title="Mapear columnas"
                    @click="openMappingDialog(slotProps.data)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Dialog: Subir Archivo -->
      <Dialog 
        v-model:visible="showUploadDialog" 
        modal 
        header="Subir Archivo de Cartera"
        :style="{ width: '600px' }"
        :pt="{ 
          root: { class: 'border-none shadow-2' },
          header: { class: 'bg-primary text-white border-none p-4' },
          content: { class: 'p-0' },
          footer: { class: 'p-4 border-top-1 surface-border bg-surface-50' }
        }"
      >
        <div class="p-4 surface-ground">
          <Message severity="info" class="mb-4">
            <i class="pi pi-info-circle mr-2"></i>
            Suba archivos Excel (.xlsx, .xls) o CSV con los datos de cartera. El sistema detectará automáticamente las columnas.
          </Message>

          <div class="flex flex-column gap-4">
            <div class="field">
              <label for="fileInput" class="block mb-2 font-medium">
                <i class="pi pi-file-excel mr-2 text-green-600"></i>Archivo
              </label>
              <FileUpload 
                mode="basic" 
                name="fileInput" 
                @select="onFileSelect" 
                accept=".xlsx,.xls,.csv" 
                :maxFileSize="50000000" 
                chooseLabel="Seleccionar Archivo" 
                class="w-full"
              />
              <small class="text-gray-500 block mt-2">
                <i class="pi pi-check-circle mr-1"></i>
                Formatos permitidos: .xlsx, .xls, .csv (máximo 50MB)
              </small>
            </div>

            <div class="field" v-if="mappingTemplates.length > 0">
              <label class="block mb-2 font-medium">
                <i class="pi pi-book mr-2 text-blue-600"></i>Plantilla de Mapeo (opcional)
              </label>
              <Dropdown 
                v-model="selectedTemplate" 
                :options="mappingTemplates" 
                optionLabel="name" 
                optionValue="id" 
                placeholder="Seleccionar plantilla de mapeo" 
                class="w-full"
                showClear
              />
              <small class="text-gray-500 block mt-1">
                <i class="pi pi-info-circle mr-1"></i>
                Si tiene una plantilla de mapeo guardada, selecciónela para saltar el paso de mapeo
              </small>
            </div>

            <!-- Nuevo campo para seleccionar estado inicial del proceso -->
            <div class="field">
              <label class="block mb-2 font-medium">
                <i class="pi pi-sitemap mr-2 text-purple-600"></i>Estado Inicial del Proceso (opcional)
              </label>
              <Dropdown 
                v-model="initialProcessState" 
                :options="processStates" 
                optionLabel="name" 
                optionValue="code" 
                placeholder="Seleccionar estado inicial del proceso" 
                class="w-full"
                showClear
              />
              <small class="text-gray-500 block mt-1">
                <i class="pi pi-info-circle mr-1"></i>
                Si selecciona un estado, los registros importados iniciarán en este estado del flujo de proceso
              </small>
            </div>

            <div v-if="selectedFile" class="bg-blue-50 p-3 border-round">
              <div class="flex align-items-center gap-3">
                <i class="pi pi-file-excel text-green-600 text-2xl"></i>
                <div class="flex-1">
                  <p class="m-0 font-medium">{{ selectedFile.name }}</p>
                  <p class="m-0 text-sm text-gray-600">{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB</p>
                </div>
              </div>
              <ProgressBar v-if="uploading" mode="indeterminate" class="mt-3" style="height: 4px" />
            </div>
          </div>
        </div>

        <template #footer>
          <Button 
            label="Cancelar" 
            icon="pi pi-times" 
            @click="showUploadDialog = false; selectedFile = null; selectedTemplate = null; initialProcessState = null"
            class="p-button-text"
          />
          <Button 
            label="Subir y Procesar" 
            icon="pi pi-upload" 
            @click="uploadFile" 
            :disabled="!selectedFile" 
            :loading="uploading" 
            severity="success"
            raised
          />
        </template>
      </Dialog>

      <!-- Dialog: Mapeo de Columnas -->
      <Dialog 
        v-model:visible="showMappingDialog" 
        modal 
        header="Mapeo de Columnas del Archivo"
        :style="{ width: '900px' }"
        :closable="false"
      >
        <Message severity="info" class="mb-4">
          <i class="pi pi-info-circle mr-2"></i>
          Asigne cada columna del archivo a un campo del sistema. Las columnas sin mapeo serán ignoradas.
        </Message>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="col in currentBatch?.detected_columns || []" :key="col" class="field">
            <label class="block mb-2 font-medium text-sm">
              <i class="pi pi-table mr-1"></i>{{ col }}
            </label>
            <Dropdown 
              v-model="columnMapping[col]" 
              :options="systemFields" 
              optionLabel="label" 
              optionValue="value"
              placeholder="-- Seleccionar campo --"
              class="w-full"
              showClear
              filter
            />
          </div>
        </div>

        <Divider class="my-4" />

        <div class="flex align-items-center gap-2 mb-4">
          <Checkbox v-model="saveAsTemplate" inputId="saveTemplate" :binary="true" />
          <label for="saveTemplate" class="cursor-pointer font-medium">
            <i class="pi pi-save mr-2"></i>Guardar este mapeo como plantilla reutilizable
          </label>
        </div>

        <div v-if="saveAsTemplate" class="field">
          <label for="templateName" class="block mb-2 font-medium">Nombre de la plantilla</label>
          <div class="p-inputgroup">
            <span class="p-inputgroup-addon">
              <i class="pi pi-tag"></i>
            </span>
            <InputText 
              id="templateName" 
              v-model="templateName" 
              placeholder="Ej: Importación Alumbrado Público 2024"
              class="w-full"
            />
          </div>
        </div>

        <template #footer>
          <Button 
            label="Cancelar" 
            icon="pi pi-times" 
            @click="showMappingDialog = false; columnMapping = {}; saveAsTemplate = false; templateName = ''; initialProcessState = null"
            class="p-button-text"
          />
          <Button 
            label="Procesar Importación" 
            icon="pi pi-check-circle" 
            @click="processMapping" 
            :loading="processing" 
            severity="success"
            raised
          />
        </template>
      </Dialog>

      <!-- Dialog: Detalles del Lote -->
      <Dialog 
        v-model:visible="showDetailsDialog" 
        modal 
        header="Detalles del Lote de Importación"
        :style="{ width: '700px' }"
      >
        <div v-if="selectedBatch" class="flex flex-column gap-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-file mr-1"></i>Archivo
              </label>
              <p class="m-0 font-medium">{{ selectedBatch.original_filename }}</p>
            </div>
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-calendar mr-1"></i>Fecha
              </label>
              <p class="m-0 font-medium">{{ formatDateTime(selectedBatch.created_at) }}</p>
            </div>
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-list mr-1"></i>Total filas
              </label>
              <p class="m-0 font-medium">{{ selectedBatch.total_rows }}</p>
            </div>
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-check-circle mr-1"></i>Exitosas
              </label>
              <p class="m-0 font-medium text-green-600">{{ selectedBatch.success_rows }}</p>
            </div>
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-exclamation-circle mr-1"></i>Con errores
              </label>
              <p class="m-0 font-medium" :class="selectedBatch.error_rows > 0 ? 'text-red-600' : 'text-gray-600'">
                {{ selectedBatch.error_rows }}
              </p>
            </div>
            <div class="card-detail">
              <label class="text-sm text-gray-500">
                <i class="pi pi-tag mr-1"></i>Estado
              </label>
              <Tag 
                :value="getStatusLabel(selectedBatch.status)" 
                :severity="getStatusSeverity(selectedBatch.status)"
                class="font-medium"
              />
            </div>
          </div>

          <Divider v-if="selectedBatch.errors_log && selectedBatch.errors_log.length > 0" />

          <div v-if="selectedBatch.errors_log && selectedBatch.errors_log.length > 0">
            <label class="block mb-2 font-medium">
              <i class="pi pi-exclamation-triangle text-red-500 mr-1"></i>Errores de Importación
            </label>
            <Card>
              <ScrollPanel style="max-height: 250px" class="p-3">
                <ul class="text-sm space-y-2">
                  <li v-for="(error, idx) in selectedBatch.errors_log.slice(0, 20)" :key="idx" 
                      class="p-2 bg-red-50 border-round border-red-200">
                    <div class="flex align-items-center gap-2">
                      <i class="pi pi-times-circle text-red-500"></i>
                      <div>
                        <strong>Fila {{ error.row }}:</strong> {{ error.error }}
                      </div>
                    </div>
                  </li>
                </ul>
              </ScrollPanel>
              <small class="text-gray-500 block mt-2 text-center">
                Mostrando primeros 20 errores
              </small>
            </Card>
          </div>

          <div v-else-if="selectedBatch.status === 'COMPLETED'" class="text-center py-4">
            <i class="pi pi-check-circle text-4xl text-green-500 mb-2"></i>
            <p class="text-green-600 font-medium text-lg">Importación completada exitosamente</p>
            <p class="text-gray-500 mt-2">{{ selectedBatch.success_rows }} de {{ selectedBatch.total_rows }} filas procesadas</p>
          </div>
        </div>

        <template #footer>
          <Button 
            label="Cerrar" 
            icon="pi pi-times" 
            @click="showDetailsDialog = false"
          />
        </template>
      </Dialog>

      <Toast position="top-right" />
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import Layout from '../components/Layout.vue';
import api from '../services/api';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

// Estados
const loading = ref(false);
const uploading = ref(false);
const processing = ref(false);
const batches = ref([]);
const mappingTemplates = ref([]);
const filterStatus = ref(null);

// Estados para la selección de estado inicial del proceso
const processStates = ref([]);
const initialProcessState = ref(null);

// Dialogs
const showUploadDialog = ref(false);
const showMappingDialog = ref(false);
const showDetailsDialog = ref(false);

// Archivo y mapeo
const selectedFile = ref(null);
const selectedTemplate = ref(null);
const currentBatch = ref(null);
const selectedBatch = ref(null);
const columnMapping = ref({});
const saveAsTemplate = ref(false);
const templateName = ref('');

// Opciones de estado
const statusOptions = ref([
  { label: 'Todos', value: null },
  { label: 'Pendiente', value: 'PENDING' },
  { label: 'En mapeo', value: 'MAPPING' },
  { label: 'Procesando', value: 'PROCESSING' },
  { label: 'Completado', value: 'COMPLETED' },
  { label: 'Parcial', value: 'PARTIAL' },
  { label: 'Fallido', value: 'FAILED' }
]);

// Campos del sistema para mapeo
const systemFields = ref([
  // Cliente
  { label: '--- CLIENTE ---', value: '', disabled: true },
  { label: 'Identificación', value: 'identificacion' },
  { label: 'Nombre/Razón Social', value: 'nombre' },
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
]);

// Cargar lotes
const loadBatches = async () => {
  loading.value = true;
  try {
    const params = filterStatus.value ? { status: filterStatus.value } : {};
    const response = await api.get('/importer/batches', { params });
    batches.value = response.data;
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: 'No se pudieron cargar los lotes de importación' 
    });
  } finally {
    loading.value = false;
  }
};

// Cargar estados de proceso
const loadProcessStates = async () => {
  try {
    const response = await api.get('/workflows/states/');
    processStates.value = response.data || [];
  } catch (error) {
    console.error('Error cargando estados de proceso:', error);
    // Usar estados por defecto si falla la carga
    processStates.value = [
      { name: 'Pendiente', code: 'PENDING' },
      { name: 'En Proceso', code: 'IN_PROGRESS' },
      { name: 'Por Cobrar', code: 'FOR_COLLECTION' },
      { name: 'Cobrado', code: 'COLLECTED' },
      { name: 'Cancelado', code: 'CANCELLED' },
      { name: 'Devuelto', code: 'RETURNED' }
    ];
  }
};

// Cargar plantillas de mapeo
const loadMappingTemplates = async () => {
  try {
    const response = await api.get('/importer/mapping-templates');
    mappingTemplates.value = response.data;
  } catch (error) {
    console.error('Error cargando plantillas:', error);
  }
};

// Seleccionar archivo
const onFileSelect = (event) => {
  selectedFile.value = event.files[0];
};

// Subir archivo
const uploadFile = async () => {
  if (!selectedFile.value) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append('file', selectedFile.value);
  if (selectedTemplate.value) {
    formData.append('template_id', selectedTemplate.value);
  }
  // Agregar estado inicial del proceso si está seleccionado
  if (initialProcessState.value) {
    formData.append('initial_process_state', initialProcessState.value);
  }
  try {
    const response = await api.post('/importer/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    toast.add({ 
      severity: 'success', 
      summary: 'Archivo subido', 
      detail: `Se detectaron ${response.data.total_rows} filas` 
    });
    showUploadDialog.value = false;
    selectedFile.value = null;
    selectedTemplate.value = null;
    initialProcessState.value = null;
    if (response.data.status === 'MAPPING' && response.data.detected_columns) {
      currentBatch.value = response.data;
      columnMapping.value = {};
      openMappingDialog(response.data);
    } else {
      loadBatches();
    }
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'Error al subir archivo' 
    });
  } finally {
    uploading.value = false;
  }
};

// Abrir dialog de mapeo
const openMappingDialog = (batch) => {
  currentBatch.value = batch;
  columnMapping.value = {};
  showMappingDialog.value = true;
};

// Procesar mapeo
const processMapping = async () => {
  const hasMapping = Object.values(columnMapping.value).some(v => v && v !== '');
  if (!hasMapping) {
    toast.add({ 
      severity: 'warn', 
      summary: 'Advertencia', 
      detail: 'Debe mapear al menos una columna' 
    });
    return;
  }
  processing.value = true;
  try {
    const cleanMapping = {};
    for (const [col, field] of Object.entries(columnMapping.value)) {
      if (field && field !== '') {
        cleanMapping[col] = field;
      }
    }
    await api.post(`/importer/batches/${currentBatch.value.id}/map-and-process`, {
      mapping: cleanMapping,
      save_as_template: saveAsTemplate.value,
      template_name: saveAsTemplate.value ? templateName.value : null,
      // Incluir estado inicial del proceso si está definido
      initial_process_state: initialProcessState.value
    });
    toast.add({ 
      severity: 'success', 
      summary: 'Procesamiento iniciado', 
      detail: 'La importación se está procesando' 
    });
    showMappingDialog.value = false;
    saveAsTemplate.value = false;
    templateName.value = '';
    currentBatch.value = null;
    initialProcessState.value = null;
    loadBatches();
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'Error al procesar mapeo' 
    });
  } finally {
    processing.value = false;
  }
};

// Ver detalles
const viewBatchDetails = async (batch) => {
  selectedBatch.value = batch;
  if (['PROCESSING', 'MAPPING'].includes(batch.status)) {
    try {
      const response = await api.get(`/importer/batches/${batch.id}/status`);
      selectedBatch.value = response.data;
    } catch (error) {
      console.error('Error:', error);
    }
  }
  showDetailsDialog.value = true;
};

// Utilidades
const getStatusLabel = (status) => {
  const labels = {
    'PENDING': 'Pendiente',
    'PROCESSING': 'Procesando',
    'MAPPING': 'Requiere Mapeo',
    'VALIDATING': 'Validando',
    'COMPLETED': 'Completado',
    'PARTIAL': 'Parcial',
    'FAILED': 'Fallido'
  };
  return labels[status] || status;
};

const getStatusSeverity = (status) => {
  const severities = {
    'PENDING': 'secondary',
    'PROCESSING': 'info',
    'MAPPING': 'warn',
    'VALIDATING': 'info',
    'COMPLETED': 'success',
    'PARTIAL': 'warn',
    'FAILED': 'danger'
  };
  return severities[status] || 'secondary';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit'
  });
};

const formatDateTime = (dateString) => {
  return formatDate(dateString);
};

// Lifecycle
onMounted(() => {
  loadBatches();
  loadMappingTemplates();
  loadProcessStates(); // Cargar estados de proceso
});
</script>

<style scoped>
.import-view {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (min-width: 768px) {
  .view-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.card-detail {
  background: var(--surface-card);
  padding: 1rem;
  border-radius: 8px;
}

::v-deep(.p-datatable .p-column-header-content) {
  font-weight: 600;
  color: var(--text-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.85rem;
}

::v-deep(.p-datatable-gridlines .p-datatable-thead > tr > th) {
  border-right: 1px solid var(--surface-border);
  border-bottom: 2px solid var(--surface-border);
}

::v-deep(.p-datatable-gridlines .p-datatable-tbody > tr > td) {
  border-right: 1px solid var(--surface-border);
  border-bottom: 1px solid var(--surface-border);
}
</style>