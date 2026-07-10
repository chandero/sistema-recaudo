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

    <DataTableWrapper
      :value="obligations"
      :columns="tableColumns"
      :loading="loading"
      @refresh="loadObligations"
      @search-change="onSearchChange"
      :filter-fields="['concept', 'clientName', 'amount']"
    >
      <template #actions>
        <Button 
          label="Exportar" 
          icon="pi pi-download" 
          severity="secondary" 
          outlined
        />
      </template>
      
      <template #column-amount="slotProps">
        <span class="amount">{{ formatCurrency(slotProps.fieldData) }}</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PageHeader from '@/components/PageHeader.vue';
import DataTableWrapper from '@/components/DataTableWrapper.vue';
import FormWrapper from '@/components/FormWrapper.vue';

// Sample data - in a real app this would come from an API
const obligations = ref([]);
const obligationDialog = ref(false);
const deleteObligationDialog = ref(false);
const obligationToDelete = ref(null);
const loading = ref(true);
const submitted = ref(false);
const obligation = ref({
  id: null,
  concept: '',
  clientId: null,
  amount: null,
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

// Define sample clients
const clients = ref([
  { id: 1, name: 'Juan Pérez' },
  { id: 2, name: 'María García' },
  { id: 3, name: 'Carlos López' },
  { id: 4, name: 'Ana Rodríguez' },
  { id: 5, name: 'Luis Martínez' }
]);

onMounted(() => {
  loadObligations();
});

const loadObligations = () => {
  // Simulate API call
  setTimeout(() => {
    obligations.value = [
      { id: 1, concept: 'Servicios Públicos', clientName: 'Juan Pérez', clientId: 1, amount: 250000, dueDate: '2023-10-15', status: 'pending' },
      { id: 2, concept: 'Impuesto Predial', clientName: 'María García', clientId: 2, amount: 450000, dueDate: '2023-09-20', status: 'overdue' },
      { id: 3, concept: 'Multas de Tránsito', clientName: 'Carlos López', clientId: 3, amount: 120000, dueDate: '2023-11-05', status: 'pending' },
      { id: 4, concept: 'Cuota Administrativa', clientName: 'Ana Rodríguez', clientId: 4, amount: 85000, dueDate: '2023-08-30', status: 'paid' },
      { id: 5, concept: 'Servicios Públicos', clientName: 'Luis Martínez', clientId: 5, amount: 320000, dueDate: '2023-12-10', status: 'pending' }
    ];
    loading.value = false;
  }, 800);
};

const openNewObligation = () => {
  obligation.value = {
    id: null,
    concept: '',
    clientId: null,
    amount: null,
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

const saveObligation = () => {
  submitted.value = true;

  if (obligation.value.concept && obligation.value.clientId && obligation.value.amount && obligation.value.dueDate) {
    // Find client name to display in table
    const client = clients.value.find(c => c.id === obligation.value.clientId);
    
    if (obligation.value.id) {
      // Update existing obligation
      const index = obligations.value.findIndex(o => o.id === obligation.value.id);
      obligations.value[index] = { ...obligation.value, clientName: client?.name };
    } else {
      // Add new obligation
      obligation.value.id = Math.max(...obligations.value.map(o => o.id)) + 1;
      obligations.value.push({ ...obligation.value, clientName: client?.name });
    }
    hideDialog();
  }
};

const editObligation = (o) => {
  obligation.value = {...o};
  obligationDialog.value = true;
};

const confirmDeleteObligation = (o) => {
  obligationToDelete.value = o;
  deleteObligationDialog.value = true;
};

const deleteObligation = () => {
  obligations.value = obligations.value.filter(o => o.id !== obligationToDelete.value.id);
  deleteObligationDialog.value = false;
  obligationToDelete.value = null;
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
  console.log('Searching for:', value);
  // In a real app, this would trigger a filtered API call
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('es-CO', { 
    style: 'currency', 
    currency: 'COP',
    minimumFractionDigits: 0
  }).format(amount);
};

const viewObligation = (o) => {
  console.log('Viewing obligation:', o);
  // In a real app, this would navigate to the obligation detail page
};

const generateDocument = (o) => {
  console.log('Generating document for obligation:', o);
  // In a real app, this would generate a PDF document
};
</script>

<style scoped>
.obligaciones {
  display: flex;
  flex-direction: column;
}

.confirmation-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.amount {
  font-weight: 500;
}
</style>