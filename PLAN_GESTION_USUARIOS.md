# Plan de diseño e implementación — Gestión de usuarios

## Estado de implementación

Primera entrega implementada el 15 de julio de 2026:

- API administrativa multi-tenant disponible en `/api/v1/users`.
- Registro público restringido y login bloqueado para cuentas inactivas.
- Pantalla `/admin/usuarios` con búsqueda, filtros, paginación y operaciones administrativas.
- Menú y rutas protegidos para `PLATFORM_ADMIN` y `TENANT_ADMIN`.
- Suite backend aislada: 14 pruebas aprobadas para autorización, separación de tenants, escalamiento de rol, estado, login, auditoría e invitaciones.
- Suite frontend: 12 pruebas aprobadas para reglas de formulario, asignación de roles, rutas públicas/protegidas y visibilidad del menú.
- Auditoría persistente de altas, ediciones, cambios de estado y restablecimientos; historial filtrado por tenant y sin secretos.
- Invitaciones de un solo uso con token hasheado, expiración, envío SMTP opcional y activación pública de cuenta.

La primera versión definida en este plan está implementada. Las evoluciones posteriores pueden incluir MFA, permisos personalizados y una bandeja visual de auditoría.

## 1. Objetivo

Implementar una opción segura y completa para administrar usuarios del sistema, respetando el modelo multi-tenant existente.

La funcionalidad permitirá:

- Al administrador de plataforma gestionar usuarios de cualquier tenant.
- Al administrador de tenant gestionar únicamente usuarios de su organización.
- Consultar, buscar y filtrar usuarios.
- Crear y editar usuarios.
- Activar o desactivar cuentas sin eliminar su historial.
- Restablecer contraseñas de forma controlada.
- Impedir acciones que comprometan el acceso o el aislamiento entre tenants.

La eliminación física de usuarios no forma parte del alcance inicial. Se utilizará desactivación para conservar la trazabilidad de procesos, tareas, importaciones y documentos asociados.

## 2. Estado actual

El proyecto ya cuenta con:

- Modelo `User` con `tenant_id`, rol, estado y contraseña cifrada.
- Roles `PLATFORM_ADMIN`, `TENANT_ADMIN`, `MANAGER`, `OPERATOR` y `VIEWER`.
- Repositorio y servicio con operaciones básicas de usuario.
- Un prototipo de interfaz dentro de `AdminView.vue`.
- Autenticación JWT y dependencias para usuario activo y administrador de plataforma.

Brechas detectadas:

- El frontend llama a `/users/` y `/tenants/{id}/users`, pero esas rutas no existen.
- Las rutas actuales `GET /auth/users` y `GET /auth/users/{id}` no exigen autenticación ni autorización.
- `POST /auth/register` permite registro público y asignación de rol/tenant; debe cerrarse o limitarse.
- La consulta actual del repositorio no filtra por tenant.
- La ruta `/admin` y la opción del menú no validan roles administrativos.
- No existen reglas para impedir auto-desactivación, escalamiento de privilegios o modificación de usuarios de otro tenant.
- No existe paginación con total, filtros ni respuestas de conflicto consistentes.
- El formulario tiene validación mínima y no muestra adecuadamente errores del backend.
- `AdminView.vue` usa `authStore.user`, pero el store expone `currentUser`.

## 3. Alcance funcional de la primera versión

### Incluido

- Pantalla independiente `/admin/usuarios`.
- Tabla paginada con búsqueda por nombre, usuario o correo.
- Filtros por tenant (solo plataforma), rol y estado.
- Alta de usuario.
- Edición de nombre, correo, nombre de usuario, rol y estado.
- Activación y desactivación con confirmación.
- Restablecimiento administrativo de contraseña.
- Restricción de opciones según el rol del usuario autenticado.
- Mensajes de éxito, validación y error.
- Pruebas de autorización y aislamiento multi-tenant.

### Fuera de alcance inicial

- Permisos personalizados por usuario.
- Invitaciones por correo y definición inicial de contraseña mediante enlace.
- Autenticación multifactor.
- Eliminación física.
- Auditoría visual completa. Los eventos mínimos pueden registrarse desde backend y evolucionar a una pantalla posterior.

## 4. Matriz de autorización

| Acción | Plataforma | Admin tenant | Otros roles |
|---|---:|---:|---:|
| Ver todos los tenants | Sí | No | No |
| Ver usuarios del tenant propio | Sí | Sí | No |
| Crear usuario de tenant | Sí | Sí | No |
| Crear `PLATFORM_ADMIN` | Sí | No | No |
| Asignar/cambiar tenant | Sí | No | No |
| Asignar `TENANT_ADMIN` | Sí | Sí | No |
| Editar usuario del tenant propio | Sí | Sí | No |
| Activar/desactivar | Sí | Sí, dentro de su tenant | No |
| Restablecer contraseña | Sí | Sí, dentro de su tenant | No |

Reglas adicionales:

- Un administrador de tenant nunca puede consultar ni modificar otro tenant.
- El backend determina el tenant efectivo; no confía en `tenant_id` enviado por un administrador de tenant.
- Nadie puede desactivar su propia cuenta.
- No se puede desactivar al último administrador activo de un tenant.
- Un administrador de tenant no puede crear, promover, editar ni desactivar un administrador de plataforma.
- Los usuarios inactivos no pueden iniciar sesión.

## 5. Diseño de experiencia de usuario

### Navegación

- Agregar “Usuarios” dentro de Administración.
- Mostrar la opción únicamente a `PLATFORM_ADMIN` y `TENANT_ADMIN`.
- Proteger también la ruta; ocultar el menú no sustituye la autorización del backend.

### Pantalla principal

Encabezado con título, descripción breve y botón “Nuevo usuario”. Debajo:

- Búsqueda con espera corta antes de consultar.
- Filtros: tenant, rol y estado.
- Tabla con: nombre, usuario, correo, tenant, rol, estado, último acceso si se incorpora después y acciones.
- Paginación desde servidor.
- Estados explícitos de carga, lista vacía y error.

Para un administrador de tenant se ocultan el filtro y la columna tenant.

### Crear/editar

Usar un diálogo o panel lateral con:

- Nombre completo.
- Nombre de usuario.
- Correo electrónico.
- Tenant, solo para administrador de plataforma.
- Rol, limitado a las opciones autorizadas.
- Contraseña temporal al crear.
- Estado al editar.

Validaciones visibles junto al campo. Al editar, la contraseña no se mezcla con los demás datos; el restablecimiento se ofrece como una acción separada.

### Acciones de estado y contraseña

- Preferir activar/desactivar frente a eliminar.
- Solicitar confirmación al desactivar e indicar el efecto sobre el acceso.
- Restablecer contraseña en un diálogo separado y no devolver ni registrar contraseñas.

## 6. Diseño técnico

### API propuesta

Crear un router dedicado con prefijo `/api/v1/users`:

- `GET /users?search=&role=&is_active=&tenant_id=&page=&page_size=`
- `GET /users/{user_id}`
- `POST /users`
- `PATCH /users/{user_id}`
- `PATCH /users/{user_id}/status`
- `POST /users/{user_id}/reset-password`

La lista responderá con `items`, `total`, `page`, `page_size` y `pages`. Los errores usarán de forma consistente `400` para reglas de negocio, `403` para falta de permiso, `404` para recursos no visibles/existentes y `409` para usuario o correo duplicado.

Las rutas de usuarios dentro de `auth.py` deben retirarse o migrarse al nuevo router. El registro público debe deshabilitarse; la creación administrativa se hará mediante `POST /users`.

### Backend

- Crear dependencias reutilizables para roles administrativos.
- Centralizar la resolución de alcance: plataforma puede seleccionar tenant; administrador de tenant queda forzado a su `tenant_id`.
- Añadir consultas paginadas y filtradas al repositorio.
- Incorporar validación de duplicados para correo y nombre de usuario.
- Sincronizar `role == PLATFORM_ADMIN` con `is_platform_admin`, evitando dos fuentes de verdad inconsistentes. Como mejora posterior, eliminar el booleano redundante mediante migración.
- Aplicar la política de contraseña existente tanto en creación como en restablecimiento.
- Rechazar autenticación de usuarios inactivos antes de emitir JWT.
- Actualizar `updated_at` en toda mutación.
- Traducir excepciones de integridad a respuestas `409`, sin exponer detalles internos.

### Datos

- Verificar en todos los ambientes los índices únicos de `email` y `username` definidos por la migración inicial.
- Mantener inicialmente unicidad global, consistente con el inicio de sesión por correo/usuario sin tenant.
- No agregar una migración salvo que la base real difiera del esquema o se decida cambiar la unicidad a nivel tenant.

### Frontend

- Crear `UsuariosView.vue` en lugar de seguir ampliando el diálogo anidado de `AdminView.vue`.
- Crear `userService` en `services/api.js`.
- Añadir ruta con metadatos de roles y una guarda de autorización.
- Hacer el menú reactivo a `authStore.currentUser`.
- Reutilizar `PageHeader`, `DataTableWrapper`, `ConfirmationDialog`, `UserFeedback` y los patrones de formularios existentes cuando sean adecuados.
- Añadir textos a los archivos de internacionalización.

## 7. Tareas de implementación

### Fase 0 — Cerrar brechas críticas

- [ ] Proteger o retirar `GET /auth/users` y `GET /auth/users/{id}`.
- [ ] Deshabilitar el registro público o restringirlo a administradores autorizados.
- [ ] Impedir login de usuarios inactivos.
- [ ] Añadir pruebas que demuestren que un usuario anónimo o no administrativo recibe `401/403`.

### Fase 1 — Contrato y autorización backend

- [ ] Crear esquemas de creación, actualización, cambio de estado, restablecimiento y lista paginada.
- [ ] Crear dependencia para `PLATFORM_ADMIN | TENANT_ADMIN`.
- [ ] Implementar el resolver de tenant y las reglas de escalamiento de rol.
- [ ] Crear router `/users` y registrarlo en `api.py`.
- [ ] Implementar listado paginado con búsqueda y filtros.
- [ ] Implementar detalle, creación y actualización parcial.
- [ ] Implementar activar/desactivar con reglas de auto-desactivación y último administrador.
- [ ] Implementar restablecimiento de contraseña.
- [ ] Normalizar conflictos de correo/usuario a `409`.

### Fase 2 — Interfaz

- [ ] Crear `userService` con los seis casos de uso de la API.
- [ ] Crear `UsuariosView.vue` con carga, vacío, error, filtros y paginación.
- [ ] Crear formulario de alta/edición con validación de campos y roles permitidos.
- [ ] Crear confirmación de activación/desactivación.
- [ ] Crear diálogo independiente para restablecer contraseña.
- [ ] Mostrar retroalimentación de éxito y mensajes del backend.
- [ ] Añadir ruta `/admin/usuarios` y control de acceso por rol.
- [ ] Mostrar “Usuarios” en el menú solo a roles administrativos.
- [ ] Corregir referencias a `authStore.user` por `authStore.currentUser` donde aplique.
- [ ] Retirar el prototipo de usuarios anidado en `AdminView.vue` una vez migrado.
- [ ] Añadir traducciones en español e inglés.

### Fase 3 — Pruebas y calidad

- [ ] Pruebas backend para cada endpoint y rol.
- [ ] Pruebas de aislamiento: un admin de tenant no ve ni modifica otro tenant.
- [ ] Pruebas de escalamiento: un admin de tenant no puede crear `PLATFORM_ADMIN` ni cambiar `tenant_id`.
- [ ] Pruebas de duplicados, contraseña débil, auto-desactivación y último administrador.
- [ ] Pruebas frontend de visibilidad del menú, guarda de ruta, filtros y formularios.
- [ ] Verificación manual responsive y accesibilidad básica: etiquetas, foco, teclado y contraste.
- [ ] Ejecutar análisis/build del frontend y suite backend.

### Fase 4 — Entrega

- [ ] Documentar endpoints y matriz de permisos.
- [ ] Definir procedimiento para crear el primer administrador de plataforma sin registro público.
- [ ] Preparar datos de prueba para plataforma, dos tenants y todos los roles.
- [ ] Validar criterios de aceptación con usuarios administrativos.

## 8. Criterios de aceptación

- Un usuario no autenticado no puede consultar ni modificar usuarios.
- Un rol no administrativo no puede acceder a la pantalla ni a la API administrativa.
- Un administrador de tenant solo obtiene usuarios de su tenant, aunque manipule parámetros o cuerpos HTTP.
- Solo plataforma puede crear administradores de plataforma o cambiar un usuario de tenant.
- Crear o editar muestra errores comprensibles ante correo/usuario duplicado o datos inválidos.
- Desactivar un usuario bloquea un nuevo inicio de sesión.
- No es posible auto-desactivarse ni dejar un tenant sin administrador activo.
- La lista conserva filtros al cambiar de página y refleja el total entregado por el servidor.
- Las acciones exitosas actualizan la tabla y muestran confirmación sin recargar toda la aplicación.
- No se envían hashes ni contraseñas en respuestas, logs o mensajes de error.

## 9. Orden recomendado y estimación

1. Seguridad crítica y pruebas de regresión: 0.5–1 día.
2. API, reglas multi-tenant y pruebas: 2–3 días.
3. Pantalla, formularios y navegación: 2–3 días.
4. Pruebas integrales, ajustes y documentación: 1–2 días.

Estimación total: 5.5–9 días de desarrollo, dependiendo de la infraestructura actual de pruebas y del estado real de las bases desplegadas.

## 10. Decisiones pendientes

- Confirmar si `TENANT_ADMIN` puede nombrar a otro `TENANT_ADMIN`; el plan propone que sí, protegiendo al último administrador activo.
- Confirmar si la contraseña inicial será comunicada por un canal externo o si se implementará invitación por correo en una segunda versión.
- Confirmar si correo y nombre de usuario seguirán siendo únicos globalmente. El plan conserva esa regla porque el login actual no solicita tenant.
- Definir si se requiere auditoría persistente desde la primera versión; es recomendable registrar al menos actor, acción, usuario afectado y fecha.
