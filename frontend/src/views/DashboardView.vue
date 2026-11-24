<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <div>
        <h1>Dashboard</h1>
        <p>
          Resumen general de la gestión de cartera
          <span v-if="authStore.activeTenant" class="tenant-badge">
            <i class="pi pi-building"></i>
            {{ authStore.activeTenant.tenant_name }}
          </span>
        </p>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Actualizar"
        :loading="loading"
        @click="loadDashboardData"
        outlined
      />
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !stats" class="loading-container">
      <ProgressSpinner />
    </div>

    <template v-else-if="stats">
      <!-- KPI Cards -->
      <div class="stats-grid">
        <Card class="stat-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-users stat-icon" style="color: var(--blue-500)"></i>
              <span>Total Clientes</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value">{{ formatNumber(stats.total_clients) }}</div>
          </template>
        </Card>

        <Card class="stat-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-file-edit stat-icon" style="color: var(--orange-500)"></i>
              <span>Obligaciones Activas</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value">{{ formatNumber(stats.active_obligations) }}</div>
          </template>
        </Card>

        <Card class="stat-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-spinner stat-icon" style="color: var(--yellow-600)"></i>
              <span>En Proceso</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value">{{ formatNumber(stats.processes_in_progress) }}</div>
          </template>
        </Card>

        <Card class="stat-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-check-circle stat-icon" style="color: var(--green-500)"></i>
              <span>Pagados</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value">{{ formatNumber(stats.paid_processes) }}</div>
          </template>
        </Card>
      </div>

      <!-- Financial KPIs -->
      <div class="stats-grid">
        <Card class="stat-card financial-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-wallet stat-icon" style="color: var(--purple-500)"></i>
              <span>Valor Total Cartera</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value financial">${{ formatCurrency(stats.total_portfolio_value) }}</div>
          </template>
        </Card>

        <Card class="stat-card financial-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-arrow-up stat-icon" style="color: var(--green-500)"></i>
              <span>Valor Recuperado</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value financial">${{ formatCurrency(stats.recovered_value) }}</div>
          </template>
        </Card>

        <Card class="stat-card financial-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-exclamation-triangle stat-icon" style="color: var(--red-500)"></i>
              <span>Valor Vencido</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value financial">${{ formatCurrency(stats.overdue_value) }}</div>
          </template>
        </Card>

        <Card class="stat-card financial-card">
          <template #title>
            <div class="stat-title">
              <i class="pi pi-chart-line stat-icon" style="color: var(--teal-500)"></i>
              <span>% Recuperación</span>
            </div>
          </template>
          <template #content>
            <div class="stat-value financial">{{ recoveryPercentage }}%</div>
          </template>
        </Card>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <Card class="chart-card">
          <template #header>
            <div class="card-header">
              <h2>Distribución por Estado</h2>
            </div>
          </template>
          <template #content>
            <div v-if="stateChartData" class="chart-container">
              <Chart
                type="doughnut"
                :data="stateChartData"
                :options="doughnutOptions"
                class="w-full"
              />
            </div>
            <div v-else class="empty-chart">
              <i class="pi pi-chart-bar" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay datos de distribución disponibles</p>
            </div>
          </template>
        </Card>

        <Card class="chart-card">
          <template #header>
            <div class="card-header">
              <h2>Indicadores de Gestión</h2>
            </div>
          </template>
          <template #content>
            <div class="management-indicators">
              <div class="indicator-item">
                <div class="indicator-label">Días promedio en proceso</div>
                <div class="indicator-value">{{ stats.avg_days_in_process }}</div>
                <ProgressBar
                  :value="Math.min(stats.avg_days_in_process / 90 * 100, 100)"
                  :showValue="false"
                  :style="{ height: '8px' }"
                  :class="getAvgDaysSeverity(stats.avg_days_in_process)"
                />
              </div>
              <div class="indicator-item">
                <div class="indicator-label">Tasa de recuperación</div>
                <div class="indicator-value">{{ recoveryPercentage }}%</div>
                <ProgressBar
                  :value="recoveryPercentage"
                  :showValue="false"
                  :style="{ height: '8px' }"
                  :class="recoveryPercentage >= 50 ? 'recovery-good' : 'recovery-bad'"
                />
              </div>
              <div class="indicator-item">
                <div class="indicator-label">Procesos activos vs cerrados</div>
                <div class="indicator-value">
                  {{ stats.processes_in_progress }} / {{ stats.paid_processes }}
                </div>
                <ProgressBar
                  :value="processCompletionRate"
                  :showValue="false"
                  :style="{ height: '8px' }"
                  class="recovery-good"
                />
              </div>
              <div class="indicator-item">
                <div class="indicator-label">Obligaciones vencidas vs activas</div>
                <div class="indicator-value">
                  {{ formatCurrency(stats.overdue_value) }} / {{ formatCurrency(stats.total_portfolio_value) }}
                </div>
                <ProgressBar
                  :value="overdueRatio"
                  :showValue="false"
                  :style="{ height: '8px' }"
                  :class="overdueRatio > 50 ? 'recovery-bad' : 'recovery-good'"
                />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Top Debtors Table -->
      <div class="bottom-section">
        <Card class="debtors-card">
          <template #header>
            <div class="card-header">
              <h2>Top 10 Deudores</h2>
              <Button
                label="Ver clientes"
                icon="pi pi-arrow-right"
                text
                @click="$router.push('/clientes')"
              />
            </div>
          </template>
          <template #content>
            <DataTable
              :value="stats.top_debtors"
              stripedRows
              size="small"
              :paginator="stats.top_debtors.length > 5"
              :rows="5"
              v-if="stats.top_debtors.length > 0"
            >
              <Column header="#" style="width: 50px">
                <template #body="slotProps">
                  {{ slotProps.index + 1 }}
                </template>
              </Column>
              <Column field="client_name" header="Cliente"></Column>
              <Column field="identification" header="Identificación">
                <template #body="slotProps">
                  {{ slotProps.data.identification || '-' }}
                </template>
              </Column>
              <Column field="obligation_count" header="Obligaciones" style="width: 120px">
                <template #body="slotProps">
                  <Tag :value="String(slotProps.data.obligation_count)" severity="info" />
                </template>
              </Column>
              <Column field="total_amount" header="Valor Total" style="width: 160px">
                <template #body="slotProps">
                  ${{ formatCurrency(slotProps.data.total_amount) }}
                </template>
              </Column>
            </DataTable>
            <div v-else class="empty-state">
              <i class="pi pi-users" style="font-size: 3rem; color: var(--surface-400)"></i>
              <p>No hay deudores registrados</p>
            </div>
          </template>
        </Card>
      </div>
    </template>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <div class="error-box">
        <i class="pi pi-exclamation-circle" style="font-size: 1.5rem; color: #ef4444;"></i>
        <p>{{ error }}</p>
        <Button label="Reintentar" icon="pi pi-refresh" text @click="loadDashboardData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardService } from '../services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const stats = ref(null)
const loading = ref(false)
const error = ref(null)

// Computed
const recoveryPercentage = computed(() => {
  if (!stats.value || stats.value.total_portfolio_value === 0) return 0
  return Math.round(
    (stats.value.recovered_value / (stats.value.recovered_value + stats.value.total_portfolio_value)) * 100
  )
})

const processCompletionRate = computed(() => {
  if (!stats.value) return 0
  const total = stats.value.processes_in_progress + stats.value.paid_processes
  if (total === 0) return 0
  return Math.round((stats.value.paid_processes / total) * 100)
})

const overdueRatio = computed(() => {
  if (!stats.value || stats.value.total_portfolio_value === 0) return 0
  return Math.round((stats.value.overdue_value / stats.value.total_portfolio_value) * 100)
})

const stateChartData = computed(() => {
  if (!stats.value || !stats.value.state_distribution || stats.value.state_distribution.length === 0) {
    return null
  }
  const dist = stats.value.state_distribution
  return {
    labels: dist.map(d => d.state_name),
    datasets: [
      {
        data: dist.map(d => d.count),
        backgroundColor: [
          '#42A5F5', '#66BB6A', '#FFA726', '#EF5350', '#AB47BC',
          '#26C6DA', '#FFCA28', '#78909C', '#EC407D', '#8D6E63',
          '#7E57C2', '#26A69A', '#FF7043', '#5C6BC0', '#29B6F6',
          '#9CCC65', '#FFB300', '#D4E157', '#BDBDBD', '#80DEEA', '#F48FB1'
        ],
        borderWidth: 1
      }
    ]
  }
})

const doughnutOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right',
      labels: {
        boxWidth: 12,
        padding: 10,
        font: { size: 11 }
      }
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const total = context.dataset.data.reduce((a, b) => a + b, 0)
          const pct = Math.round((context.parsed / total) * 100)
          return `${context.label}: ${context.parsed} (${pct}%)`
        }
      }
    }
  }
}))

// Methods
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('es-CO')
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '0'
  return Math.round(value).toLocaleString('es-CO')
}

const getAvgDaysSeverity = (days) => {
  if (days <= 30) return 'recovery-good'
  if (days <= 60) return 'recovery-warn'
  return 'recovery-bad'
}

const loadDashboardData = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await dashboardService.getStats()
    stats.value = response.data
  } catch (err) {
    console.error('Error loading dashboard:', err)
    error.value = 'Error al cargar las estadísticas del dashboard. Por favor, intente nuevamente.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-view {
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
}

.dashboard-header p {
  color: var(--text-color-secondary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tenant-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f0f4ff;
  border: 1px solid #d0d9ff;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.8rem;
  color: var(--primary-color, #3b82f6);
  font-weight: 500;
}

.tenant-badge i {
  font-size: 0.7rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.financial-card {
  border-left: 4px solid var(--purple-400);
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1;
}

.stat-value.financial {
  font-size: 1.8rem;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.chart-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
}

.card-header h2 {
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0;
}

.chart-container {
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
}

.empty-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--text-color-secondary);
}

.empty-chart p {
  margin-top: 1rem;
}

.management-indicators {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem 0.5rem;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.indicator-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  font-weight: 500;
}

.indicator-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
}

:deep(.recovery-good .p-progressbar-label) {
  display: none;
}
:deep(.recovery-good) .p-progressbar-value {
  background: var(--green-500) !important;
}
:deep(.recovery-warn) .p-progressbar-value {
  background: var(--orange-500) !important;
}
:deep(.recovery-bad) .p-progressbar-value {
  background: var(--red-500) !important;
}

.bottom-section {
  margin-bottom: 2rem;
}

.debtors-card {
  border-radius: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--text-color-secondary);
}

.empty-state p {
  margin-top: 1rem;
}

.error-state {
  display: flex;
  justify-content: center;
  padding: 3rem;
}

@media (max-width: 992px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
  }

  .stat-value {
    font-size: 1.8rem;
  }

  .stat-value.financial {
    font-size: 1.3rem;
  }
}
</style>
