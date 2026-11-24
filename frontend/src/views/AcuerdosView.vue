<template>
  <div class="acuerdos-view">
    <PageHeader title="Acuerdos de Pago" subtitle="Gestione los acuerdos de pago con deudores">
      <template #actions>
        <Button label="Nuevo Acuerdo" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="filters-bar">
      <Dropdown
        v-model="filterStatus"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Todos los estados"
        showClear
        class="status-filter"
        @change="loadAgreements"
      />
    </div>

    <!-- Table -->
    <DataTable :value="agreements" stripedRows :loading="loading" paginator :rows="20">
      <Column field="agreement_number" header="N° Acuerdo" style="width: 140px"></Column>
      <Column field="process_id" header="Proceso" style="width: 80px"></Column>
      <Column field="status" header="Estado" style="width: 130px">
        <template #body="slotProps">
          <Tag :value="slotProps.data.status" :severity="getAgreementSeverity(slotProps.data.status)" />
        </template>
      </Column>
      <Column field="total_debt" header="Deuda Total" style="width: 140px">
        <template #body="slotProps">
          ${{ formatCurrency(slotProps.data.total_debt) }}
        </template>
      </Column>
      <Column field="total_agreed" header="Valor Acordado" style="width: 140px">
        <template #body="slotProps">
          ${{ formatCurrency(slotProps.data.total_agreed) }}
        </template>
      </Column>
      <Column field="installment_count" header="Cuotas" style="width: 80px"></Column>
      <Column field="installment_amount" header="Valor Cuota" style="width: 130px">
        <template #body="slotProps">
          ${{ formatCurrency(slotProps.data.installment_amount) }}
        </template>
      </Column>
      <Column field="first_payment_date" header="Primera Cuota" style="width: 130px">
        <template #body="slotProps">
          {{ formatDate(slotProps.data.first_payment_date) }}
        </template>
      </Column>
      <Column header="Acciones" style="width: 120px">
        <template #body="slotProps">
          <Button icon="pi pi-eye" text severity="info" @click="openDetail(slotProps.data)" v-tooltip="'Ver detalle'" />
          <Button
            v-if="slotProps.data.status === 'PROPUESTA'"
            icon="pi pi-check"
            text
            severity="success"
            @click="acceptAgreement(slotProps.data)"
            v-tooltip="'Aceptar'"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Create Dialog -->
    <Dialog v-model:visible="createDialogVisible" header="Nuevo Acuerdo de Pago" :modal="true" style="width: 600px">
      <div class="form-grid">
        <div class="field full-width">
          <label>Seleccionar Proceso / Obligación</label>
          <Dropdown
            v-model="selectedProcess"
            :options="allProcesses"
            optionLabel="reference"
            :placeholder="processSearchLoading ? 'Cargando procesos...' : 'Seleccione un proceso...'"
            :loading="processSearchLoading"
            class="w-full"
            filter
            filterPlaceholder="Buscar por referencia..."
            :showClear="true"
            @change="onProcessDropdownChange"
          >
            <template #value="slotProps">
              <span v-if="slotProps.value">{{ slotProps.value.reference }}</span>
              <span v-else>{{ placeholder || 'Seleccione un proceso...' }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex align-items-center" style="gap: 0.5rem">
                <span>{{ slotProps.option.reference }}</span>
                <span v-if="slotProps.option.obligation_amount" style="color: var(--text-color-secondary); font-size: 0.85rem">
                  - ${{ formatCurrency(slotProps.option.obligation_amount) }}
                </span>
              </div>
            </template>
          </Dropdown>
          <div v-if="newAgreement.process_id" class="process-selected">
            <i class="pi pi-check-circle" style="color: var(--green-500)"></i>
            <span>Proceso seleccionado: {{ selectedProcess?.reference || '#' + newAgreement.process_id }}</span>
          </div>
        </div>
        <div class="field">
          <label>Deuda Total</label>
          <InputNumber v-model="newAgreement.total_debt" :min="0" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Valor Acordado</label>
          <InputNumber v-model="newAgreement.total_agreed" :min="0" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Número de Cuotas</label>
          <InputNumber v-model="newAgreement.installment_count" :min="1" :max="120" class="w-full" />
        </div>
        <div class="field">
          <label>Tasa de Interés (%)</label>
          <InputNumber v-model="newAgreement.interest_rate" :min="0" :max="100" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Fecha Primera Cuota</label>
          <Calendar v-model="newAgreement.first_payment_date" dateFormat="yy-mm-dd" showIcon class="w-full" />
        </div>
        <div class="field">
          <label>Día de Pago (1-31)</label>
          <InputNumber v-model="newAgreement.payment_day" :min="1" :max="31" class="w-full" />
        </div>
        <div class="field">
          <label>Meses de Gracia</label>
          <InputNumber v-model="newAgreement.grace_period_months" :min="0" :max="12" class="w-full" />
        </div>
        <div class="field full-width">
          <label>Observaciones</label>
          <Textarea v-model="newAgreement.observations" rows="3" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="createDialogVisible = false" />
        <Button label="Crear" icon="pi pi-save" :loading="saving" @click="createAgreement" :disabled="!newAgreement.process_id || !newAgreement.total_agreed" />
      </template>
    </Dialog>

    <!-- Detail Dialog -->
    <Dialog v-model:visible="detailDialogVisible" :header="`Acuerdo: ${selectedAgreement?.agreement_number || ''}`" :modal="true" style="width: 800px">
      <div v-if="selectedAgreement" class="detail-content">
        <div class="detail-grid-info">
          <div class="detail-item">
            <span class="detail-label">Estado</span>
            <Tag :value="selectedAgreement.status" :severity="getAgreementSeverity(selectedAgreement.status)" />
          </div>
          <div class="detail-item">
            <span class="detail-label">Deuda Total</span>
            <strong>${{ formatCurrency(selectedAgreement.total_debt) }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Valor Acordado</span>
            <strong>${{ formatCurrency(selectedAgreement.total_agreed) }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Cuotas</span>
            <strong>{{ selectedAgreement.installment_count }} x ${{ formatCurrency(selectedAgreement.installment_amount) }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Tasa Interés</span>
            <strong>{{ selectedAgreement.interest_rate }}%</strong>
          </div>
        </div>

        <h3 style="margin-top: 1.5rem">Cuotas</h3>
        <DataTable :value="selectedAgreement.installments" stripedRows size="small">
          <Column field="installment_number" header="#" style="width: 50px"></Column>
          <Column field="due_date" header="Vencimiento">
            <template #body="slotProps">{{ formatDate(slotProps.data.due_date) }}</template>
          </Column>
          <Column field="amount" header="Valor">
            <template #body="slotProps">${{ formatCurrency(slotProps.data.amount) }}</template>
          </Column>
          <Column field="paid_amount" header="Pagado">
            <template #body="slotProps">${{ formatCurrency(slotProps.data.paid_amount) }}</template>
          </Column>
          <Column field="status" header="Estado">
            <template #body="slotProps">
              <Tag :value="slotProps.data.status" :severity="getInstallmentSeverity(slotProps.data.status)" size="small" />
            </template>
          </Column>
          <Column header="Acción" style="width: 100px">
            <template #body="slotProps">
              <Button
                v-if="slotProps.data.status !== 'PAGADA'"
                icon="pi pi-dollar"
                text
                size="small"
                severity="success"
                @click="openPayDialog(slotProps.data)"
                v-tooltip="'Registrar pago'"
              />
            </template>
          </Column>
        </DataTable>
      </div>
      <template #footer>
        <Button
          v-if="selectedAgreement?.status === 'VIGENTE'"
          label="Cancelar Acuerdo"
          icon="pi pi-times"
          severity="danger"
          text
          @click="cancelAgreement(selectedAgreement)"
        />
        <Button label="Cerrar" icon="pi pi-times" text @click="detailDialogVisible = false" />
      </template>
    </Dialog>

    <!-- Pay Installment Dialog -->
    <Dialog v-model:visible="payDialogVisible" header="Registrar Pago de Cuota" :modal="true" style="width: 400px">
      <div v-if="selectedInstallment" class="form-grid">
        <div class="field">
          <label>Cuota #{{ selectedInstallment.installment_number }}</label>
          <span class="info-text">Vence: {{ formatDate(selectedInstallment.due_date) }}</span>
        </div>
        <div class="field">
          <label>Valor de la cuota</label>
          <strong>${{ formatCurrency(selectedInstallment.amount) }}</strong>
        </div>
        <div class="field">
          <label>Valor a pagar</label>
          <InputNumber v-model="payAmount" :min="1" :max="selectedInstallment.amount" :locale="'es-CO'" mode="decimal" :minFractionDigits="2" class="w-full" />
        </div>
        <div class="field">
          <label>Observaciones</label>
          <Textarea v-model="payObservations" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="payDialogVisible = false" />
        <Button label="Registrar Pago" icon="pi pi-check" :loading="paying" @click="processPayment" :disabled="!payAmount || payAmount <= 0" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { agreementService, processService } from '../services/api'
import PageHeader from '@/components/PageHeader.vue'

const toast = useToast()
const agreements = ref([])
const loading = ref(false)
const filterStatus = ref(null)
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const payDialogVisible = ref(false)
const saving = ref(false)
const paying = ref(false)
const selectedAgreement = ref(null)
const selectedInstallment = ref(null)
const payAmount = ref(0)
const payObservations = ref('')

const statusOptions = [
  { label: 'Propuesta', value: 'PROPUESTA' },
  { label: 'Vigente', value: 'VIGENTE' },
  { label: 'Cumplido', value: 'CUMPLIDO' },
  { label: 'Incumplido', value: 'INCUMPLIDO' },
  { label: 'Cancelado', value: 'CANCELADO' },
]

const newAgreement = reactive({
  process_id: null,
  total_debt: 0,
  total_agreed: 0,
  interest_rate: 0,
  installment_count: 1,
  first_payment_date: new Date(),
  payment_day: 1,
  grace_period_months: 0,
  default_interest_rate: 0,
  observations: '',
})

// Process dropdown
const allProcesses = ref([])
const selectedProcess = ref(null)
const processSearchLoading = ref(false)

const loadAllProcesses = async () => {
  processSearchLoading.value = true
  try {
    const resp = await processService.getAll({ page_size: 100, agreement_eligible: true })
    const data = resp.data
    allProcesses.value = data?.items || data || []
  } catch (e) {
    console.error('Error loading processes:', e)
    allProcesses.value = []
  } finally {
    processSearchLoading.value = false
  }
}

const onProcessDropdownChange = (e) => {
  if (e.value) {
    newAgreement.process_id = e.value.id
    // Precargar deuda total con el monto de la obligación
    if (e.value.obligation_amount) {
      newAgreement.total_debt = e.value.obligation_amount
    }
  } else {
    newAgreement.process_id = null
    newAgreement.total_debt = 0
  }
}

const formatDate = (d) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })
}

const formatCurrency = (v) => {
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

const loadAgreements = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    const resp = await agreementService.getAll(params)
    agreements.value = resp.data
  } catch (e) {
    console.error('Error loading agreements:', e)
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los acuerdos', life: 3000 })
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  Object.assign(newAgreement, {
    process_id: null, total_debt: 0, total_agreed: 0, interest_rate: 0,
    installment_count: 1, first_payment_date: new Date(), payment_day: 1,
    grace_period_months: 0, default_interest_rate: 0, observations: '',
  })
  selectedProcess.value = null
  createDialogVisible.value = true
  loadAllProcesses()
}

const createAgreement = async () => {
  saving.value = true
  try {
    await agreementService.create({
      ...newAgreement,
      first_payment_date: new Date(newAgreement.first_payment_date).toISOString().split('T')[0],
    })
    createDialogVisible.value = false
    toast.add({ severity: 'success', summary: 'Acuerdo creado', detail: 'El acuerdo de pago fue creado exitosamente', life: 3000 })
    await loadAgreements()
  } catch (e) {
    console.error('Error creating agreement:', e)
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo crear el acuerdo', life: 5000 })
  } finally {
    saving.value = false
  }
}

const openDetail = async (agreement) => {
  try {
    const resp = await agreementService.getById(agreement.id)
    selectedAgreement.value = resp.data
    detailDialogVisible.value = true
  } catch (e) {
    console.error('Error loading agreement detail:', e)
  }
}

const acceptAgreement = async (agreement) => {
  try {
    await agreementService.accept(agreement.id)
    toast.add({ severity: 'success', summary: 'Acuerdo aceptado', detail: 'El acuerdo ahora está VIGENTE', life: 3000 })
    await loadAgreements()
  } catch (e) {
    console.error('Error accepting agreement:', e)
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo aceptar el acuerdo', life: 5000 })
  }
}

const openPayDialog = (installment) => {
  selectedInstallment.value = installment
  payAmount.value = installment.amount
  payObservations.value = ''
  payDialogVisible.value = true
}

const processPayment = async () => {
  if (!selectedInstallment.value || !selectedAgreement.value) return
  paying.value = true
  try {
    await agreementService.payInstallment(selectedAgreement.value.id, selectedInstallment.value.id, {
      paid_amount: payAmount.value,
      observations: payObservations.value,
    })
    payDialogVisible.value = false
    toast.add({ severity: 'success', summary: 'Pago registrado', detail: `Cuota #${selectedInstallment.value.installment_number} pagada`, life: 3000 })
    await openDetail(selectedAgreement.value)
  } catch (e) {
    console.error('Error processing payment:', e)
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo registrar el pago', life: 5000 })
  } finally {
    paying.value = false
  }
}

const cancelAgreement = async (agreement) => {
  try {
    await agreementService.cancel(agreement.id)
    detailDialogVisible.value = false
    toast.add({ severity: 'warn', summary: 'Acuerdo cancelado', detail: 'El acuerdo fue cancelado', life: 3000 })
    await loadAgreements()
  } catch (e) {
    console.error('Error cancelling agreement:', e)
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo cancelar el acuerdo', life: 5000 })
  }
}

onMounted(() => {
  loadAgreements()
})
</script>

<style scoped>
.acuerdos-view {
  padding: 2rem;
}

.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-filter {
  width: 200px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.full-width {
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

.detail-content {
  padding: 0.5rem 0;
}

.detail-grid-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

.info-text {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

.process-selected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--green-600);
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
