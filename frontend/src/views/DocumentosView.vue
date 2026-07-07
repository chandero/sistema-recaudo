"""
Vista para generación de documentos y gestión de plantillas
Permite subir plantillas DOCX, generar documentos individuales o masivos
"""
<template>
  <div class="p-4">
    <h2 class="text-2xl font-bold mb-4 text-gray-800">Gestión Documental</h2>

    <!-- Pestañas -->
    <TabView>
      <TabPanel header="Plantillas">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold">Plantillas Disponibles</h3>
          <Button label="Nueva Plantilla" icon="pi pi-plus" @click="showNewTemplateDialog = true" />
        </div>

        <DataTable :value="templates" stripedRows responsiveLayout="scroll">
          <Column field="name" header="Nombre"></Column>
          <Column field="code" header="Código"></Column>
          <Column field="version" header="Versión"></Column>
          <Column field="created_at" header="Fecha Creación">
            <template #body="slotProps">
              {{ formatDate(slotProps.data.created_at) }}
            </template>
          </Column>
          <Column header="Acciones">
            <template #body="slotProps">
              <Button icon="pi pi-download" class="p-button-rounded p-button-success mr-2" 
                      title="Descargar Plantilla" />
              <Button icon="pi pi-file-pdf" class="p-button-rounded p-button-info" 
                      title="Generar Documento" 
                      @click="openGenerateDialog(slotProps.data)" />
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <TabPanel header="Generar Documentos">
        <div class="grid">
          <div class="col-12 md:col-6">
            <Card>
              <template #title>Generación Individual</template>
              <template #content>
                <div class="field mb-3">
                  <label for="templateSelect" class="block mb-2">Plantilla</label>
                  <Dropdown id="templateSelect" v-model="selectedTemplate" 
                            :options="templates" optionLabel="name" 
                            placeholder="Seleccione plantilla" class="w-full" />
                </div>
                <div class="field mb-3">
                  <label for="processSelect" class="block mb-2">Proceso/Cartera</label>
                  <Dropdown id="processSelect" v-model="selectedProcess" 
                            :options="processes" optionLabel="radicado_number" 
                            optionValue="id" placeholder="Seleccione proceso" class="w-full" />
                </div>
                <Button label="Generar PDF" icon="pi pi-file" class="w-full" 
                        @click="generateSingleDocument" :loading="generating" />
              </template>
            </Card>
          </div>

          <div class="col-12 md:col-6">
            <Card>
              <template #title>Generación Masiva</template>
              <template #content>
                <div class="field mb-3">
                  <label class="block mb-2">Seleccionar Procesos</label>
                  <Listbox v-model="selectedProcesses" :options="processes" 
                           optionLabel="radicado_number" optionValue="id" 
                           multiple filter class="w-full" style="height: 200px" />
                </div>
                <div class="alert alert-info mb-3 text-sm">
                  <i class="pi pi-info-circle"></i> 
                  Se generarán {{ selectedProcesses.length }} documentos en un archivo ZIP
                </div>
                <Button label="Generar Lote ZIP" icon="pi pi-download" class="w-full" 
                        @click="generateBatchDocuments" :loading="generating" />
              </template>
            </Card>
          </div>
        </div>
      </TabPanel>

      <TabPanel header="Documentos Generados">
        <DataTable :value="generatedDocs" stripedRows responsiveLayout="scroll">
          <Column field="id" header="#"></Column>
          <Column field="template_name" header="Plantilla"></Column>
          <Column field="radicado" header="Radicado"></Column>
          <Column field="created_at" header="Fecha Generación">
            <template #body="slotProps">
              {{ formatDate(slotProps.data.created_at) }}
            </template>
          </Column>
          <Column header="Descarga">
            <template #body>
              <Button icon="pi pi-download" class="p-button-rounded p-button-sm" />
            </template>
          </Column>
        </DataTable>
      </TabPanel>
    </TabView>

    <!-- Dialog Nueva Plantilla -->
    <Dialog v-model:visible="showNewTemplateDialog" modal header="Nueva Plantilla Documental" 
            :style="{ width: '500px' }">
      <div class="flex flex-col gap-4">
        <div class="field">
          <label for="tplName" class="block mb-2">Nombre</label>
          <InputText id="tplName" v-model="newTemplate.name" class="w-full" />
        </div>
        <div class="field">
          <label for="tplCode" class="block mb-2">Código Único</label>
          <InputText id="tplCode" v-model="newTemplate.code" class="w-full" />
        </div>
        <div class="field">
          <label for="tplFile" class="block mb-2">Archivo DOCX</label>
          <input type="file" id="tplFile" @change="onFileSelect" accept=".docx" class="block w-full" />
        </div>
        <div class="field">
          <label for="tplVars" class="block mb-2">Variables (JSON)</label>
          <Textarea id="tplVars" v-model="newTemplate.variables_schema" rows="5" 
                    class="w-full font-mono text-sm" 
                    placeholder='{"cliente_nombre": "", "valor_total": 0}' />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" @click="showNewTemplateDialog = false" 
                class="p-button-text" />
        <Button label="Guardar" icon="pi pi-check" @click="saveTemplate" :loading="saving" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const toast = useToast();

// Estado
const templates = ref([]);
const processes = ref([]);
const generatedDocs = ref([]);
const showNewTemplateDialog = ref(false);
const generating = ref(false);
const saving = ref(false);

// Formularios
const newTemplate = ref({
  name: '',
  code: '',
  variables_schema: '{}'
});
const selectedTemplate = ref(null);
const selectedProcess = ref(null);
const selectedProcesses = ref([]);
const selectedFile = ref(null);

// Cargar datos
const loadTemplates = async () => {
  try {
    const res = await api.get('/documents/templates');
    templates.value = res.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar las plantillas' });
  }
};

const loadProcesses = async () => {
  try {
    // Simulado - debería venir del endpoint de procesos
    processes.value = [
      { id: 1, radicado_number: 'RAD-2024-001', client_name: 'Juan Pérez' },
      { id: 2, radicado_number: 'RAD-2024-002', client_name: 'María Gómez' },
      { id: 3, radicado_number: 'RAD-2024-003', client_name: 'Empresa XYZ' }
    ];
  } catch (error) {
    console.error('Error cargando procesos', error);
  }
};

// Manejadores
const onFileSelect = (event) => {
  selectedFile.value = event.target.files[0];
};

const saveTemplate = async () => {
  if (!selectedFile.value) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'Seleccione un archivo DOCX' });
    return;
  }

  const formData = new FormData();
  formData.append('name', newTemplate.value.name);
  formData.append('code', newTemplate.value.code);
  formData.append('variables_schema', newTemplate.value.variables_schema);
  formData.append('file', selectedFile.value);

  saving.value = true;
  try {
    await api.post('/documents/templates', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    toast.add({ severity: 'success', summary: 'Éxito', detail: 'Plantilla guardada' });
    showNewTemplateDialog.value = false;
    loadTemplates();
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo guardar la plantilla' });
  } finally {
    saving.value = false;
  }
};

const openGenerateDialog = (template) => {
  selectedTemplate.value = template;
  // Cambiar a pestaña de generación
};

const generateSingleDocument = async () => {
  if (!selectedTemplate.value || !selectedProcess.value) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'Seleccione plantilla y proceso' });
    return;
  }

  generating.value = true;
  try {
    await api.post('/documents/generate', {
      template_id: selectedTemplate.value.id,
      process_id: selectedProcess.value,
      variables: {}
    });
    toast.add({ severity: 'success', summary: 'Éxito', detail: 'Documento generado' });
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo generar el documento' });
  } finally {
    generating.value = false;
  }
};

const generateBatchDocuments = async () => {
  if (selectedProcesses.value.length === 0) {
    toast.add({ severity: 'warn', summary: 'Advertencia', detail: 'Seleccione al menos un proceso' });
    return;
  }

  generating.value = true;
  try {
    const response = await api.post('/documents/generate/batch', {
      template_id: selectedTemplate.value?.id || templates.value[0]?.id,
      process_ids: selectedProcesses.value
    }, { responseType: 'blob' });

    // Descargar ZIP
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'lote_documentos.zip');
    document.body.appendChild(link);
    link.click();
    
    toast.add({ severity: 'success', summary: 'Éxito', detail: `Lote de ${selectedProcesses.value.length} documentos generado` });
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo generar el lote' });
  } finally {
    generating.value = false;
  }
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('es-CO');
};

onMounted(() => {
  loadTemplates();
  loadProcesses();
});
</script>

<style scoped>
.alert {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.alert-info {
  background-color: #e3f2fd;
  color: #0d47a1;
  border-left: 4px solid #2196f3;
}
</style>
