<template>
  <div class="reports-view">
    <PageHeader title="Reportes" subtitle="Análisis y exportación de datos">
      <template #actions>
        <Button label="Exportar procesos" icon="pi pi-file-excel" @click="exportExcel" :loading="exporting" />
      </template>
    </PageHeader>

    <!-- Aging Report -->
    <div class="card">
      <h3>Cartera por antigüedad (Aging)</h3>
      <div v-if="loadingAging" class="loading-section">
        <ProgressSpinner style="width: 40px; height: 40px;" />
      </div>
      <div v-else-if="agingData" class="aging-grid">
        <div v-for="(bucket, key) in agingData.buckets" :key="key" class="aging-card" :class="getAgingClass(key)">
          <div class="aging-label">{{ key }} días</div>
          <div class="aging-amount">{{ formatCurrency(bucket.amount) }}</div>
          <div class="aging-count">{{ bucket.count }} obligaciones</div>
        </div>
        <div class="aging-total">
          <div class="aging-label">Total</div>
          <div class="aging-amount">{{ formatCurrency(agingData.total_amount) }}</div>
          <div class="aging-count">{{ agingData.total_count }} obligaciones</div>
        </div>
      </div>
    </div>

    <!-- Performance Report -->
    <div class="card">
      <div class="card-header">
        <h3>Indicadores de gestión</h3>
        <div class="period-filter">
          <Calendar v-model="startDate" placeholder="Desde" dateFormat="yy-mm-dd" showIcon class="period-input" />
          <Calendar v-model="endDate" placeholder="Hasta" dateFormat="yy-mm-dd" showIcon class="period-input" />
          <Button label="Consultar" icon="pi pi-search" @click="fetchPerformance" size="small" />
        </div>
      </div>
      <div v-if="loadingPerf" class="loading-section">
        <ProgressSpinner style="width: 40px; height: 40px;" />
      </div>
      <div v-else-if="perfData" class="perf-grid">
        <div class="perf-card">
          <i class="pi pi-plus-circle perf-icon new"></i>
          <div class="perf-value">{{ perfData.new_processes }}</div>
          <div class="perf-label">Procesos nuevos</div>
        </div>
        <div class="perf-card">
          <i class="pi pi-check-circle perf-icon closed"></i>
          <div class="perf-value">{{ perfData.closed_processes }}</div>
          <div class="perf-label">Procesos cerrados</div>
        </div>
        <div class="perf-card">
          <i class="pi pi-handshake perf-icon agreement"></i>
          <div class="perf-value">{{ perfData.active_agreements }}</div>
          <div class="perf-label">Acuerdos vigentes</div>
        </div>
        <div class="perf-card">
          <i class="pi pi-dollar perf-icon paid"></i>
          <div class="perf-value">{{ perfData.paid_installments }}</div>
          <div class="perf-label">Cuotas pagadas</div>
        </div>
        <div class="perf-card">
          <i class="pi pi-exclamation-triangle perf-icon overdue"></i>
          <div class="perf-value">{{ perfData.overdue_installments }}</div>
          <div class="perf-label">Cuotas vencidas</div>
        </div>
      </div>
    </div>

    <!-- Operator Report -->
    <div class="card">
      <div class="card-header">
        <h3>Reporte por operador</h3>
        <div class="operator-filter">
          <Dropdown v-model="selectedOperator" :options="operators" optionLabel="full_name" placeholder="Seleccionar operador" class="operator-dropdown" />
          <Button label="Consultar" icon="pi pi-search" @click="fetchOperatorReport" :disabled="!selectedOperator" size="small" />
        </div>
      </div>
      <div v-if="loadingOperator" class="loading-section">
        <ProgressSpinner style="width: 40px; height: 40px;" />
      </div>
      <div v-else-if="operatorData" class="operator-report">
        <h4>{{ operatorData.operator_name }}</h4>
        <div class="operator-grid">
          <div class="stat-item">
            <span class="stat-value">{{ operatorData.transitions_made }}</span>
            <span class="stat-label">Transiciones realizadas</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ operatorData.processes_managed }}</span>
            <span class="stat-label">Procesos gestionados</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ operatorData.notes_created }}</span>
            <span class="stat-label">Notas creadas</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Button from 'primevue/button';
import Calendar from 'primevue/calendar';
import Dropdown from 'primevue/dropdown';
import ProgressSpinner from 'primevue/progressspinner';
import PageHeader from '@/components/PageHeader.vue';
import { reportService } from '@/services/api';
import { userService } from '@/services/api';

const loadingAging = ref(false);
const agingData = ref(null);
const loadingPerf = ref(false);
const perfData = ref(null);
const startDate = ref(null);
const endDate = ref(null);
const loadingOperator = ref(false);
const operatorData = ref(null);
const selectedOperator = ref(null);
const operators = ref([]);
const exporting = ref(false);

const fetchAging = async () => {
  loadingAging.value = true;
  try {
    const res = await reportService.getAging();
    agingData.value = res.data;
  } catch (error) {
    console.error('Error fetching aging report:', error);
  } finally {
    loadingAging.value = false;
  }
};

const fetchPerformance = async () => {
  loadingPerf.value = true;
  try {
    const start = startDate.value ? startDate.value.toISOString().split('T')[0] : undefined;
    const end = endDate.value ? endDate.value.toISOString().split('T')[0] : undefined;
    const res = await reportService.getPerformance(start, end);
    perfData.value = res.data;
  } catch (error) {
    console.error('Error fetching performance report:', error);
  } finally {
    loadingPerf.value = false;
  }
};

const fetchOperatorReport = async () => {
  if (!selectedOperator.value) return;
  loadingOperator.value = true;
  try {
    const res = await reportService.getOperatorReport(selectedOperator.value.id);
    operatorData.value = res.data;
  } catch (error) {
    console.error('Error fetching operator report:', error);
  } finally {
    loadingOperator.value = false;
  }
};

const fetchOperators = async () => {
  try {
    const res = await userService.getAll({ role: 'OPERATOR' });
    operators.value = res.data.items || res.data;
  } catch (error) {
    console.error('Error fetching operators:', error);
  }
};

const exportExcel = async () => {
  exporting.value = true;
  try {
    const res = await reportService.exportProcessesExcel();
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `procesos_${new Date().toISOString().split('T')[0]}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exporting:', error);
  } finally {
    exporting.value = false;
  }
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(amount || 0);
};

const getAgingClass = (key) => {
  const classes = { '0-30': 'aging-green', '31-60': 'aging-yellow', '61-90': 'aging-orange', '90+': 'aging-red' };
  return classes[key] || '';
};

onMounted(() => {
  fetchAging();
  fetchPerformance();
  fetchOperators();
});
</script>

<style scoped>
.reports-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card h3 {
  margin: 0 0 16px;
  font-size: 1.1rem;
  color: #333;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.card-header h3 {
  margin: 0;
}

.loading-section {
  display: flex;
  justify-content: center;
  padding: 30px;
}

/* Aging */
.aging-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.aging-card {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.aging-green { background: #f0fdf4; border-color: #22c55e; }
.aging-yellow { background: #fefce8; border-color: #eab308; }
.aging-orange { background: #fff7ed; border-color: #f97316; }
.aging-red { background: #fef2f2; border-color: #ef4444; }

.aging-total {
  background: #f8fafc;
  border-left: 4px solid #6366f1;
  padding: 16px;
  border-radius: 8px;
}

.aging-label {
  font-size: 0.8rem;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
}

.aging-amount {
  font-size: 1.3rem;
  font-weight: 700;
  color: #333;
  margin: 4px 0;
}

.aging-count {
  font-size: 0.78rem;
  color: #888;
}

/* Performance */
.period-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.period-input {
  width: 150px;
}

.perf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.perf-card {
  text-align: center;
  padding: 20px 12px;
  border-radius: 8px;
  background: #f8fafc;
}

.perf-icon {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.perf-icon.new { color: #3b82f6; }
.perf-icon.closed { color: #22c55e; }
.perf-icon.agreement { color: #6366f1; }
.perf-icon.paid { color: #059669; }
.perf-icon.overdue { color: #ef4444; }

.perf-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
}

.perf-label {
  font-size: 0.78rem;
  color: #666;
  margin-top: 4px;
}

/* Operator */
.operator-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.operator-dropdown {
  width: 220px;
}

.operator-report h4 {
  margin: 0 0 12px;
  color: #333;
}

.operator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #6366f1;
}

.stat-label {
  display: block;
  font-size: 0.78rem;
  color: #666;
  margin-top: 4px;
}
</style>
