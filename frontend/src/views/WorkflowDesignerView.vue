<template>
  <div class="workflow-designer">
    <PageHeader title="Diseñador de Flujo" :subtitle="`Workflow de ${designer?.tenant_name || '...'} — Estados y transiciones del proceso de cobro`">
      <template #actions>
        <Button label="Cargar predeterminado" icon="pi pi-database" severity="help" outlined @click="confirmSeed" :loading="seeding" />
        <Button label="Refrescar" icon="pi pi-refresh" severity="secondary" outlined @click="loadDesigner" :loading="loading" />
      </template>
    </PageHeader>

    <!-- Stats bar -->
    <div class="stats-bar" v-if="designer">
      <div class="stat-card tenant-card">
        <i class="pi pi-building stat-icon tenant"></i>
        <div>
          <span class="stat-value tenant-name">{{ designer.tenant_name }}</span>
          <span class="stat-label">Tenant</span>
        </div>
      </div>
      <div class="stat-card">
        <i class="pi pi-th-large stat-icon"></i>
        <div>
          <span class="stat-value">{{ designer.states.length }}</span>
          <span class="stat-label">Estados</span>
        </div>
      </div>
      <div class="stat-card">
        <i class="pi pi-arrows-h stat-icon transitions"></i>
        <div>
          <span class="stat-value">{{ designer.transitions.length }}</span>
          <span class="stat-label">Transiciones</span>
        </div>
      </div>
      <div class="stat-card">
        <i class="pi pi-sitemap stat-icon processes"></i>
        <div>
          <span class="stat-value">{{ designer.total_active_processes }}</span>
          <span class="stat-label">Procesos activos</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && designer && designer.states.length === 0" class="empty-state">
      <i class="pi pi-exclamation-circle"></i>
      <h3>No hay estados configurados</h3>
      <p>Cargue los 21 estados predeterminados con sus transiciones para comenzar.</p>
      <Button label="Cargar workflow predeterminado" icon="pi pi-database" @click="confirmSeed" :loading="seeding" />
    </div>

    <!-- Tabs -->
    <TabView v-if="designer && designer.states.length > 0" v-model:activeIndex="activeTab">
      <!-- States Tab -->
      <TabPanel header="Estados">
        <div class="tab-toolbar">
          <Button label="Nuevo estado" icon="pi pi-plus" @click="openStateDialog(null)" size="small" />
          <label class="toggle-label">
            <Checkbox v-model="showInactiveStates" :binary="true" @change="loadDesigner" />
            <span>Mostrar inactivos</span>
          </label>
        </div>

        <DataTable :value="filteredStates" stripedRows responsiveLayout="scroll" class="p-datatable-sm">
          <Column field="order" header="#" style="width: 50px" />
          <Column field="code" header="Código" style="width: 200px">
            <template #body="{ data }">
              <Tag :value="data.code" :severity="getStateSeverity(data.code)" />
            </template>
          </Column>
          <Column field="name" header="Nombre" />
          <Column field="max_days" header="Max días" style="width: 100px">
            <template #body="{ data }">
              <span v-if="data.max_days">{{ data.max_days }} días</span>
              <span v-else class="text-muted">—</span>
            </template>
          </Column>
          <Column field="is_final" header="Final" style="width: 80px">
            <template #body="{ data }">
              <i :class="data.is_final ? 'pi pi-check-circle text-success' : 'pi pi-minus-circle text-muted'"></i>
            </template>
          </Column>
          <Column header="Procesos" style="width: 90px">
            <template #body="{ data }">
              <span class="process-count">{{ designer.state_process_counts[data.id] || 0 }}</span>
            </template>
          </Column>
          <Column field="is_active" header="Activo" style="width: 80px">
            <template #body="{ data }">
              <Tag :value="data.is_active ? 'Sí' : 'No'" :severity="data.is_active ? 'success' : 'secondary'" size="small" />
            </template>
          </Column>
          <Column header="Acciones" style="width: 120px">
            <template #body="{ data }">
              <Button icon="pi pi-pencil" text size="small" @click="openStateDialog(data)" v-tooltip="'Editar'" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click="confirmDeleteState(data)" v-tooltip="'Desactivar'" :disabled="!data.is_active" />
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Transitions Tab -->
      <TabPanel header="Transiciones">
        <div class="tab-toolbar">
          <Button label="Nueva transición" icon="pi pi-plus" @click="openTransitionDialog(null)" size="small" />
          <label class="toggle-label">
            <Checkbox v-model="showInactiveTransitions" :binary="true" @change="loadDesigner" />
            <span>Mostrar inactivas</span>
          </label>
        </div>

        <DataTable :value="filteredTransitions" stripedRows responsiveLayout="scroll" class="p-datatable-sm">
          <Column header="Origen" style="width: 200px">
            <template #body="{ data }">
              <span class="transition-state">{{ getStateName(data.source_state_id) }}</span>
            </template>
          </Column>
          <Column header="" style="width: 40px">
            <template #body>
              <i class="pi pi-arrow-right text-muted"></i>
            </template>
          </Column>
          <Column header="Destino" style="width: 200px">
            <template #body="{ data }">
              <span class="transition-state">{{ getStateName(data.target_state_id) }}</span>
            </template>
          </Column>
          <Column field="name" header="Nombre" />
          <Column header="Automática" style="width: 100px">
            <template #body="{ data }">
              <Tag v-if="data.is_automatic" value="Auto" severity="warning" size="small" />
              <span v-else class="text-muted">Manual</span>
            </template>
          </Column>
          <Column header="Condición" style="width: 120px">
            <template #body="{ data }">
              <span v-if="data.condition_days">{{ data.condition_days }} días</span>
              <span v-else class="text-muted">—</span>
            </template>
          </Column>
          <Column field="is_active" header="Activa" style="width: 80px">
            <template #body="{ data }">
              <Tag :value="data.is_active ? 'Sí' : 'No'" :severity="data.is_active ? 'success' : 'secondary'" size="small" />
            </template>
          </Column>
          <Column header="Acciones" style="width: 120px">
            <template #body="{ data }">
              <Button icon="pi pi-pencil" text size="small" @click="openTransitionDialog(data)" v-tooltip="'Editar'" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click="confirmDeleteTransition(data)" v-tooltip="'Desactivar'" :disabled="!data.is_active" />
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Visual Flow Tab -->
      <TabPanel header="Diagrama Visual">
        <div class="flow-diagram" v-if="designer">
          <div v-if="!flowLayout.nodes.length" class="flow-empty">
            <i class="pi pi-exclamation-circle" style="font-size:2rem;color:#ccc"></i>
            <p>No hay transiciones configuradas. Cargue el workflow predeterminado.</p>
          </div>
          <svg v-else ref="svgRef" :viewBox="flowLayout.viewBox" class="flow-svg" preserveAspectRatio="xMidYMid meet" @mouseup="onDragEnd" @mousemove="onDragMove">
            <defs>
              <marker id="ah-gray" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="6" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="#94a3b8"/></marker>
              <marker id="ah-green" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="6" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="#22c55e"/></marker>
              <marker id="ah-red" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="6" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="#ef4444"/></marker>
              <marker id="ah-amber" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="6" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="#f59e0b"/></marker>
            </defs>
            <!-- Phase columns -->
            <g v-for="p in displayPhases" :key="p.label" class="phase-g" @mousedown.stop.prevent="onPhaseDragStart($event, p)">
              <rect :x="p.x - 12" :y="p.y - 38" :width="p.w + 24" :height="p.h + 52" rx="12" class="phase-bg"/>
              <text :x="p.x + p.w / 2" :y="p.y - 18" text-anchor="middle" class="phase-label-text">{{ p.label }}</text>
            </g>
            <!-- Arrows -->
            <g v-for="(a, i) in displayArrows" :key="'a' + i">
              <path :d="a.path" :class="['flow-arrow', `arrow-${a.type}`]" :marker-end="`url(#ah-${a.marker})`" :stroke-width="a.type === 'success' ? 2.5 : 2"/>
              <rect v-if="a.label" :x="a.labelX - a.labelW / 2 - 3" :y="a.labelY - 8" :width="a.labelW + 6" height="14" rx="3" class="arrow-label-bg"/>
              <text v-if="a.label" :x="a.labelX" :y="a.labelY + 3" text-anchor="middle" class="arrow-label-text">{{ a.label }}</text>
            </g>
            <!-- State nodes -->
            <g v-for="n in displayNodes" :key="'n' + n.state.id" :transform="`translate(${n.x},${n.y})`" class="flow-node-g" :class="{ 'is-dragging': dragState.nodeId === n.state.id }" @mousedown.stop.prevent="onDragStart($event, n)">
              <rect width="190" height="72" rx="10" :class="['fn-rect', { 'fn-final': n.state.is_final, 'fn-active': !!designer.state_process_counts[n.state.id] }]" :stroke="n.border" stroke-width="2"/>
              <rect width="5" height="52" x="2" y="10" rx="2.5" :fill="n.border"/>
              <text x="95" y="24" text-anchor="middle" class="fn-name">{{ n.state.name }}</text>
              <text x="95" y="40" text-anchor="middle" class="fn-code">{{ n.state.code.replace(/_/g, ' ') }}</text>
              <text x="95" y="58" text-anchor="middle" class="fn-meta">
                <tspan v-if="n.state.max_days">{{ n.state.max_days }}d </tspan>
                <tspan v-if="designer.state_process_counts[n.state.id]" class="fn-count">· {{ designer.state_process_counts[n.state.id] }} proc.</tspan>
              </text>
            </g>
            <!-- Legend -->
            <g :transform="`translate(${flowLayout.bounds.maxX - 180}, ${flowLayout.bounds.maxY + 25})`">
              <line x1="0" y1="0" x2="24" y2="0" stroke="#94a3b8" stroke-width="2" marker-end="url(#ah-gray)"/><text x="30" y="4" class="legend-text">Normal</text>
              <line x1="90" y1="0" x2="114" y2="0" stroke="#22c55e" stroke-width="2.5" marker-end="url(#ah-green)"/><text x="120" y="4" class="legend-text">Éxito</text>
              <line x1="0" y1="22" x2="24" y2="22" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#ah-red)"/><text x="30" y="26" class="legend-text">Reintento / Fallo</text>
              <line x1="90" y1="22" x2="114" y2="22" stroke="#f59e0b" stroke-width="2" marker-end="url(#ah-amber)"/><text x="120" y="26" class="legend-text">Automática</text>
              <text x="0" y="46" class="legend-text" style="fill:#94a3b8;font-style:italic">Arrastra los cuadros para reorganizar</text>
            </g>
          </svg>
        </div>
      </TabPanel>
    </TabView>

    <!-- State Dialog -->
    <Dialog v-model:visible="stateDialogVisible" :header="editingState ? 'Editar Estado' : 'Nuevo Estado'" :style="{ width: '500px' }" :modal="true">
      <div class="form-grid">
        <div class="field">
          <label>Código</label>
          <Dropdown v-model="stateForm.code" :options="stateCodeOptions" optionLabel="label" optionValue="value" placeholder="Seleccionar código" :disabled="!!editingState" class="w-full" />
        </div>
        <div class="field">
          <label>Nombre *</label>
          <InputText v-model="stateForm.name" class="w-full" />
        </div>
        <div class="field">
          <label>Descripción</label>
          <Textarea v-model="stateForm.description" rows="2" class="w-full" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Orden</label>
            <InputNumber v-model="stateForm.order" :min="0" class="w-full" />
          </div>
          <div class="field">
            <label>Max días</label>
            <InputNumber v-model="stateForm.max_days" :min="0" class="w-full" />
          </div>
        </div>
        <div class="field-row">
          <label class="checkbox-label">
            <Checkbox v-model="stateForm.is_final" :binary="true" />
            <span>Estado final</span>
          </label>
          <label class="checkbox-label">
            <Checkbox v-model="stateForm.is_active" :binary="true" />
            <span>Activo</span>
          </label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="stateDialogVisible = false" />
        <Button label="Guardar" icon="pi pi-check" @click="saveState" :loading="saving" :disabled="!stateForm.name || !stateForm.code" />
      </template>
    </Dialog>

    <!-- Transition Dialog -->
    <Dialog v-model:visible="transitionDialogVisible" :header="editingTransition ? 'Editar Transición' : 'Nueva Transición'" :style="{ width: '520px' }" :modal="true">
      <div class="form-grid">
        <div class="field">
          <label>Estado Origen *</label>
          <Dropdown v-model="transitionForm.source_state_id" :options="activeStates" optionLabel="name" optionValue="id" placeholder="Seleccionar estado origen" class="w-full" />
        </div>
        <div class="field">
          <label>Estado Destino *</label>
          <Dropdown v-model="transitionForm.target_state_id" :options="activeStates" optionLabel="name" optionValue="id" placeholder="Seleccionar estado destino" class="w-full" />
        </div>
        <div class="field">
          <label>Nombre</label>
          <InputText v-model="transitionForm.name" class="w-full" placeholder="Ej: Validar obligación" />
        </div>
        <div class="field-row">
          <label class="checkbox-label">
            <Checkbox v-model="transitionForm.is_automatic" :binary="true" />
            <span>Transición automática</span>
          </label>
        </div>
        <div v-if="transitionForm.is_automatic" class="field-row">
          <div class="field">
            <label>Condición (días)</label>
            <InputNumber v-model="transitionForm.condition_days" :min="1" class="w-full" />
          </div>
          <div class="field">
            <label>Tipo condición</label>
            <Dropdown v-model="transitionForm.condition_type" :options="conditionTypes" optionLabel="label" optionValue="value" placeholder="Tipo" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="transitionDialogVisible = false" />
        <Button label="Guardar" icon="pi pi-check" @click="saveTransition" :loading="saving" :disabled="!transitionForm.source_state_id || !transitionForm.target_state_id" />
      </template>
    </Dialog>

    <!-- Confirm dialogs -->
    <ConfirmationDialog
      v-model:visible="confirmDeleteVisible"
      :header="confirmTitle"
      :message="confirmMessage"
      @accept="executeDelete"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import Checkbox from 'primevue/checkbox';
import Tag from 'primevue/tag';
import PageHeader from '@/components/PageHeader.vue';
import ConfirmationDialog from '@/components/ConfirmationDialog.vue';
import { workflowService } from '@/services/api';
import { useAuthStore } from '@/stores/auth';

const toast = useToast();
const authStore = useAuthStore();

const designer = ref(null);
const loading = ref(false);
const saving = ref(false);
const seeding = ref(false);
const activeTab = ref(0);
const showInactiveStates = ref(false);
const showInactiveTransitions = ref(false);

// State dialog
const stateDialogVisible = ref(false);
const editingState = ref(null);
const stateForm = ref({ code: '', name: '', description: '', order: 0, max_days: null, is_final: false, is_active: true });

// Transition dialog
const transitionDialogVisible = ref(false);
const editingTransition = ref(null);
const transitionForm = ref({ source_state_id: null, target_state_id: null, name: '', is_automatic: false, condition_days: null, condition_type: null });

// Confirm delete
const confirmDeleteVisible = ref(false);
const confirmTitle = ref('');
const confirmMessage = ref('');
const deleteAction = ref(null);

const conditionTypes = [
  { label: 'Max días en estado', value: 'max_days' },
  { label: 'Días desde creación', value: 'days_since_creation' },
];

const stateCodeOptions = computed(() => {
  const codes = [
    'CARTERA_CARGADA', 'OBLIGACION_VALIDADA', 'PENDIENTE_ASIGNACION_RESOLUCION',
    'RESOLUCION_RADICADOS_ASIGNADOS', 'DOCUMENTO_NOTIFICACION_GENERADO', 'NOTIFICACION_ENVIADA',
    'ESPERANDO_RESULTADO_NOTIFICACION', 'NOTIFICACION_ENTREGADA', 'NOTIFICACION_DEVUELTA',
    'NOTIFICACION_WEB_PUBLICADA', 'REINTENTO_NOTIFICACION', 'ESPERANDO_PAGO_VOLUNTARIO',
    'COBRO_PERSUASIVO', 'ACUERDO_DE_PAGO', 'SEGUIMIENTO_ACUERDO', 'ACUERDO_INCUMPLIDO',
    'COBRO_PREJURIDICO', 'COBRO_COACTIVO', 'PAGADO', 'ARCHIVADO', 'INCOBRABLE',
  ];
  return codes.map(c => ({ label: c.replace(/_/g, ' '), value: c }));
});

const activeStates = computed(() => (designer.value?.states || []).filter(s => s.is_active));

const filteredStates = computed(() => {
  if (!designer.value) return [];
  if (showInactiveStates.value) return designer.value.states;
  return designer.value.states.filter(s => s.is_active);
});

const filteredTransitions = computed(() => {
  if (!designer.value) return [];
  if (showInactiveTransitions.value) return designer.value.transitions;
  return designer.value.transitions.filter(t => t.is_active);
});

const flowPhases = computed(() => {
  if (!designer.value) return [];
  const states = designer.value.states.filter(s => s.is_active);
  return [
    { label: 'Carga', states: states.filter(s => s.order <= 1) },
    { label: 'Resolución', states: states.filter(s => s.order >= 2 && s.order <= 3) },
    { label: 'Notificación', states: states.filter(s => s.order >= 4 && s.order <= 10) },
    { label: 'Cobro', states: states.filter(s => s.order >= 11 && s.order <= 12) },
    { label: 'Acuerdo', states: states.filter(s => s.order >= 13 && s.order <= 15) },
    { label: 'Jurídico', states: states.filter(s => s.order >= 16 && s.order <= 17) },
    { label: 'Cierre', states: states.filter(s => s.is_final) },
  ].filter(p => p.states.length > 0);
});

const isManager = computed(() => {
  const role = authStore.currentUser?.role;
  return ['PLATFORM_ADMIN', 'TENANT_ADMIN', 'MANAGER'].includes(role);
});

// Load
const loadDesigner = async () => {
  loading.value = true;
  try {
    const res = await workflowService.getDesigner();
    designer.value = res.data;
  } catch (error) {
    console.error('Error loading designer:', error);
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cargar el diseñador', life: 3000 });
  } finally {
    loading.value = false;
  }
};

// Seed
const confirmSeed = () => {
  if (designer.value && designer.value.states.length > 0) {
    confirmTitle.value = 'Reiniciar workflow';
    confirmMessage.value = 'Se desactivarán los estados actuales y se crearán los 21 predeterminados. ¿Continuar?';
    deleteAction.value = async () => {
      seeding.value = true;
      try {
        await workflowService.seed(true);
        toast.add({ severity: 'success', summary: 'Workflow cargado', life: 3000 });
        await loadDesigner();
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error al cargar workflow', life: 4000 });
      } finally {
        seeding.value = false;
      }
    };
    confirmDeleteVisible.value = true;
  } else {
    seedWorkflow();
  }
};

const seedWorkflow = async () => {
  seeding.value = true;
  try {
    await workflowService.seed(false);
    toast.add({ severity: 'success', summary: 'Workflow creado', life: 3000 });
    await loadDesigner();
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error', life: 4000 });
  } finally {
    seeding.value = false;
  }
};

// State CRUD
const openStateDialog = (state) => {
  if (state) {
    editingState.value = state;
    stateForm.value = { code: state.code, name: state.name, description: state.description || '', order: state.order, max_days: state.max_days, is_final: state.is_final, is_active: state.is_active };
  } else {
    editingState.value = null;
    const maxOrder = Math.max(0, ...(designer.value?.states.map(s => s.order) || [0]));
    stateForm.value = { code: '', name: '', description: '', order: maxOrder + 1, max_days: null, is_final: false, is_active: true };
  }
  stateDialogVisible.value = true;
};

const saveState = async () => {
  saving.value = true;
  try {
    if (editingState.value) {
      await workflowService.updateState(editingState.value.id, stateForm.value);
      toast.add({ severity: 'success', summary: 'Estado actualizado', life: 3000 });
    } else {
      await workflowService.createState(stateForm.value);
      toast.add({ severity: 'success', summary: 'Estado creado', life: 3000 });
    }
    stateDialogVisible.value = false;
    await loadDesigner();
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error al guardar', life: 4000 });
  } finally {
    saving.value = false;
  }
};

const confirmDeleteState = (state) => {
  confirmTitle.value = 'Desactivar estado';
  confirmMessage.value = `¿Desactivar el estado "${state.name}"? No se mostrará en el Kanban ni se podrá usar en nuevas transiciones.`;
  deleteAction.value = async () => {
    try {
      await workflowService.deleteState(state.id);
      toast.add({ severity: 'success', summary: 'Estado desactivado', life: 3000 });
      await loadDesigner();
    } catch (error) {
      toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error', life: 4000 });
    }
  };
  confirmDeleteVisible.value = true;
};

// Transition CRUD
const openTransitionDialog = (transition) => {
  if (transition) {
    editingTransition.value = transition;
    transitionForm.value = {
      source_state_id: transition.source_state_id,
      target_state_id: transition.target_state_id,
      name: transition.name || '',
      is_automatic: transition.is_automatic,
      condition_days: transition.condition_days,
      condition_type: transition.condition_type,
    };
  } else {
    editingTransition.value = null;
    transitionForm.value = { source_state_id: null, target_state_id: null, name: '', is_automatic: false, condition_days: null, condition_type: null };
  }
  transitionDialogVisible.value = true;
};

const saveTransition = async () => {
  saving.value = true;
  try {
    if (editingTransition.value) {
      await workflowService.updateTransition(editingTransition.value.id, transitionForm.value);
      toast.add({ severity: 'success', summary: 'Transición actualizada', life: 3000 });
    } else {
      await workflowService.createTransition(transitionForm.value);
      toast.add({ severity: 'success', summary: 'Transición creada', life: 3000 });
    }
    transitionDialogVisible.value = false;
    await loadDesigner();
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error al guardar', life: 4000 });
  } finally {
    saving.value = false;
  }
};

const confirmDeleteTransition = (transition) => {
  const sourceName = getStateName(transition.source_state_id);
  const targetName = getStateName(transition.target_state_id);
  confirmTitle.value = 'Desactivar transición';
  confirmMessage.value = `¿Desactivar la transición "${sourceName}" → "${targetName}"?`;
  deleteAction.value = async () => {
    try {
      await workflowService.deleteTransition(transition.id);
      toast.add({ severity: 'success', summary: 'Transición desactivada', life: 3000 });
      await loadDesigner();
    } catch (error) {
      toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Error', life: 4000 });
    }
  };
  confirmDeleteVisible.value = true;
};

const executeDelete = async () => {
  confirmDeleteVisible.value = false;
  if (deleteAction.value) await deleteAction.value();
  deleteAction.value = null;
};

// Helpers
const getStateName = (stateId) => {
  const state = designer.value?.states.find(s => s.id === stateId);
  return state ? state.name : `#${stateId}`;
};

const getOutgoingTransitions = (stateId) => {
  return (designer.value?.transitions || []).filter(t => t.source_state_id === stateId && t.is_active);
};

const getNodeClass = (state) => {
  const classes = [];
  if (state.is_final) classes.push('node-final');
  if (!state.is_active) classes.push('node-inactive');
  if (designer.value?.state_process_counts[state.id]) classes.push('node-active');
  return classes;
};

const getStateSeverity = (code) => {
  if (code.includes('PAGADO')) return 'success';
  if (code.includes('INCOBRABLE') || code.includes('INCUMPLIDO')) return 'danger';
  if (code.includes('ARCHIVADO')) return 'secondary';
  if (code.includes('COBRO') || code.includes('NOTIFICACION')) return 'warning';
  return 'info';
};

const selectStateForDetail = (state) => {
  openStateDialog(state);
};

// ── SVG Flow Layout ──
const flowLayout = computed(() => {
  if (!designer.value || !designer.value.transitions?.length) {
    return { nodes: [], arrows: [], phases: [], viewBox: '0 0 100 100', bounds: { minX: 0, maxX: 100, minY: 0, maxY: 100 } };
  }
  const NW = 190, NH = 72, NG = 18, CG = 55;
  const states = designer.value.states.filter(s => s.is_active);
  const phases = [
    { label: 'Carga', items: states.filter(s => s.order <= 1) },
    { label: 'Resolución', items: states.filter(s => s.order >= 2 && s.order <= 3) },
    { label: 'Notificación', items: states.filter(s => s.order >= 4 && s.order <= 10) },
    { label: 'Cobro', items: states.filter(s => s.order >= 11 && s.order <= 12) },
    { label: 'Acuerdo', items: states.filter(s => s.order >= 13 && s.order <= 15) },
    { label: 'Jurídico', items: states.filter(s => s.order >= 16 && s.order <= 17) },
    { label: 'Cierre', items: states.filter(s => s.is_final) },
  ].filter(p => p.items.length > 0);
  const phaseOf = {};
  phases.forEach((p, i) => p.items.forEach(s => { phaseOf[s.id] = i; }));
  let cx = 0, maxY = 0;
  const nodes = [], pLayout = [];
  phases.forEach((phase, pIdx) => {
    const ch = phase.items.length * NH + (phase.items.length - 1) * NG;
    const my = maxY + 40;
    phase.items.forEach((state, sIdx) => {
      nodes.push({ state, x: cx, y: my + sIdx * (NH + NG), pIdx });
    });
    pLayout.push({ label: phase.label, x: cx, y: my, w: NW, h: ch, idx: pIdx });
    cx += NW + CG;
    maxY = Math.max(maxY, my + ch);
  });
  const bMinX = 0, bMaxX = cx - CG, bMinY = Math.min(...nodes.map(n => n.y)), bMaxY = maxY;
  const bounds = { minX: bMinX, maxX: bMaxX, minY: bMinY, maxY: bMaxY };
  const nMap = {};
  nodes.forEach(n => { nMap[n.state.id] = n; });
  const vb = `${bMinX - 25} ${bMinY - 80} ${bMaxX - bMinX + 50} ${bMaxY - bMinY + 130}`;
  return { nodes, phases: pLayout, viewBox: vb, bounds };
});

// ── Drag state ──
const svgRef = ref(null);
const dragState = ref({ nodeId: null, phaseIdx: null, startMouseX: 0, startMouseY: 0, startNodeX: 0, startNodeY: 0 });
const nodeOffsets = ref({});
const phaseOffsets = ref({});

const displayPhases = computed(() => {
  if (!flowLayout.value?.phases) return [];
  return flowLayout.value.phases.map((p, i) => ({
    ...p,
    x: p.x + (phaseOffsets.value[i]?.x || 0),
    y: p.y + (phaseOffsets.value[i]?.y || 0),
  }));
});

const displayNodes = computed(() => {
  if (!flowLayout.value?.nodes) return [];
  return flowLayout.value.nodes.map(n => ({
    ...n,
    x: n.x + (nodeOffsets.value[n.state.id]?.x || 0) + (phaseOffsets.value[n.pIdx]?.x || 0),
    y: n.y + (nodeOffsets.value[n.state.id]?.y || 0) + (phaseOffsets.value[n.pIdx]?.y || 0),
  }));
});

const displayArrows = computed(() => {
  const nodes = displayNodes.value;
  if (!nodes.length || !designer.value?.transitions?.length) return [];
  const NW = 190, NH = 72;
  const nMap = {};
  nodes.forEach(n => { nMap[n.state.id] = n; });
  const bMinY = flowLayout.value.bounds.minY;
  return designer.value.transitions.filter(t => t.is_active && nMap[t.source_state_id] && nMap[t.target_state_id]).map(t => {
    const s = nMap[t.source_state_id], d = nMap[t.target_state_id];
    const sp = s.pIdx, dp = d.pIdx;
    let path, lx, ly, lw = 0;
    if (sp === dp) {
      const sx = s.x + NW / 2, sy = s.y + NH, dx = d.x + NW / 2, dy = d.y + NH;
      const bulge = Math.max(35, Math.abs(dy - sy) * 0.35);
      path = `M${sx},${sy} C${sx + bulge},${sy + 25} ${dx + bulge},${dy - 25} ${dx},${dy}`;
      lx = Math.max(sx, dx) + bulge / 2 + 5; ly = (sy + dy) / 2;
    } else if (dp > sp) {
      const sx = s.x + NW, sy = s.y + NH / 2, dx = d.x, dy = d.y + NH / 2;
      const gap = dx - sx;
      path = `M${sx},${sy} C${sx + gap * 0.4},${sy} ${dx - gap * 0.4},${dy} ${dx},${dy}`;
      lx = (sx + dx) / 2; ly = (sy + dy) / 2;
    } else {
      const sx = s.x + NW / 2, sy = s.y, dx = d.x + NW / 2, dy = d.y;
      const rt = bMinY - 50 - Math.abs(sp - dp) * 28;
      path = `M${sx},${sy} L${sx},${rt} L${dx},${rt} L${dx},${dy}`;
      lx = (sx + dx) / 2; ly = rt - 6;
    }
    if (t.name) lw = Math.min(t.name.length * 5.5 + 8, 130);
    const isAuto = t.is_automatic;
    const nm = (t.name || '').toLowerCase();
    const isSuccess = nm.includes('pago') || nm.includes('entregada') || nm.includes('cumplió');
    const isFail = nm.includes('reintento') || nm.includes('devuelta') || nm.includes('incumplido');
    return {
      path, labelX: lx, labelY: ly, label: t.name || '', labelW: lw,
      type: isAuto ? 'auto' : (isSuccess ? 'success' : (isFail ? 'fail' : 'normal')),
      marker: isAuto ? 'amber' : (isSuccess ? 'green' : (isFail ? 'red' : 'gray')),
    };
  });
});

const onDragStart = (e, node) => {
  const svg = svgRef.value;
  if (!svg) return;
  const rect = svg.getBoundingClientRect();
  const vb = flowLayout.value.viewBox.split(' ').map(Number);
  const scaleX = vb[2] / rect.width;
  const scaleY = vb[3] / rect.height;
  const scale = Math.max(scaleX, scaleY);
  dragState.value = {
    nodeId: node.state.id,
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startNodeX: node.x,
    startNodeY: node.y,
    _scale: scale,
    _rect: rect,
    _vb: vb,
  };
  document.addEventListener('mousemove', onDragMove);
  document.addEventListener('mouseup', onDragEnd);
};

const onDragMove = (e) => {
  const ds = dragState.value;
  const dx = (e.clientX - ds.startMouseX) * ds._scale;
  const dy = (e.clientY - ds.startMouseY) * ds._scale;
  if (ds.nodeId) {
    nodeOffsets.value[ds.nodeId] = { x: dx, y: dy };
  } else if (ds.phaseIdx !== null) {
    phaseOffsets.value[ds.phaseIdx] = { x: dx, y: dy };
  }
};

const onDragEnd = () => {
  dragState.value.nodeId = null;
  dragState.value.phaseIdx = null;
  document.removeEventListener('mousemove', onDragMove);
  document.removeEventListener('mouseup', onDragEnd);
};

const onPhaseDragStart = (e, phase) => {
  const svg = svgRef.value;
  if (!svg) return;
  const rect = svg.getBoundingClientRect();
  const vb = flowLayout.value.viewBox.split(' ').map(Number);
  const scaleX = vb[2] / rect.width;
  const scaleY = vb[3] / rect.height;
  const scale = Math.max(scaleX, scaleY);
  dragState.value = {
    nodeId: null,
    phaseIdx: phase.idx,
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startNodeX: phase.x,
    startNodeY: phase.y,
    _scale: scale,
    _rect: rect,
    _vb: vb,
  };
  document.addEventListener('mousemove', onDragMove);
  document.addEventListener('mouseup', onDragEnd);
};

const resetLayout = () => {
  nodeOffsets.value = {};
  phaseOffsets.value = {};
};

onMounted(() => {
  loadDesigner();
});
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-bar {
  display: flex;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border-radius: 8px;
  padding: 14px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  min-width: 160px;
}

.stat-card.tenant-card {
  border-left: 3px solid var(--primary-color, #3b82f6);
}

.tenant-name {
  font-size: 1rem !important;
  color: var(--primary-color, #3b82f6);
}

.stat-icon.tenant {
  color: var(--primary-color, #3b82f6);
}

.stat-icon { font-size: 1.5rem; color: #6366f1; }
.stat-icon.transitions { color: #f59e0b; }
.stat-icon.processes { color: #22c55e; }
.stat-value { display: block; font-size: 1.4rem; font-weight: 700; color: #333; }
.stat-label { display: block; font-size: 0.78rem; color: #888; }

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
}
.empty-state i { font-size: 3rem; color: #ccc; }
.empty-state h3 { margin: 12px 0 8px; color: #555; }
.empty-state p { color: #888; margin-bottom: 20px; }

.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #666;
  cursor: pointer;
}

.text-muted { color: #aaa; }
.text-success { color: #22c55e; }
.process-count {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

.transition-state { font-weight: 500; }

/* Form */
.form-grid { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.field label { font-size: 0.85rem; font-weight: 500; color: #555; }
.field-row { display: flex; gap: 12px; align-items: center; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: #555; cursor: pointer; }

/* Flow diagram – SVG */
.flow-diagram { background: #fff; border-radius: 10px; padding: 20px; overflow: auto; }
.flow-empty { text-align: center; padding: 50px 20px; color: #aaa; }
.flow-svg { width: 100%; min-width: 700px; height: auto; min-height: 480px; overflow: visible; }
.phase-bg { fill: #f8fafc; stroke: #e2e8f0; stroke-width: 1; }
.phase-label-text { font-size: 10px; font-weight: 700; fill: #6366f1; text-transform: uppercase; letter-spacing: .5px; font-family: inherit; }
.phase-g { cursor: grab; }
.phase-g:active { cursor: grabbing; }
.flow-node-g { cursor: grab; }
.flow-node-g:active { cursor: grabbing; }
.flow-node-g.is-dragging { cursor: grabbing; opacity: 0.85; }
.flow-svg { user-select: none; -webkit-user-select: none; }
.fn-rect { fill: #ffffff; }
.fn-final { fill: #f0fdf4; }
.fn-active { stroke-width: 2.5; }
.fn-name { font-size: 10.5px; font-weight: 600; fill: #1e293b; font-family: inherit; }
.fn-code { font-size: 7.5px; fill: #94a3b8; font-family: monospace; }
.fn-meta { font-size: 8px; fill: #94a3b8; font-family: inherit; }
.fn-count { fill: #6366f1; font-weight: 600; }
.flow-arrow { fill: none; }
.arrow-normal { stroke: #94a3b8; }
.arrow-success { stroke: #22c55e; }
.arrow-fail { stroke: #ef4444; stroke-dasharray: 6,3; }
.arrow-auto { stroke: #f59e0b; stroke-dasharray: 4,2; }
.arrow-label-bg { fill: #fff; stroke: #e2e8f0; stroke-width: .5; opacity: .92; }
.arrow-label-text { font-size: 7px; fill: #64748b; text-anchor: middle; font-family: inherit; }
.legend-text { font-size: 8px; fill: #64748b; font-family: inherit; }
</style>
