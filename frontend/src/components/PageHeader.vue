<template>
  <div class="page-header">
    <div class="header-content">
      <div class="header-title-section">
        <Button 
          v-if="showBackButton" 
          icon="pi pi-arrow-left" 
          text 
          rounded 
          class="back-button mr-2"
          @click="$router.back()"
          v-tooltip="'Volver atrás'"
        />
        <div class="header-text">
          <h2 class="title">{{ title }}</h2>
          <p class="subtitle" v-if="subtitle">{{ subtitle }}</p>
        </div>
      </div>
      <div class="header-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="header-bottom" v-if="$slots.bottom">
      <slot name="bottom" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: null
  },
  showBackButton: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.page-header {
  background: var(--surface-card);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.header-title-section {
  display: flex;
  align-items: center;
  flex: 1;
}

.back-button {
  width: 2.5rem;
  height: 2.5rem;
  margin-right: 0.75rem;
}

.header-text {
  flex: 1;
}

.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
}

.subtitle {
  margin: 0.25rem 0 0 0;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.header-bottom {
  padding: 1rem 1.5rem;
  background: var(--surface-section);
}
</style>