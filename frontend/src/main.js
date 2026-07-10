import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import router from './router'
import App from './App.vue'

// PrimeVue 3.x - Import styles for production bundle
import 'primevue/resources/themes/lara-light-indigo/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.min.css'

// Import and register commonly used components globally
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Menu from 'primevue/menu'
import Sidebar from 'primevue/sidebar'
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import FileUpload from 'primevue/fileupload'
import ToastService from 'primevue/toastservice'
import Divider from 'primevue/divider'
import ScrollPanel from 'primevue/scrollpanel'
import Listbox from 'primevue/listbox'
import InputNumber from 'primevue/inputnumber'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(PrimeVue, { ripple: true })

// Global error handler for uncaught errors
window.onerror = function(message, source, lineno, colno, error) {
  console.error('Global error:', message, error);
  // Show error on screen
  document.body.innerHTML = `
    <div style="padding: 40px; background: #ff4444; color: white; font-family: sans-serif; font-size: 18px;">
      <h1 style="font-size: 24px; margin-bottom: 20px;">❌ Error de la aplicación</h1>
      <p><strong>Mensaje:</strong> ${message}</p>
      <p><strong>Archivo:</strong> ${source}</p>
      <p><strong>Línea:</strong> ${lineno}</p>
      <p style="margin-top: 20px;">Recarga la página (F5) para intentar de nuevo</p>
    </div>
  `;
  return true;
};

// Also catch unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
  console.error('Unhandled rejection:', event.reason);
  document.body.innerHTML = `
    <div style="padding: 40px; background: #ff4444; color: white; font-family: sans-serif; font-size: 18px;">
      <h1 style="font-size: 24px; margin-bottom: 20px;">❌ Error en la aplicación</h1>
      <p><strong>Error:</strong> ${event.reason.message || event.reason}</p>
      <p style="margin-top: 20px;">Recarga la página (F5) para intentar de nuevo</p>
    </div>
  `;
});

// Register global components
app.component('InputText', InputText)
app.component('Password', Password)
app.component('Button', Button)
app.component('Message', Message)
app.component('Card', Card)
app.component('Dialog', Dialog)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Tag', Tag)
app.component('Dropdown', Dropdown)
app.component('Textarea', Textarea)
app.component('Checkbox', Checkbox)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('Menu', Menu)
app.component('Drawer', Sidebar)  // Drawer is called Sidebar in PrimeVue 3.x
app.component('Avatar', Avatar)
app.component('Badge', Badge)
app.component('IconField', IconField)
app.component('InputIcon', InputIcon)
app.component('FileUpload', FileUpload)
app.component('Divider', Divider)
app.component('ScrollPanel', ScrollPanel)
app.component('Listbox', Listbox)
app.component('InputNumber', InputNumber)

// Install ToastService
app.use(ToastService)

app.mount('#app')
