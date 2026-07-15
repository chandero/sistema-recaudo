<template>
  <div class="obligaciones">
    <PageHeader 
      title="Gestión de Obligaciones" 
      subtitle="Administra las obligaciones pendientes de los clientes"
    >
      <template #actions>
        <Button 
          label="Agregar Obligación" 
          icon="pi pi-plus" 
          @click="openNewObligation"
        />
      </template>
    </PageHeader>

    <div class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">Total de registros</span>
        <strong class="summary-value">{{ totalRecords }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">Página actual</span>
        <strong class="summary-value">{{ currentPageLabel }}</strong>
      </div>
    </div>

    <DataTableWrapper
      :value="obligations"
      :columns="tableColumns"
      :loading="loading"
      :lazy="true"
      :first="tableFirst"
      :default-rows="tableRows"
      :total-records="totalRecords"
      :rows-per-page-options="[10, 20, 50, 100]"
      current-page-report-template="Mostrando {first} - {last} de {totalRecords} obligaciones"
      @refresh="loadObligations"
      @search-change="onSearchChange"
      @page="onPageChange"
      :filter-fields="['concept', 'clientName', 'amount']"
    >
      <template #actions>
        <Button 
          label="Exportar" 
          icon="pi pi-download" 
          severity="secondary" 
          outlined
          @click="exportObligations"
          :disabled="!obligations.length"
        />
      </template>
      
      <template #column-amount="slotProps">
        <span class="amount">{{ formatCurrency(slotProps.fieldData) }}</span>
      </template>

      <template #column-dueDate="slotProps">
        <span>{{ formatDate(slotProps.fieldData) }}</span>
      </template>
      
      <template #column-status="slotProps">
        <Tag 
          :value="getStatus(slotProps.fieldData)" 
          :severity="getStatusSeverity(slotProps.fieldData)" 
        />
      </template>
      
      <template #column-actions="slotProps">
        <Button 
          icon="pi pi-eye" 
          text 
          severity="info" 
          @click="viewObligation(slotProps.rowData)"
          v-tooltip="'Ver detalle'"
        />
        <Button 
          icon="pi pi-pencil" 
          text 
          severity="info" 
          @click="editObligation(slotProps.rowData)"
          v-tooltip="'Editar'"
        />
        <Button 
          icon="pi pi-file-pdf" 
          text 
          severity="success" 
          @click="generateDocument(slotProps.rowData)"
          v-tooltip="'Generar documento'"
        />
        <Button 
          icon="pi pi-trash" 
          text 
          severity="danger" 
          @click="confirmDeleteObligation(slotProps.rowData)"
          v-tooltip="'Eliminar'"
        />
      </template>
    </DataTableWrapper>

    <!-- Dialog for adding/editing obligations -->
    <Dialog 
      v-model:visible="obligationDialog" 
      :style="{ width: '500px' }" 
      header="Detalles de Obligación" 
      :modal="true" 
      class="p-fluid"
    >
      <FormWrapper
        :title="obligation.id ? 'Editar Obligación' : 'Nueva Obligación'"
        submit-label="Guardar"
        @submit="saveObligation"
        @cancel="hideDialog"
      >
        <template #default>
          <div class="field">
            <label for="concept">Concepto</label>
            <InputText 
              id="concept" 
              v-model.trim="obligation.concept" 
              required="true" 
              autofocus 
              :class="{ 'p-invalid': submitted && !obligation.concept }" 
            />
            <small class="p-error" v-if="submitted && !obligation.concept">El concepto es obligatorio.</small>
          </div>
          <div class="field">
            <label for="clientId">Cliente</label>
            <Dropdown 
              id="clientId" 
              v-model="obligation.clientId" 
              :options="clients" 
              optionLabel="name" 
              optionValue="id"
              placeholder="Seleccione un cliente"
              :class="{ 'p-invalid': submitted && !obligation.clientId }"
            />
            <small class="p-error" v-if="submitted && !obligation.clientId">El cliente es obligatorio.</small>
          </div>
          <div class="field">
            <label for="amount">Monto</label>
            <InputNumber 
              id="amount" 
              v-model="obligation.amount" 
              mode="currency" 
              currency="USD" 
              locale="en-US"
              :class="{ 'p-invalid': submitted && !obligation.amount }"
            />
            <small class="p-error" v-if="submitted && !obligation.amount">El monto es obligatorio.</small>
          </div>
          <div class="field">
            <label for="issueDate">Fecha de Emisión</label>
            <Calendar 
              id="issueDate" 
              v-model="obligation.issueDate" 
              dateFormat="dd/mm/yy"
              :class="{ 'p-invalid': submitted && !obligation.issueDate }"
            />
            <small class="p-error" v-if="submitted && !obligation.issueDate">La fecha de emisión es obligatoria.</small>
          </div>
          <div class="field">
            <label for="dueDate">Fecha de Vencimiento</label>
            <Calendar 
              id="dueDate" 
              v-model="obligation.dueDate" 
              dateFormat="dd/mm/yy"
              :class="{ 'p-invalid': submitted && !obligation.dueDate }"
            />
            <small class="p-error" v-if="submitted && !obligation.dueDate">La fecha de vencimiento es obligatoria.</small>
          </div>
          <div class="field">
            <label for="status">Estado</label>
            <Dropdown 
              id="status" 
              v-model="obligation.status" 
              :options="statuses" 
              optionLabel="label" 
              optionValue="value"
              placeholder="Seleccione un estado"
            />
          </div>
        </template>
      </FormWrapper>
    </Dialog>

    <!-- Confirmation dialog for deletion -->
    <Dialog 
      v-model:visible="deleteObligationDialog" 
      :style="{ width: '450px' }" 
      header="Confirmar" 
      :modal="true"
    >
      <div class="confirmation-content">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
        <span v-if="obligationToDelete">¿Está seguro de eliminar la obligación <b>{{ obligationToDelete.concept }}</b> por ${{ obligationToDelete.amount }}?</span>
      </div>
      <template #footer>
        <Button 
          label="No" 
          icon="pi pi-times" 
          text 
          @click="deleteObligationDialog = false"
        />
        <Button 
          label="Sí" 
          icon="pi pi-check" 
          @click="deleteObligation"
        />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="detailDialog"
      :style="{ width: '520px' }"
      header="Detalle de Obligación"
      :modal="true"
    >
      <div v-if="selectedObligation" class="detail-grid">
        <span>Concepto</span>
        <strong>{{ selectedObligation.concept }}</strong>
        <span>Cliente</span>
        <strong>{{ selectedObligation.clientName }}</strong>
        <span>Monto</span>
        <strong>{{ formatCurrency(selectedObligation.amount) }}</strong>
        <span>Emisión</span>
        <strong>{{ formatDate(selectedObligation.issueDate) }}</strong>
        <span>Vencimiento</span>
        <strong>{{ formatDate(selectedObligation.dueDate) }}</strong>
        <span>Estado</span>
        <Tag :value="getStatus(selectedObligation.status)" :severity="getStatusSeverity(selectedObligation.status)" />
      </div>
      <template #footer>
        <Button label="Cerrar" icon="pi pi-times" text @click="detailDialog = false" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import PageHeader from '@/components/PageHeader.vue';
import DataTableWrapper from '@/components/DataTableWrapper.vue';
import FormWrapper from '@/components/FormWrapper.vue';
import { clientService, obligationService } from '@/services/api';
import { useErrorHandler } from '@/composables/useErrorHandler';

const router = useRouter();
const toast = useToast();
const { handleError } = useErrorHandler();

const obligations = ref([]);
const obligationDialog = ref(false);
const deleteObligationDialog = ref(false);
const detailDialog = ref(false);
const obligationToDelete = ref(null);
const selectedObligation = ref(null);
const loading = ref(false);
const submitted = ref(false);
const totalRecords = ref(0);
const tableFirst = ref(0);
const tableRows = ref(10);
const obligation = ref({
  id: null,
  concept: '',
  clientId: null,
  amount: null,
  issueDate: null,
  dueDate: null,
  status: 'pending'
});

// Define table columns
const tableColumns = ref([
  { field: 'concept', header: 'Concepto', sortable: true },
  { field: 'clientName', header: 'Cliente', sortable: true },
  { field: 'amount', header: 'Monto', sortable: true },
  { field: 'dueDate', header: 'Vence', sortable: true },
  { field: 'status', header: 'Estado', sortable: true },
  { field: 'actions', header: 'Acciones' }
]);

// Define statuses
const statuses = ref([
  { label: 'Pendiente', value: 'pending' },
  { label: 'Pagada', value: 'paid' },
  { label: 'Vencida', value: 'overdue' },
  { label: 'Anulada', value: 'cancelled' }
]);

const clients = ref([]);
const currentPageLabel = computed(() => {
  if (!totalRecords.value) return '0 - 0';
  const first = tableFirst.value + 1;
  const last = Math.min(tableFirst.value + obligations.value.length, totalRecords.value);
  return `${first} - ${last}`;
});

onMounted(() => {
  loadInitialData();
});

const toDate = (value) => value ? new Date(value) : null;

const toIsoDate = (value) => {
  if (!value) return null;
  return value instanceof Date ? value.toISOString() : new Date(value).toISOString();
};

const mapApiObligation = (apiObligation) => {
  const client = clients.value.find((item) => item.id === apiObligation.client_id);
  return {
    id: apiObligation.id,
    concept: apiObligation.description || apiObligation.type || `Obligación ${apiObligation.id}`,
    clientId: apiObligation.client_id,
    clientName: client?.name || `Cliente #${apiObligation.client_id}`,
    amount: apiObligation.amount,
    currency: apiObligation.currency || 'COP',
    issueDate: apiObligation.issue_date,
    dueDate: apiObligation.due_date,
    status: apiObligation.status,
    type: apiObligation.type || 'invoice',
    processId: apiObligation.process_id
  };
};

const buildPayload = () => ({
  amount: Number(obligation.value.amount),
  currency: 'COP',
  issue_date: toIsoDate(obligation.value.issueDate),
  due_date: toIsoDate(obligation.value.dueDate),
  status: obligation.value.status,
  type: 'invoice',
  description: obligation.value.concept,
  client_id: obligation.value.clientId,
  process_id: null
});

const loadInitialData = async () => {
  loading.value = true;
  try {
    const clientsResponse = await clientService.getAll({ limit: 1000 });
    clients.value = clientsResponse.data || [];
    await loadObligations();
  } catch (error) {
    handleError(error, 'No se pudieron cargar los datos de obligaciones');
  } finally {
    loading.value = false;
  }
};

const loadObligations = async () => {
  loading.value = true;
  try {
    const [listResponse, countResponse] = await Promise.all([
      obligationService.getAll({ skip: tableFirst.value, limit: tableRows.value }),
      obligationService.getCount()
    ]);
    totalRecords.value = countResponse.data || 0;
    const response = listResponse;
    obligations.value = (response.data || []).map(mapApiObligation);
  } catch (error) {
    handleError(error, 'No se pudieron cargar las obligaciones');
  } finally {
    loading.value = false;
  }
};

const onPageChange = async (event) => {
  tableFirst.value = event.first;
  tableRows.value = event.rows;
  await loadObligations();
};

const openNewObligation = () => {
  obligation.value = {
    id: null,
    concept: '',
    clientId: null,
    amount: null,
    issueDate: new Date(),
    dueDate: null,
    status: 'pending'
  };
  submitted.value = false;
  obligationDialog.value = true;
};

const hideDialog = () => {
  obligationDialog.value = false;
  submitted.value = false;
};

const saveObligation = async () => {
  submitted.value = true;

  if (obligation.value.concept && obligation.value.clientId && obligation.value.amount && obligation.value.issueDate && obligation.value.dueDate) {
    try {
      if (obligation.value.id) {
        await obligationService.update(obligation.value.id, buildPayload());
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Obligación actualizada', life: 3000 });
      } else {
        await obligationService.create(buildPayload());
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Obligación creada', life: 3000 });
      }
      await loadObligations();
      hideDialog();
    } catch (error) {
      handleError(error, 'No se pudo guardar la obligación');
    }
  }
};

const editObligation = (currentObligation) => {
  obligation.value = {
    ...currentObligation,
    issueDate: toDate(currentObligation.issueDate),
    dueDate: toDate(currentObligation.dueDate)
  };
  obligationDialog.value = true;
};

const confirmDeleteObligation = (currentObligation) => {
  obligationToDelete.value = currentObligation;
  deleteObligationDialog.value = true;
};

const deleteObligation = async () => {
  if (!obligationToDelete.value) return;

  try {
    await obligationService.delete(obligationToDelete.value.id);
    toast.add({ severity: 'success', summary: 'Éxito', detail: 'Obligación eliminada', life: 3000 });
    await loadObligations();
    hideDialog();
  } catch (error) {
    handleError(error, 'No se pudo eliminar la obligación');
  } finally {
    deleteObligationDialog.value = false;
    obligationToDelete.value = null;
  }
};

const getStatus = (status) => {
  const statusObj = statuses.value.find(s => s.value === status);
  return statusObj ? statusObj.label : status;
};

const getStatusSeverity = (status) => {
  switch(status) {
    case 'pending': return 'warning';
    case 'paid': return 'success';
    case 'overdue': return 'danger';
    case 'cancelled': return 'secondary';
    default: return 'info';
  }
};

const onSearchChange = (value) => {
  const search = value.trim().toLowerCase();
  if (!search) {
    loadObligations();
    return;
  }
  obligations.value = obligations.value.filter((item) =>
    [item.concept, item.clientName, String(item.amount), item.status]
      .some((field) => field?.toLowerCase?.().includes(search) || String(field).includes(search))
  );
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('es-CO', { 
    style: 'currency', 
    currency: 'COP',
    minimumFractionDigits: 0
  }).format(amount);
};

const formatDate = (value) => {
  if (!value) return 'N/A';
  return new Intl.DateTimeFormat('es-CO').format(new Date(value));
};

const viewObligation = (currentObligation) => {
  selectedObligation.value = currentObligation;
  detailDialog.value = true;
};

const generateDocument = (currentObligation) => {
  localStorage.setItem('selected_obligation_for_document', JSON.stringify(currentObligation));
  router.push('/documentos');
};

const exportObligations = () => {
  const headers = ['Concepto', 'Cliente', 'Monto', 'Fecha emisión', 'Fecha vencimiento', 'Estado'];
  const rows = obligations.value.map((item) => [
    item.concept,
    item.clientName,
    item.amount,
    formatDate(item.issueDate),
    formatDate(item.dueDate),
    getStatus(item.status)
  ]);
  const csv = [headers, ...rows]
    .map((row) => row.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `obligaciones-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.obligaciones {
  display: flex;
  flex-direction: column;
}

.summary-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.summary-item {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 0.875rem 1rem;
  min-width: 180px;
}

.summary-label {
  display: block;
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.summary-value {
  color: var(--text-color);
  font-size: 1.4rem;
  line-height: 1;
}

.confirmation-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.amount {
  font-weight: 500;
}

.detail-grid {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 0.75rem 1rem;
  align-items: center;
}

.detail-grid span {
  color: #6b7280;
}
</style>