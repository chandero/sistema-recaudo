<template>
  <div class="global-search">
    <span class="p-input-icon-left">
      <i class="pi pi-search" />
      <InputText
        v-model="query"
        placeholder="Buscar procesos, clientes, obligaciones..."
        class="search-input"
        @input="handleInput"
        @focus="showResults = true"
        @keydown.enter="handleEnter"
      />
    </span>

    <div v-if="showResults && (results.length > 0 || searching)" class="search-dropdown">
      <div v-if="searching" class="search-loading">
        <ProgressSpinner style="width: 30px; height: 30px;" />
        <span>Buscando...</span>
      </div>

      <div v-else-if="results.length === 0 && query.length >= 2" class="search-empty">
        <i class="pi pi-search"></i>
        <p>No se encontraron resultados para "{{ query }}"</p>
      </div>

      <div v-else>
        <div
          v-for="(group, type) in groupedResults"
          :key="type"
          class="result-group"
        >
          <div class="group-header">
            <i :class="getGroupIcon(type)"></i>
            <span>{{ getGroupLabel(type) }}</span>
            <span class="group-count">{{ group.length }}</span>
          </div>
          <div
            v-for="item in group"
            :key="`${item.type}-${item.id}`"
            class="result-item"
            @click="handleSelect(item)"
          >
            <div class="result-title">{{ item.title }}</div>
            <div v-if="item.subtitle" class="result-subtitle">{{ item.subtitle }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Overlay to close dropdown on outside click -->
    <div v-if="showResults" class="search-overlay" @click="showResults = false"></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import { searchService } from '@/services/api';

const router = useRouter();
const query = ref('');
const results = ref([]);
const searching = ref(false);
const showResults = ref(false);
let debounceTimer = null;

const groupedResults = computed(() => {
  const groups = {};
  results.value.forEach(item => {
    if (!groups[item.type]) groups[item.type] = [];
    groups[item.type].push(item);
  });
  return groups;
});

const handleInput = () => {
  clearTimeout(debounceTimer);
  if (query.value.length < 2) {
    results.value = [];
    showResults.value = false;
    return;
  }
  debounceTimer = setTimeout(() => {
    performSearch();
  }, 300);
};

const handleEnter = () => {
  clearTimeout(debounceTimer);
  if (query.value.length >= 2) {
    performSearch();
  }
};

const performSearch = async () => {
  searching.value = true;
  showResults.value = true;
  try {
    const res = await searchService.search(query.value);
    results.value = res.data;
  } catch (error) {
    console.error('Search error:', error);
    results.value = [];
  } finally {
    searching.value = false;
  }
};

const handleSelect = (item) => {
  showResults.value = false;
  query.value = '';
  results.value = [];
  if (item.link) {
    router.push(item.link);
  }
};

const getGroupIcon = (type) => {
  const icons = {
    process: 'pi pi-sitemap',
    client: 'pi pi-users',
    obligation: 'pi pi-file-invoice-dollar',
  };
  return icons[type] || 'pi pi-search';
};

const getGroupLabel = (type) => {
  const labels = {
    process: 'Procesos',
    client: 'Clientes',
    obligation: 'Obligaciones',
  };
  return labels[type] || type;
};
</script>

<style scoped>
.global-search {
  position: relative;
  flex: 1;
  max-width: 400px;
  margin: 0 20px;
}

.search-input {
  width: 100%;
  padding-left: 2.5rem;
  border-radius: 20px;
  border: 1px solid #dee2e6;
  font-size: 0.875rem;
}

.search-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.p-input-icon-left {
  width: 100%;
  position: relative;
}

.p-input-icon-left > .pi {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  z-index: 1;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1100;
}

.search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  color: #666;
}

.search-empty {
  text-align: center;
  padding: 20px;
  color: #999;
}

.search-empty i {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 6px;
}

.search-empty p {
  margin: 0;
  font-size: 0.85rem;
}

.result-group {
  border-bottom: 1px solid #f0f0f0;
}

.result-group:last-child {
  border-bottom: none;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  background: #fafafa;
}

.group-count {
  margin-left: auto;
  background: #e9ecef;
  border-radius: 10px;
  padding: 1px 7px;
  font-size: 0.7rem;
}

.result-item {
  padding: 8px 14px 8px 28px;
  cursor: pointer;
  transition: background-color 0.1s;
}

.result-item:hover {
  background-color: #f0f7ff;
}

.result-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #333;
}

.result-subtitle {
  font-size: 0.78rem;
  color: #888;
  margin-top: 1px;
}

.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1099;
}
</style>
