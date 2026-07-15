---
trigger: always_on
---

### 📐 CONVENCIÓN DE CÓDIGO
- **Python (FastAPI):**
  - Usa snake_case para variables y funciones
  - Usa PascalCase para clases y modelos de Pydantic
  - Máximo 100 caracteres por línea (PEP 8)
  - Documenta funciones con docstrings tipo Google: """Descripción\n\nArgs:\nReturns:"""
  
- **Vue 3:**
  - Usa camelCase para variables y funciones en <script setup>
  - Usa PascalCase para nombres de componentes
  - Usa kebab-case para nombres de archivos .vue
  - Orden en SFC: <template> → <script setup> → <style scoped>
  
- **Nomenclatura:**
  - Booleanos: isX, hasX, canX (ej: isLoading, hasError)
  - Funciones: verbo + sustantivo (ej: getUser, submitForm)
  - Eventos en Vue: handleX o onX (ej: handleSubmit, onClick)