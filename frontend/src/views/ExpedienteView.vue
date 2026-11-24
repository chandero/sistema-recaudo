<template>
  <div class="expediente-view">
    <!-- Header -->
    <div class="expediente-header">
      <div class="header-left">
        <Button icon="pi pi-arrow-left" label="Volver a Procesos" text @click="$router.push('/procesos')" />
        <div class="header-title">
          <h1>Expediente: {{ expedient?.process?.reference || 'Cargando...' }}</h1>
          <Tag
            v-if="expedient?.state_name"
            :value="expedient.state_name"
            :severity="getStateSeverity(expedient.state_code)"
          />
        </div>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Actualizar"
        :loading="loading"
        @click="loadExpedient"
        outlined
      />
    </div>

    <!-- Loading -->
    <div v-if="loading && !expedient" class="loading-container">
      <ProgressSpinner />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-container">
      <Message severity="error">{{ error }}</Message>
    </div>

    <!-- Content -->
    <div v-else-if="expedient" class="expediente-content">
      <!-- Client Info Bar -->
      <Card class="client-bar">
        <template #content>
          <div class="client-info-grid">
            <div class="info-item">
              <span class="info-label">Cliente</span>
              <span class="info-value">{{ expedient.client_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Identificación</span>
              <span class="info-value">{{ expedient.client_identification || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Teléfono</span>
              <span class="info-value">{{ expedient.client_phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Email</span>
              <span class="info-value">{{ expedient.client_email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Dirección</span>
              <span class="info-value">{{ expedient.client_address || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Días en estado</span>
              <span class="info-value" :class="getDaysClass(expedient.days_in_state)">
                {{ expedient.days_in_state }} días
              </span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Tabs -->
      <TabView class="expediente-tabs">
        <!-- Resumen Tab -->
        <TabPanel header="Resumen">
          <div class="tab-content">
            <div class="summary-grid">
              <Card>
                <template #title>Datos del Proceso</template>
                <template #content>
                  <div class="detail-list">
                    <div class="detail-row">
                      <span class="detail-label">Referencia:</span>
                      <span class="detail-value">{{ expedient.process.reference }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Estado actual:</span>
                      <Tag :value="expedient.state_name" :severity="getStateSeverity(expedient.state_code)" />
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Estado código:</span>
                      <span class="detail-value">{{ expedient.state_code }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Días en estado:</span>
                      <span class="detail-value">{{ expedient.days_in_state }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Fecha creación:</span>
                      <span class="detail-value">{{ formatDate(expedient.process.created_at) }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Última actualización:</span>
                      <span class="detail-value">{{ formatDate(expedient.process.updated_at) }}</span>
                    </div>
                    <div v-if="expedient.process.observation" class="detail-row">
                      <span class="detail-label">Observación:</span>
                      <span class="detail-value">{{ expedient.process.observation }}</span>
                    </div>
                  </div>
                </template>
              </Card>

              <Card>
                <template #title>Resumen Financiero</template>
                <template #content>
                  <div class="financial-summary">
                    <div class="fin-item">
                      <span class="fin-label">Total obligaciones</span>
                      <span class="fin-value">{{ expedient.obligations.length }}</span>
                    </div>
                    <div class="fin-item">
                      <span class="fin-label">Valor total</span>
                      <span class="fin-value">${{ formatCurrency(totalObligationAmount) }}</span>
                    </div>
                    <div class="fin-item">
                      <span class="fin-label">Obligaciones vencidas</span>
                      <span class="fin-value text-red">{{ overdueCount }}</span>
                    </div>
                    <div class="fin-item">
                      <span class="fin-label">Obligaciones pagadas</span>
                      <span class="fin-value text-green">{{ paidCount }}</span>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </TabPanel>

        <!-- Obligaciones Tab -->
        <TabPanel header="Obligaciones">
          <div class="tab-content">
            <DataTable :value="expedient.obligations" stripedRows size="small"
              v-if="expedient.obligations.length > 0">
              <Column field="id" header="ID" style="width: 60px"></Column>
              <Column field="description" header="Descripción"></Column>
              <Column field="type" header="Tipo">
                <template #body="slotProps">
                  <Tag :value="slotProps.data.type" severity="secondary" />
                </template>
              </Column>
              <Column field="amount" header="Valor">
                <template #body="slotProps">
                  ${{ formatCurrency(slotProps.data.amount) }}
                </template>
              </Column>
              <Column field="currency" header="Moneda" style="width: 80px"></Column>
              <Column field="status" header="Estado">
                <template #body="slotProps">
                  <Tag :value="slotProps.data.status" :severity="getObligationSeverity(slotProps.data.status)" />
                </template>
              </Column>
              <Column field="due_date" header="Vencimiento">
                <template #body="slotProps">
                  {{ formatDate(slotProps.data.due_date) }}
                </template>
              </Column>
              <Column field="resolution_number" header="Resolución">
                <template #body="slotProps">
                  {{ slotProps.data.resolution_number || '-' }}
                </template>
              </Column>
              <Column field="radicado_number" header="Radicado">
                <template #body="slotProps">
                  {{ slotProps.data.radicado_number || '-' }}
                </template>
              </Column>
            </DataTable>
            <div v-else class="empty-tab">
              <i class="pi pi-file" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay obligaciones registradas</p>
            </div>
          </div>
        </TabPanel>

        <!-- Documentos Tab -->
        <TabPanel header="Documentos">
          <div class="tab-content">
            <div class="tab-toolbar" v-if="expedient.documents.length > 0">
              <Button
                icon="pi pi-download"
                label="Descargar todos"
                outlined
                size="small"
                @click="downloadAllDocuments"
              />
            </div>
            <DataTable :value="expedient.documents" stripedRows size="small"
              v-if="expedient.documents.length > 0">
              <Column field="filename" header="Nombre del archivo"></Column>
              <Column field="document_type" header="Tipo" style="width: 100px">
                <template #body="slotProps">
                  <Tag :value="slotProps.data.document_type" severity="info" />
                </template>
              </Column>
              <Column field="file_size" header="Tamaño" style="width: 100px">
                <template #body="slotProps">
                  {{ formatFileSize(slotProps.data.file_size) }}
                </template>
              </Column>
              <Column field="resolution_number" header="Resolución" style="width: 130px">
                <template #body="slotProps">
                  {{ slotProps.data.resolution_number || '-' }}
                </template>
              </Column>
              <Column field="created_by_name" header="Generado por" style="width: 150px">
                <template #body="slotProps">
                  {{ slotProps.data.created_by_name || '-' }}
                </template>
              </Column>
              <Column field="created_at" header="Fecha" style="width: 140px">
                <template #body="slotProps">
                  {{ formatDate(slotProps.data.created_at) }}
                </template>
              </Column>
              <Column field="is_sent" header="Enviado" style="width: 90px">
                <template #body="slotProps">
                  <i :class="slotProps.data.is_sent ? 'pi pi-check text-green' : 'pi pi-times text-red'"></i>
                </template>
              </Column>
            </DataTable>
            <div v-else class="empty-tab">
              <i class="pi pi-file" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay documentos generados</p>
            </div>
          </div>
        </TabPanel>

        <!-- Notas Tab -->
        <TabPanel header="Notas y Actuaciones">
          <div class="tab-content">
            <!-- New Note Form -->
            <Card class="new-note-card">
              <template #title>Nueva Nota</template>
              <template #content>
                <div class="note-form">
                  <div class="note-form-row">
                    <InputText
                      v-model="newNote.title"
                      placeholder="Título de la nota"
                      class="note-title-input"
                    />
                    <Dropdown
                      v-model="newNote.note_type"
                      :options="noteTypes"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Tipo"
                      class="note-type-dropdown"
                    />
                  </div>
                  <Textarea
                    v-model="newNote.content"
                    placeholder="Contenido de la nota..."
                    rows="3"
                    class="note-content-input"
                  />
                  <div class="note-form-actions">
                    <Checkbox v-model="newNote.is_pinned" :binary="true" inputId="pinNote" />
                    <label for="pinNote" class="ml-2 mr-3">Fijar nota</label>
                    <Button
                      label="Guardar Nota"
                      icon="pi pi-save"
                      :loading="savingNote"
                      :disabled="!newNote.title || !newNote.content"
                      @click="saveNote"
                      size="small"
                    />
                  </div>
                </div>
              </template>
            </Card>

            <!-- Notes List -->
            <div class="notes-list" v-if="expedient.notes.length > 0">
              <div
                v-for="note in expedient.notes"
                :key="note.id"
                class="note-item"
                :class="{ 'note-pinned': note.is_pinned }"
              >
                <div class="note-header">
                  <div class="note-meta">
                    <i v-if="note.is_pinned" class="pi pi-bookmark note-pin-icon"></i>
                    <Tag :value="getNoteTypeLabel(note.note_type)" :severity="getNoteTypeSeverity(note.note_type)" size="small" />
                    <span class="note-author">{{ note.user_name || 'Sistema' }}</span>
                    <span class="note-date">{{ formatDateTime(note.created_at) }}</span>
                  </div>
                </div>
                <h4 class="note-title">{{ note.title }}</h4>
                <p class="note-content">{{ note.content }}</p>
              </div>
            </div>
            <div v-else class="empty-tab">
              <i class="pi pi-comment" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay notas registradas</p>
            </div>
          </div>
        </TabPanel>

        <!-- Historial Tab -->
        <TabPanel header="Historial">
          <div class="tab-content">
            <div class="timeline" v-if="expedient.timeline.length > 0">
              <div
                v-for="entry in expedient.timeline"
                :key="entry.id"
                class="timeline-item"
              >
                <div class="timeline-marker">
                  <i class="pi pi-circle-fill"></i>
                </div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <Tag :value="entry.action" severity="info" size="small" />
                    <span class="timeline-date">{{ formatDateTime(entry.created_at) }}</span>
                  </div>
                  <div class="timeline-body">
                    <p v-if="entry.description">{{ entry.description }}</p>
                    <div v-if="entry.previous_state_name || entry.new_state_name" class="state-change">
                      <span v-if="entry.previous_state_name" class="prev-state">{{ entry.previous_state_name }}</span>
                      <i v-if="entry.previous_state_name && entry.new_state_name" class="pi pi-arrow-right mx-2"></i>
                      <span v-if="entry.new_state_name" class="new-state">{{ entry.new_state_name }}</span>
                    </div>
                    <span v-if="entry.user_name" class="timeline-user">
                      <i class="pi pi-user"></i> {{ entry.user_name }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-tab">
              <i class="pi pi-history" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay historial de actuaciones</p>
            </div>
          </div>
        </TabPanel>

        <!-- Acuerdos de Pago Tab -->
        <TabPanel header="Acuerdos de Pago">
          <div class="tab-content">
            <div class="tab-actions-bar">
              <Button label="Nuevo Acuerdo" icon="pi pi-plus" size="small" @click="openExpedientAgreementCreate" />
            </div>
            <DataTable v-if="expedientAgreements.length" :value="expedientAgreements" stripedRows :loading="agreementsLoading">
              <Column field="agreement_number" header="N° Acuerdo" style="width: 140px" />
              <Column field="status" header="Estado" style="width: 120px">
                <template #body="s">
                  <Tag :value="s.data.status" :severity="getAgreementSeverity(s.data.status)" />
                </template>
              </Column>
              <Column field="total_agreed" header="Valor Acordado" style="width: 140px">
                <template #body="s">${{ formatCurrencyShort(s.data.total_agreed) }}</template>
              </Column>
              <Column field="installment_count" header="Cuotas" style="width: 80px" />
              <Column field="installment_amount" header="Valor Cuota" style="width: 130px">
                <template #body="s">${{ formatCurrencyShort(s.data.installment_amount) }}</template>
              </Column>
              <Column field="first_payment_date" header="Primera Cuota" style="width: 130px">
                <template #body="s">{{ formatDate(s.data.first_payment_date) }}</template>
              </Column>
              <Column header="Acción" style="width: 100px">
                <template #body="s">
                  <Button icon="pi pi-eye" text severity="info" size="small" @click="viewExpedientAgreement(s.data)" v-tooltip="'Ver detalle'" />
                </template>
              </Column>
            </DataTable>
            <div v-else-if="!agreementsLoading" class="empty-tab">
              <i class="pi pi-handshake" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay acuerdos de pago registrados</p>
              <Button label="Crear Acuerdo" icon="pi pi-plus" @click="openExpedientAgreementCreate" outlined />
            </div>
          </div>
        </TabPanel>
      </TabView>
    </div>

    <!-- Agreement Create Dialog -->
    <Dialog v-model:visible="expAgreementCreateVisible" header="Nuevo Acuerdo de Pago" :modal="true" style="width: 550px">
      <div class="form-grid">
        <div class="field">
          <label>Deuda Total</label>
          <InputNumber v-model="expNewAgreement.total_debt" :min="0" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Valor Acordado</label>
          <InputNumber v-model="expNewAgreement.total_agreed" :min="0" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Número de Cuotas</label>
          <InputNumber v-model="expNewAgreement.installment_count" :min="1" :max="120" class="w-full" />
        </div>
        <div class="field">
          <label>Tasa de Interés (%)</label>
          <InputNumber v-model="expNewAgreement.interest_rate" :min="0" :max="100" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Fecha Primera Cuota</label>
          <Calendar v-model="expNewAgreement.first_payment_date" dateFormat="yy-mm-dd" showIcon class="w-full" />
        </div>
        <div class="field">
          <label>Día de Pago (1-31)</label>
          <InputNumber v-model="expNewAgreement.payment_day" :min="1" :max="31" class="w-full" />
        </div>
        <div class="field full-width">
          <label>Observaciones</label>
          <Textarea v-model="expNewAgreement.observations" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="expAgreementCreateVisible = false" />
        <Button label="Crear" icon="pi pi-save" :loading="agreementsLoading" @click="createExpedientAgreement" :disabled="!expNewAgreement.total_agreed || expNewAgreement.total_agreed <= 0" />
      </template>
    </Dialog>

    <!-- Agreement Detail Dialog -->
    <Dialog v-model:visible="expAgreementDetailVisible" :header="`Acuerdo: ${expAgreementDetail?.agreement_number || ''}`" :modal="true" style="width: 750px">
      <div v-if="expAgreementDetail">
        <div class="detail-grid-info">
          <div class="detail-item"><span class="detail-label">Estado</span><Tag :value="expAgreementDetail.status" :severity="getAgreementSeverity(expAgreementDetail.status)" /></div>
          <div class="detail-item"><span class="detail-label">Deuda Total</span><strong>${{ formatCurrencyShort(expAgreementDetail.total_debt) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Valor Acordado</span><strong>${{ formatCurrencyShort(expAgreementDetail.total_agreed) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Cuotas</span><strong>{{ expAgreementDetail.installment_count }} x ${{ formatCurrencyShort(expAgreementDetail.installment_amount) }}</strong></div>
        </div>
        <h3 style="margin-top: 1.5rem">Cuotas</h3>
        <DataTable :value="expAgreementDetail.installments || []" stripedRows size="small">
          <Column field="installment_number" header="#" style="width: 50px" />
          <Column field="due_date" header="Vencimiento"><template #body="s">{{ formatDate(s.data.due_date) }}</template></Column>
          <Column field="amount" header="Valor"><template #body="s">${{ formatCurrencyShort(s.data.amount) }}</template></Column>
          <Column field="paid_amount" header="Pagado"><template #body="s">${{ formatCurrencyShort(s.data.paid_amount) }}</template></Column>
          <Column field="status" header="Estado"><template #body="s"><Tag :value="s.data.status" :severity="getInstallmentSeverity(s.data.status)" size="small" /></template></Column>
          <Column header="Acción" style="width: 80px">
            <template #body="s">
              <Button v-if="s.data.status !== 'PAGADA'" icon="pi pi-dollar" text size="small" severity="success" @click="openExpPayInstallment(s.data)" v-tooltip="'Pagar'" />
            </template>
          </Column>
        </DataTable>
      </div>
      <template #footer>
        <Button v-if="expAgreementDetail?.status === 'PROPUESTA'" label="Aceptar" icon="pi pi-check" severity="success" @click="acceptExpedientAgreement" :loading="agreementsLoading" />
        <Button v-if="expAgreementDetail?.status === 'VIGENTE'" label="Cancelar" icon="pi pi-times" severity="danger" text @click="cancelExpedientAgreement" />
        <Button label="Cerrar" icon="pi pi-times" text @click="expAgreementDetailVisible = false" />
      </template>
    </Dialog>

    <!-- Pay Installment Dialog -->
    <Dialog v-model:visible="expAgreementPayVisible" header="Registrar Pago de Cuota" :modal="true" style="width: 400px">
      <div v-if="expSelectedInstallment" class="form-grid">
        <div class="field">
          <label>Cuota #{{ expSelectedInstallment.installment_number }}</label>
          <span class="info-text">Vence: {{ formatDate(expSelectedInstallment.due_date) }}</span>
        </div>
        <div class="field">
          <label>Valor cuota</label>
          <strong>${{ formatCurrencyShort(expSelectedInstallment.amount) }}</strong>
        </div>
        <div class="field">
          <label>Valor a pagar</label>
          <InputNumber v-model="expPayAmount" :min="1" :max="expSelectedInstallment.amount - expSelectedInstallment.paid_amount" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field full-width">
          <label>Observaciones</label>
          <Textarea v-model="expPayObservations" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="expAgreementPayVisible = false" />
        <Button label="Registrar Pago" icon="pi pi-check" :loading="agreementsLoading" @click="processExpInstallmentPayment" :disabled="!expPayAmount || expPayAmount <= 0" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { processService, agreementService } from '../services/api'

const toast = useToast()
const route = useRoute()
const processId = route.params.id

const expedient = ref(null)
const loading = ref(false)
const error = ref(null)
const savingNote = ref(false)

const newNote = reactive({
  title: '',
  content: '',
  note_type: 'general',
  is_pinned: false,
})

const noteTypes = [
  { label: 'General', value: 'general' },
  { label: 'Gestión', value: 'gestion' },
  { label: 'Compromiso', value: 'compromiso' },
  { label: 'Recordatorio', value: 'recordatorio' },
]

// Computed
const totalObligationAmount = computed(() => {
  if (!expedient.value?.obligations) return 0
  return expedient.value.obligations.reduce((sum, o) => sum + (o.amount || 0), 0)
})

const overdueCount = computed(() => {
  if (!expedient.value?.obligations) return 0
  return expedient.value.obligations.filter(o => o.status === 'overdue').length
})

const paidCount = computed(() => {
  if (!expedient.value?.obligations) return 0
  return expedient.value.obligations.filter(o => o.status === 'paid').length
})

// Methods
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('es-CO', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('es-CO', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '0'
  return Math.round(value).toLocaleString('es-CO')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

const getStateSeverity = (code) => {
  if (!code) return 'info'
  const finalStates = ['PAGADO', 'ARCHIVADO', 'INCOBRABLE']
  if (finalStates.includes(code)) return 'success'
  if (code.includes('COBRO')) return 'warning'
  if (code.includes('NOTIFICACION')) return 'info'
  return 'info'
}

const getObligationSeverity = (status) => {
  const map = { paid: 'success', overdue: 'danger', pending: 'warning', active: 'info' }
  return map[status] || 'info'
}

const getNoteTypeLabel = (type) => {
  const map = { general: 'General', gestion: 'Gestión', compromiso: 'Compromiso', recordatorio: 'Recordatorio' }
  return map[type] || type
}

const getNoteTypeSeverity = (type) => {
  const map = { general: 'info', gestion: 'warning', compromiso: 'danger', recordatorio: 'success' }
  return map[type] || 'info'
}

const getDaysClass = (days) => {
  if (days <= 15) return 'days-ok'
  if (days <= 30) return 'days-warn'
  return 'days-danger'
}

const loadExpedient = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await processService.getExpedient(processId)
    expedient.value = response.data
  } catch (err) {
    console.error('Error loading expedient:', err)
    error.value = 'Error al cargar el expediente. Por favor, intente nuevamente.'
  } finally {
    loading.value = false
  }
}

const saveNote = async () => {
  if (!newNote.title || !newNote.content) return
  savingNote.value = true
  try {
    await processService.createNote(processId, {
      title: newNote.title,
      content: newNote.content,
      note_type: newNote.note_type,
      is_pinned: newNote.is_pinned,
    })
    newNote.title = ''
    newNote.content = ''
    newNote.note_type = 'general'
    newNote.is_pinned = false
    await loadExpedient()
  } catch (err) {
    console.error('Error saving note:', err)
  } finally {
    savingNote.value = false
  }
}

const downloadAllDocuments = () => {
  // Placeholder for mass download (ZIP) — will be implemented in FASE 4.3
  console.log('Download all documents — to be implemented with ZIP generation')
}

onMounted(() => {
  loadExpedient()
  loadExpedientAgreements()
})

// --- Agreement management ---
const expedientAgreements = ref([])
const agreementsLoading = ref(false)
const expAgreementCreateVisible = ref(false)
const expAgreementDetailVisible = ref(false)
const expAgreementPayVisible = ref(false)
const expAgreementDetail = ref(null)
const expSelectedInstallment = ref(null)
const expPayAmount = ref(0)
const expPayObservations = ref('')
const expNewAgreement = ref({
  total_debt: 0, total_agreed: 0, interest_rate: 0,
  installment_count: 1, first_payment_date: new Date(), payment_day: 1,
  grace_period_months: 0, default_interest_rate: 0, observations: '',
})

const formatCurrencyShort = (v) => {
  if (v === null || v === undefined) return '0'
  return Math.round(v).toLocaleString('es-CO')
}

const getAgreementSeverity = (s) => {
  const map = { PROPUESTA: 'info', VIGENTE: 'success', CUMPLIDO: 'success', INCUMPLIDO: 'danger', CANCELADO: 'secondary' }
  return map[s] || 'info'
}

const getInstallmentSeverity = (s) => {
  const map = { PENDIENTE: 'warning', PAGADA: 'success', VENCIDA: 'danger', PARCIAL: 'info' }
  return map[s] || 'info'
}

const loadExpedientAgreements = async () => {
  agreementsLoading.value = true
  try {
    const resp = await agreementService.getAll({ process_id: processId })
    expedientAgreements.value = resp.data || []
  } catch (e) {
    console.error('Error loading agreements:', e)
  } finally {
    agreementsLoading.value = false
  }
}

const openExpedientAgreementCreate = () => {
  const totalObl = expedient.value?.obligations?.reduce((sum, o) => sum + (o.amount || 0), 0) || 0
  expNewAgreement.value = {
    total_debt: totalObl, total_agreed: totalObl, interest_rate: 0,
    installment_count: 1, first_payment_date: new Date(), payment_day: 1,
    grace_period_months: 0, default_interest_rate: 0, observations: '',
  }
  expAgreementCreateVisible.value = true
}

const createExpedientAgreement = async () => {
  agreementsLoading.value = true
  try {
    await agreementService.create({
      process_id: parseInt(processId),
      ...expNewAgreement.value,
      first_payment_date: new Date(expNewAgreement.value.first_payment_date).toISOString().split('T')[0],
    })
    expAgreementCreateVisible.value = false
    toast.add({ severity: 'success', summary: 'Acuerdo creado', life: 3000 })
    await loadExpedientAgreements()
    await loadExpedient()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo crear el acuerdo', life: 5000 })
  } finally {
    agreementsLoading.value = false
  }
}

const viewExpedientAgreement = async (agreement) => {
  try {
    const resp = await agreementService.getById(agreement.id)
    expAgreementDetail.value = resp.data
    expAgreementDetailVisible.value = true
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cargar el detalle', life: 3000 })
  }
}

const acceptExpedientAgreement = async () => {
  if (!expAgreementDetail.value) return
  agreementsLoading.value = true
  try {
    await agreementService.accept(expAgreementDetail.value.id)
    toast.add({ severity: 'success', summary: 'Acuerdo aceptado', life: 3000 })
    expAgreementDetailVisible.value = false
    await loadExpedientAgreements()
    await loadExpedient()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo aceptar', life: 5000 })
  } finally {
    agreementsLoading.value = false
  }
}

const cancelExpedientAgreement = async () => {
  if (!expAgreementDetail.value) return
  if (!confirm('¿Cancelar este acuerdo?')) return
  agreementsLoading.value = true
  try {
    await agreementService.cancel(expAgreementDetail.value.id)
    toast.add({ severity: 'warn', summary: 'Acuerdo cancelado', life: 3000 })
    expAgreementDetailVisible.value = false
    await loadExpedientAgreements()
    await loadExpedient()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo cancelar', life: 5000 })
  } finally {
    agreementsLoading.value = false
  }
}

const openExpPayInstallment = (installment) => {
  expSelectedInstallment.value = installment
  expPayAmount.value = installment.amount - installment.paid_amount
  expPayObservations.value = ''
  expAgreementPayVisible.value = true
}

const processExpInstallmentPayment = async () => {
  if (!expSelectedInstallment.value || !expAgreementDetail.value) return
  agreementsLoading.value = true
  try {
    await agreementService.payInstallment(expAgreementDetail.value.id, expSelectedInstallment.value.id, {
      paid_amount: expPayAmount.value,
      observations: expPayObservations.value,
    })
    expAgreementPayVisible.value = false
    toast.add({ severity: 'success', summary: 'Pago registrado', life: 3000 })
    const resp = await agreementService.getById(expAgreementDetail.value.id)
    expAgreementDetail.value = resp.data
    await loadExpedientAgreements()
    await loadExpedient()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo registrar el pago', life: 5000 })
  } finally {
    agreementsLoading.value = false
  }
}
</script>

<style scoped>
.expediente-view {
  padding: 2rem;
}

.expediente-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-left: 0.5rem;
}

.header-title h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.loading-container, .error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.client-bar {
  margin-bottom: 1.5rem;
  border-radius: 12px;
}

.client-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.info-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-color);
}

.days-ok { color: var(--green-600); }
.days-warn { color: var(--orange-600); }
.days-danger { color: var(--red-600); font-weight: 700; }

.expediente-tabs {
  border-radius: 12px;
}

.tab-content {
  padding: 1rem 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-weight: 600;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.detail-value {
  color: var(--text-color);
  font-weight: 500;
}

.financial-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.fin-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fin-label {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

.fin-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
}

.text-green { color: var(--green-600); }
.text-red { color: var(--red-600); }

.tab-toolbar {
  margin-bottom: 1rem;
  display: flex;
  gap: 0.5rem;
}

.empty-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--text-color-secondary);
}

.empty-tab p {
  margin-top: 1rem;
}

.tab-actions-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.detail-grid-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
  text-transform: uppercase;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-grid .full-width {
  grid-column: 1 / -1;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-color);
}

.info-text {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

/* Notes */
.new-note-card {
  margin-bottom: 1.5rem;
  border: 2px dashed var(--surface-300);
  border-radius: 12px;
}

.note-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.note-form-row {
  display: flex;
  gap: 1rem;
}

.note-title-input {
  flex: 1;
}

.note-type-dropdown {
  width: 160px;
}

.note-content-input {
  width: 100%;
}

.note-form-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.note-item {
  border: 1px solid var(--surface-200);
  border-radius: 8px;
  padding: 1rem;
  background: var(--surface-0);
}

.note-pinned {
  border-left: 4px solid var(--yellow-500);
  background: var(--yellow-50);
}

.note-header {
  margin-bottom: 0.5rem;
}

.note-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.note-pin-icon {
  color: var(--yellow-500);
  font-size: 0.9rem;
}

.note-author {
  font-weight: 600;
  color: var(--text-color);
  font-size: 0.875rem;
}

.note-date {
  color: var(--text-color-secondary);
  font-size: 0.8rem;
}

.note-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
}

.note-content {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 2rem;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 0.55rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--surface-300);
}

.timeline-item {
  position: relative;
  margin-bottom: 1.5rem;
}

.timeline-marker {
  position: absolute;
  left: -1.55rem;
  top: 0.25rem;
  color: var(--primary-color);
  font-size: 0.7rem;
}

.timeline-content {
  border: 1px solid var(--surface-200);
  border-radius: 8px;
  padding: 1rem;
  background: var(--surface-0);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.timeline-date {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
}

.timeline-body p {
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
  font-size: 0.9rem;
}

.state-change {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.prev-state {
  color: var(--red-500);
  font-weight: 500;
}

.new-state {
  color: var(--green-500);
  font-weight: 500;
}

.timeline-user {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
}

.timeline-user i {
  font-size: 0.75rem;
}

@media (max-width: 768px) {
  .summary-grid, .financial-summary {
    grid-template-columns: 1fr;
  }

  .expediente-header {
    flex-direction: column;
    gap: 1rem;
  }

  .note-form-row {
    flex-direction: column;
  }

  .note-type-dropdown {
    width: 100%;
  }
}
</style>
