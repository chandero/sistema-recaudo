import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/clientes',
    name: 'Clientes',
    component: () => import('../views/ClientesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/obligaciones',
    name: 'Obligaciones',
    component: () => import('../views/ObligacionesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/procesos',
    name: 'Procesos',
    component: () => import('../views/ProcesosView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/workflow',
    name: 'Workflow',
    component: () => import('../views/WorkflowView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/documentos',
    name: 'Documentos',
    component: () => import('../views/DocumentosView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/importar',
    name: 'Importar',
    component: () => import('../views/ImportarView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Administración',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/resoluciones',
    name: 'Resoluciones',
    component: () => import('../views/ResolucionesView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard para autenticación
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  
  if (requiresAuth && !token) {
    next('/login')
  } else if (requiresGuest && token) {
    next('/')
  } else if (requiresAdmin) {
    // Verificar si el usuario es admin de plataforma
    const userRole = localStorage.getItem('user_role')
    if (userRole !== 'platform_admin') {
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
