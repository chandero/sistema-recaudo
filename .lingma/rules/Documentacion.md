---
trigger: manual
---

### 📚 DOCUMENTACIÓN
- Genera comentarios solo para lógica compleja (no para código obvio)
- Documenta funciones públicas con:
  - Qué hace
  - Parámetros esperados
  - Qué retorna
  - Posibles excepciones
- Para endpoints de FastAPI, usa response_model para generar OpenAPI docs automáticamente
- En Vue, documenta props con JSDoc o TypeScript