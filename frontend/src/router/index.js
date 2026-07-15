import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// Importación de vistas
const LoginView = () => import('@/views/LoginView.vue');
const ProtectedLayout = () => import('@/layouts/ProtectedLayout.vue');

// Importar vistas secundarias
const DashboardView = () => import('@/views/DashboardView.vue');
const ClientesView = () => import('@/views/ClientesView.vue');
const ObligacionesView = () => import('@/views/ObligacionesView.vue');
const ProcesosView = () => import('@/views/ProcesosView.vue');
const WorkflowView = () => import('@/views/WorkflowView.vue');
const ResolucionesView = () => import('@/views/ResolucionesView.vue');
const DocumentosView = () => import('@/views/DocumentosView.vue');
const ImportarView = () => import('@/views/ImportarView.vue');
const AdminView = () => import('@/views/AdminView.vue');

// Guard para rutas protegidas
const requireAuth = async (to, from, next) => {
  const authStore = useAuthStore();
  if (!authStore.isAuthenticated) {
    next('/login');
  } else {
    if (!authStore.currentUser) {
      try {
        await authStore.getCurrentUser();
      } catch (error) {
        console.error('Error obteniendo usuario actual, redirigiendo a login:', error);
        // Si hay error al obtener el usuario, limpiar sesión y redirigir al login
        authStore.logout();
        next('/login');
        return;
      }
    }
    next();
  }
};

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: LoginView
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/',
      component: ProtectedLayout,
      beforeEnter: requireAuth,
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: DashboardView
        },
        {
          path: 'clientes',
          name: 'Clientes',
          component: ClientesView
        },
        {
          path: 'obligaciones',
          name: 'Obligaciones',
          component: ObligacionesView
        },
        {
          path: 'procesos',
          name: 'Procesos',
          component: ProcesosView
        },
        {
          path: 'workflow',
          name: 'Workflow',
          component: WorkflowView
        },
        {
          path: 'resoluciones',
          name: 'Resoluciones',
          component: ResolucionesView
        },
        {
          path: 'documentos',
          name: 'Documentos',
          component: DocumentosView
        },
        {
          path: 'importar',
          name: 'Importar',
          component: ImportarView
        },
        {
          path: 'admin',
          name: 'Admin',
          component: AdminView
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard'
    }
  ]
});

export default router;