<template>
  <Layout>
    <div class="resoluciones-view">
      <!-- Header -->
      <div class="view-header mb-4">
        <div class="flex align-items-center gap-3">
          <i class="pi pi-file-signature text-3xl text-purple-600"></i>
          <div>
            <h2 class="text-2xl font-bold text-gray-800 m-0">Asignación de Resoluciones y Radicados</h2>
            <p class="text-gray-500 m-0">Generación de documentos para correspondencia oficial</p>
          </div>
        </div>
      </div>

      <!-- Tarjetas de Resumen -->
      <div class="grid gap-3 mb-4">
        <Card class="shadow-1">
          <template #content>
            <div class="flex align-items-center gap-3">
              <div class="resumen-icon bg-primary">
                <i class="pi pi-file"></i>
              </div>
              <div class="flex-1">
                <span class="text-sm text-gray-500 block">Documentos Pendientes</span>
                <span class="text-2xl font-bold text-primary">{{ documentosPendientes }}</span>
              </div>
            </div>
          </template>
        </Card>

        <Card class="shadow-1">
          <template #content>
            <div class="flex align-items-center gap-3">
              <div class="resumen-icon bg-success">
                <i class="pi pi-check-circle"></i>
              </div>
              <div class="flex-1">
                <span class="text-sm text-gray-500 block">Resoluciones Asignadas</span>
                <span class="text-2xl font-bold text-green-600">{{ resolucionesAsignadas }}</span>
              </div>
            </div>
          </template>
        </Card>

        <Card class="shadow-1">
          <template #content>
            <div class="flex align-items-center gap-3">
              <div class="resumen-icon bg-warning">
                <i class="pi pi-exclamation-triangle"></i>
              </div>
              <div class="flex-1">
                <span class="text-sm text-gray-500 block">Radicados Generados</span>
                <span class="text-2xl font-bold text-orange-600">{{ radicadosGenerados }}</span>
              </div>
            </div>
          </template>
        </Card>

        <Card class="shadow-1">
          <template #content>
            <div class="flex align-items-center gap-3">
              <div class="resumen-icon bg-info">
                <i class="pi pi-send"></i>
              </div>
              <div class="flex-1">
                <span class="text-sm text-gray-500 block">En Correspondencia</span>
                <span class="text-2xl font-bold text-blue-600">{{ enCorrespondencia }}</span>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Configuración de Consecutivos -->
      <Card class="mb-4 shadow-1">
        <template #header>
          <div class="flex justify-content-between align-items-center">
            <h3 class="m-0 flex align-items-center gap-2">
              <i class="pi pi-cog"></i>Configuración de Consecutivos
            </h3>
            <Button 
              label="Editar Configuración" 
              icon="pi pi-pencil" 
              @click="openConfigDialog"
              outlined
              size="small"
            />
          </div>
        </template>
        <template #content>
          <div class="grid gap-3">
            <div class="col-12 md:col-6 lg:col-3">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-tag mr-2"></i>Prefijo Resolución
                </label>
                <InputText v-model="config.prefijo_resolucion" class="w-full" disabled />
              </div>
            </div>
            <div class="col-12 md:col-6 lg:col-3">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-hashtag mr-2"></i>Número Inicial
                </label>
                <InputText v-model="config.numero_inicial" class="w-full" disabled />
              </div>
            </div>
            <div class="col-12 md:col-6 lg:col-3">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-hashtag mr-2"></i>Número Actual
                </label>
                <InputText v-model="config.numero_actual" class="w-full" disabled />
              </div>
            </div>
            <div class="col-12 md:col-6 lg:col-3">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-tag mr-2"></i>Prefijo Radicado
                </label>
                <InputText v-model="config.prefijo_radicado" class="w-full" disabled />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Generación Masiva de Documentos -->
      <Card class="shadow-1">
        <template #header>
          <div class="flex justify-content-between align-items-center">
            <h3 class="m-0 flex align-items-center gap-2">
              <i class="pi pi-file-export"></i>Generación Masiva de Documentos
            </h3>
            <Button 
              label="Asignar Resoluciones" 
              icon="pi pi-file-export" 
              @click="openAsignacionDialog"
              severity="success"
              :disabled="procesosSeleccionados.length === 0"
              raised
            />
          </div>
        </template>
        <template #content>
          <!-- Filtros -->
          <div class="flex flex-wrap gap-3 mb-4">
            <Dropdown 
              v-model="filtroEstado" 
              :options="estadosDisponibles" 
              optionLabel="name" 
              optionValue="code" 
              placeholder="Filtrar por estado"
              class="w-full md:w-250px"
              showClear
            />
            <Button label="Aplicar" icon="pi pi-filter-fill" severity="primary" @click="aplicarFiltros" />
            <Button label="Limpiar" icon="pi pi-trash" severity="secondary" outlined @click="limpiarFiltros" />
          </div>

          <!-- Tabla de Procesos -->
          <DataTable 
            :value="procesosFiltrados" 
            :loading="loading"
            selectionMode="checkbox"
            v-model:selection="procesosSeleccionados"
            :paginator="true" 
            :rows="15"
            stripedRows
            responsiveLayout="scroll"
            class="p-datatable-gridlines"
          >
            <Column selectionMode="multiple" style="width: 50px"></Column>
            <Column field="reference" header="Referencia" sortable class="col-reference"></Column>
            <Column field="cliente" header="Cliente" sortable class="col-cliente">
              <template #body="slotProps">
                {{ slotProps.data.cliente?.nombre || slotProps.data.cliente?.full_name || 'N/A' }}
              </template>
            </Column>
            <Column field="obligacion" header="Obligación" sortable class="col-obligacion">
              <template #body="slotProps">
                {{ slotProps.data.obligacion?.numero_obligacion || slotProps.data.obligation_number || 'N/A' }}
              </template>
            </Column>
            <Column field="valor_total" header="Valor Total" sortable class="col-valor">
              <template #body="slotProps">
                <span class="font-semibold text-green-600">
                  {{ formatCurrency(slotProps.data.obligacion?.valor_total || slotProps.data.valor_total || 0) }}
                </span>
              </template>
            </Column>
            <Column field="current_state" header="Estado" class="col-estado">
              <template #body="slotProps">
                <Tag :value="slotProps.data.current_state?.name || slotProps.data.estado" severity="info" />
              </template>
            </Column>
            <Column field="created_at" header="Fecha" sortable class="col-fecha">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column header="Acciones" class="col-acciones" style="width: 100px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-eye" 
                  class="p-button-rounded p-button-outlined p-button-info p-button-sm"
                  @click="verDetalle(slotProps.data)"
                  v-tooltip.top="'Ver Detalle'"
                />
              </template>
            </Column>
          </DataTable>

          <!-- Resumen de Selección -->
          <div v-if="procesosSeleccionados.length > 0" class="mt-4">
            <Card class="bg-blue-50 border-blue-200">
              <template #content>
                <div class="flex flex-column gap-3">
                  <div class="flex justify-content-between align-items-center">
                    <div class="flex align-items-center gap-2">
                      <i class="pi pi-info-circle text-blue-600"></i>
                      <span class="font-semibold text-blue-800">
                        {{ procesosSeleccionados.length }} proceso(s) seleccionado(s)
                      </span>
                    </div>
                    <div class="flex gap-2">
                      <Button 
                        label="Calcular Consecutivos" 
                        icon="pi pi-calculator" 
                        @click="calcularConsecutivos"
                        outlined
                        size="small"
                      />
                      <Button 
                        label="Asignar" 
                        icon="pi pi-check" 
                        @click="asignarResoluciones"
                        size="small"
                        severity="success"
                      />
                    </div>
                  </div>
                  
                  <div v-if="consecutivosCalculados" class="grid gap-3">
                    <div class="col-12 md:col-6">
                      <div class="p-3 bg-white border-round border-1 surface-border">
                        <label class="text-sm text-gray-500 block mb-1">
                          <i class="pi pi-file mr-1"></i>Rango de Resoluciones
                        </label>
                        <p class="m-0 font-medium">
                          {{ config.prefijo_resolucion }}-{{ numeroResolucionInicial }} a 
                          {{ config.prefijo_resolucion }}-{{ numeroResolucionFinal }}
                        </p>
                      </div>
                    </div>
                    <div class="col-12 md:col-6">
                      <div class="p-3 bg-white border-round border-1 surface-border">
                        <label class="text-sm text-gray-500 block mb-1">
                          <i class="pi pi-hashtag mr-1"></i>Rango de Radicados
                        </label>
                        <p class="m-0 font-medium">
                          {{ config.prefijo_radicado }}-{{ numeroRadicadoInicial }} a 
                          {{ config.prefijo_radicado }}-{{ numeroRadicadoFinal }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </Card>
          </div>
        </template>
      </Card>

      <!-- Dialog: Configuración -->
      <Dialog 
        v-model:visible="configDialogVisible" 
        modal 
        header="Configuración de Consecutivos"
        :style="{ width: '600px' }"
      >
        <div class="flex flex-column gap-4">
          <Message severity="info" class="mb-2">
            <i class="pi pi-info-circle mr-2"></i>
            Configure los prefijos y números iniciales para resoluciones y radicados
          </Message>

          <div class="grid gap-3">
            <div class="col-12">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-tag mr-2"></i>Prefijo de Resolución
                </label>
                <InputText v-model="config.prefijo_resolucion" class="w-full" placeholder="Ej: RES-2024" />
              </div>
            </div>
            <div class="col-12 md:col-6">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-hashtag mr-2"></i>Número Inicial de Resolución
                </label>
                <InputNumber v-model="config.numero_inicial" class="w-full" />
              </div>
            </div>
            <div class="col-12 md:col-6">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-tag mr-2"></i>Prefijo de Radicado
                </label>
                <InputText v-model="config.prefijo_radicado" class="w-full" placeholder="Ej: RAD-2024" />
              </div>
            </div>
            <div class="col-12 md:col-6">
              <div class="field">
                <label class="font-semibold block mb-2">
                  <i class="pi pi-hashtag mr-2"></i>Número Inicial de Radicado
                </label>
                <InputNumber v-model="config.radicado_inicial" class="w-full" />
              </div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <Button 
            label="Cancelar" 
            icon="pi pi-times" 
            @click="configDialogVisible = false; restoreConfig()"
            class="p-button-text"
          />
          <Button 
            label="Guardar Configuración" 
            icon="pi pi-check" 
            @click="guardarConfiguracion" 
            severity="success"
          />
        </template>
      </Dialog>

      <!-- Dialog: Confirmación Asignación -->
      <Dialog 
        v-model:visible="asignacionDialogVisible" 
        modal 
        header="Confirmar Asignación de Resoluciones"
        :style="{ width: '700px' }"
      >
        <div class="flex flex-column gap-4">
          <Message severity="warn" class="mb-2">
            <i class="pi pi-exclamation-triangle mr-2"></i>
            Está a punto de asignar números de resolución y radicado a 
            <strong>{{ procesosSeleccionados.length }} procesos</strong>.
            <br />Esta acción <strong>no se puede deshacer</strong>.
          </Message>
          
          <Card>
            <template #content>
              <h5 class="mt-0 mb-3 flex align-items-center gap-2">
                <i class="pi pi-info-circle text-blue-600"></i>Resumen de Asignación
              </h5>
              <div class="grid gap-3">
                <div class="col-12">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-list-check text-green-600"></i>
                    <span><strong>Procesos seleccionados:</strong> {{ procesosSeleccionados.length }}</span>
                  </div>
                </div>
                <div class="col-12">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-file text-purple-600"></i>
                    <span><strong>Resoluciones:</strong> {{ config.prefijo_resolucion }}-{{ numeroResolucionInicial }} al {{ config.prefijo_resolucion }}-{{ numeroResolucionFinal }}</span>
                  </div>
                </div>
                <div class="col-12">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-hashtag text-blue-600"></i>
                    <span><strong>Radicados:</strong> {{ config.prefijo_radicado }}-{{ numeroRadicadoInicial }} al {{ config.prefijo_radicado }}-{{ numeroRadicadoFinal }}</span>
                  </div>
                </div>
              </div>
            </template>
          </Card>
          
          <div class="field">
            <label class="font-semibold block mb-2">
              <i class="pi pi-comment mr-2"></i>Observaciones
            </label>
            <Textarea 
              v-model="observaciones" 
              rows="3" 
              class="w-full" 
              placeholder="Observaciones opcionales para esta asignación..."
              autoResize
            />
          </div>
        </div>
        
        <template #footer>
          <Button 
            label="Cancelar" 
            icon="pi pi-times" 
            @click="asignacionDialogVisible = false; consecutivosCalculados = false"
            class="p-button-text"
          />
          <Button 
            label="Confirmar y Generar Documentos" 
            icon="pi pi-check-circle" 
            @click="confirmarAsignacion" 
            severity="success"
            :loading="asignando"
            raised
          />
        </template>
      </Dialog>

      <Toast position="top-right" />
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import Layout from '../components/Layout.vue';
import api from '../services/api';

// Estados
const loading = ref(false);
const asignando = ref(false);
const procesos = ref([]);
const procesosFiltrados = ref([]);
const procesosSeleccionados = ref([]);
const estadosDisponibles = ref([]);
const filtroEstado = ref(null);

// Configuración
const config = ref({
  prefijo_resolucion: 'RES-2024',
  numero_inicial: 1000,
  numero_actual: 1050,
  prefijo_radicado: 'RAD-2024',
  radicado_inicial: 5000
});
const originalConfig = ref({});

// Cálculos
const consecutivosCalculados = ref(false);
const numeroResolucionInicial = ref(0);
const numeroResolucionFinal = ref(0);
const numeroRadicadoInicial = ref(0);
const numeroRadicadoFinal = ref(0);

// Diálogos
const configDialogVisible = ref(false);
const asignacionDialogVisible = ref(false);

// Observaciones
const observaciones = ref('');

// Computed
const documentosPendientes = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'PENDIENTE_ASIGNACION_RESOLUCION').length
);

const resolucionesAsignadas = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'RESOLUCION_RADICADOS_ASIGNADOS').length
);

const radicadosGenerados = computed(() => procesos.value.length);

const enCorrespondencia = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'RESOLUCION_RADICADOS_ASIGNADOS' && p.documento_enviado).length
);

// Métodos
const loadProcesos = async () => {
  loading.value = true;
  try {
    const response = await api.get('/processes/');
    procesos.value = response.data || [];
    aplicarFiltros();
  } catch (error) {
    console.error('Error cargando procesos:', error);
  } finally {
    loading.value = false;
  }
};

const loadEstados = async () => {
  try {
    const response = await api.get('/workflows/states/');
    estadosDisponibles.value = response.data || [];
  } catch (error) {
    console.error('Error cargando estados:', error);
  }
};

const loadConfig = async () => {
  try {
    const response = await api.get('/processes/config');
    if (response.data) {
      config.value = { ...config.value, ...response.data };
      originalConfig.value = { ...config.value };
    }
  } catch (error) {
    console.error('Error cargando configuración:', error);
  }
};

const aplicarFiltros = () => {
  if (!filtroEstado.value) {
    procesosFiltrados.value = procesos.value.filter(p => 
      p.current_state?.code === 'PENDIENTE_ASIGNACION_RESOLUCION'
    );
  } else {
    procesosFiltrados.value = procesos.value.filter(p => 
      p.current_state?.code === filtroEstado.value
    );
  }
};

const limpiarFiltros = () => {
  filtroEstado.value = null;
  aplicarFiltros();
};

const formatCurrency = (value) => {
  if (!value && value !== 0) return '$ 0';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0
  }).format(value);
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

const openConfigDialog = () => {
  configDialogVisible.value = true;
};

const restoreConfig = () => {
  config.value = { ...originalConfig.value };
};

const guardarConfiguracion = async () => {
  try {
    await api.post('/processes/config', config.value);
    originalConfig.value = { ...config.value };
    toast.add({ 
      severity: 'success', 
      summary: 'Éxito', 
      detail: 'Configuración guardada correctamente',
      life: 3000 
    });
    configDialogVisible.value = false;
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: 'No se pudo guardar la configuración',
      life: 5000 
    });
  }
};

const calcularConsecutivos = () => {
  const cantidad = procesosSeleccionados.value.length;
  numeroResolucionInicial.value = config.value.numero_actual + 1;
  numeroResolucionFinal.value = config.value.numero_actual + cantidad;
  numeroRadicadoInicial.value = config.value.radicado_inicial + 1;
  numeroRadicadoFinal.value = config.value.radicado_inicial + cantidad;
  consecutivosCalculados.value = true;
};

const openAsignacionDialog = () => {
  calcularConsecutivos();
  asignacionDialogVisible.value = true;
};

const asignarResoluciones = () => {
  // Abre el dialog de confirmación
  if (procesosSeleccionados.value.length === 0) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'Seleccione al menos un proceso' });
    return;
  }
  openAsignacionDialog();
};

const confirmarAsignacion = async () => {
  asignando.value = true;
  try {
    const payload = {
      process_ids: procesosSeleccionados.value.map(p => p.id),
      resolucion_inicial: numeroResolucionInicial.value,
      radicado_inicial: numeroRadicadoInicial.value,
      observaciones: observaciones.value
    };
    
    await api.post('/processes/assign-resolution/', payload);
    
    // Actualizar números
    config.value.numero_actual = numeroResolucionFinal.value;
    config.value.radicado_inicial = numeroRadicadoFinal.value;
    
    await loadProcesos();
    asignacionDialogVisible.value = false;
    procesosSeleccionados.value = [];
    consecutivosCalculados.value = false;
    observaciones.value = '';
    
    toast.add({ 
      severity: 'success', 
      summary: 'Éxito', 
      detail: `Resoluciones asignadas a ${procesosSeleccionados.value.length} procesos`,
      life: 5000 
    });
  } catch (error) {
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'Error al asignar resoluciones',
      life: 5000 
    });
  } finally {
    asignando.value = false;
  }
};

const verDetalle = (proceso) => {
  console.log('Ver detalle:', proceso);
  // Podría abrir un dialog con más detalles
};

// Lifecycle
onMounted(() => {
  loadProcesos();
  loadEstados();
  loadConfig();
});
</script>

<style scoped>
.resoluciones-view {
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

.resumen-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
}

.resumen-icon.bg-primary {
  background: var(--primary-color);
}

.resumen-icon.bg-success {
  background: var(--green-500);
}

.resumen-icon.bg-warning {
  background: var(--orange-500);
}

.resumen-icon.bg-info {
  background: var(--blue-500);
}

.col-reference { width: 120px; }
.col-cliente { width: 25%; }
.col-obligacion { width: 150px; }
.col-valor { width: 120px; text-align: right; }
.col-estado { width: 120px; }
.col-fecha { width: 120px; }
.col-acciones { width: 100px; }

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
