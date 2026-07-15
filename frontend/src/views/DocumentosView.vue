de <template>
  <div class="documentos">
    <PageHeader 
      title="Gestión de Documentos" 
      subtitle="Administra los documentos asociados a los procesos de recaudo"
    >
      <template #actions>
        <SplitButton 
          label="Subir Documento" 
          icon="pi pi-upload" 
          :model="uploadMenuItems"
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

    <TabView>
      <TabPanel header="Documentos">
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
      </TabPanel>
      
      <TabPanel header="Plantillas" @tab-show="loadTemplates">
        <div class="card">
          <Toolbar class="mb-3">
            <template #start>
              <IconField iconPosition="left" class="search-field">
                <InputIcon class="pi pi-search" />
                <InputText 
                  v-model="templateSearchValue" 
                  placeholder="Buscar plantillas..." 
                />
              </IconField>
            </template>
            <template #end>
              <Button 
                icon="pi pi-refresh" 
                text 
                @click="loadTemplates"
                class="mr-2"
              />
              <Button 
                label="Exportar" 
                icon="pi pi-download" 
                severity="secondary" 
                outlined
              />
            </template>
          </Toolbar>
          
          <DataTable 
            :value="templates" 
            :paginator="true" 
            :rows="10" 
            :rowsPerPageOptions="[10, 20, 50]"
            :loading="templatesLoading"
            :globalFilterFields="['name', 'code']"
            removableSort
            tableStyle="min-width: 100%"
          >
            <template #empty>
              <div class="empty-message">
                <i class="pi pi-inbox" style="font-size: 3rem;"></i>
                <p>No se encontraron plantillas</p>
              </div>
            </template>
            
            <template #loading>
              <div class="loading-message">
                <i class="pi pi-spin pi-spinner" style="font-size: 2rem;"></i>
                <p>Cargando plantillas...</p>
              </div>
            </template>
            
            <Column field="name" header="Nombre" sortable>
              <template #body="slotProps">
                {{ slotProps.data.name }}
              </template>
            </Column>
            <Column field="code" header="Código" sortable>
              <template #body="slotProps">
                {{ slotProps.data.code }}
              </template>
            </Column>
            <Column field="type" header="Tipo" sortable>
              <template #body="slotProps">
                <Tag 
                  :value="getTemplateTypeLabel(slotProps.data.type)" 
                  :severity="getTemplateTypeSeverity(slotProps.data.type)" 
                />
              </template>
            </Column>
            <Column field="description" header="Descripción" sortable>
              <template #body="slotProps">
                {{ slotProps.data.description }}
              </template>
            </Column>
            <Column header="Acciones">
              <template #body="slotProps">
                <Button 
                  icon="pi pi-eye" 
                  text 
                  severity="info" 
                  @click="viewTemplate(slotProps.data)"
                  v-tooltip="'Ver plantilla'"
                  class="mr-1"
                />
                <Button 
                  icon="pi pi-download" 
                  text 
                  severity="success" 
                  @click="downloadTemplate(slotProps.data)"
                  v-tooltip="'Descargar'"
                  class="mr-1"
                />
                <Button 
                  icon="pi pi-trash" 
                  text 
                  severity="danger" 
                  @click="confirmDeleteTemplate(slotProps.data)"
                  v-tooltip="'Eliminar'"
                />
              </template>
            </Column>
          </DataTable>
        </div>
      </TabPanel>
    </TabView>

    <!-- Dialog for uploading documents -->
    <Dialog 
      v-model:visible="uploadDialog" 
      :style="{ width: '500px' }" 
      header="Subir Documento Existente" 
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

    <!-- Confirmation dialog for template deletion -->
    <Dialog 
      v-model:visible="deleteTemplateDialog" 
      :style="{ width: '450px' }" 
      header="Confirmar Eliminación" 
      :modal="true"
    >
      <div class="confirmation-content">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
        <span v-if="templateToDelete">¿Está seguro de eliminar la plantilla <b>{{ templateToDelete.name }}</b>? Esta acción no se puede deshacer.</span>
      </div>
      <template #footer>
        <Button 
          label="No" 
          icon="pi pi-times" 
          text 
          @click="deleteTemplateDialog = false"
        />
        <Button 
          label="Sí" 
          icon="pi pi-check" 
          @click="deleteTemplate"
          severity="danger"
        />
      </template>
    </Dialog>

    <!-- Dialog for template preview -->
    <Dialog 
      v-model:visible="templatePreviewDialog" 
      :style="{ width: '800px', height: '80vh' }" 
      header="Vista Previa de Plantilla" 
      :modal="true"
    >
      <div v-if="selectedTemplateForPreview" class="flex flex-column gap-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="card-detail">
            <label class="text-sm text-gray-500">
              <i class="pi pi-tag mr-1"></i>Nombre
            </label>
            <p class="m-0 font-medium">{{ selectedTemplateForPreview.name }}</p>
          </div>
          <div class="card-detail">
            <label class="text-sm text-gray-500">
              <i class="pi pi-hashtag mr-1"></i>Código
            </label>
            <p class="m-0 font-medium">{{ selectedTemplateForPreview.code }}</p>
          </div>
          <div class="card-detail">
            <label class="text-sm text-gray-500">
              <i class="pi pi-file mr-1"></i>Tipo
            </label>
            <Tag 
              :value="getTemplateTypeLabel(selectedTemplateForPreview.type)" 
              :severity="getTemplateTypeSeverity(selectedTemplateForPreview.type)"
              class="font-medium"
            />
          </div>
          <div class="card-detail">
            <label class="text-sm text-gray-500">
              <i class="pi pi-tag mr-1"></i>Versión
            </label>
            <p class="m-0 font-medium">{{ selectedTemplateForPreview.version || '1.0' }}</p>
          </div>
          <div class="card-detail md:col-span-2">
            <label class="text-sm text-gray-500">
              <i class="pi pi-align-left mr-1"></i>Descripción
            </label>
            <p class="m-0">{{ selectedTemplateForPreview.description || 'Sin descripción' }}</p>
          </div>
        </div>

        <Divider />

        <div class="field">
          <label class="block mb-2 font-medium">
            <i class="pi pi-info-circle mr-1"></i>Metadatos
          </label>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div class="p-3 bg-gray-50 border-round">
              <div class="text-sm text-gray-500">Estado</div>
              <Tag 
                :value="selectedTemplateForPreview.is_active ? 'Activa' : 'Inactiva'" 
                :severity="selectedTemplateForPreview.is_active ? 'success' : 'danger'"
                class="font-medium mt-1"
              />
            </div>
            <div class="p-3 bg-gray-50 border-round">
              <div class="text-sm text-gray-500">Fecha Creación</div>
              <div class="font-medium mt-1">{{ formatDate(selectedTemplateForPreview.created_at) }}</div>
            </div>
            <div class="p-3 bg-gray-50 border-round">
              <div class="text-sm text-gray-500">Última Actualización</div>
              <div class="font-medium mt-1">{{ formatDate(selectedTemplateForPreview.updated_at) }}</div>
            </div>
          </div>
        </div>

        <Divider />

        <div class="field">
          <label class="block mb-2 font-medium">
            <i class="pi pi-code mr-1"></i>Variables Disponibles
          </label>
          <div v-if="selectedTemplateForPreview.variables_schema_str" class="surface-ground p-3 border-round">
            <pre class="m-0 text-sm">{{ JSON.stringify(JSON.parse(selectedTemplateForPreview.variables_schema_str), null, 2) }}</pre>
          </div>
          <div v-else class="text-gray-500 italic">
            No se han definido variables para esta plantilla
          </div>
        </div>

        <Divider />

        <div class="field">
          <label class="block mb-2 font-medium">
            <i class="pi pi-user mr-1"></i>Seleccionar Cliente para Vista Previa
          </label>
          <Dropdown 
            v-model="selectedPreviewClient" 
            :options="clients" 
            optionLabel="name" 
            optionValue="id"
            placeholder="Seleccione un cliente para generar la vista previa"
            class="w-full"
          />
        </div>

        <Divider />

        <div class="field">
          <label class="block mb-2 font-medium">
            <i class="pi pi-eye mr-1"></i>Vista Previa del Contenido
          </label>
          <div class="border-1 surface-border border-round p-4" style="height: 300px; overflow-y: auto;">
            <div v-if="templatePreviewUrl" class="template-preview-container">
              <iframe 
                :src="templatePreviewUrl" 
                width="100%" 
                height="250px"
                frameborder="0"
                style="border: none;"
              ></iframe>
            </div>
            <div v-else-if="!selectedPreviewClient" class="text-center p-4 text-gray-500">
              Vista previa no disponible. Seleccione un cliente para generar la vista previa.
            </div>
            <div v-else class="text-center p-4 text-gray-500">
              Haga clic en "Generar Vista Previa" para ver el contenido de la plantilla con los datos del cliente seleccionado.
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button 
          label="Cerrar" 
          icon="pi pi-times" 
          @click="closeTemplatePreview"
        />
        <Button 
          label="Generar Vista Previa" 
          icon="pi pi-refresh" 
          @click="generateTemplatePreview(selectedTemplateForPreview)"
          severity="secondary"
          outlined
          :disabled="!selectedPreviewClient"
        />
        <Button 
          label="Descargar" 
          icon="pi pi-download" 
          @click="downloadTemplate(selectedTemplateForPreview)"
          severity="info"
          outlined
        />
      </template>
    </Dialog>

    <!-- Dialog for uploading templates -->
    <Dialog 
      v-model:visible="templateUploadDialog" 
      :style="{ width: '500px' }" 
      header="Cargar Nueva Plantilla" 
      :modal="true" 
      class="p-fluid"
    >
      <div class="field">
        <label for="templateFile">Seleccionar Archivo de Plantilla</label>
        <FileUpload 
          id="templateFile" 
          name="templateFile" 
          :multiple="false" 
          accept=".docx,.pdf,.html,.txt" 
          customUpload 
          @uploader="customTemplateUploader"
          :maxFileSize="10000000"
        />
      </div>
      <div class="field">
        <label for="templateName">Nombre de la Plantilla</label>
        <InputText 
          id="templateName" 
          v-model.trim="newTemplate.name" 
          required="true" 
          autofocus 
          :class="{ 'p-invalid': submitted && !newTemplate.name }" 
        />
        <small class="p-error" v-if="submitted && !newTemplate.name">El nombre es obligatorio.</small>
      </div>
      <div class="field">
        <label for="templateCode">Código de la Plantilla</label>
        <InputText 
          id="templateCode" 
          v-model.trim="newTemplate.code" 
          required="true" 
          :class="{ 'p-invalid': submitted && !newTemplate.code }" 
        />
        <small class="p-error" v-if="submitted && !newTemplate.code">El código es obligatorio.</small>
      </div>
      <div class="field">
        <label for="templateType">Tipo de Plantilla</label>
        <Dropdown 
          id="templateType" 
          v-model="newTemplate.type" 
          :options="templateTypes" 
          optionLabel="label" 
          optionValue="value"
          placeholder="Seleccione tipo"
        />
      </div>
      <div class="field">
        <label for="templateDescription">Descripción</label>
        <Textarea 
          id="templateDescription" 
          v-model="newTemplate.description" 
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
          @click="hideTemplateUploadDialog"
        />
        <Button 
          label="Cargar Plantilla" 
          icon="pi pi-upload" 
          @click="uploadTemplate"
          :disabled="!newTemplate.file || !newTemplate.name || !newTemplate.code"
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
    
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import PageHeader from '@/components/PageHeader.vue';
import DataTableWrapper from '@/components/DataTableWrapper.vue';
import DocumentGenerator from '@/components/DocumentGenerator.vue';
import { FilterMatchMode } from 'primevue/api';
import { documentService } from '@/services/api'; // Corregir import

// Importar componentes adicionales
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toolbar from 'primevue/toolbar';
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import InputText from 'primevue/inputtext';
import Divider from 'primevue/divider';

// Variables para manejo de archivos
const selectedTemplateFile = ref(null);
const selectedTemplateName = ref('');
const templateSearchValue = ref('');

// Variables para vista previa de plantillas
const templatePreviewDialog = ref(false);
const selectedTemplateForPreview = ref(null);

// Sample data - in a real app this would come from an API
const documents = ref([]);
const templates = ref([]);
const uploadDialog = ref(false);
const templateUploadDialog = ref(false);
const documentDialog = ref(false);
const deleteDocumentDialog = ref(false);
const deleteTemplateDialog = ref(false);
const documentToDelete = ref(null);
const templateToDelete = ref(null);
const loading = ref(true);
const templatesLoading = ref(true);
const submitted = ref(false);
const newDocument = ref({
  file: null,
  type: null,
  description: ''
});
const newTemplate = ref({
  file: null,
  name: '',
  code: '',
  type: null,
  description: '',
  categories: []
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

const openDialogFromMenu = (openDialog) => {
  // Let PrimeVue close the overlay menu before opening another focus trap.
  window.setTimeout(() => {
    openDialog();
  }, 0);
};

// Define upload menu items for SplitButton
const uploadMenuItems = ref([
  {
    label: 'Subir Documento Existente',
    icon: 'pi pi-file',
    command: () => {
      openDialogFromMenu(openUploadDialog);
    }
  },
  {
    label: 'Cargar Plantilla',
    icon: 'pi pi-file-import',
    command: () => {
      openDialogFromMenu(openTemplateUploadDialog);
    }
  }
]);

// Define table columns
const tableColumns = ref([
  { field: 'name', header: 'Nombre', sortable: true },
  { field: 'type', header: 'Tipo', sortable: true },
  { field: 'clientName', header: 'Cliente', sortable: true },
  { field: 'dateCreated', header: 'Fecha', sortable: true },
  { field: 'status', header: 'Estado', sortable: true },
  { field: 'actions', header: 'Acciones' }
]);

// Define template columns
const templateColumns = ref([
  { field: 'name', header: 'Nombre', sortable: true },
  { field: 'code', header: 'Código', sortable: true },
  { field: 'type', header: 'Tipo', sortable: true },
  { field: 'description', header: 'Descripción', sortable: true },
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

// Define template types
const templateTypes = ref([
  { label: 'Contrato', value: 'contract_template' },
  { label: 'Notificación', value: 'notification_template' },
  { label: 'Acuerdo de Pago', value: 'payment_agreement_template' },
  { label: 'Carta', value: 'letter_template' },
  { label: 'Informe', value: 'report_template' },
  { label: 'Otro', value: 'other_template' }
]);

// Define categories
const categories = ref([
  { id: 1, name: 'Cobro Judicial' },
  { id: 2, name: 'Cobro Extrajudicial' },
  { id: 3, name: 'Negociación' },
  { id: 4, name: 'Legal' },
  { id: 5, name: 'Administrativo' }
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
  loadTemplates();
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

const loadTemplates = async () => {
  templatesLoading.value = true;
  try {
    // Llamada real al backend para obtener las plantillas
    const response = await documentService.getTemplates();
    
    console.log('Datos recibidos del backend:', response.data);
    
    // Mapear los datos del backend a la estructura esperada por la tabla
    const mappedTemplates = response.data.map(template => {
      // Mapear template_type del backend a los valores esperados por las funciones
      let mappedType = 'other_template'; // Valor por defecto
      
      // Mapear según el valor real recibido del backend
      if (template.template_type) {
        const typeLower = template.template_type.toLowerCase();
        if (typeLower.includes('contract')) mappedType = 'contract_template';
        else if (typeLower.includes('notific')) mappedType = 'notification_template';
        else if (typeLower.includes('payment') || typeLower.includes('acuerdo')) mappedType = 'payment_agreement_template';
        else if (typeLower.includes('letter') || typeLower.includes('carta')) mappedType = 'letter_template';
        else if (typeLower.includes('report') || typeLower.includes('informe')) mappedType = 'report_template';
        else mappedType = 'other_template';
      }
      
      const mappedTemplate = {
        id: template.id,
        name: template.name,
        code: template.code,
        type: mappedType, // Mapear al tipo compatible con las funciones existentes
        description: template.description || 'Sin descripción',
        version: template.version,
        is_active: template.is_active,
        created_at: template.created_at,
        updated_at: template.updated_at
      };
      
      console.log('Template mapeado:', mappedTemplate);
      return mappedTemplate;
    });
    
    // Actualizar la referencia para forzar la reactividad
    templates.value = [];
    await nextTick(); // Esperar a que se procese el cambio anterior
    templates.value = mappedTemplates;
    
    console.log('Templates finales:', templates.value);
  } catch (error) {
    console.error('Error al cargar las plantillas:', error);
    // Datos de ejemplo en caso de error
    templates.value = [
      { id: 1, name: 'Plantilla de Notificación', code: 'NOTIF-001', type: 'notification_template', description: 'Plantilla estándar para notificaciones' },
      { id: 2, name: 'Plantilla de Acuerdo de Pago', code: 'PAGO-001', type: 'payment_agreement_template', description: 'Plantilla para acuerdos de pago' },
      { id: 3, name: 'Plantilla de Contrato', code: 'CONTR-001', type: 'contract_template', description: 'Plantilla de contrato estándar' }
    ];
  } finally {
    templatesLoading.value = false;
  }
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

const openTemplateUploadDialog = () => {
  newTemplate.value = {
    file: null,
    name: '',
    code: '',
    type: null,
    description: '',
    categories: []
  };
  submitted.value = false;
  templateUploadDialog.value = true;
};

const hideTemplateUploadDialog = () => {
  templateUploadDialog.value = false;
  submitted.value = false;
  // Resetear las variables de archivo
  selectedTemplateFile.value = null;
  selectedTemplateName.value = '';
  // No usar getElementById aquí, dejar que Vue maneje el estado del input
  newTemplate.value = {
    file: null,
    name: '',
    code: '',
    type: null,
    description: '',
    categories: []
  };
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

const viewTemplate = (template) => {
  selectedTemplateForPreview.value = template;
  templatePreviewDialog.value = true;
  
  // Generar la vista previa del contenido de la plantilla
  nextTick(() => {
    generateTemplatePreview(template);
  });
};

const closeTemplatePreview = () => {
  templatePreviewDialog.value = false;
  // Liberar la URL de vista previa para evitar fugas de memoria
  if (templatePreviewUrl.value) {
    URL.revokeObjectURL(templatePreviewUrl.value);
    templatePreviewUrl.value = '';
  }
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

const getTemplateTypeLabel = (type) => {
  const typeObj = templateTypes.value.find(t => t.value === type);
  return typeObj ? typeObj.label : type;
};

const getTemplateTypeSeverity = (type) => {
  switch(type) {
    case 'contract_template': return 'info';
    case 'notification_template': return 'warning';
    case 'payment_agreement_template': return 'success';
    case 'letter_template': return 'primary';
    case 'report_template': return 'help';
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
  console.log('Searching for documents:', value);
  // In a real app, this would trigger a filtered API call
};

const onTemplateSearchChange = (value) => {
  console.log('Searching for templates:', value);
  // In a real app, this would trigger a filtered API call
};

const customUploader = (event) => {
  // Upload the file to a server
  newDocument.value.file = event.files[0];
};

const customTemplateUploader = (event) => {
  // Handle the file upload for templates
  const file = event.files[0];
  if (file) {
    selectedTemplateFile.value = file;
    selectedTemplateName.value = file.name;
    newTemplate.value.file = file;
    
    // Actualizar el valor del template para que coincida con el nombre del archivo si no hay un nombre establecido
    if (!newTemplate.value.name || newTemplate.value.name === '') {
      // Obtener el nombre sin extensión
      const fileNameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.'));
      newTemplate.value.name = fileNameWithoutExt;
    }
  }
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

const uploadTemplate = async () => {
  submitted.value = true;

  if (selectedTemplateFile.value && newTemplate.value.name && newTemplate.value.code) {
    try {
      // Prepare form data for multipart upload
      const formData = new FormData();
      formData.append('name', newTemplate.value.name);
      formData.append('code', newTemplate.value.code);
      formData.append('description', newTemplate.value.description || '');
      formData.append('file', selectedTemplateFile.value); // Asegurar que se adjunta el archivo real
      formData.append('variables_schema', JSON.stringify({})); // Default empty schema
      
      console.log('FormData keys:', Array.from(formData.keys()));
      console.log('FormData file:', formData.get('file'));
      
      const response = await documentService.createTemplate(formData);
      console.log('Template uploaded successfully:', response);
      
      // Refresh the template list
      await loadTemplates();
      hideTemplateUploadDialog();
    } catch (error) {
      console.error('Error uploading template:', error);
      // Aquí podrías mostrar un mensaje de error al usuario
    }
  } else {
    console.log('Faltan campos requeridos o archivo no seleccionado');
    console.log('selectedTemplateFile:', selectedTemplateFile.value);
    console.log('newTemplate.name:', newTemplate.value.name);
    console.log('newTemplate.code:', newTemplate.value.code);
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

// Función para formatear fechas
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO');
};

// Variable para almacenar la URL de vista previa de la plantilla
const templatePreviewUrl = ref('');
// Variable para almacenar el cliente seleccionado para la vista previa
const selectedPreviewClient = ref(null);

// Función para generar vista previa de la plantilla
const generateTemplatePreview = async (template) => {
  try {
    // Si no hay cliente seleccionado, usar uno de ejemplo
    let clientToUse;
    if (selectedPreviewClient.value) {
      // Buscar el cliente completo basado en el ID seleccionado
      clientToUse = clients.value.find(client => client.id === selectedPreviewClient.value);
      if (!clientToUse) {
        // Si no se encuentra el cliente, usar datos de ejemplo
        clientToUse = {
          id: 1,
          name: 'Cliente Prueba',
          email: 'cliente@prueba.com',
          phone: '3001234567',
          address: 'Calle prueba 123',
          city: 'Ciudad Prueba',
        };
      }
    } else {
      // Usar un cliente de ejemplo para generar la vista previa
      clientToUse = {
        id: 1,
        name: 'Cliente Prueba',
        email: 'cliente@prueba.com',
        phone: '3001234567',
        address: 'Calle prueba 123',
        city: 'Ciudad Prueba',
        // Agregar más campos según las variables de la plantilla
      };
    }

    // Generar el documento con la plantilla y los datos del cliente
    const response = await documentService.generateDocumentFromTemplate(template.id, clientToUse);

    // Crear una URL para la vista previa
    const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    templatePreviewUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    console.error('Error generando vista previa de la plantilla:', error);
    templatePreviewUrl.value = '';
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
