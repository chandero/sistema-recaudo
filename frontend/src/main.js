import { createApp } from 'vue';
import { createPinia } from 'pinia';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';
import Tooltip from 'primevue/tooltip';
import BadgeDirective from 'primevue/badgedirective';
import StyleClass from 'primevue/styleclass';

// Importar componentes específicos de PrimeVue
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Message from 'primevue/message';
import FileUpload from 'primevue/fileupload';
import Dropdown from 'primevue/dropdown';
import InputNumber from 'primevue/inputnumber';
import Calendar from 'primevue/calendar';
import Textarea from 'primevue/textarea';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Toast from 'primevue/toast';
import MultiSelect from 'primevue/multiselect';
import SplitButton from 'primevue/splitbutton';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toolbar from 'primevue/toolbar';
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import Checkbox from 'primevue/checkbox';
import Avatar from 'primevue/avatar';
import Menu from 'primevue/menu';

import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';
import { useI18n } from './composables/useI18n'; // Importar el composable de internacionalización

import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';
import 'primevue/resources/primevue.min.css';
import 'primevue/resources/themes/lara-light-indigo/theme.css';
import './assets/styles/layout.css';
import './assets/styles/overrides.css';

const app = createApp(App);

app.use(createPinia());
app.use(router);

// Configurar i18n manualmente en lugar de usar un plugin externo
const { currentLocale, t } = useI18n();
// Añadir t como propiedad global para que esté disponible en todos los componentes
app.config.globalProperties.$t = t;

app.use(PrimeVue, {
    ripple: true
});
app.use(ToastService);
app.use(ConfirmationService);

app.directive('tooltip', Tooltip);
app.directive('badge', BadgeDirective);
app.directive('styleclass', StyleClass);

// Registrar componentes de PrimeVue
app.component('InputText', InputText);
app.component('Password', Password);
app.component('Button', Button);
app.component('Card', Card);
app.component('Message', Message);
app.component('FileUpload', FileUpload);
app.component('Dropdown', Dropdown);
app.component('InputNumber', InputNumber);
app.component('Calendar', Calendar);
app.component('Textarea', Textarea);
app.component('Dialog', Dialog);
app.component('Tag', Tag);
app.component('Toast', Toast);
app.component('MultiSelect', MultiSelect);
app.component('SplitButton', SplitButton);
app.component('TabView', TabView);
app.component('TabPanel', TabPanel);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Toolbar', Toolbar);
app.component('IconField', IconField);
app.component('InputIcon', InputIcon);
app.component('Checkbox', Checkbox);
app.component('Avatar', Avatar);
app.component('Menu', Menu);

// Manejador global de errores
app.config.errorHandler = (err, instance, info) => {
    console.error('Error Global:', err);
    console.error('Info:', info);
    
    // Intentar obtener la store de autenticación para mostrar el error
    try {
        const authStore = useAuthStore();
        // Aquí podrías agregar lógica para mostrar el error al usuario
        // por ejemplo, mostrando un toast o guardando el error para mostrarlo
    } catch (e) {
        console.error('Error accediendo a authStore:', e);
    }
};

app.mount('#app');