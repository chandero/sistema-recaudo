de <template>
  <div class="documentos">
    <PageHeader 
      title="Gestión de Documentos" 
      subtitle="Administra los documentos asociados a los procesos de recaudo"
    >
      <template #actions>
        <Button 
          label="Subir Documento" 
          icon="pi pi-upload" 
          @click="openUploadDialog"
        />
        <Button 
          label="Generar Documento" 
          icon="pi pi-file" 
          severity="secondary" 
          @click="openDocumentGenerator"
        />
      </template>
    </PageHeader>

    <DataTableWrapper
      :value="documents"
      :columns="tableColumns"
      :loading="loading"
      @refresh="loadDocuments"
      @search-change="onSearchChange"
      :filter-fields="['name', 'type', 'clientName']"
    >
      <template #actions>
        <Button 
          label="Exportar" 
          icon="pi pi-download" 
          severity="secondary" 
          outlined
        />
      </template>
      
      <template #column-type="slotProps">
        <Tag 
          :value="getTypeLabel(slotProps.fieldData)" 
          :severity="getTypeSeverity(slotProps.fieldData)" 
        />
      </template>
      
      <template #column-status="slotProps">
        <Tag 
          :value="getStatusLabel(slotProps.fieldData)" 
          :severity="getStatusSeverity(slotProps.fieldData)" 
        />
      </template>
      
      <template #column-actions="slotProps">
        <Button 
          icon="pi pi-eye" 
          text 
          severity="info" 
          @click="viewDocument(slotProps.rowData)"
          v-tooltip="'Ver documento'"
        />
        <Button 
          icon="pi pi-download" 
          text 
          severity="success" 
          @click="downloadDocument(slotProps.rowData)"
          v-tooltip="'Descargar'"
        />
        <Button 
          icon="pi pi-print" 
          text 
          severity="secondary" 
          @click="printDocument(slotProps.rowData)"
          v-tooltip="'Imprimir'"
        />
        <Button 
          icon="pi pi-trash" 
          text 
          severity="danger" 
          @click="confirmDeleteDocument(slotProps.rowData)"
          v-tooltip="'Eliminar'"
        />
      </template>
    </DataTableWrapper>

    <!-- Dialog for uploading documents -->
    <Dialog 
      v-model:visible="uploadDialog" 
      :style="{ width: '500px' }" 
      header="Subir Documento" 
      :modal="true" 
      class="p-fluid"
    >
      <div class="field">
        <label for="file">Seleccionar Archivo</label>
        <FileUpload 
          id="file" 
          name="demo[]" 
          :multiple="false" 
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" 
          customUpload 
          @uploader="customUploader"
          :maxFileSize="10000000"
        />
      </div>
      <div class="field">
        <label for="documentType">Tipo de Documento</label>
        <Dropdown 
          id="documentType" 
          v-model="newDocument.type" 
          :options="documentTypes" 
          optionLabel="label" 
          optionValue="value"
          placeholder="Seleccione tipo"
        />
      </div>
      <div class="field">
        <label for="documentDescription">Descripción</label>
        <Textarea 
          id="documentDescription" 
          v-model="newDocument.description" 
          :autoResize="true" 
          rows="3" 
          cols="30" 
        />
      </div>
      <template #footer>
        <Button 
          label="Cancelar" 
          icon="pi pi-times" 
          text 
          @click="hideUploadDialog"
        />
        <Button 
          label="Subir" 
          icon="pi pi-upload" 
          @click="uploadDocument"
          :disabled="!newDocument.file"
        />
      </template>
    </Dialog>

    <!-- Dialog for adding new documents -->
    <Dialog 
      v-model:visible="documentDialog" 
      :style="{ width: '500px' }" 
      header="Nuevo Documento" 
      :modal="true" 
      class="p-fluid"
    >
      <div class="field">
        <label for="documentName">Nombre del Documento</label>
        <InputText 
          id="documentName" 
          v-model.trim="document.name" 
          required="true" 
          autofocus 
          :class="{ 'p-invalid': submitted && !document.name }" 
        />
        <small class="p-error" v-if="submitted && !document.name">El nombre es obligatorio.</small>
      </div>
      <div class="field">
        <label for="documentTypeNew">Tipo de Documento</label>
        <Dropdown 
          id="documentTypeNew" 
          v-model="document.type" 
          :options="documentTypes" 
          optionLabel="label" 
          optionValue="value"
          placeholder="Seleccione tipo"
        />
      </div>
      <div class="field">
        <label for="documentStatus">Estado</label>
        <Dropdown 
          id="documentStatus" 
          v-model="document.status" 
          :options="statuses" 
          optionLabel="label" 
          optionValue="value"
          placeholder="Seleccione estado"
        />
      </div>
      <div class="field">
        <label for="documentClient">Cliente Asociado</label>
        <Dropdown 
          id="documentClient" 
          v-model="document.clientId" 
          :options="clients" 
          optionLabel="name" 
          optionValue="id"
          placeholder="Seleccione cliente"
        />
      </div>
      <div class="field">
        <label for="documentDescriptionNew">Descripción</label>
        <Textarea 
          id="documentDescriptionNew" 
          v-model="document.description" 
          :autoResize="true" 
          rows="3" 
          cols="30" 
        />
      </div>
      <template #footer>
        <Button 
          label="Cancelar" 
          icon="pi pi-times" 
          text 
          @click="hideDocumentDialog"
        />
        <Button 
          label="Guardar" 
          icon="pi pi-check" 
          @click="saveDocument"
        />
      </template>
    </Dialog>

    <!-- Confirmation dialog for deletion -->
    <Dialog 
      v-model:visible="deleteDocumentDialog" 
      :style="{ width: '450px' }" 
      header="Confirmar" 
      :modal="true"
    >
      <div class="confirmation-content">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
        <span v-if="documentToDelete">¿Está seguro de eliminar el documento <b>{{ documentToDelete.name }}</b>?</span>
      </div>
      <template #footer>
        <Button 
          label="No" 
          icon="pi pi-times" 
          text 
          @click="deleteDocumentDialog = false"
        />
        <Button 
          label="Sí" 
          icon="pi pi-check" 
          @click="deleteDocument"
        />
      </template>
    </Dialog>

    <!-- Document Generator Dialog -->
    <DocumentGenerator 
      v-model:visible="showDocumentGenerator" 
      :client="selectedClientForGen" 
      :obligation="selectedObligationForGen"
      @document-generated="onDocumentGenerated"
    />
    
    <!-- Template Analysis Dialog -->
    <Dialog 
      v-model:visible="analysisDialog" 
      :style="{ width: '600px' }" 
      header="Análisis de Variables de Plantilla" 
      :modal="true"
    >
      <div v-if="analysisResult">
        <h4>Variables encontradas: {{ analysisResult.count }}</h4>
        <div class="field">
          <label>Variables extraídas:</label>
          <div class="flex flex-wrap gap-2 mt-2">
            <Tag v-for="variable in analysisResult.variables" :key="variable" :value="variable" severity="info" />
          </div>
        </div>
        <div class="mt-3">
          <label>Esquema JSON generado:</label>
          <Textarea :value="JSON.stringify(schemaFromAnalysis, null, 2)" autoResize rows="5" cols="30" readonly />
        </div>
      </div>
      <div v-else-if="analysisLoading">
        <p>Analizando plantilla, por favor espere...</p>
        <ProgressBar mode="indeterminate" class="mt-2" />
      </div>
      <template #footer>
        <Button 
          label="Cerrar" 
          icon="pi pi-times" 
          text 
          @click="analysisDialog = false; analysisResult = null"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import PageHeader from '@/components/PageHeader.vue';
import DataTableWrapper from '@/components/DataTableWrapper.vue';
import DocumentGenerator from '@/components/DocumentGenerator.vue';
import { FilterMatchMode } from 'primevue/api';
import api from '@/services/api'; // Asegurarse de importar el servicio API

// Sample data - in a real app this would come from an API
const documents = ref([]);
const uploadDialog = ref(false);
const documentDialog = ref(false);
const deleteDocumentDialog = ref(false);
const documentToDelete = ref(null);
const loading = ref(true);
const submitted = ref(false);
const newDocument = ref({
  file: null,
  type: null,
  description: ''
});
const document = ref({
  id: null,
  name: '',
  type: '',
  status: 'active',
  clientId: null,
  description: ''
});

// Document generation
const showDocumentGenerator = ref(false);
const selectedClientForGen = ref(null);
const selectedObligationForGen = ref(null);

// Template analysis
const analysisDialog = ref(false);
const analysisResult = ref(null);
const analysisLoading = ref(false);
const currentTemplateToAnalyze = ref(null);

// Calculate schema from analysis for the JSON editor
const schemaFromAnalysis = computed(() => {
  if (!analysisResult.value || !analysisResult.value.variables) return {};
  const schema = {};
  analysisResult.value.variables.forEach(varName => {
    schema[varName] = "string"; // Default type
  });
  return schema;
});

// Define table columns
const tableColumns = ref([
  { field: 'name', header: 'Nombre', sortable: true },
  { field: 'type', header: 'Tipo', sortable: true },
  { field: 'clientName', header: 'Cliente', sortable: true },
  { field: 'dateCreated', header: 'Fecha', sortable: true },
  { field: 'status', header: 'Estado', sortable: true },
  { field: 'actions', header: 'Acciones' }
]);

// Define document types
const documentTypes = ref([
  { label: 'Contrato', value: 'contract' },
  { label: 'Notificación', value: 'notification' },
  { label: 'Acuerdo de Pago', value: 'payment_agreement' },
  { label: 'Resolución', value: 'resolution' },
  { label: 'Otro', value: 'other' }
]);

// Define statuses
const statuses = ref([
  { label: 'Activo', value: 'active' },
  { label: 'Inactivo', value: 'inactive' },
  { label: 'Archivado', value: 'archived' }
]);

// Define sample clients
const clients = ref([
  { id: 1, name: 'Juan Pérez' },
  { id: 2, name: 'María García' },
  { id: 3, name: 'Carlos López' }
]);

onMounted(() => {
  loadDocuments();
});

const loadDocuments = () => {
  // Simulate API call
  setTimeout(() => {
    documents.value = [
      { id: 1, name: 'Contrato Servicio Público', type: 'contract', clientName: 'Juan Pérez', dateCreated: '2023-05-15', status: 'active' },
      { id: 2, name: 'Notificación de Cobro', type: 'notification', clientName: 'María García', dateCreated: '2023-06-20', status: 'active' },
      { id: 3, name: 'Acuerdo de Pago', type: 'payment_agreement', clientName: 'Carlos López', dateCreated: '2023-07-10', status: 'archived' },
      { id: 4, name: 'Resolución Final', type: 'resolution', clientName: 'Ana Rodríguez', dateCreated: '2023-04-05', status: 'inactive' },
      { id: 5, name: 'Documento Adjunto', type: 'other', clientName: 'Luis Martínez', dateCreated: '2023-08-12', status: 'active' }
    ];
    loading.value = false;
  }, 800);
};

const openUploadDialog = () => {
  newDocument.value = {
    file: null,
    type: null,
    description: ''
  };
  uploadDialog.value = true;
};

const hideUploadDialog = () => {
  uploadDialog.value = false;
};

const openNewDocument = () => {
  document.value = {
    id: null,
    name: '',
    type: '',
    status: 'active',
    clientId: null,
    description: ''
  };
  submitted.value = false;
  documentDialog.value = true;
};

const hideDocumentDialog = () => {
  documentDialog.value = false;
  submitted.value = false;
};

const saveDocument = () => {
  submitted.value = true;

  if (document.value.name.trim()) {
    if (document.value.id) {
      // Update existing document
      const index = documents.value.findIndex(d => d.id === document.value.id);
      documents.value[index] = {...document.value};
    } else {
      // Add new document
      document.value.id = Math.max(...documents.value.map(d => d.id)) + 1;
      document.value.dateCreated = new Date().toISOString().split('T')[0];
      document.value.clientName = clients.value.find(c => c.id === document.value.clientId)?.name || '';
      documents.value.push({...document.value});
    }
    hideDocumentDialog();
  }
};

const viewDocument = (doc) => {
  console.log('Viewing document:', doc);
  // In a real app, this would open a preview modal or redirect to a document viewer
};

const downloadDocument = (doc) => {
  console.log('Downloading document:', doc);
  // In a real app, this would initiate a file download
};

const printDocument = (doc) => {
  console.log('Printing document:', doc);
  // In a real app, this would initiate a print action
};

const confirmDeleteDocument = (doc) => {
  documentToDelete.value = doc;
  deleteDocumentDialog.value = true;
};

const deleteDocument = () => {
  documents.value = documents.value.filter(d => d.id !== documentToDelete.value.id);
  deleteDocumentDialog.value = false;
  documentToDelete.value = null;
};

const getTypeLabel = (type) => {
  const typeObj = documentTypes.value.find(t => t.value === type);
  return typeObj ? typeObj.label : type;
};

const getTypeSeverity = (type) => {
  switch(type) {
    case 'contract': return 'info';
    case 'notification': return 'warning';
    case 'payment_agreement': return 'success';
    case 'resolution': return 'help';
    default: return 'secondary';
  }
};

const getStatusLabel = (status) => {
  const statusObj = statuses.value.find(s => s.value === status);
  return statusObj ? statusObj.label : status;
};

const getStatusSeverity = (status) => {
  switch(status) {
    case 'active': return 'success';
    case 'inactive': return 'secondary';
    case 'archived': return 'info';
    default: return 'info';
  }
};

const onSearchChange = (value) => {
  console.log('Searching for:', value);
  // In a real app, this would trigger a filtered API call
};

const customUploader = (event) => {
  // Upload the file to a server
  newDocument.value.file = event.files[0];
};

const uploadDocument = () => {
  if (newDocument.value.file && newDocument.value.type) {
    // Create a new document entry
    const newDoc = {
      id: Math.max(...documents.value.map(d => d.id)) + 1,
      name: newDocument.value.file.name,
      type: newDocument.value.type,
      clientName: 'Cliente Ejemplo', // Would come from selection in real app
      dateCreated: new Date().toISOString().split('T')[0],
      status: 'active',
      description: newDocument.value.description
    };
    
    documents.value.push(newDoc);
    hideUploadDialog();
  }
};

// Document generation methods
const openDocumentGenerator = () => {
  showDocumentGenerator.value = true;
};

const onDocumentGenerated = (documentData) => {
  console.log('Document generated:', documentData);
  // In a real app, this would save the generated document to the system
  // and possibly add it to the documents list
};

// Template analysis methods
const analyzeTemplate = async (templateId) => {
  analysisLoading.value = true;
  analysisResult.value = null;
  
  try {
    const response = await api.get(`/documents/templates/${templateId}/analyze`);
    analysisResult.value = response.data;
    analysisLoading.value = false;
    analysisDialog.value = true;
  } catch (error) {
    console.error('Error analyzing template:', error);
    analysisLoading.value = false;
    alert('Error al analizar la plantilla: ' + error.message);
  }
};

</script>

<style scoped>
.documentos {
  display: flex;
  flex-direction: column;
}

.confirmation-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.p-tag {
  margin: 0.2rem;
}
</style>