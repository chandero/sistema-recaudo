<template>
  <ul class="layout-menu">
    <li class="layout-menuitem">
      <router-link to="/dashboard">
        <i class="pi pi-home"></i>
        <span>{{ t('navigation.dashboard') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/clientes">
        <i class="pi pi-users"></i>
        <span>{{ t('navigation.clients') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/obligaciones">
        <i class="pi pi-file-invoice-dollar"></i>
        <span>{{ t('navigation.obligations') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/procesos">
        <i class="pi pi-sitemap"></i>
        <span>{{ t('navigation.processes') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/workflow">
        <i class="pi pi-sync"></i>
        <span>{{ t('navigation.workflow') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/resoluciones">
        <i class="pi pi-file-signature"></i>
        <span>{{ t('navigation.resolutions') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/documentos">
        <i class="pi pi-file-pdf"></i>
        <span>{{ t('navigation.documents') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/importar">
        <i class="pi pi-upload"></i>
        <span>{{ t('navigation.import') }}</span>
      </router-link>
    </li>
    <li class="layout-menuitem">
      <router-link to="/admin">
        <i class="pi pi-cog"></i>
        <span>{{ t('navigation.administration') }}</span>
      </router-link>
    </li>
  </ul>
</template>

<script setup>
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();
</script>

<style scoped>
.layout-menu {
  list-style: none;
  margin: 0;
  padding: 0;
}

.layout-menuitem {
  padding: 5px 20px;
}

.layout-menuitem a {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  color: #b0b0ba;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
}

.layout-menuitem a:hover {
  background-color: #2d2d40;
  color: white;
}

.layout-menuitem a.router-link-active {
  background-color: #3d3d50;
  color: white;
}

.layout-menuitem i {
  margin-right: 10px;
  width: 24px;
  text-align: center;
}
</style>