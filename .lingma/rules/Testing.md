---
trigger: glob
glob: test_*
---

### 🧪 TESTING
- **Python (pytest):**
  - Usa pytest con fixtures para datos de prueba
  - Nombra tests: test_<funcion>_<escenario> (ej: test_get_user_not_found)
  - Usa httpx.AsyncClient para testear endpoints async
  - Mockea dependencias externas con pytest-mock
  
- **Vue 3:**
  - Usa Vitest + @vue/test-utils
  - Testea componentes clave (formularios, modales)
  - Verifica que se emitan los eventos correctos
  - Ejemplo:
    ```javascript
    import { mount } from '@vue/test-utils'
    import LoginForm from './LoginForm.vue'
    
    test('emite submit con datos del formulario', async () => {
      const wrapper = mount(LoginForm)
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('submit')).toBeTruthy()
    })
    ```