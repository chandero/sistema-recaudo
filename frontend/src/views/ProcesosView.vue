<template>
  <Layout>
    <div class="placeholder-view">
      <Card class="text-center py-5">
        <template #header>
          <div class="pt-4">
            <i class="pi pi-briefcase text-6xl text-color-secondary"></i>
          </div>
        </template>
        <template #title>
          Procesos de Cobro
        </template>
        <template #content>
          <p class="m-0 text-color-secondary">
            Esta funcionalidad estará disponible próximamente.
          </p>
        </template>
      </Card>
    </div>
  </Layout>
</template>

<script setup>
import Layout from '../components/Layout.vue'
</script>

<style scoped>
.placeholder-view {
  padding: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.text-center {
  text-align: center;
  max-width: 500px;
  width: 100%;
}
</style>
