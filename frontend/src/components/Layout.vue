<template>
  <div class="layout">
    <!-- Topbar -->
    <div class="topbar">
      <div class="topbar-start">
        <Button 
          icon="pi pi-bars" 
          text 
          @click="sidebarVisible = !sidebarVisible"
          class="mr-2"
        />
        <div class="logo">
          <i class="pi pi-wallet"></i>
          <span>Gestión de Cartera</span>
        </div>
      </div>

      <div class="topbar-end">
        <div class="user-info">
          <Avatar :label="userInitials" shape="circle" size="small" class="mr-2" />
          <span class="user-name">{{ currentUser?.email }}</span>
        </div>
        <Button 
          icon="pi pi-sign-out" 
          text 
          severity="danger"
          @click="handleLogout"
          v-tooltip="'Cerrar sesión'"
        />
      </div>
    </div>

    <!-- Sidebar -->
    <Drawer v-model:visible="sidebarVisible" position="left" class="sidebar">
      <Menu :model="menuItems" class="w-full border-none">
        <template #item="{ item, props }">
          <a v-ripple class="flex align-items-center menu-item" v-bind="props.action">
            <span :class="item.icon" class="menu-icon" />
            <span class="ml-2">{{ item.label }}</span>
            <Badge v-if="item.badge" :value="item.badge" class="ml-auto" />
          </a>
        </template>
      </Menu>
    </Drawer>

    <!-- Main Content -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const sidebarVisible = ref(false)

const currentUser = computed(() => authStore.currentUser)
const userInitials = computed(() => {
  if (!currentUser.value?.email) return 'U'
  const email = currentUser.value.email
  return email.charAt(0).toUpperCase()
})

const menuItems = ref([
  {
    label: 'Dashboard',
    icon: 'pi pi-home',
    command: () => router.push('/')
  },
  {
    label: 'Clientes',
    icon: 'pi pi-users',
    command: () => router.push('/clientes')
  },
  {
    label: 'Obligaciones',
    icon: 'pi pi-file-edit',
    command: () => router.push('/obligaciones')
  },
  {
    label: 'Procesos',
    icon: 'pi pi-briefcase',
    command: () => router.push('/procesos')
  },
  {
    label: 'Workflow',
    icon: 'pi pi-sitemap',
    command: () => router.push('/workflow')
  },
  {
    label: 'Resoluciones',
    icon: 'pi pi-file-export',
    command: () => router.push('/resoluciones')
  },
  {
    label: 'Documentos',
    icon: 'pi pi-file-pdf',
    command: () => router.push('/documentos')
  },
  {
    label: 'Importar',
    icon: 'pi pi-upload',
    command: () => router.push('/importar')
  },
  {
    separator: true
  },
  {
    label: 'Administración',
    icon: 'pi pi-cog',
    command: () => router.push('/admin'),
    visible: computed(() => authStore.isPlatformAdmin)
  }
])

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  // Cerrar sidebar en móviles al cambiar de ruta
  router.afterEach(() => {
    sidebarVisible.value = false
  })
})
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--surface-card);
  border-bottom: 1px solid var(--surface-border);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.topbar-start,
.topbar-end {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary-color);
}

.user-info {
  display: flex;
  align-items: center;
  margin-right: 1rem;
}

.user-name {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.main-content {
  flex: 1;
  background: var(--surface-ground);
}

.sidebar {
  width: 280px;
}

.menu-item {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.25rem;
  color: var(--text-color);
  text-decoration: none;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background: var(--surface-hover);
}

.menu-icon {
  color: var(--text-color-secondary);
}

@media (max-width: 768px) {
  .user-name {
    display: none;
  }
}
</style>
