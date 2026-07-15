<template>
  <div class="feedback-container" v-if="showFeedback">
    <div 
      class="feedback-indicator"
      :class="`feedback-${type}`"
      :style="feedbackStyle"
    >
      <div class="feedback-content">
        <i :class="iconClass" class="feedback-icon"></i>
        <div class="feedback-message">
          <strong>{{ title }}</strong>
          <p>{{ message }}</p>
        </div>
        <Button 
          icon="pi pi-times" 
          class="p-button-text p-button-rounded p-button-plain feedback-close-btn"
          @click="closeFeedback"
        />
      </div>
      <div class="feedback-progress" :style="progressStyle"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();

// Props
const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  duration: {
    type: Number,
    default: 5000
  },
  closable: {
    type: Boolean,
    default: true
  }
});

// Emits
const emit = defineEmits(['close']);

// Estados
const showFeedback = ref(true);
const remainingTime = ref(props.duration);

// Calcular icono según el tipo
const iconClass = computed(() => {
  switch (props.type) {
    case 'success':
      return 'pi pi-check-circle';
    case 'error':
      return 'pi pi-exclamation-triangle';
    case 'warning':
      return 'pi pi-exclamation-triangle';
    case 'info':
      return 'pi pi-info-circle';
    default:
      return 'pi pi-info-circle';
  }
});

// Estilo del indicador
const feedbackStyle = computed(() => ({
  top: '20px',
  right: '20px',
  position: 'fixed',
  zIndex: '9999'
}));

// Estilo de la barra de progreso
const progressStyle = computed(() => ({
  width: `${(remainingTime.value / props.duration) * 100}%`,
  height: '3px',
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  position: 'absolute',
  bottom: '0',
  left: '0',
  transition: 'width 100ms linear'
}));

// Cerrar feedback
const closeFeedback = () => {
  showFeedback.value = false;
  setTimeout(() => {
    emit('close');
  }, 300);
};

// Temporizador para auto-cierre
let timer = null;

onMounted(() => {
  if (props.duration > 0) {
    timer = setInterval(() => {
      remainingTime.value -= 100;
      if (remainingTime.value <= 0) {
        closeFeedback();
      }
    }, 100);
  }
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<style scoped>
.feedback-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
}

.feedback-indicator {
  padding: 1rem 1.5rem;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  animation: slideInRight 0.3s ease;
  min-width: 300px;
  max-width: 400px;
  position: relative;
  overflow: hidden;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.feedback-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.feedback-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.feedback-message {
  flex: 1;
}

.feedback-message strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 1rem;
}

.feedback-message p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.feedback-close-btn {
  color: white !important;
  opacity: 0.8;
}

.feedback-close-btn:hover {
  opacity: 1;
}

.feedback-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background-color: rgba(255, 255, 255, 0.7);
  transition: width 100ms linear;
}

/* Tipos de feedback */
.feedback-success {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.feedback-error {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.feedback-warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #1f2937;
}

.feedback-info {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.feedback-warning .feedback-message p {
  color: #1f2937;
  opacity: 0.8;
}

.feedback-warning .feedback-close-btn {
  color: #1f2937 !important;
}

@media (max-width: 768px) {
  .feedback-indicator {
    min-width: auto;
    width: calc(100% - 40px);
    right: 20px;
    left: 20px;
  }
}
</style>