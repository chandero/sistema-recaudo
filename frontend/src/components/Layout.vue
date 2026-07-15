<template>
  <div class="layout-wrapper" :class="{'layout-mobile-active': mobileMenuActive}">
    <!-- Sidebar -->
    <div class="layout-sidebar">
      <div class="layout-logo">
        <img alt="Logo" src="@/assets/images/logo.png" class="logo-image" />
        <span class="logo-text">Sistema de Recaudo</span>
      </div>
      <div class="layout-sidebar-content">
        <AppMenu :mobileMenuActive="mobileMenuActive" />
      </div>
    </div>

    <!-- Topbar -->
    <div class="layout-topbar">
      <button class="menu-button" @click="toggleMobileMenu">
        <i class="pi pi-bars"></i>
      </button>
      <div class="topbar-content">
        <Breadcrumb :home="home" :model="breadcrumbItems" class="topbar-breadcrumb" />
        <div class="user-info">
          <i class="pi pi-user mr-2"></i>
          <span>{{ currentUser?.username || 'Usuario' }}</span>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="layout-content">
      <router-view />
    </div>

    <!-- Mobile Menu Overlay -->
    <div class="layout-mask" v-if="mobileMenuActive" @click="toggleMobileMenu"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import Breadcrumb from 'primevue/breadcrumb';
import { useAuthStore } from '@/stores/auth';
import AppMenu from './AppMenu.vue'; // Importar el componente AppMenu

// Estados
const mobileMenuActive = ref(false);
const authStore = useAuthStore();
const route = useRoute();

// Obtener el usuario actual
const currentUser = computed(() => authStore.currentUser);

// Definir home para el breadcrumb
const home = ref({
  icon: 'pi pi-home',
  to: '/dashboard'
});

// Items del breadcrumb basados en la ruta actual
const breadcrumbItems = computed(() => {
  const path = route.path;
  const items = [];

  // Definir nombres para las rutas
  const routeNames = {
    '/dashboard': 'Dashboard',
    '/clientes': 'Clientes',
    '/obligaciones': 'Obligaciones',
    '/procesos': 'Procesos',
    '/workflow': 'Workflow',
    '/resoluciones': 'Resoluciones',
    '/documentos': 'Documentos',
    '/importar': 'Importar',
    '/admin': 'Administración'
  };

  const currentName = routeNames[path] || route.name || 'Inicio';
  
  items.push({
    label: currentName,
    to: path
  });

  return items;
});

// Función para alternar el menú móvil
const toggleMobileMenu = () => {
  mobileMenuActive.value = !mobileMenuActive.value;
};

// Manejar el tamaño de pantalla
const handleResize = () => {
  if (window.innerWidth > 992) {
    mobileMenuActive.value = false;
  }
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
  handleResize(); // Ejecutar una vez para establecer el estado inicial
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// Definir currentPageTitle para resolver el error
const currentPageTitle = ref('Dashboard'); // Valor por defecto
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  height: 100vh;
  position: relative;
}

.layout-sidebar {
  width: 250px;
  background: #1e1e2d;
  color: white;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 1000;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.layout-logo {
  padding: 20px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #333;
}

.logo-image {
  height: 40px;
  margin-right: 10px;
}

.logo-text {
  font-size: 1.2em;
  font-weight: bold;
}

.layout-sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

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

.layout-topbar {
  position: fixed;
  top: 0;
  left: 250px;
  right: 0;
  height: 60px;
  background: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 999;
}

.menu-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #495057;
  margin-right: 20px;
  display: none; /* Ocultar en desktop */
}

.topbar-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topbar-breadcrumb {
  flex: 1;
}

.user-info {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.layout-content {
  flex: 1;
  min-width: 0;
  margin-top: 60px;
  padding: 20px;
  background-color: #f5f5f7;
  overflow: auto;
  transition: margin-left 0.3s ease;
}

.layout-content > :deep(*) {
  width: 100%;
  max-width: none;
  box-sizing: border-box;
}

.layout-mask {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 998;
}

/* Estilos para móvil */
@media screen and (max-width: 992px) {
  .layout-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    transform: translateX(-100%);
  }

  .layout-sidebar.active {
    transform: translateX(0);
  }

  .layout-topbar {
    left: 0;
  }

  .layout-content {
    margin-left: 0;
  }

  .menu-button {
    display: block;
  }

  .layout-mobile-active .layout-sidebar {
    transform: translateX(0);
  }
}
</style>