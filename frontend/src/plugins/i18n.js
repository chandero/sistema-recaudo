import { createI18n } from 'vue-i18n';
import esMessages from '@/locales/es.json';
import enMessages from '@/locales/en.json';

// Obtener el idioma predeterminado del navegador o usar 'es'
const getDefaultLocale = () => {
  const storedLocale = localStorage.getItem('locale');
  if (storedLocale && (storedLocale === 'es' || storedLocale === 'en')) {
    return storedLocale;
  }
  
  const browserLocale = navigator.language.split('-')[0];
  return (browserLocale === 'en') ? 'en' : 'es';
};

const i18n = createI18n({
  legacy: false, // Usar composición API
  locale: getDefaultLocale(), // Idioma predeterminado
  fallbackLocale: 'es', // Idioma de reserva
  messages: {
    es: esMessages,
    en: enMessages
  }
});

export default i18n;