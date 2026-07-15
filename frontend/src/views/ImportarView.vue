<template>
  <div class="importar-view">
    <PageHeader 
      :title="t('modules.importer.title')" 
      :description="t('modules.importer.description')"
      icon="pi pi-upload"
    >
      <template #actions>
        <HelpTooltip
          :content="t('modules.importer.help_content')"
          :title="t('modules.importer.help_title')"
          position="bottom"
          :link-url="'/docs/import-guide'"
          :link-text="t('modules.importer.help_link_text')"
        />
      </template>
    </PageHeader>

    <Card class="card-elevated">
      <template #content>
        <FormWrapper
          :title="t('importer.upload_section_title')"
          :description="t('importer.upload_section_description')"
          icon="pi pi-cloud-upload"
          :as-form="false"
          :show-default-buttons="false"
        >
          <div class="upload-area" 
               @dragover="onDragOver" 
               @dragleave="onDragLeave" 
               @drop="onDrop"
               :class="{ 'drag-over': dragOver }"
          >
            <input 
              type="file" 
              ref="fileInput" 
              @change="onFileSelect" 
              :accept="'.xlsx,.xls,.csv'" 
              style="display: none;"
            />
            <div class="upload-content">
              <i class="pi pi-cloud-upload upload-icon"></i>
              <h3>{{ t('importer.upload_title') }}</h3>
              <p>{{ t('importer.upload_description') }}</p>
              <Button 
                :label="t('importer.select_file')" 
                icon="pi pi-folder-open" 
                @click="selectFile"
                class="p-button-raised"
              />
              <p class="file-info">
                {{ t('importer.supported_formats') }}: XLSX, XLS, CSV
              </p>
            </div>
          </div>

          <div class="p-grid p-formgrid p-fluid" v-if="selectedFile">
            <div class="p-col-12">
              <div class="selected-file-info">
                <i class="pi pi-file"></i>
                <div class="file-details">
                  <span class="file-name">{{ selectedFile.name }}</span>
                  <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                </div>
                <Button 
                  icon="pi pi-times" 
                  class="p-button-text p-button-danger" 
                  @click="clearFile"
                  :title="t('common.clear')"
                />
              </div>
            </div>
          </div>

          <div class="p-grid p-formgrid p-fluid" v-if="selectedFile">
            <div class="p-col-12 md:col-6">
              <label for="mappingTemplate">{{ t('importer.mapping_template') }}</label>
              <Dropdown 
                id="mappingTemplate" 
                v-model="mappingTemplateId" 
                :options="mappingTemplates" 
                optionLabel="name" 
                optionValue="id" 
                :placeholder="t('importer.select_mapping_template')"
                :emptyMessage="t('importer.no_templates_found')"
              />
            </div>
            <div class="p-col-12 md:col-6">
              <label for="initialState">{{ t('importer.initial_state') }}</label>
              <Dropdown 
                id="initialState" 
                v-model="initialProcessState" 
                :options="processStates" 
                optionLabel="name" 
                optionValue="id" 
                :placeholder="t('importer.select_initial_state')"
                :emptyMessage="t('importer.no_states_found')"
              />
            </div>
          </div>

          <div class="p-grid p-formgrid p-fluid" v-if="selectedFile">
            <div class="p-col-12">
              <Button 
                :label="t('importer.start_import')" 
                icon="pi pi-send" 
                @click="startImport"
                :disabled="!canStartImport"
                class="p-button-success p-button-raised"
              />
            </div>
          </div>
          
          <!-- Vista previa del archivo -->
          <div class="p-grid p-formgrid p-fluid" v-if="filePreview && filePreview.length > 0">
            <div class="p-col-12">
              <h4>{{ t('importer.file_preview') }}</h4>
              <p class="preview-note">
                Esta vista muestra solo las primeras {{ filePreview.length }} filas de datos detectadas para revisar columnas y mapeo; no es el total importado.
              </p>
              <DataTable
                :value="filePreview"
                :paginator="false"
                :rows="10"
                responsiveLayout="scroll"
              >
                <Column 
                  v-for="(value, header, index) in filePreview[0]" 
                  :key="index"
                  :field="header" 
                  :header="header"
                >
                  <template #body="slotProps">
                    {{ slotProps.data[header] }}
                  </template>
                </Column>
              </DataTable>
            </div>
          </div>
          
          <!-- Mapeo de columnas -->
          <div class="p-grid p-formgrid p-fluid" v-if="selectedFile && filePreview && filePreview.length > 0">
            <div class="p-col-12">
              <FormWrapper
                :title="t('importer.column_mapping_title')"
                :description="t('importer.column_mapping_description')"
                icon="pi pi-exchange"
                submit-label="Guardar mapeo"
                @submit="saveCurrentMapping"
                @cancel="clearColumnMappings"
              >
                <div class="p-grid p-formgrid">
                  <div class="p-col-12" v-if="availableColumns.length > 0">
                    <h5>{{ t('importer.available_columns') }}</h5>
                    <div class="column-mapping-grid">
                      <div 
                        class="column-item" 
                        v-for="(column, index) in availableColumns" 
                        :key="index"
                      >
                        <label>{{ column }}</label>
                        <Dropdown
                          v-model="columnMappings[column]" 
                          :options="systemFields"
                          optionLabel="label"
                          optionValue="value"
                          :placeholder="t('importer.select_field')"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="p-col-12" v-if="availableColumns.length === 0">
                    <p>{{ t('importer.no_columns_detected') }}</p>
                  </div>
                </div>
                
                <div class="p-grid p-formgrid p-fluid">
                  <div class="p-col-12 md:col-6">
                    <Checkbox 
                      v-model="saveMappingTemplate" 
                      :binary="true" 
                      inputId="saveMappingTemplate"
                    />
                    <label for="saveMappingTemplate" class="ml-2">
                      {{ t('importer.save_mapping_template') }}
                    </label>
                  </div>
                  <div class="p-col-12 md:col-6" v-if="saveMappingTemplate">
                    <label for="templateName">{{ t('importer.template_name') }}</label>
                    <InputText 
                      id="templateName"
                      v-model="newTemplateName"
                      :placeholder="t('importer.enter_template_name')"
                    />
                  </div>
                </div>
              </FormWrapper>
            </div>
          </div>
        </FormWrapper>
      </template>
    </Card>

    <Card class="card-elevated" v-if="importBatches.length > 0">
      <template #title>
        <h3>{{ t('importer.history_title') }}</h3>
      </template>
      <template #content>
        <DataTable
          :value="importBatches"
          :paginator="true"
          :rows="10"
          :rowsPerPageOptions="[5, 10, 20, 50]"
          :loading="loadingBatches"
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
          currentPageReportTemplate="Mostrando {first} - {last} de {totalRecords} importaciones"
          responsiveLayout="scroll"
        >
          <Column field="original_filename" :header="t('importer.filename')" sortable></Column>
          <Column field="created_at" :header="t('importer.date')" sortable>
            <template #body="slotProps">
              {{ formatDate(slotProps.data.created_at) }}
            </template>
          </Column>
          <Column field="status" :header="t('importer.status')" sortable>
            <template #body="slotProps">
              <Tag :value="getStatusLabel(slotProps.data.status)" 
                   :severity="getStatusSeverity(slotProps.data.status)" />
            </template>
          </Column>
          <Column header="Progreso">
            <template #body="slotProps">
              <div class="batch-progress">
                <div class="progress-summary">
                  <span>{{ getBatchProgress(slotProps.data) }}%</span>
                  <small>{{ slotProps.data.processed_rows || 0 }} / {{ slotProps.data.total_rows || 0 }}</small>
                </div>
                <div class="batch-progress-bar">
                  <div
                    class="batch-progress-fill"
                    :class="`status-${slotProps.data.status?.toLowerCase()}`"
                    :style="{ width: `${getBatchProgress(slotProps.data)}%` }"
                  ></div>
                </div>
              </div>
            </template>
          </Column>
          <Column field="total_rows" :header="t('importer.total_rows')" sortable></Column>
          <Column field="success_rows" :header="t('importer.successful_rows')" sortable></Column>
          <Column field="error_rows" :header="t('importer.failed_rows')" sortable></Column>
          <Column :header="t('common.actions')" style="width: 150px">
            <template #body="slotProps">
              <Button 
                icon="pi pi-eye" 
                class="p-button-text p-button-rounded p-button-info" 
                @click="viewBatchDetails(slotProps.data)" 
                :title="t('common.view')"
              />
              <Button 
                icon="pi pi-download" 
                class="p-button-text p-button-rounded p-button-secondary" 
                @click="downloadErrorsLog(slotProps.data)" 
                :title="t('importer.download_errors')"
                v-if="slotProps.data.error_rows > 0"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Dialog 
      v-model:visible="batchDetailsDialog" 
      :header="t('importer.batch_details')" 
      :modal="true" 
      :style="{ width: '800px' }"
      class="card-elevated"
    >
      <div v-if="selectedBatch">
        <div class="p-grid p-formgrid">
          <div class="p-col-12 md:col-6">
            <h4>{{ t('importer.basic_info') }}</h4>
            <ul class="info-list">
              <li><strong>{{ t('importer.filename') }}:</strong> {{ selectedBatch.original_filename }}</li>
              <li><strong>{{ t('importer.date') }}:</strong> {{ formatDate(selectedBatch.created_at) }}</li>
              <li><strong>{{ t('importer.status') }}:</strong> 
                <Tag :value="getStatusLabel(selectedBatch.status)" 
                     :severity="getStatusSeverity(selectedBatch.status)" />
              </li>
            </ul>
          </div>
          <div class="p-col-12 md:col-6">
            <h4>{{ t('importer.statistics') }}</h4>
            <ul class="info-list">
              <li><strong>{{ t('importer.total_rows') }}:</strong> {{ selectedBatch.total_rows }}</li>
              <li><strong>Procesadas:</strong> {{ selectedBatch.processed_rows || 0 }}</li>
              <li><strong>{{ t('importer.successful_rows') }}:</strong> {{ selectedBatch.success_rows }}</li>
              <li><strong>{{ t('importer.failed_rows') }}:</strong> {{ selectedBatch.error_rows }}</li>
              <li><strong>Progreso:</strong> {{ getBatchProgress(selectedBatch) }}%</li>
            </ul>
            <div class="batch-progress detail-progress">
              <div class="batch-progress-bar">
                <div
                  class="batch-progress-fill"
                  :class="`status-${selectedBatch.status?.toLowerCase()}`"
                  :style="{ width: `${getBatchProgress(selectedBatch)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-col-12" v-if="selectedBatch.errors_log && selectedBatch.errors_log.length > 0">
          <h4>{{ t('importer.errors') }}</h4>
          <div class="errors-container">
            <div 
              v-for="(error, index) in selectedBatch.errors_log" 
              :key="index" 
              class="error-item"
            >
              <div class="error-header">
                <span class="error-row">{{ t('importer.row') }} {{ error.row }}</span>
                <span class="error-type">{{ error.type }}</span>
              </div>
              <div class="error-message">{{ error.message }}</div>
            </div>
          </div>
        </div>
      </div>
    </Dialog>

    <ConfirmationDialog 
      v-model:visible="confirmImportDialog" 
      @accept="confirmStartImport"
      :message="t('importer.confirm_start_message')"
      :header="t('importer.confirm_start_header')" 
      :acceptLabel="t('common.yes')" 
      :rejectLabel="t('common.no')"
      type="info"
      acceptSeverity="success"
      :closable="true"
    >
      <template #default>
        <p>{{ t('importer.confirm_start_description') }}</p>
        <ul class="confirmation-list">
          <li>{{ t('importer.confirm_file', { filename: selectedFile?.name }) }}</li>
          <li>{{ t('importer.confirm_template', { template: mappingTemplates.find(t => t.id === mappingTemplateId)?.name }) }}</li>
          <li>{{ t('importer.confirm_state', { state: processStates.find(s => s.id === initialProcessState)?.name }) }}</li>
        </ul>
      </template>
    </ConfirmationDialog>

    <UserFeedback
      v-if="showFeedback"
      :type="feedbackType"
      :title="feedbackTitle"
      :message="feedbackMessage"
      :duration="5000"
      @close="showFeedback = false"
    />

    <LoadingSpinner 
      :loading="loading" 
      :text="loadingText" 
      :show-progress="showProgress"
      :progress="progress"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import * as XLSX from 'xlsx';
import { useI18n } from '@/composables/useI18n';
import { useErrorHandler } from '@/composables/useErrorHandler';
import { useAuth } from '@/composables/useAuth';
import api from '@/services/api';
import PageHeader from '@/components/PageHeader.vue';
import FormWrapper from '@/components/FormWrapper.vue';
import ConfirmationDialog from '@/components/ConfirmationDialog.vue';
import UserFeedback from '@/components/UserFeedback.vue';
import LoadingSpinner from '@/components/LoadingSpinner.vue';
import HelpTooltip from '@/components/HelpTooltip.vue';

// Importar componentes PrimeVue necesarios (estructura correcta)
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Tag from 'primevue/tag';

const { t } = useI18n();
const { currentUser } = useAuth();
const { handleError } = useErrorHandler();

// Registrar componentes
const components = {
  DataTable,
  Column,
  Dropdown,
  Checkbox,
  InputText,
  Button,
  Card,
  Tag
};

// Estados
const selectedFile = ref(null);
const mappingTemplateId = ref(null);
const initialProcessState = ref(null);
const importBatches = ref([]);
const batchDetailsDialog = ref(false);
const selectedBatch = ref(null);
const confirmImportDialog = ref(false);
const loading = ref(false);
const loadingBatches = ref(false);
const dragOver = ref(false);
const fileInput = ref(null);
const batchPollingInterval = ref(null);

// Estados para feedback
const showFeedback = ref(false);
const feedbackType = ref('info');
const feedbackTitle = ref('');
const feedbackMessage = ref('');

// Estados para carga
const loadingText = ref('');
const showProgress = ref(false);
const progress = ref(0);

// Estados para plantillas y estados de proceso
const mappingTemplates = ref([]);
const processStates = ref([]);

// Estado para vista previa del archivo
const filePreview = ref([]);

// Estados para mapeo de columnas
const availableColumns = ref([]);
const columnMappings = ref({});
const systemFields = ref([
  { label: t('importer.field_client_id'), value: 'client.identification' },
  { label: t('importer.field_client_name'), value: 'client.name' },
  { label: t('importer.field_client_address'), value: 'client.address' },
  { label: t('importer.field_client_phone'), value: 'client.phone' },
  { label: t('importer.field_client_email'), value: 'client.email' },
  { label: t('importer.field_obligation_number'), value: 'obligation.number' },
  { label: t('importer.field_obligation_amount'), value: 'obligation.amount' },
  { label: t('importer.field_obligation_date'), value: 'obligation.issue_date' },
  { label: t('importer.field_obligation_due_date'), value: 'obligation.due_date' },
  { label: t('importer.field_obligation_concept'), value: 'obligation.concept' },
  { label: t('importer.field_obligation_status'), value: 'obligation.status' },
  // Campos para atributos adicionales
  { label: 'Cliente - Atributo Adicional 1', value: 'client.additional_attributes.custom_field_1' },
  { label: 'Cliente - Atributo Adicional 2', value: 'client.additional_attributes.custom_field_2' },
  { label: 'Cliente - Atributo Adicional 3', value: 'client.additional_attributes.custom_field_3' },
  { label: 'Cliente - Tipo de Documento', value: 'client.additional_attributes.document_type' },
  { label: 'Cliente - Municipio', value: 'client.additional_attributes.municipality' },
  { label: 'Cliente - Ciclo', value: 'client.additional_attributes.cycle' },
  { label: 'Cliente - Cuenta', value: 'client.additional_attributes.account_number' },
  { label: 'Cliente - Ficha Catastral', value: 'client.additional_attributes.cadastral_record' },
  { label: 'Cliente - Clase Servicio', value: 'client.additional_attributes.service_class' },
  { label: 'Cliente - Antigüedad', value: 'client.additional_attributes.aging' },
  { label: 'Cliente - Valor APU', value: 'client.additional_attributes.apu_value' },
  { label: 'Obligación - Atributo Adicional 1', value: 'obligation.additional_attributes.custom_field_1' },
  { label: 'Obligación - Atributo Adicional 2', value: 'obligation.additional_attributes.custom_field_2' },
  { label: 'Obligación - Atributo Adicional 3', value: 'obligation.additional_attributes.custom_field_3' }
]);
const saveMappingTemplate = ref(false);
const newTemplateName = ref('');

// Propiedades computadas
const canStartImport = computed(() => {
  return selectedFile.value && availableColumns.value && availableColumns.value.length > 0;
});

const getActiveColumnMapping = () => {
  return Object.fromEntries(
    Object.entries(columnMappings.value).filter(([, targetField]) => Boolean(targetField))
  );
};

// Funciones
const selectFile = () => {
  fileInput.value.click();
};

const onFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    // Validar tipo de archivo
    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      showFeedbackMessage('error', t('common.error'), t('importer.invalid_file_type'));
      return;
    }

    // Validar tamaño de archivo (50MB máximo)
    if (file.size > 50 * 1024 * 1024) {
      showFeedbackMessage('error', t('common.error'), t('importer.file_too_large'));
      return;
    }

    selectedFile.value = file;
    generateFilePreview(file);
  }
};

const clearFile = () => {
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const resetImportForm = () => {
  clearFile();
  mappingTemplateId.value = null;
  initialProcessState.value = null;
  filePreview.value = [];
  availableColumns.value = [];
  columnMappings.value = {};
  saveMappingTemplate.value = false;
  newTemplateName.value = '';
};

const clearColumnMappings = () => {
  availableColumns.value.forEach(column => {
    columnMappings.value[column] = '';
  });
  saveMappingTemplate.value = false;
  newTemplateName.value = '';
  showFeedbackMessage('info', t('common.info'), 'Mapeo limpiado');
};

const saveCurrentMapping = async () => {
  const activeMapping = getActiveColumnMapping();

  if (Object.keys(activeMapping).length === 0) {
    showFeedbackMessage('error', t('common.error'), 'Seleccione al menos un campo para guardar el mapeo');
    return;
  }

  if (!saveMappingTemplate.value) {
    showFeedbackMessage('success', t('common.success'), 'Mapeo guardado en el formulario');
    return;
  }

  if (!newTemplateName.value.trim()) {
    showFeedbackMessage('error', t('common.error'), 'Ingrese el nombre de la plantilla');
    return;
  }

  try {
    const response = await api.post('/importer/mapping-templates', {
      name: newTemplateName.value.trim(),
      description: null,
      mapping_config: activeMapping,
      supported_fields: Object.values(activeMapping)
    });

    await loadMappingTemplates();
    mappingTemplateId.value = response.data.id;
    saveMappingTemplate.value = false;
    newTemplateName.value = '';
    showFeedbackMessage('success', t('common.success'), 'Plantilla de mapeo guardada');
  } catch (error) {
    handleError(error, 'Error al guardar la plantilla de mapeo');
  }
};

const onDragOver = (event) => {
  event.preventDefault();
  dragOver.value = true;
};

const onDragLeave = () => {
  dragOver.value = false;
};

const onDrop = (event) => {
  event.preventDefault();
  dragOver.value = false;
  
  if (event.dataTransfer.files && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0];
    
    // Validar tipo de archivo
    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      showFeedbackMessage('error', t('common.error'), t('importer.invalid_file_type'));
      return;
    }

    // Validar tamaño de archivo (50MB máximo)
    if (file.size > 50 * 1024 * 1024) {
      showFeedbackMessage('error', t('common.error'), t('importer.file_too_large'));
      return;
    }

    selectedFile.value = file;
    generateFilePreview(file);
  }
};

const setPreviewData = (headers, previewRows) => {
  availableColumns.value = headers;
  filePreview.value = previewRows;

  headers.forEach(header => {
    columnMappings.value[header] = '';
  });
};

const normalizeCellValue = (value) => String(value ?? '').trim();

const getNonEmptyCellCount = (row) => {
  return row.filter(value => normalizeCellValue(value) !== '').length;
};

const getNextDataRow = (rows, startIndex) => {
  return rows.slice(startIndex).find(row => getNonEmptyCellCount(row) > 0) || [];
};

const getHeaderScore = (rows, rowIndex) => {
  const row = rows[rowIndex];
  const nonEmptyValues = row.map(normalizeCellValue).filter(Boolean);

  if (nonEmptyValues.length < 2) {
    return -1;
  }

  const nextDataRow = getNextDataRow(rows, rowIndex + 1);
  const nextDataCount = getNonEmptyCellCount(nextDataRow);
  const uniqueValueCount = new Set(nonEmptyValues.map(value => value.toLowerCase())).size;
  const repeatedPenalty = nonEmptyValues.length - uniqueValueCount;
  const fieldNameHints = [
    'identificacion',
    'cedula',
    'nit',
    'nombre',
    'cliente',
    'obligacion',
    'valor',
    'monto',
    'fecha',
    'telefono',
    'email',
    'direccion'
  ];
  const hintMatches = nonEmptyValues.filter(value => {
    const normalizedValue = value.toLowerCase();
    return fieldNameHints.some(hint => normalizedValue.includes(hint));
  }).length;

  return (nonEmptyValues.length * 3) + Math.min(nextDataCount, nonEmptyValues.length) + (hintMatches * 2) - repeatedPenalty;
};

const findHeaderRowIndex = (rows) => {
  const candidateLimit = Math.min(rows.length, 20);
  let bestIndex = -1;
  let bestScore = -1;

  for (let index = 0; index < candidateLimit; index += 1) {
    const score = getHeaderScore(rows, index);

    if (score > bestScore) {
      bestScore = score;
      bestIndex = index;
    }
  }

  return bestIndex;
};

const getUniqueHeaders = (headerRow) => {
  const headerCounts = {};

  return headerRow.map(normalizeCellValue).map((header, index) => {
    const resolvedHeader = header || `Columna ${index + 1}`;
    headerCounts[resolvedHeader] = (headerCounts[resolvedHeader] || 0) + 1;

    return headerCounts[resolvedHeader] === 1
      ? resolvedHeader
      : `${resolvedHeader} ${headerCounts[resolvedHeader]}`;
  });
};

const setPreviewDataFromRows = (rows) => {
  const normalizedRows = rows
    .map(row => Array.isArray(row) ? row : [])
    .filter(row => getNonEmptyCellCount(row) > 0);

  if (!normalizedRows.length) {
    throw new Error('El archivo no contiene filas con datos');
  }

  const headerRowIndex = findHeaderRowIndex(normalizedRows);

  if (headerRowIndex === -1) {
    throw new Error('No se pudo detectar una fila de encabezados válida');
  }

  const headers = getUniqueHeaders(normalizedRows[headerRowIndex]);
  const previewRows = normalizedRows.slice(headerRowIndex + 1).map(row => {
    const rowData = {};

    headers.forEach((header, index) => {
      rowData[header] = normalizeCellValue(row[index]);
    });

    return rowData;
  }).filter(row => Object.values(row).some(value => value !== '')).slice(0, 5);

  setPreviewData(headers, previewRows);
};

const parseCsvPreview = (csvContent) => {
  const rows = csvContent.split(/\r?\n/).slice(0, 50).map(row => row.split(','));
  setPreviewDataFromRows(rows);
};

const parseExcelPreview = (arrayBuffer) => {
  const workbook = XLSX.read(arrayBuffer, { type: 'array' });
  const firstSheetName = workbook.SheetNames[0];

  if (!firstSheetName) {
    throw new Error('El archivo Excel no contiene hojas');
  }

  const worksheet = workbook.Sheets[firstSheetName];
  const rows = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: '',
    raw: false
  });

  if (!rows.length) {
    throw new Error('El archivo Excel no contiene filas');
  }

  setPreviewDataFromRows(rows);
};

// Función para generar vista previa del archivo
const generateFilePreview = async (file) => {
  try {
    // Limpiar vista previa anterior
    filePreview.value = [];
    availableColumns.value = [];
    columnMappings.value = {};
    
    // Solo procesar los primeros 5 registros para la vista previa
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        // Detectar tipo de archivo y procesar en consecuencia
        const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (fileExtension === '.csv') {
          parseCsvPreview(e.target.result);
        } else if (fileExtension === '.xlsx' || fileExtension === '.xls') {
          parseExcelPreview(e.target.result);
        }
      } catch (parseError) {
        console.error('Error parsing file:', parseError);
        filePreview.value = [{
          error: t('importer.preview_error'),
          message: parseError.message
        }];
      }
    };
    
    reader.onerror = () => {
      showFeedbackMessage('error', t('common.error'), t('importer.file_read_error'));
    };
    
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (fileExtension === '.csv') {
      reader.readAsText(file);
    } else {
      reader.readAsArrayBuffer(file);
    }
  } catch (error) {
    console.error('Error generating file preview:', error);
    showFeedbackMessage('error', t('common.error'), t('importer.preview_generation_failed'));
  }
};

const loadImportBatches = async ({ silent = false } = {}) => {
  if (!silent) {
    loadingBatches.value = true;
  }

  try {
    const response = await api.get('/importer/batches');
    importBatches.value = response.data;
    syncSelectedBatch();
    updateBatchPolling();
  } catch (error) {
    showFeedbackMessage('error', t('common.error'), t('messages.errors.load_failed'));
    handleError(error, t('messages.errors.load_failed'));
  } finally {
    if (!silent) {
      loadingBatches.value = false;
    }
  }
};

const loadMappingTemplates = async () => {
  try {
    const response = await api.get('/importer/mapping-templates');
    mappingTemplates.value = response.data.map(template => ({
      id: template.id,
      name: template.name,
      description: template.description,
      mapping_config: template.mapping_config
    }));
  } catch (error) {
    showFeedbackMessage('error', t('common.error'), t('messages.errors.load_failed'));
    handleError(error, t('messages.errors.load_failed'));
  }
};

// Función para aplicar un mapeo de plantilla
const applyMappingTemplate = (templateId) => {
  if (!templateId) return;
  
  const template = mappingTemplates.value.find(t => t.id === templateId);
  if (template && template.mapping_config) {
    // Aplicar el mapeo de la plantilla a las columnas actuales
    Object.assign(columnMappings.value, template.mapping_config);
  }
};

// Watcher para aplicar la plantilla cuando cambie el ID
watch(mappingTemplateId, (newVal) => {
  if (newVal) {
    applyMappingTemplate(newVal);
  }
});

const loadProcessStates = async () => {
  try {
    const response = await api.get('/workflows/states/');
    processStates.value = response.data.map(state => ({
      id: state.id,
      name: state.name,
      code: state.code
    }));
  } catch (error) {
    showFeedbackMessage('error', t('common.error'), t('messages.errors.load_failed'));
    handleError(error, t('messages.errors.load_failed'));
  }
};

const startImport = () => {
  if (canStartImport.value) {
    confirmImportDialog.value = true;
  }
};

const confirmStartImport = async () => {
  confirmImportDialog.value = false;
  loading.value = true;
  showProgress.value = true;
  progress.value = 0;
  loadingText.value = t('importer.import_in_progress');

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    
    // Agregar mapeo de columnas
    formData.append('column_mapping', JSON.stringify(getActiveColumnMapping()));
    
    // Opciones adicionales
    if (mappingTemplateId.value) {
      formData.append('template_id', mappingTemplateId.value);
    }
    
    // Solo agregar estado inicial si se ha seleccionado
    if (initialProcessState.value) {
      formData.append('initial_process_state', initialProcessState.value);
    }
    
    // Indicar si se debe guardar la plantilla de mapeo
    if (saveMappingTemplate.value && newTemplateName.value) {
      formData.append('save_template', 'true');
      formData.append('template_name', newTemplateName.value);
    } else {
      formData.append('save_template', 'false');
    }

    const response = await api.post('/importer/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        const uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        progress.value = uploadProgress;
      }
    });

    if (response.data.success !== false) {
      showFeedbackMessage('success', t('common.success'), 'Importación iniciada correctamente');
      
      // Recargar lotes de importación
      await loadImportBatches();
      
      // Resetear formulario
      resetImportForm();
    } else {
      showFeedbackMessage('error', t('common.error'), response.data.error || t('messages.errors.import_failed'));
    }
  } catch (error) {
    console.error('Error importing file:', error);
    handleError(error, t('messages.errors.import_failed'));
  } finally {
    loading.value = false;
    showProgress.value = false;
    progress.value = 0;
  }
};

const viewBatchDetails = (batch) => {
  selectedBatch.value = batch;
  batchDetailsDialog.value = true;
};

const syncSelectedBatch = () => {
  if (!selectedBatch.value) return;

  const updatedBatch = importBatches.value.find(batch => batch.id === selectedBatch.value.id);
  if (updatedBatch) {
    selectedBatch.value = updatedBatch;
  }
};

const isBatchInProgress = (batch) => {
  return ['PENDING', 'PROCESSING', 'VALIDATING'].includes(batch.status);
};

const hasActiveBatches = () => {
  return importBatches.value.some(isBatchInProgress);
};

const startBatchPolling = () => {
  if (batchPollingInterval.value) return;

  batchPollingInterval.value = window.setInterval(() => {
    loadImportBatches({ silent: true });
  }, 5000);
};

const stopBatchPolling = () => {
  if (!batchPollingInterval.value) return;

  window.clearInterval(batchPollingInterval.value);
  batchPollingInterval.value = null;
};

const updateBatchPolling = () => {
  if (hasActiveBatches()) {
    startBatchPolling();
  } else {
    stopBatchPolling();
  }
};

const downloadErrorsLog = (batch) => {
  // Crear un blob con el contenido de errores
  if (batch.errors_log && batch.errors_log.length > 0) {
    const errorsText = batch.errors_log.map(error => 
      `Fila ${error.row}: ${error.type} - ${error.message}`
    ).join('\n');
    
    const blob = new Blob([errorsText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `errores_importacion_${batch.original_filename}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
};

const getStatusLabel = (status) => {
  const labels = {
    'PENDING': t('importer.status_pending'),
    'PROCESSING': t('importer.status_processing'),
    'MAPPING': 'Pendiente de mapeo',
    'VALIDATING': 'Validando',
    'COMPLETED': t('importer.status_completed'),
    'PARTIAL': 'Completado con errores',
    'FAILED': t('importer.status_failed'),
    'CANCELLED': t('importer.status_cancelled')
  };
  return labels[status] || status;
};

const getStatusSeverity = (status) => {
  const severities = {
    'PENDING': 'warning',
    'PROCESSING': 'info',
    'MAPPING': 'warning',
    'VALIDATING': 'info',
    'COMPLETED': 'success',
    'PARTIAL': 'warning',
    'FAILED': 'danger',
    'CANCELLED': 'secondary'
  };
  return severities[status] || 'info';
};

const getBatchProgress = (batch) => {
  if (!batch || !batch.total_rows) {
    return ['COMPLETED', 'PARTIAL'].includes(batch?.status) ? 100 : 0;
  }

  if (['COMPLETED', 'PARTIAL'].includes(batch.status)) {
    return 100;
  }

  const processedRows = batch.processed_rows || 0;
  return Math.min(100, Math.round((processedRows * 100) / batch.total_rows));
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const showFeedbackMessage = (type, title, message) => {
  feedbackType.value = type;
  feedbackTitle.value = title;
  feedbackMessage.value = message;
  showFeedback.value = true;
  
  // Ocultar el feedback después de 5 segundos
  setTimeout(() => {
    showFeedback.value = false;
  }, 5000);
};

onMounted(async () => {
  await loadImportBatches();
  await loadMappingTemplates();
  await loadProcessStates();
});

onUnmounted(() => {
  stopBatchPolling();
});
</script>

<style scoped>
.importar-view {
  width: 100%;
  padding: 0;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f9fafb;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-50), 0.1);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  font-size: 3rem;
  color: #9ca3af;
}

.selected-file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: #f3f4f6;
  border-radius: 6px;
  margin-top: 1rem;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-name {
  display: block;
  font-weight: 500;
  color: #1f2937;
}

.file-size {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
}

.file-info {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.preview-note {
  margin: -0.25rem 0 1rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  padding: 0.25rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.info-list li:last-child {
  border-bottom: none;
}

.errors-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
}

.error-item {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
  border-radius: 4px;
}

.error-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.batch-progress {
  min-width: 140px;
}

.progress-summary {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
  font-size: 0.875rem;
}

.progress-summary small {
  color: #6b7280;
}

.batch-progress-bar {
  width: 100%;
  height: 0.5rem;
  overflow: hidden;
  background-color: #e5e7eb;
  border-radius: 999px;
}

.batch-progress-fill {
  height: 100%;
  background-color: #3b82f6;
  border-radius: inherit;
  transition: width 0.3s ease;
}

.batch-progress-fill.status-completed {
  background-color: #22c55e;
}

.batch-progress-fill.status-partial,
.batch-progress-fill.status-mapping,
.batch-progress-fill.status-pending {
  background-color: #f59e0b;
}

.batch-progress-fill.status-failed,
.batch-progress-fill.status-cancelled {
  background-color: #ef4444;
}

.detail-progress {
  margin-top: 0.75rem;
}

.error-row {
  font-weight: 500;
  color: #dc2626;
}

.error-type {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}

.error-message {
  color: #991b1b;
  font-size: 0.875rem;
}

.confirmation-list {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.confirmation-list li {
  margin-bottom: 0.5rem;
}

.card-elevated {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.card-elevated:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-4px);
}

.column-mapping-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.column-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background-color: #f9fafb;
}

.column-item label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}
</style>
