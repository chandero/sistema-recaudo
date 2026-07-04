<template>
  <Layout>
    <div class="resoluciones-panel">
      <h2 class="section-title">Asignación de Resoluciones y Radicados</h2>
      
      <!-- Resumen -->
      <div class="resumen-cards mb-4">
        <div class="card-resumen">
          <div class="resumen-header bg-primary">
            <i class="pi pi-file"></i>
          </div>
          <div class="resumen-content">
            <span class="resumen-label">Documentos Pendientes</span>
            <span class="resumen-value">{{ documentosPendientes }}</span>
          </div>
        </div>
        
        <div class="card-resumen">
          <div class="resumen-header bg-success">
            <i class="pi pi-check-circle"></i>
          </div>
          <div class="resumen-content">
            <span class="resumen-label">Resoluciones Asignadas</span>
            <span class="resumen-value">{{ resolucionesAsignadas }}</span>
          </div>
        </div>
        
        <div class="card-resumen">
          <div class="resumen-header bg-warning">
            <i class="pi pi-exclamation-triangle"></i>
          </div>
          <div class="resumen-content">
            <span class="resumen-label">Radicados Generados</span>
            <span class="resumen-value">{{ radicadosGenerados }}</span>
          </div>
        </div>
      </div>

      <!-- Configuración de Consecutivos -->
      <Card class="mb-4">
        <template #header>
          <div class="flex justify-content-between align-items-center p-4">
            <h3 class="m-0">Configuración de Consecutivos</h3>
            <Button 
              label="Editar Configuración" 
              icon="pi pi-cog" 
              @click="openConfigDialog"
              outlined
            />
          </div>
        </template>
        <template #content>
          <div class="grid">
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold block mb-2">Prefijo Resolución</label>
                <InputText v-model="config.prefijo_resolucion" class="w-full" disabled />
              </div>
            </div>
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold block mb-2">Número Inicial</label>
                <InputText v-model="config.numero_inicial" class="w-full" disabled />
              </div>
            </div>
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold block mb-2">Número Actual</label>
                <InputText v-model="config.numero_actual" class="w-full" disabled />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Lote de Documentos -->
      <Card>
        <template #header>
          <div class="flex justify-content-between align-items-center p-4">
            <h3 class="m-0">Generación Masiva de Documentos</h3>
            <Button 
              label="Asignar Resoluciones" 
              icon="pi pi-file-export" 
              @click="openAsignacionDialog"
              class="p-button-success"
              :disabled="procesosSeleccionados.length === 0"
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
            />
            <Button 
              label="Aplicar Filtro" 
              icon="pi pi-filter" 
              @click="aplicarFiltros"
            />
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
          >
            <Column selectionMode="multiple" style="width: 50px"></Column>
            <Column field="reference" header="Referencia" sortable></Column>
            <Column field="cliente" header="Cliente/Demandado" sortable>
              <template #body="slotProps">
                {{ slotProps.data.cliente?.nombre || 'N/A' }}
              </template>
            </Column>
            <Column field="obligacion" header="Obligación" sortable></Column>
            <Column field="valor_total" header="Valor Total" sortable>
              <template #body="slotProps">
                {{ formatCurrency(slotProps.data.obligacion?.valor_total) }}
              </template>
            </Column>
            <Column field="current_state" header="Estado Actual">
              <template #body="slotProps">
                <Tag :value="slotProps.data.current_state?.name" severity="info" />
              </template>
            </Column>
            <Column field="created_at" header="Fecha Creación" sortable>
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column header="Acciones" style="width: 150px">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-eye" 
                  class="p-button-rounded p-button-info p-button-sm mr-2"
                  @click="verDetalle(slotProps.data)"
                  v-tooltip="'Ver Detalle'"
                />
              </template>
            </Column>
          </DataTable>

          <!-- Resumen de Selección -->
          <div v-if="procesosSeleccionados.length > 0" class="mt-4 p-3 bg-blue-50 border-round">
            <div class="flex justify-content-between align-items-center">
              <span class="font-semibold">
                <i class="pi pi-info-circle mr-2"></i>
                {{ procesosSeleccionados.length }} proceso(s) seleccionado(s)
              </span>
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
                />
              </div>
            </div>
            <div v-if="consecutivosCalculados" class="mt-3">
              <p class="m-0 text-sm">
                <strong>Rango de Resoluciones:</strong> 
                {{ config.prefijo_resolucion }}-{{ numeroResolucionInicial }} - 
                {{ config.prefijo_resolucion }}-{{ numeroResolucionFinal }}
              </p>
              <p class="m-0 text-sm">
                <strong>Rango de Radicados:</strong> 
                RAD-{{ numeroRadicadoInicial }} - RAD-{{ numeroRadicadoFinal }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <!-- Dialog Configuración -->
      <Dialog 
        v-model:visible="configDialogVisible" 
        modal 
        header="Configuración de Consecutivos"
        :style="{ width: '600px' }"
      >
        <div class="flex flex-column gap-4">
          <div class="field">
            <label class="font-semibold block mb-2">Prefijo de Resolución</label>
            <InputText v-model="config.prefijo_resolucion" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold block mb-2">Número Inicial de Resolución</label>
            <InputNumber v-model="config.numero_inicial" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold block mb-2">Prefijo de Radicado</label>
            <InputText v-model="config.prefijo_radicado" class="w-full" />
          </div>
          
          <div class="field">
            <label class="font-semibold block mb-2">Número Inicial de Radicado</label>
            <InputNumber v-model="config.radicado_inicial" class="w-full" />
          </div>
        </div>
        
        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="configDialogVisible = false" class="p-button-text" />
          <Button label="Guardar" icon="pi pi-check" @click="guardarConfiguracion" />
        </template>
      </Dialog>

      <!-- Dialog Confirmación Asignación -->
      <Dialog 
        v-model:visible="asignacionDialogVisible" 
        modal 
        header="Confirmar Asignación de Resoluciones"
        :style="{ width: '700px' }"
      >
        <div class="flex flex-column gap-4">
          <Message severity="warn">
            <p class="m-0">
              Está a punto de asignar números de resolución y radicado a 
              <strong>{{ procesosSeleccionados.length }} procesos</strong>.
              Esta acción no se puede deshacer.
            </p>
          </Message>
          
          <div class="bg-gray-100 p-3 border-round">
            <h5 class="mt-0 mb-3">Resumen de Asignación:</h5>
            <ul class="m-0 pl-4">
              <li><strong>Procesos:</strong> {{ procesosSeleccionados.length }}</li>
              <li><strong>Resoluciones:</strong> {{ config.prefijo_resolucion }}-{{ numeroResolucionInicial }} al {{ config.prefijo_resolucion }}-{{ numeroResolucionFinal }}</li>
              <li><strong>Radicados:</strong> RAD-{{ numeroRadicadoInicial }} al RAD-{{ numeroRadicadoFinal }}</li>
            </ul>
          </div>
          
          <div class="field">
            <label class="font-semibold block mb-2">Observaciones</label>
            <Textarea v-model="observaciones" rows="3" class="w-full" placeholder="Observaciones opcionales..." />
          </div>
        </div>
        
        <template #footer>
          <Button label="Cancelar" icon="pi pi-times" @click="asignacionDialogVisible = false" class="p-button-text" />
          <Button 
            label="Confirmar Asignación" 
            icon="pi pi-check" 
            @click="confirmarAsignacion"
            class="p-button-success"
            :loading="asignando"
          />
        </template>
      </Dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import api from '../services/api'

// Estados
const loading = ref(false)
const asignando = ref(false)
const procesos = ref([])
const procesosFiltrados = ref([])
const procesosSeleccionados = ref([])
const estadosDisponibles = ref([])
const filtroEstado = ref(null)

// Configuración
const config = ref({
  prefijo_resolucion: 'RES-2024',
  numero_inicial: 1000,
  numero_actual: 1050,
  prefijo_radicado: 'RAD-2024',
  radicado_inicial: 5000
})

// Cálculos
const consecutivosCalculados = ref(false)
const numeroResolucionInicial = ref(0)
const numeroResolucionFinal = ref(0)
const numeroRadicadoInicial = ref(0)
const numeroRadicadoFinal = ref(0)

// Diálogos
const configDialogVisible = ref(false)
const asignacionDialogVisible = ref(false)

// Observaciones
const observaciones = ref('')

// Computed
const documentosPendientes = computed(() => procesos.value.filter(p => 
  p.current_state?.code === 'PENDIENTE_ASIGNACION_RESOLUCION'
).length)

const resolucionesAsignadas = computed(() => procesos.value.filter(p => 
  p.current_state?.code === 'RESOLUCION_RADICADOS_ASIGNADOS'
).length)

const radicadosGenerados = computed(() => procesos.value.length)

// Métodos
const loadProcesos = async () => {
  loading.value = true
  try {
    const response = await api.get('/processes/')
    procesos.value = response.data || []
    aplicarFiltros()
  } catch (error) {
    console.error('Error cargando procesos:', error)
  } finally {
    loading.value = false
  }
}

const loadEstados = async () => {
  try {
    const response = await api.get('/workflows/states/')
    estadosDisponibles.value = response.data || []
  } catch (error) {
    console.error('Error cargando estados:', error)
  }
}

const aplicarFiltros = () => {
  if (!filtroEstado.value) {
    procesosFiltrados.value = procesos.value.filter(p => 
      p.current_state?.code === 'PENDIENTE_ASIGNACION_RESOLUCION'
    )
  } else {
    procesosFiltrados.value = procesos.value.filter(p => 
      p.current_state?.code === filtroEstado.value
    )
  }
}

const formatCurrency = (value) => {
  if (!value && value !== 0) return '$ 0'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0
  }).format(value)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CO')
}

const openConfigDialog = () => {
  configDialogVisible.value = true
}

const guardarConfiguracion = async () => {
  try {
    // Guardar configuración en backend
    console.log('Guardando configuración:', config.value)
    configDialogVisible.value = false
  } catch (error) {
    console.error('Error guardando configuración:', error)
  }
}

const calcularConsecutivos = () => {
  const cantidad = procesosSeleccionados.value.length
  numeroResolucionInicial.value = config.value.numero_actual + 1
  numeroResolucionFinal.value = config.value.numero_actual + cantidad
  numeroRadicadoInicial.value = config.value.radicado_inicial + 1
  numeroRadicadoFinal.value = config.value.radicado_inicial + cantidad
  consecutivosCalculados.value = true
}

const openAsignacionDialog = () => {
  calcularConsecutivos()
  asignacionDialogVisible.value = true
}

const asignarResoluciones = () => {
  // Se abre el dialog de confirmación
}

const confirmarAsignacion = async () => {
  asignando.value = true
  try {
    const payload = {
      process_ids: procesosSeleccionados.value.map(p => p.id),
      resolucion_inicial: numeroResolucionInicial.value,
      radicado_inicial: numeroRadicadoInicial.value,
      observaciones: observaciones.value
    }
    
    await api.post('/processes/assign-resolution/', payload)
    
    // Actualizar configuración local
    config.value.numero_actual = numeroResolucionFinal.value
    config.value.radicado_inicial = numeroRadicadoFinal.value
    
    await loadProcesos()
    asignacionDialogVisible.value = false
    procesosSeleccionados.value = []
    consecutivosCalculados.value = false
    observaciones.value = ''
  } catch (error) {
    console.error('Error asignando resoluciones:', error)
  } finally {
    asignando.value = false
  }
}

const verDetalle = (proceso) => {
  console.log('Ver detalle:', proceso)
}

onMounted(() => {
  loadProcesos()
  loadEstados()
})
</script>

<style scoped>
.resoluciones-panel {
  padding: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--text-color);
}

.resumen-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.card-resumen {
  background: var(--surface-card);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
}

.resumen-header {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.resumen-header i {
  font-size: 2rem;
}

.bg-primary {
  background: var(--primary-color);
}

.bg-success {
  background: var(--green-500);
}

.bg-warning {
  background: var(--orange-500);
}

.resumen-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.resumen-label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.resumen-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-color);
}
</style>
