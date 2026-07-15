import { ref, reactive } from 'vue'

/**
 * Composable para manejo de formularios reutilizable
 * @param {Object} initialForm - Estado inicial del formulario
 */
export function useForm(initialForm = {}) {
  const form = reactive({ ...initialForm })
  const errors = ref({})
  const submitting = ref(false)

  /**
   * Actualiza un campo del formulario
   * @param {string} field - Nombre del campo
   * @param {any} value - Valor del campo
   */
  const updateField = (field, value) => {
    form[field] = value
    // Limpiar error si se actualiza el campo
    if (errors.value[field]) {
      delete errors.value[field]
    }
  }

  /**
   * Reinicia el formulario a sus valores iniciales
   */
  const resetForm = () => {
    Object.keys(form).forEach(key => {
      form[key] = initialForm[key] || null
    })
    errors.value = {}
  }

  /**
   * Valida el formulario
   * @param {Object} validationRules - Reglas de validación
   * @returns {boolean} - True si es válido, false si hay errores
   */
  const validate = (validationRules = {}) => {
    errors.value = {}
    let isValid = true

    for (const [field, rules] of Object.entries(validationRules)) {
      for (const rule of rules) {
        const result = rule(form[field], form)
        if (typeof result === 'string') {
          errors.value[field] = result
          isValid = false
          break
        }
      }
    }

    return isValid
  }

  /**
   * Establece errores manualmente
   * @param {Object} newErrors - Objeto con errores
   */
  const setErrors = (newErrors) => {
    errors.value = { ...newErrors }
  }

  /**
   * Limpia un error específico o todos los errores
   * @param {string} field - Nombre del campo (opcional)
   */
  const clearError = (field = null) => {
    if (field && errors.value[field]) {
      delete errors.value[field]
    } else {
      errors.value = {}
    }
  }

  return {
    form,
    errors,
    submitting,
    updateField,
    resetForm,
    validate,
    setErrors,
    clearError
  }
}