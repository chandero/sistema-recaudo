---
trigger: model_decision
description: Optimización de rendimiento para FastAPI y Vue 3: aplicar cuando se creen endpoints con listas, consultas a base de datos, componentes con datos derivados, búsquedas, o cualquier código que pueda bene
---

### ⚡ PERFORMANCE
- **FastAPI:**
  - Usa connection pooling para bases de datos
  - Implementa caché con Redis para datos frecuentes
  - Usa background tasks para operaciones pesadas
  - Paginación obligatoria en endpoints que retornen listas
  
- **Vue 3:**
  - Usa computed() para datos derivados (evita recálculos)
  - Lazy loading para rutas y componentes pesados
  - Usa v-memo para listas grandes que no cambian
  - Debounce en inputs de búsqueda (300ms mínimo)
  - Evita watchers innecesarios (prefiere computed)