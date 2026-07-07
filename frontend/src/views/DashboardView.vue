<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <p>Resumen general de la gestión de cartera</p>
    </div>

    <div class="stats-grid">
      <Card class="stat-card">
        <template #title>
          <div class="stat-title">
            <i class="pi pi-users stat-icon" style="color: var(--blue-500)"></i>
            <span>Total Clientes</span>
          </div>
        </template>
        <template #content>
          <div class="stat-value">{{ stats.totalClientes }}</div>
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
          <div class="stat-value">{{ stats.obligacionesActivas }}</div>
        </template>
      </Card>

      <Card class="stat-card">
        <template #title>
          <div class="stat-title">
            <i class="pi pi-spinner stat-icon" style="color: var(--yellow-500)"></i>
            <span>En Proceso</span>
          </div>
        </template>
        <template #content>
          <div class="stat-value">{{ stats.enProceso }}</div>
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
          <div class="stat-value">{{ stats.pagados }}</div>
        </template>
      </Card>
    </div>

    <div class="dashboard-content">
      <Card class="processes-card">
        <template #header>
          <div class="card-header">
            <h2>Últimos Procesos</h2>
            <Button 
              label="Ver todos" 
              icon="pi pi-arrow-right" 
              text 
              @click="$router.push('/procesos')"
            />
          </div>
        </template>
        <template #content>
          <DataTable :value="recentProcesses" stripedRows size="small">
            <Column field="id" header="ID" style="width: 60px"></Column>
            <Column field="client_name" header="Cliente"></Column>
            <Column field="obligation_number" header="Obligación"></Column>
            <Column field="current_state" header="Estado">
              <template #body="slotProps">
                <Tag :value="slotProps.data.current_state" severity="info" />
              </template>
            </Column>
            <Column field="created_at" header="Fecha">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <Card class="workflow-card">
        <template #header>
          <div class="card-header">
            <h2>Estados del Workflow</h2>
            <Button 
              label="Gestionar" 
              icon="pi pi-cog" 
              text 
              @click="$router.push('/workflow')"
            />
          </div>
        </template>
        <template #content>
          <div class="workflow-states">
            <Tag 
              v-for="state in workflowStates" 
              :key="state.code"
              :value="state.description"
              severity="secondary"
              class="mr-2 mb-2"
            />
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { processService, workflowService } from '../services/api'

const stats = ref({
  totalClientes: 0,
  obligacionesActivas: 0,
  enProceso: 0,
  pagados: 0
})

const recentProcesses = ref([])
const workflowStates = ref([])

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const loadDashboardData = async () => {
  try {
    // Cargar procesos recientes
    const processesResponse = await processService.getAll({ limit: 5 })
    recentProcesses.value = processesResponse.data || []

    // Cargar estados del workflow
    const workflowResponse = await workflowService.getStates()
    workflowStates.value = workflowResponse.data || []

    // Calcular estadísticas (en producción esto vendría del backend)
    stats.value.totalClientes = Math.floor(Math.random() * 1000) + 100
    stats.value.obligacionesActivas = Math.floor(Math.random() * 500) + 50
    stats.value.enProceso = Math.floor(Math.random() * 200) + 20
    stats.value.pagados = Math.floor(Math.random() * 300) + 30
  } catch (error) {
    console.error('Error loading dashboard data:', error)
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
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
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

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
}

.card-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.workflow-states {
  padding: 1rem;
}

@media (max-width: 768px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}
</style>
