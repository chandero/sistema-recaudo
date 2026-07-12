---
trigger: always_on
---

### 🚨 MANEJO DE ERRORES (OBLIGATORIO)
- **FastAPI:**
  - NUNCA dejes un endpoint sin try-except
  - Usa HTTPException con códigos HTTP correctos (400, 404, 500)
  - Retorna mensajes de error claros y seguros (no expongas stack traces)
  - Ejemplo:
    ```python
    try:
        result = await service.get_user(user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    ```

- **Vue 3:**
  - Usa try-catch en todas las funciones async
  - Muestra errores al usuario con PrimeVue Toast o Message
  - Ejemplo:
    ```javascript
    const submitForm = async () => {
      try {
        isLoading.value = true
        await api.submit(formData.value)
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Datos guardados' })
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message })
      } finally {
        isLoading.value = false
      }
    }
    ```