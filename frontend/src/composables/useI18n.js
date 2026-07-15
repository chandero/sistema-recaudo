import { ref, computed } from 'vue';

// Importar archivos de traducción
import esMessages from '@/locales/es.json';
import enMessages from '@/locales/en.json';

const messages = {
  es: esMessages,
  en: enMessages
};

// Obtener el idioma predeterminado del navegador o usar 'es'
const getDefaultLocale = () => {
  const storedLocale = localStorage.getItem('locale');
  // Verificar que el idioma almacenado exista en nuestros mensajes
  if (storedLocale && messages[storedLocale]) {
    return storedLocale;
  }
  
  const browserLocale = navigator.language.split('-')[0];
  // Verificar que el idioma del navegador exista en nuestros mensajes
  return messages[browserLocale] ? browserLocale : 'es';
};

export const useI18n = () => {
  const locale = ref(getDefaultLocale());

  const t = (key, params = {}) => {
    // Asegurarse de que el idioma actual exista en los mensajes
    if (!messages[locale.value]) {
      console.error(`Idioma no encontrado: ${locale.value}, usando 'es' por defecto`);
      return key;
    }

    const keys = key.split('.');
    let message = messages[locale.value];
    
    for (const k of keys) {
      if (message && typeof message === 'object') {
        message = message[k];
      } else {
        // Si no encontramos el mensaje, intentar buscar en otros niveles
        break;
      }
    }
    
    if (typeof message !== 'string') {
      // Devolver la clave original si no se encuentra la traducción
      console.warn(`Traducción no encontrada para la clave: ${key}`);
      return key;
    }
    
    // Reemplazar parámetros en el mensaje
    let translatedMessage = message;
    for (const param in params) {
      translatedMessage = translatedMessage.replace(new RegExp(`\\{\\{${param}\\}\\}`, 'g'), params[param]);
    }
    
    return translatedMessage;
  };

  const setLocale = (newLocale) => {
    if (messages[newLocale]) {
      locale.value = newLocale;
      localStorage.setItem('locale', newLocale);
    } else {
      console.warn(`Intentando establecer un idioma no soportado: ${newLocale}`);
    }
  };

  const currentLocale = computed(() => locale.value);

  return {
    t,
    setLocale,
    currentLocale,
    availableLocales: Object.keys(messages)
  };
};