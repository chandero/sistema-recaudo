<template>
  <Dialog 
    v-model:visible="isVisible" 
    :modal="true" 
    :closable="closable"
    :style="{ width: width }"
    class="confirmation-dialog"
  >
    <template #header>
      <div class="confirmation-header">
        <div class="header-content">
          <i :class="iconClass" :style="{ color: iconColor }" class="header-icon"></i>
          <h3>{{ title || t('common.confirmation') }}</h3>
        </div>
      </div>
    </template>

    <div class="confirmation-content">
      <p>{{ message }}</p>
      <div class="confirmation-details" v-if="details">
        <small>{{ details }}</small>
      </div>
    </div>

    <template #footer>
      <div class="confirmation-footer">
        <Button 
          :label="cancelLabel || t('common.cancel')" 
          icon="pi pi-times" 
          class="p-button-text"
          @click="onCancel"
        />
        <Button 
          :label="acceptLabel || t('common.accept')" 
          :icon="acceptIcon" 
          :severity="acceptSeverity"
          @click="onAccept"
          :loading="confirming"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, defineEmits, defineProps } from 'vue';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    required: true
  },
  details: {
    type: String,
    default: null
  },
  header: {
    type: String,
    default: null
  },
  acceptLabel: {
    type: String,
    default: null
  },
  cancelLabel: {
    type: String,
    default: null
  },
  acceptIcon: {
    type: String,
    default: 'pi pi-check'
  },
  acceptSeverity: {
    type: String,
    default: 'danger'
  },
  rejectIcon: {
    type: String,
    default: 'pi pi-times'
  },
  rejectSeverity: {
    type: String,
    default: 'secondary'
  },
  width: {
    type: String,
    default: '450px'
  },
  closable: {
    type: Boolean,
    default: true
  },
  type: {
    type: String,
    default: 'warn', // warn, info, success, error
    validator: (value) => ['warn', 'info', 'success', 'error'].includes(value)
  }
});

// Emits
const emit = defineEmits(['accept', 'reject', 'update:visible']);

// Estados
const confirming = defineModel('confirming', { default: false });

// Computed property para manejar v-model correctamente
const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
});

// Calcular título
const title = computed(() => {
  if (props.header) return props.header;
  
  switch (props.type) {
    case 'info':
      return t('common.information');
    case 'success':
      return t('common.success');
    case 'error':
      return t('common.error');
    default:
      return t('common.warning');
  }
});

// Calcular icono y color
const iconClass = computed(() => {
  switch (props.type) {
    case 'info':
      return 'pi pi-info-circle';
    case 'success':
      return 'pi pi-check-circle';
    case 'error':
      return 'pi pi-exclamation-triangle';
    default:
      return 'pi pi-exclamation-triangle';
  }
});

const iconColor = computed(() => {
  switch (props.type) {
    case 'info':
      return '#3b82f6'; // blue-500
    case 'success':
      return '#22c55e'; // green-500
    case 'error':
      return '#ef4444'; // red-500
    default:
      return '#f59e0b'; // amber-500
  }
});

// Handlers
const onAccept = () => {
  emit('accept');
  emit('update:visible', false);
};

const onCancel = () => {
  emit('reject');
  emit('update:visible', false);
};
</script>

<style scoped>
.confirmation-header {
  padding: 1.5rem 1.5rem 0;
  border-bottom: none;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 1.5rem;
}

.header-content h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.confirmation-content {
  padding: 1rem 1.5rem;
}

.confirmation-content p {
  margin: 0 0 1rem 0;
  color: #4b5563;
}

.confirmation-details {
  background-color: #f9fafb;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 4px solid #d1d5db;
}

.confirmation-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.confirmation-dialog :deep(.p-dialog-header) {
  border-bottom: none;
}

.confirmation-dialog :deep(.p-dialog-content) {
  padding: 0;
}

.confirmation-dialog :deep(.p-dialog-footer) {
  border-top: none;
  padding: 0 1.5rem 1.5rem;
}
</style>