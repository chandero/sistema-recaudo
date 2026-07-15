<template>
  <span class="help-tooltip">
    <i 
      class="pi pi-question-circle tooltip-trigger" 
      @mouseenter="showTooltip"
      @mouseleave="hideTooltip"
      @focus="showTooltip"
      @blur="hideTooltip"
      :aria-label="t('components.help_tooltip.aria_label')"
      role="tooltip"
      tabindex="0"
    ></i>
    <transition name="tooltip-fade">
      <div 
        v-if="visible" 
        class="tooltip-content"
        :class="positionClass"
        :style="tooltipStyle"
      >
        <div class="tooltip-arrow"></div>
        <div class="tooltip-body">
          <h4 v-if="title" class="tooltip-title">{{ title }}</h4>
          <p class="tooltip-text">{{ content }}</p>
          <div class="tooltip-actions" v-if="hasActions">
            <Button 
              v-if="linkUrl"
              :label="linkText || t('components.help_tooltip.learn_more')" 
              class="p-button-text p-button-sm" 
              @click="goToLink"
            />
            <Button 
              v-if="actionCallback"
              :label="actionText || t('components.help_tooltip.action_button')" 
              class="p-button-outlined p-button-sm" 
              @click="executeAction"
            />
          </div>
        </div>
      </div>
    </transition>
  </span>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from '@/composables/useI18n';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const router = useRouter();

// Props
const props = defineProps({
  content: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: null
  },
  position: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'right', 'bottom', 'left'].includes(value)
  },
  linkUrl: {
    type: String,
    default: null
  },
  linkText: {
    type: String,
    default: null
  },
  actionCallback: {
    type: Function,
    default: null
  },
  actionText: {
    type: String,
    default: null
  },
  delay: {
    type: Number,
    default: 500
  }
});

// Estados
const visible = ref(false);
let showTimer = null;

// Calcular clases de posición
const positionClass = computed(() => {
  return `tooltip-position-${props.position}`;
});

// Calcular estilo del tooltip
const tooltipStyle = computed(() => {
  const styles = {};
  
  switch (props.position) {
    case 'top':
      styles.bottom = '100%';
      styles.left = '50%';
      styles.transform = 'translateX(-50%)';
      break;
    case 'right':
      styles.top = '50%';
      styles.left = '100%';
      styles.transform = 'translateY(-50%)';
      break;
    case 'bottom':
      styles.top = '100%';
      styles.left = '50%';
      styles.transform = 'translateX(-50%)';
      break;
    case 'left':
      styles.top = '50%';
      styles.right = '100%';
      styles.transform = 'translateY(-50%)';
      break;
  }
  
  return styles;
});

// Verificar si hay acciones
const hasActions = computed(() => {
  return props.linkUrl || props.actionCallback;
});

// Mostrar tooltip
const showTooltip = () => {
  clearTimeout(showTimer);
  showTimer = setTimeout(() => {
    visible.value = true;
  }, props.delay);
};

// Ocultar tooltip
const hideTooltip = () => {
  clearTimeout(showTimer);
  visible.value = false;
};

// Ir a enlace
const goToLink = (event) => {
  event.stopPropagation();
  if (props.linkUrl.startsWith('http')) {
    window.open(props.linkUrl, '_blank');
  } else {
    router.push(props.linkUrl);
  }
  visible.value = false;
};

// Ejecutar acción
const executeAction = (event) => {
  event.stopPropagation();
  if (props.actionCallback) {
    props.actionCallback();
  }
  visible.value = false;
};
</script>

<style scoped>
.help-tooltip {
  position: relative;
  display: inline-block;
  margin-left: 0.5rem;
}

.tooltip-trigger {
  color: #9ca3af;
  font-size: 0.875rem;
  cursor: help;
  border-radius: 50%;
  width: 1.25rem;
  height: 1.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.tooltip-trigger:hover {
  color: var(--primary-color);
  background-color: rgba(var(--primary-500), 0.1);
}

.tooltip-trigger:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.tooltip-content {
  position: absolute;
  z-index: 1000;
  background: #1f2937;
  color: white;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  max-width: 280px;
  min-width: 200px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  white-space: normal;
  word-wrap: break-word;
}

.tooltip-arrow {
  position: absolute;
  width: 0;
  height: 0;
  border-style: solid;
}

/* Posición superior */
.tooltip-position-top {
  margin-bottom: 0.5rem;
}

.tooltip-position-top .tooltip-arrow {
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 6px 6px 0 6px;
  border-color: #1f2937 transparent transparent transparent;
}

/* Posición derecha */
.tooltip-position-right {
  margin-left: 0.5rem;
}

.tooltip-position-right .tooltip-arrow {
  top: 50%;
  left: -6px;
  transform: translateY(-50%);
  border-width: 6px 6px 6px 0;
  border-color: transparent #1f2937 transparent transparent;
}

/* Posición inferior */
.tooltip-position-bottom {
  margin-top: 0.5rem;
}

.tooltip-position-bottom .tooltip-arrow {
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 0 6px 6px 6px;
  border-color: transparent transparent #1f2937 transparent;
}

/* Posición izquierda */
.tooltip-position-left {
  margin-right: 0.5rem;
}

.tooltip-position-left .tooltip-arrow {
  top: 50%;
  right: -6px;
  transform: translateY(-50%);
  border-width: 6px 0 6px 6px;
  border-color: transparent transparent transparent #1f2937;
}

.tooltip-body {
  position: relative;
  z-index: 1;
}

.tooltip-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

.tooltip-text {
  margin: 0 0 0.75rem 0;
  line-height: 1.5;
  color: #d1d5db;
}

.tooltip-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-start;
}

.tooltip-actions .p-button {
  margin: 0;
}

/* Transiciones */
.tooltip-fade-enter-active {
  transition: opacity 0.2s ease;
}

.tooltip-fade-leave-active {
  transition: opacity 0.2s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}

/* Estilos para dispositivos móviles */
@media (max-width: 768px) {
  .tooltip-content {
    max-width: 220px;
    font-size: 0.8rem;
  }
  
  .tooltip-actions {
    flex-direction: column;
  }
}
</style>