<template>
  <Dialog 
    v-model:visible="visible" 
    :style="{ width: '700px' }" 
    :header="dialogTitle" 
    :modal="true"
    @hide="$emit('update:visible', false)"
  >
    <FormWrapper
      :title="formTitle"
      submit-label="Generar Documento"
      @submit="generateDocument"
      @cancel="cancelOperation"
    >
      <template #default>
        <div class="field">
          <label for="documentType">Tipo de Documento</label>
          <Dropdown 
            id="documentType" 
            v-model="documentData.type" 
            :options="documentTypes" 
            optionLabel="name" 
            optionValue="value"
            @change="onDocumentTypeChange"
          />
        </div>
        
        <div class="field" v-if="documentData.clientId">
          <label>Cliente Seleccionado</label>
          <div class="selected-client">
            <span>{{ selectedClient?.name }}</span>
            <Button 
              icon="pi pi-times" 
              text 
              severity="danger" 
              @click="clearClientSelection"
              v-tooltip="'Limpiar selección'"
            />
          </div>
        </div>
        
        <div class="field" v-if="documentData.obligationId">
          <label>Obligación Seleccionada</label>
          <div class="selected-obligation">
            <span>{{ selectedObligation?.concept }} - ${{ selectedObligation?.amount.toLocaleString('es-CO') }}</span>
            <Button 
              icon="pi pi-times" 
              text 
              severity="danger" 
              @click="clearObligationSelection"
              v-tooltip="'Limpiar selección'"
            />
          </div>
        </div>
        
        <div class="field" v-if="documentData.type === 'agreement'">
          <label for="agreementTotal">Monto Total del Acuerdo</label>
          <InputNumber 
            id="agreementTotal" 
            v-model="documentData.agreementTerms.totalAmount" 
            mode="currency" 
            currency="COP" 
            locale="es-CO"
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'agreement'">
          <label for="installmentCount">Número de Cuotas</label>
          <InputNumber 
            id="installmentCount" 
            v-model="documentData.agreementTerms.installmentCount" 
            :min="1" 
            :max="60"
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'agreement'">
          <label for="startDate">Fecha de Inicio</label>
          <Calendar 
            id="startDate" 
            v-model="documentData.agreementTerms.startDate" 
            dateFormat="dd/mm/yy"
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'resolution'">
          <label for="resolutionNumber">Número de Resolución</label>
          <div class="resolution-number-input">
            <InputText 
              id="resolutionNumber" 
              v-model="documentData.resolution.number" 
              :placeholder="'Número único o patrón (ej: RES-' + getCurrentDate() + '-001)'"
            />
            <Button 
              label="Autocompletar" 
              icon="pi pi-sync" 
              @click="generateSequentialNumbers"
              severity="secondary"
              outlined
            />
          </div>
        </div>
        
        <div class="field" v-if="documentData.type === 'resolution'">
          <label for="resolutionDate">Fecha de Resolución</label>
          <Calendar 
            id="resolutionDate" 
            v-model="documentData.resolution.date" 
            dateFormat="dd/mm/yy"
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'resolution'">
          <label for="resolutionSubject">Asunto</label>
          <InputText 
            id="resolutionSubject" 
            v-model="documentData.resolution.subject" 
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'resolution'">
          <label for="resolutionContent">Contenido</label>
          <Textarea 
            id="resolutionContent" 
            v-model="documentData.resolution.content" 
            :autoResize="true" 
            rows="5" 
          />
        </div>
        
        <div class="field" v-if="documentData.type === 'notification'">
          <label for="notificationTemplate">Plantilla de Notificación</label>
          <Dropdown 
            id="notificationTemplate" 
            v-model="documentData.template" 
            :options="notificationTemplates" 
            optionLabel="name" 
            optionValue="value"
          />
        </div>
        
        <!-- Opciones para generación masiva -->
        <div class="field" v-if="showBulkOptions">
          <div class="field-checkbox">
            <Checkbox 
              id="bulkGeneration" 
              v-model="documentData.bulkGeneration" 
              :binary="true"
            />
            <label for="bulkGeneration">Generación Masiva</label>
          </div>
          
          <div v-if="documentData.bulkGeneration" class="bulk-options">
            <div class="field">
              <label for="clientFilter">Filtrar Clientes</label>
              <MultiSelect 
                id="clientFilter" 
                v-model="documentData.bulkOptions.clients" 
                :options="allClients" 
                optionLabel="name" 
                optionValue="id"
                placeholder="Seleccionar clientes..."
              />
            </div>
            
            <div class="field">
              <label for="resolutionPattern">Patrón de Numeración</label>
              <InputText 
                id="resolutionPattern" 
                v-model="documentData.bulkOptions.numberPattern" 
                placeholder="Ej: RES-YYYY-XXX"
              />
            </div>
            
            <div class="field">
              <label for="sequentialStart">Número Inicial Secuencial</label>
              <InputNumber 
                id="sequentialStart" 
                v-model="documentData.bulkOptions.sequentialStart" 
                :min="1"
              />
            </div>
          </div>
        </div>
      </template>
    </FormWrapper>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import FormWrapper from '@/components/FormWrapper.vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  client: {
    type: Object,
    default: null
  },
  obligation: {
    type: Object,
    default: null
  },
  allClients: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:visible', 'document-generated']);

// Document data
const documentData = ref({
  type: 'notification',
  clientId: null,
  obligationId: null,
  template: 'notification',
  bulkGeneration: false,
  bulkOptions: {
    clients: [],
    numberPattern: 'RES-YYYY-XXX',
    sequentialStart: 1
  },
  agreementTerms: {
    totalAmount: 0,
    installmentCount: 1,
    startDate: new Date(),
    installmentAmount: 0
  },
  resolution: {
    number: '',
    date: new Date(),
    subject: '',
    content: ''
  }
});

// Selected data
const selectedClient = ref(null);
const selectedObligation = ref(null);

// Document types
const documentTypes = [
  { name: 'Notificación de Cobro', value: 'notification' },
  { name: 'Acuerdo de Pago', value: 'agreement' },
  { name: 'Resolución', value: 'resolution' },
  { name: 'Carta de Recordatorio', value: 'reminder' },
  { name: 'Aviso Final', value: 'final_notice' }
];

// Notification templates
const notificationTemplates = [
  { name: 'Notificación Estándar', value: 'notification' },
  { name: 'Carta de Recordatorio', value: 'reminder' },
  { name: 'Aviso Final', value: 'final_notice' }
];

// Computed properties
const dialogTitle = computed(() => {
  const type = documentTypes.find(t => t.value === documentData.value.type);
  return `Generar ${type ? type.name : 'Documento'}`;
});

const formTitle = computed(() => {
  const type = documentTypes.find(t => t.value === documentData.value.type);
  return `Datos para ${type ? type.name : 'Documento'}`;
});

const showBulkOptions = computed(() => {
  return documentData.value.type === 'resolution';
});

// Watch for changes in props
watch(
  () => props.client,
  (newClient) => {
    if (newClient) {
      selectedClient.value = newClient;
      documentData.value.clientId = newClient.id;
    }
  }
);

watch(
  () => props.obligation,
  (newObligation) => {
    if (newObligation) {
      selectedObligation.value = newObligation;
      documentData.value.obligationId = newObligation.id;
    }
  }
);

// Calculate installment amount when agreement terms change
watch(
  () => documentData.value.agreementTerms,
  (terms) => {
    if (terms.totalAmount && terms.installmentCount) {
      documentData.value.agreementTerms.installmentAmount = 
        Math.round(terms.totalAmount / terms.installmentCount);
    }
  },
  { deep: true }
);

// Handle document type change
const onDocumentTypeChange = () => {
  // Reset specific fields based on document type
  if (documentData.value.type !== 'agreement') {
    documentData.value.agreementTerms = {
      totalAmount: 0,
      installmentCount: 1,
      startDate: new Date(),
      installmentAmount: 0
    };
  }
  
  if (documentData.value.type !== 'resolution') {
    documentData.value.resolution = {
      number: '',
      date: new Date(),
      subject: '',
      content: ''
    };
  }
  
  if (documentData.value.type !== 'notification') {
    documentData.value.template = 'notification';
  }
};

// Clear selections
const clearClientSelection = () => {
  selectedClient.value = null;
  documentData.value.clientId = null;
};

const clearObligationSelection = () => {
  selectedObligation.value = null;
  documentData.value.obligationId = null;
};

// Generate sequential numbers for bulk generation
const generateSequentialNumbers = () => {
  if (documentData.value.type === 'resolution') {
    const date = getCurrentDate();
    const pattern = documentData.value.bulkOptions.numberPattern.replace('YYYY', date);
    const startNum = documentData.value.bulkOptions.sequentialStart;
    
    // Si es generación masiva, generamos números para cada cliente seleccionado
    if (documentData.value.bulkGeneration && documentData.value.bulkOptions.clients.length > 0) {
      // En un escenario real, aquí se generarían números secuenciales para cada cliente
      documentData.value.resolution.number = `${pattern}-${String(startNum).padStart(3, '0')}`;
    } else {
      // Si no es masiva, solo generamos uno
      documentData.value.resolution.number = `${pattern}-${String(startNum).padStart(3, '0')}`;
    }
  }
};

// Get current date in YYYYMMDD format
const getCurrentDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
};

// Generate document
const generateDocument = async () => {
  // Validar campos requeridos
  if (!documentData.value.clientId && !documentData.value.bulkGeneration) {
    alert('Por favor seleccione un cliente o habilite la generación masiva');
    return;
  }
  
  if (!documentData.value.obligationId && documentData.value.type !== 'resolution' && !documentData.value.bulkGeneration) {
    alert('Por favor seleccione una obligación');
    return;
  }
  
  // Si es resolución, asegurarse de que tenga número y fecha
  if (documentData.value.type === 'resolution') {
    if (!documentData.value.resolution.number) {
      alert('Por favor ingrese o genere un número de resolución');
      return;
    }
    if (!documentData.value.resolution.date) {
      alert('Por favor ingrese la fecha de resolución');
      return;
    }
  }
  
  // Emitir evento para generar el documento
  emit('document-generated', { ...documentData.value });
  
  // Cerrar diálogo
  emit('update:visible', false);
};

// Cancel operation
const cancelOperation = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.selected-client, .selected-obligation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background-color: var(--surface-section);
}

.resolution-number-input {
  display: flex;
  gap: 0.5rem;
}

.bulk-options {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background-color: var(--surface-section);
}

.field-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.field-checkbox label {
  margin-left: 0.5rem;
}
</style>