<template>
  <component :is="asForm ? 'form' : 'div'" @submit.prevent="onSubmit" class="form-wrapper">
    <div class="form-header" v-if="title || $slots.header">
      <h3 v-if="title">{{ title }}</h3>
      <slot name="header" />
    </div>
    
    <div class="form-body">
      <slot :errors="errors" />
    </div>
    
    <div class="form-footer" v-if="$slots.footer || showDefaultButtons">
      <slot name="footer">
        <div class="form-buttons">
          <Button 
            v-if="showCancelButton" 
            :label="cancelLabel" 
            type="button" 
            @click="onCancel"
            severity="secondary"
            :disabled="submitting"
          />
          <Button 
            :label="submitLabel" 
            type="submit" 
            :loading="submitting"
            :severity="submitSeverity"
            :icon="submitIcon"
          />
        </div>
      </slot>
    </div>
  </component>
</template>

<script setup>
import { ref, reactive } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: null
  },
  asForm: {
    type: Boolean,
    default: true
  },
  showDefaultButtons: {
    type: Boolean,
    default: true
  },
  showCancelButton: {
    type: Boolean,
    default: true
  },
  submitLabel: {
    type: String,
    default: 'Guardar'
  },
  cancelLabel: {
    type: String,
    default: 'Cancelar'
  },
  submitSeverity: {
    type: String,
    default: 'primary'
  },
  submitIcon: {
    type: String,
    default: 'pi pi-check'
  }
});

const emit = defineEmits(['submit', 'cancel']);

const submitting = ref(false);
const errors = reactive({});

const onSubmit = async () => {
  submitting.value = true;
  try {
    await emit('submit');
  } catch (err) {
    console.error('Form submission error:', err);
  } finally {
    submitting.value = false;
  }
};

const onCancel = () => {
  emit('cancel');
};
</script>

<style scoped>
.form-wrapper {
  background: var(--surface-card);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.form-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--surface-border);
}

.form-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.form-body {
  margin-bottom: 1.5rem;
}

.form-footer {
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.form-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

@media (max-width: 576px) {
  .form-buttons {
    width: 100%;
    justify-content: space-between;
  }
}
</style>