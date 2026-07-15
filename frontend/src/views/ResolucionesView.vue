<template>
  <div class="resoluciones-view">
      <!-- Header -->
      <div class="view-header mb-4">
        <div class="flex align-items-center gap-3">
          <i class="pi pi-file-signature text-3xl text-purple-600"></i>
          <div>
            <h2 class="text-2xl font-bold text-gray-800 m-0">Asignación de Resoluciones y Radicados</h2>
            <p class="text-gray-500 m-0">Asigna consecutivos oficiales a obligaciones según su estado actual</p>
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
                <span class="text-sm text-gray-500 block">Obligaciones Pendientes</span>
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

      <!-- Asignación Masiva de Resoluciones -->
      <Card class="shadow-1">
        <template #header>
          <div class="flex justify-content-between align-items-center">
            <h3 class="m-0 flex align-items-center gap-2">
              <i class="pi pi-file-export"></i>Asignación Masiva de Resoluciones
            </h3>
            <div class="flex gap-2">
              <Button
                label="Generar correspondencia ZIP"
                icon="pi pi-envelope"
                @click="generarCorrespondencia"
                severity="info"
                :loading="generandoCorrespondencia"
                :disabled="procesosSeleccionados.length === 0"
                outlined
              />
              <Button 
                label="Asignar Resoluciones" 
                icon="pi pi-file-export" 
                @click="asignarResoluciones"
                severity="success"
                raised
              />
            </div>
          </div>
        </template>
        <template #content>
          <!-- Datos obligatorios de la resolución -->
          <div class="resolution-data mb-4">
            <h4 class="mt-0 mb-3 flex align-items-center gap-2">
              <i class="pi pi-file-edit text-purple-600"></i>
              Datos de la resolución
            </h4>
            <div class="grid gap-3">
              <div class="col-12 md:col-3">
                <div class="field">
                  <label class="font-semibold block mb-2" for="main-resolution-number">
                    Número inicial de resolución <span class="text-red-500">*</span>
                  </label>
                  <InputNumber
                    id="main-resolution-number"
                    v-model="resolutionNumber"
                    :useGrouping="false"
                    :min="1"
                    class="w-full"
                    placeholder="Ingrese el número inicial"
                  />
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="field">
                  <label class="font-semibold block mb-2" for="main-resolution-year">
                    Año de resolución <span class="text-red-500">*</span>
                  </label>
                  <InputNumber
                    id="main-resolution-year"
                    v-model="resolutionYear"
                    :useGrouping="false"
                    :min="1900"
                    :max="9999"
                    class="w-full"
                    placeholder="Ej: 2026"
                  />
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="field">
                  <label class="font-semibold block mb-2" for="main-resolution-date">
                    Fecha de resolución <span class="text-red-500">*</span>
                  </label>
                  <InputText
                    id="main-resolution-date"
                    v-model="resolutionDate"
                    type="date"
                    class="w-full"
                  />
                </div>
              </div>
              <div class="col-12 md:col-3">
                <div class="field">
                  <label class="font-semibold block mb-2" for="main-radicado-number">
                    Número inicial de radicado <span class="text-red-500">*</span>
                  </label>
                  <InputNumber
                    id="main-radicado-number"
                    v-model="numeroRadicadoInicial"
                    :useGrouping="false"
                    :min="1"
                    class="w-full"
                    placeholder="Ingrese el número"
                  />
                </div>
              </div>
            </div>
            <small class="text-gray-500">
              Las resoluciones y los radicados se incrementarán consecutivamente desde los números iniciales ingresados.
            </small>
            <div class="flex align-items-center gap-2 mt-3">
              <Checkbox v-model="overwriteAssignments" inputId="overwrite-assignments" binary />
              <label for="overwrite-assignments" class="font-semibold cursor-pointer">
                Sobrescribir resolución, año, fecha y radicado existentes
              </label>
              <Tag
                :value="overwriteAssignments ? 'Activo' : 'Inactivo'"
                :severity="overwriteAssignments ? 'warning' : 'secondary'"
              />
            </div>
            <Message v-if="overwriteAssignments" severity="warn" :closable="false" class="mt-3 mb-0">
              Los datos actuales de las obligaciones seleccionadas serán reemplazados.
            </Message>
          </div>

          <div class="resolution-data mb-4">
            <h4 class="mt-0 mb-3 flex align-items-center gap-2">
              <i class="pi pi-print text-blue-600"></i>
              Impresión de correspondencia por rango
            </h4>
            <div class="grid gap-3 align-items-end">
              <div class="col-12 md:col-3">
                <label class="font-semibold block mb-2" for="print-resolution-from">Resolución desde</label>
                <InputNumber
                  id="print-resolution-from"
                  v-model="printRange.from"
                  :useGrouping="false"
                  :min="1"
                  class="w-full"
                />
              </div>
              <div class="col-12 md:col-3">
                <label class="font-semibold block mb-2" for="print-resolution-to">Resolución hasta</label>
                <InputNumber
                  id="print-resolution-to"
                  v-model="printRange.to"
                  :useGrouping="false"
                  :min="1"
                  class="w-full"
                />
              </div>
              <div class="col-12 md:col-6 flex gap-2">
                <Button
                  label="Descargar DOCX"
                  icon="pi pi-file-word"
                  severity="secondary"
                  class="w-full"
                  @click="generarImpresionPorRango('docx')"
                  :loading="generandoImpresion"
                  :disabled="!printRange.from || !printRange.to"
                  outlined
                />
                <Button
                  label="Abrir PDF para imprimir"
                  icon="pi pi-print"
                  severity="info"
                  class="w-full"
                  @click="generarImpresionPorRango('pdf')"
                  :loading="generandoImpresion"
                  :disabled="!printRange.from || !printRange.to"
                />
              </div>
            </div>
            <small class="text-gray-500">
              El rango genera un solo archivo, con las correspondencias ordenadas por resolución. El PDF se abre en un visor con opción de imprimir o descargar.
            </small>
          </div>

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
            <Button
              label="Seleccionar todas"
              icon="pi pi-check-square"
              severity="success"
              outlined
              @click="seleccionarTodas"
              :disabled="procesosElegibles.length === 0"
            />
            <Button
              label="Deseleccionar todas"
              icon="pi pi-times"
              severity="secondary"
              text
              @click="deseleccionarTodas"
              :disabled="procesosSeleccionados.length === 0"
            />
            <Button
              label="Seleccionar con resolución"
              icon="pi pi-envelope"
              severity="info"
              outlined
              @click="seleccionarConResolucion"
              :disabled="procesosConResolucion.length === 0"
            />
          </div>

          <!-- Tabla de Obligaciones -->
          <DataTable 
            :value="procesosFiltrados" 
            :loading="loading"
            dataKey="obligation_id"
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
            <Column field="resolution_number" header="Resolución" class="col-reference">
              <template #body="slotProps">
                {{ slotProps.data.resolution_number || 'Sin asignar' }}
              </template>
            </Column>
            <Column field="resolution_year" header="Año resolución" class="col-reference">
              <template #body="slotProps">
                {{ slotProps.data.resolution_year || 'Sin asignar' }}
              </template>
            </Column>
            <Column field="resolution_date" header="Fecha resolución" class="col-fecha">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.resolution_date) }}
              </template>
            </Column>
            <Column field="radicado_number" header="Radicado" class="col-reference">
              <template #body="slotProps">
                {{ slotProps.data.radicado_number || 'Sin asignar' }}
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
                        {{ procesosSeleccionados.length }} obligación(es) seleccionada(s)
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
                          {{ resolutionNumber }} a {{ resolutionNumberFinal }}
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
            <strong>{{ procesosSeleccionados.length }} obligaciones</strong>.
            <br />Esta acción <strong>no se puede deshacer</strong>.
            <template v-if="overwriteAssignments">
              <br /><strong>Modo sobrescritura activo:</strong> se reemplazarán los datos existentes.
            </template>
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
                    <span><strong>Obligaciones seleccionadas:</strong> {{ procesosSeleccionados.length }}</span>
                  </div>
                </div>
                <div class="col-12 md:col-6">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-calendar text-purple-600"></i>
                    <span><strong>Año de resolución:</strong> {{ resolutionYear }}</span>
                  </div>
                </div>
                <div class="col-12 md:col-6">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-calendar text-purple-600"></i>
                    <span><strong>Fecha de resolución:</strong> {{ formatDate(resolutionDate) }}</span>
                  </div>
                </div>
                <div class="col-12">
                  <div class="flex align-items-center gap-2 mb-2">
                    <i class="pi pi-file text-purple-600"></i>
                    <span><strong>Resoluciones:</strong> {{ resolutionNumber }} al {{ resolutionNumberFinal }}</span>
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
            label="Confirmar asignación" 
            icon="pi pi-check-circle" 
            @click="confirmarAsignacion" 
            severity="success"
            :loading="asignando"
            :disabled="!resolutionNumber || !resolutionYear || !resolutionDate || !numeroRadicadoInicial"
            raised
          />
        </template>
      </Dialog>

      <Toast position="top-right" />
    </div>
  </template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import Checkbox from 'primevue/checkbox';
import api from '../services/api';

const toast = useToast();

// Estados
const loading = ref(false);
const asignando = ref(false);
const generandoCorrespondencia = ref(false);
const generandoImpresion = ref(false);
const procesos = ref([]);
const procesosFiltrados = ref([]);
const procesosSeleccionados = ref([]);
const estadosDisponibles = ref([]);
const filtroEstado = ref(null);
const printRange = ref({ from: null, to: null });

// Configuración
const config = ref({
  prefijo_resolucion: 'RES-2024',
  numero_inicial: 1000,
  numero_actual: 1050,
  prefijo_radicado: 'RAD-2024',
  radicado_inicial: 5000
});

// Cálculos
const consecutivosCalculados = ref(false);
const resolutionNumber = ref(0);
const resolutionNumberFinal = ref(0);
const numeroRadicadoInicial = ref(0);
const numeroRadicadoFinal = ref(0);

// Diálogos
const asignacionDialogVisible = ref(false);

// Observaciones
const observaciones = ref('');
const overwriteAssignments = ref(false);
const today = new Date();
const resolutionYear = ref(today.getFullYear());
const resolutionDate = ref([
  today.getFullYear(),
  String(today.getMonth() + 1).padStart(2, '0'),
  String(today.getDate()).padStart(2, '0')
].join('-'));

// Computed
const documentosPendientes = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'PENDIENTE_ASIGNACION_RESOLUCION').length
);

const resolucionesAsignadas = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'RESOLUCION_RADICADOS_ASIGNADOS').length
);

const radicadosGenerados = computed(() =>
  procesos.value.filter(p => Boolean(p.radicado_number)).length
);

const enCorrespondencia = computed(() => 
  procesos.value.filter(p => p.current_state?.code === 'RESOLUCION_RADICADOS_ASIGNADOS' && p.documento_enviado).length
);

const puedeAsignarResoluciones = computed(() =>
  procesosSeleccionados.value.length > 0 &&
  Boolean(resolutionNumber.value) &&
  Boolean(numeroRadicadoInicial.value) &&
  Boolean(resolutionYear.value) &&
  Boolean(resolutionDate.value) &&
  (overwriteAssignments.value || procesosSeleccionados.value.every(p => !p.resolution_number && !p.radicado_number))
);

const procesosElegibles = computed(() =>
  overwriteAssignments.value
    ? procesosFiltrados.value
    : procesosFiltrados.value.filter(p => !p.resolution_number && !p.radicado_number)
);

const procesosConResolucion = computed(() =>
  procesosFiltrados.value.filter(p => p.resolution_number && p.resolution_date)
);

// Métodos
const loadProcesos = async () => {
  loading.value = true;
  try {
    const response = await api.get('/processes/resolution-obligations', {
      params: {
        state_code: filtroEstado.value || undefined,
        limit: 10000
      }
    });
    procesos.value = response.data || [];
    procesosFiltrados.value = procesos.value;
    procesosSeleccionados.value = [];
  } catch (error) {
    console.error('Error cargando obligaciones:', error);
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
      if (!numeroRadicadoInicial.value) {
        numeroRadicadoInicial.value = config.value.radicado_inicial + 1;
      }
    }
  } catch (error) {
    console.error('Error cargando configuración:', error);
  }
};

const aplicarFiltros = () => {
  loadProcesos();
};

const limpiarFiltros = () => {
  filtroEstado.value = null;
  aplicarFiltros();
};

const seleccionarTodas = () => {
  procesosSeleccionados.value = [...procesosElegibles.value];
};

const deseleccionarTodas = () => {
  procesosSeleccionados.value = [];
};

const seleccionarConResolucion = () => {
  procesosSeleccionados.value = [...procesosConResolucion.value];
};

const generarCorrespondencia = async () => {
  const seleccion = procesosSeleccionados.value.filter(p => p.resolution_number && p.resolution_date);
  if (seleccion.length !== procesosSeleccionados.value.length) {
    toast.add({
      severity: 'warn',
      summary: 'Selección inválida',
      detail: 'Todas las obligaciones seleccionadas deben tener resolución y fecha',
      life: 5000
    });
    return;
  }

  generandoCorrespondencia.value = true;
  try {
    const response = await api.post('/documents/correspondence/batch', {
      obligation_ids: seleccion.map(p => p.obligation_id)
    }, { responseType: 'blob' });
    const blobUrl = URL.createObjectURL(new Blob([response.data], { type: 'application/zip' }));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `correspondencia_certificada_${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(blobUrl);
    toast.add({
      severity: 'success',
      summary: 'Correspondencia generada',
      detail: `ZIP generado con ${seleccion.length} documentos individuales`,
      life: 5000
    });
  } catch (error) {
    let detail = 'No se pudo generar la correspondencia';
    if (error.response?.data instanceof Blob) {
      try {
        const errorBody = JSON.parse(await error.response.data.text());
        detail = errorBody.detail || detail;
      } catch (_) {
        // Mantener el mensaje genérico si la respuesta no es JSON.
      }
    }
    toast.add({ severity: 'error', summary: 'Error', detail, life: 6000 });
  } finally {
    generandoCorrespondencia.value = false;
  }
};

const generarImpresionPorRango = async (format = 'docx') => {
  if (printRange.value.from > printRange.value.to) {
    toast.add({
      severity: 'warn',
      summary: 'Rango inválido',
      detail: 'La resolución inicial no puede superar la resolución final',
      life: 5000
    });
    return;
  }

  const printWindow = format === 'pdf' ? window.open('', '_blank') : null;
  if (format === 'pdf' && printWindow) {
    printWindow.document.write(`<!doctype html><html lang="es"><head><title>Generando PDF...</title></head>
      <body style="font-family:Arial,sans-serif;padding:32px;color:#334155">
        <h2>Generando correspondencia</h2><p>Espere mientras se prepara el PDF del rango ${printRange.value.from} al ${printRange.value.to}...</p>
      </body></html>`);
    printWindow.document.close();
  }
  generandoImpresion.value = true;
  try {
    const response = await api.post('/documents/correspondence/print-range', {
      resolution_from: printRange.value.from,
      resolution_to: printRange.value.to,
      output_format: format
    }, { responseType: 'blob' });
    const blobUrl = URL.createObjectURL(new Blob([response.data], {
      type: format === 'pdf'
        ? 'application/pdf'
        : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }));
    if (format === 'pdf' && printWindow) {
      const fileName = `impresion_correspondencia_${printRange.value.from}_${printRange.value.to}.pdf`;
      printWindow.document.open();
      printWindow.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>${fileName}</title>
        <style>html,body{height:100%;margin:0;font-family:Arial,sans-serif;background:#e2e8f0}.bar{height:56px;box-sizing:border-box;padding:10px 18px;background:#1e293b;color:white;display:flex;align-items:center;gap:12px}.bar span{flex:1}.bar a,.bar button{border:0;border-radius:6px;padding:9px 14px;background:#0ea5e9;color:white;text-decoration:none;cursor:pointer;font-weight:600}object{display:block;width:100%;height:calc(100% - 56px);border:0}.fallback{padding:30px;background:white}</style></head>
        <body><div class="bar"><span>Correspondencia: resoluciones ${printRange.value.from} a ${printRange.value.to}</span><a href="${blobUrl}" download="${fileName}">Descargar PDF</a><button onclick="window.print()">Imprimir</button></div>
        <object data="${blobUrl}" type="application/pdf"><div class="fallback"><p>El navegador no puede mostrar el PDF dentro de la página.</p><a href="${blobUrl}" download="${fileName}">Descargar el PDF generado</a></div></object></body></html>`);
      printWindow.document.close();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10 * 60 * 1000);
    } else {
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `impresion_correspondencia_${printRange.value.from}_${printRange.value.to}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(blobUrl);
    }
    toast.add({
      severity: 'success',
      summary: 'Archivo de impresión generado',
      detail: format === 'pdf' ? 'El PDF se abrió en una pestaña nueva' : 'Abra el DOCX descargado y envíelo a la impresora',
      life: 6000
    });
  } catch (error) {
    if (printWindow) printWindow.close();
    let detail = 'No se pudo generar el archivo de impresión';
    if (error.response?.data instanceof Blob) {
      try {
        const errorBody = JSON.parse(await error.response.data.text());
        detail = errorBody.detail || detail;
      } catch (_) {
        // Mantener mensaje genérico.
      }
    }
    toast.add({ severity: 'error', summary: 'Error', detail, life: 6000 });
  } finally {
    generandoImpresion.value = false;
  }
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
  const dateOnly = String(dateString).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const date = dateOnly
    ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
    : new Date(dateString);
  return date.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

const calcularConsecutivos = () => {
  const cantidad = procesosSeleccionados.value.length;
  resolutionNumberFinal.value = resolutionNumber.value + cantidad - 1;
  if (!numeroRadicadoInicial.value) {
    numeroRadicadoInicial.value = config.value.radicado_inicial + 1;
  }
  numeroRadicadoFinal.value = numeroRadicadoInicial.value + cantidad - 1;
  consecutivosCalculados.value = true;
};

const openAsignacionDialog = () => {
  calcularConsecutivos();
  asignacionDialogVisible.value = true;
};

const asignarResoluciones = () => {
  // Abre el dialog de confirmación
  if (procesosSeleccionados.value.length === 0) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'Seleccione al menos una obligación' });
    return;
  }
  if (!resolutionNumber.value) {
    toast.add({ severity: 'warn', summary: 'Dato requerido', detail: 'Ingrese el número de resolución', life: 4000 });
    return;
  }
  if (!resolutionYear.value) {
    toast.add({ severity: 'warn', summary: 'Dato requerido', detail: 'Ingrese el año de resolución', life: 4000 });
    return;
  }
  if (!resolutionDate.value) {
    toast.add({ severity: 'warn', summary: 'Dato requerido', detail: 'Ingrese la fecha de resolución', life: 4000 });
    return;
  }
  if (!numeroRadicadoInicial.value) {
    toast.add({ severity: 'warn', summary: 'Dato requerido', detail: 'Ingrese el número inicial de radicado', life: 4000 });
    return;
  }
  if (!puedeAsignarResoluciones.value) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'La selección contiene obligaciones que ya tienen resolución asignada' });
    return;
  }
  openAsignacionDialog();
};

const confirmarAsignacion = async () => {
  if (!resolutionNumber.value || !resolutionYear.value || !resolutionDate.value) {
    toast.add({
      severity: 'warn',
      summary: 'Datos requeridos',
      detail: 'Ingrese número, año y fecha de resolución',
      life: 4000
    });
    return;
  }
  asignando.value = true;
  try {
    const payload = {
      obligation_ids: procesosSeleccionados.value.map(p => p.obligation_id),
      resolution_initial: resolutionNumber.value,
      radicado_inicial: numeroRadicadoInicial.value,
      prefijo_radicado: config.value.prefijo_radicado,
      resolution_year: resolutionYear.value,
      resolution_date: resolutionDate.value,
      state_code: filtroEstado.value || 'PENDIENTE_ASIGNACION_RESOLUCION',
      observaciones: observaciones.value,
      overwrite: overwriteAssignments.value
    };
    
    const response = await api.post('/processes/assign-resolution/', payload);
    const assignedCount = response.data?.assigned_count || procesosSeleccionados.value.length;
    
    // Actualizar números
    config.value = { ...config.value, ...(response.data?.config || {}) };
    resolutionNumber.value = config.value.numero_actual + 1;
    numeroRadicadoInicial.value = config.value.radicado_inicial + 1;
    
    await loadProcesos();
    asignacionDialogVisible.value = false;
    procesosSeleccionados.value = [];
    consecutivosCalculados.value = false;
    observaciones.value = '';
    overwriteAssignments.value = false;
    
    toast.add({ 
      severity: 'success', 
      summary: 'Éxito', 
      detail: `Resoluciones asignadas a ${assignedCount} obligaciones`,
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
  width: 100%;
  padding: 0;
}

.view-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resolution-data {
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-50);
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
