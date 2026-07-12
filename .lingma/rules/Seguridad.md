---
trigger: always_on
---

### 🔒 SEGURIDAD (CRÍTICO)
- **FastAPI:**
  - NUNCA guardes contraseñas en texto plano (usa bcrypt/passlib)
  - Valida TODAS las entradas con Pydantic (previene inyección SQL)
  - Usa OAuth2 con JWT para autenticación
  - Configura CORS correctamente (no uses allow_origins=["*"] en producción)
  - Sanitiza inputs de usuario antes de procesarlos
  
- **Vue 3:**
  - NUNCA uses v-html con datos de usuario (riesgo de XSS)
  - Valida inputs en el frontend ANTES de enviar al backend
  - Usa HTTPS para todas las llamadas a la API
  - No almacenes tokens sensibles en localStorage (usa httpOnly cookies si es posible)