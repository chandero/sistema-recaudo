<template>
  <div class="loading-overlay" v-if="loading">
    <div class="loading-content">
      <div class="loading-spinner">
        <i class="pi pi-spin pi-spinner" :style="{ fontSize: spinnerSize }"></i>
      </div>
      <div class="loading-text" v-if="text">
        {{ text }}
      </div>
      <div class="loading-progress" v-if="showProgress">
        <div class="progress-bar">
          <div 
            class="progress-bar-fill" 
            :style="{ width: progress + '%' }"
          ></div>
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();

// Props
const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: null
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0,
    validator: (value) => value >= 0 && value <= 100
  },
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  }
});

// Calcular tamaño del spinner
const spinnerSize = computed(() => {
  switch (props.size) {
    case 'small':
      return '1.5rem';
    case 'large':
      return '3rem';
    default:
      return '2rem';
  }
});
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  text-align: center;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-text {
  font-size: 1rem;
  color: #4b5563;
  font-weight: 500;
}

.loading-progress {
  width: 100%;
  max-width: 200px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), var(--primary-400));
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  font-size: 0.875rem;
  color: #4b5563;
  font-weight: 500;
}
</style>