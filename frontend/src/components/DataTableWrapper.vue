<template>
  <div class="data-table-wrapper">
    <div class="table-header" v-if="showHeader">
      <div class="table-controls">
        <IconField iconPosition="left" class="search-field">
          <InputIcon class="pi pi-search" />
          <InputText 
            v-model="searchValue" 
            placeholder="Buscar..." 
            @input="onSearchChange"
          />
        </IconField>
        <Button 
          v-if="showRefresh" 
          icon="pi pi-refresh" 
          text 
          @click="onRefresh"
          class="refresh-btn"
        />
        <div class="table-actions">
          <slot name="actions" />
        </div>
      </div>
    </div>
    <DataTable 
      :value="value" 
      :paginator="hasPaginator" 
      :rows="defaultRows" 
      :rowsPerPageOptions="rowsPerPageOptions"
      :totalRecords="totalRecords"
      :lazy="lazy"
      :first="first"
      :loading="loading"
      :globalFilterFields="filterFields"
      :selection="selection"
      :currentPageReportTemplate="currentPageReportTemplate"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      @selection-change="onSelectionChange"
      @page="onPage"
      removableSort
      tableStyle="min-width: 100%"
    >
      <template #empty>
        <div class="empty-message">
          <i class="pi pi-inbox" style="font-size: 3rem;"></i>
          <p>No se encontraron registros</p>
        </div>
      </template>
      
      <template #loading>
        <div class="loading-message">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem;"></i>
          <p>Cargando...</p>
        </div>
      </template>
      
      <Column 
        v-for="col in columns" 
        :key="col.field"
        :field="col.field" 
        :header="col.header"
        :sortable="col.sortable"
        :style="col.style"
      >
        <template #body="slotProps">
          <slot 
            :name="`column-${col.field}`" 
            :rowData="slotProps.data" 
            :fieldData="slotProps.data[col.field]"
          >
            {{ slotProps.data[col.field] }}
          </slot>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  value: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  selection: {
    type: [Array, Object],
    default: null
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  showRefresh: {
    type: Boolean,
    default: true
  },
  hasPaginator: {
    type: Boolean,
    default: true
  },
  defaultRows: {
    type: Number,
    default: 10
  },
  rowsPerPageOptions: {
    type: Array,
    default: () => [10, 20, 50]
  },
  totalRecords: {
    type: Number,
    default: 0
  },
  lazy: {
    type: Boolean,
    default: false
  },
  first: {
    type: Number,
    default: 0
  },
  currentPageReportTemplate: {
    type: String,
    default: 'Mostrando {first} - {last} de {totalRecords}'
  },
  filterFields: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['search-change', 'refresh', 'selection-change', 'page']);

const searchValue = ref('');

const onSearchChange = (event) => {
  emit('search-change', event.target.value);
};

const onRefresh = () => {
  emit('refresh');
};

const onSelectionChange = (event) => {
  emit('selection-change', event.value);
};

const onPage = (event) => {
  emit('page', event);
};

// Watch for external search value changes
watch(() => props.searchValue, (newVal) => {
  searchValue.value = newVal;
});
</script>

<style scoped>
.data-table-wrapper {
  background: var(--surface-card);
  border-radius: 8px;
  padding: 1rem;
  width: 100%;
  max-width: none;
  box-sizing: border-box;
  overflow-x: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.table-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--surface-border);
}

.table-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  width: 100%;
}

.search-field {
  min-width: 250px;
}

.refresh-btn {
  width: 2.5rem;
  height: 2.5rem;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-left: auto;
}

.empty-message, .loading-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--text-color-secondary);
}

.empty-message i, .loading-message i {
  margin-bottom: 1rem;
}
</style>