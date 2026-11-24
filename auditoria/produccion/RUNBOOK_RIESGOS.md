# RUNBOOK — atención de riesgos en giron.cyberrit.tiksgroup.co

Rama que contiene las correcciones de código: `hardening/riesgos-pre-tarea`
(sobre `baseline/produccion-20261124`, que es idéntica byte a byte a lo desplegado).

Este documento separa dos cosas distintas:

- **Resuelto en código** (ya está en la rama, solo espera despliegue).
- **Resuelto en el servidor** (nada de esto se puede arreglar desde el repositorio;
  requiere escribir en producción). Cada procedimiento trae backup y rollback.

Variables usadas (`/opt/cyberrit/.env` en el servidor, `SSH_KEY` local):

```bash
SSH="ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co"
```

---

## 1. Estado de los riesgos

| # | Riesgo | Estado | Dónde |
|---|--------|--------|-------|
| R1 | Funcionalidad de producción fuera de control de versiones | **Cerrado** | rama `baseline/produccion-20261124` + etiqueta `prod-20261124` |
| R2 | Alembic con dos cabeceras (rompe `upgrade head` y `run_migrations.py`) | **Cerrado** | `008_merge_cabeceras.py` |
| R3 | Cuenta `admin` / `admin123` como PLATFORM_ADMIN accesible desde internet | **Abierto** | servidor (§2) |
| R4 | `SECRET_KEY` publicada en el historial de git | **Abierto** | servidor + git (§3) |
| R5 | Base de datos activa dentro del árbol de código (`backend/test.db`) | **Abierto** | servidor (§4) |
| R6 | Producción con `DEBUG=True`, `--reload`, `/docs` y `/openapi.json` públicos | **Cerrado en código / abierto en servidor** | §5 |
| R7 | `.env`, 40 `__pycache__/*.pyc` y un `.bak` versionados | **Cerrado** | índice de git limpio |
| R8 | Despliegue sin versión registrada ni respaldo previo | **Cerrado** | `update_system.sh`, `deploy_to_server.sh` |
| R9 | Esquema producido por `create_all` y no por migraciones (4 tablas sin revisión) | **Abierto** | §6 |

---

## 2. R3 — CREDENCIAL COMPROMETIDA: `admin` / `admin123` (P0)

Evidencia tomada el 2026-11-24 sobre `/opt/cyberrit/backend/test.db` (solo lectura):

- Usuario `id=1`, `username=admin`, `role=PLATFORM_ADMIN`, `is_active=1`,
  `is_platform_admin=1`.
- `verify_password("admin123", hash)` devolvió **True** dentro del contenedor.
- La cuenta la creó el arranque de la aplicación (`app/main.py` sembraba
  `get_password_hash("admin123")` si no existía `admin`).
- Alcance de la cuenta: tenant real **Alcaldia de Giron** (130 deudores, 1 417
  obligaciones, 30 acuerdos de pago).

La aplicación ya no siembra esa contraseña (ahora exige `BOOTSTRAP_ADMIN_PASSWORD`),
pero **la cuenta sigue existiendo con la clave débil**. Hay que rotarla.

```bash
# 2.1 Rotar dentro del contenedor: la clave se genera y se aplica en el servidor,
#     nunca viaja por la línea de órdenes ni queda en el historial de bash.
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co \
  "docker exec -i cartera_backend python3 -" <<'PY'
from sqlalchemy import text
from app.core.database import engine
from app.core.security import get_password_hash, verify_password
import secrets

nueva = secrets.token_urlsafe(18)
with engine.connect() as con:
    antes = con.execute(text("SELECT hashed_password FROM users WHERE username='admin'")).scalar_one()
    print("antes acepta admin123:", verify_password("admin123", antes))

with engine.begin() as con:
    con.execute(
        text("UPDATE users SET hashed_password=:h, is_active=0 WHERE username='admin'"),
        {"h": get_password_hash(nueva)},
    )

with engine.connect() as con:
    despues = con.execute(text("SELECT hashed_password FROM users WHERE username='admin'")).scalar_one()
    print("despues acepta admin123:", verify_password("admin123", despues))
    print("CREDENCIAL ADMIN NUEVA (guardala en el gestor y borra esta linea):", nueva)
PY
```

`is_active=0` deja la cuenta inhabilitada pero conserva el historial de auditoría.
Si prefieres conservarla operativa, quita el `is_active=0` de la sentencia.

**Comprobar si hubo accesos no autorizados** (lecturas del log de la app):

```bash
# 2.2 Comprobar si hubo accesos no autorizados (lecturas del log de la app)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co \
  "grep -a 'login' /opt/cyberrit/backend/logs/app.log 2>/dev/null | tail -40; \
   grep -ac 'admin@sistema-cobro.com' /opt/cyberrit/backend/logs/app.log 2>/dev/null"
```

Rollback: devolver `is_active=1` y restaurar la contraseña previa desde el backup de
`/opt/cyberrit/backups` **solo** si hace falta algún acceso histórico; la clave débil
no debe volver a existir.

---

## 3. R4 — `SECRET_KEY` publicada en git (P0)

`.env` estuvo commiteado (y sigue en el historial de `main` y de las ramas). Todos los
JWT firmados con esa clave son forjables por quien tenga el repositorio.

```bash
# 3.1 Clave nueva generada en el propio servidor y escrita en .env (modo 600)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  cd /opt/cyberrit &&
  cp -a .env .env.pre-rot-\$(date +%Y%m%d-%H%M%S) && chmod 600 .env.pre-rot-* &&
  NUEVA=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))') &&
  sed -i \"s|^SECRET_KEY=.*|SECRET_KEY=\$NUEVA|\" .env && chmod 600 .env &&
  grep -q '^SECRET_KEY=' .env && echo 'SECRET_KEY rotada (los JWT activos quedan invalidos)'
"

# 3.2 Reiniciar backend (cierra todas las sesiones activas: los usuarios vuelven a entrar)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "cd /opt/cyberrit && docker compose up -d backend"
```

Efecto esperado: cualquier token emitido antes deja de ser válido. Es la intención.

Borrar la clave del historial (`git filter-repo` + force-push) es destructivo sobre
`origin`; no se hizo. Mientras el historial exista, **la rotación es obligatoria**, no
opcional.

---

## 4. R5 — Sacar la base de datos del árbol de código (P1)

Hoy la base activa es `/opt/cyberrit/backend/test.db`, dentro del directorio que se
sincroniza con rsync. Está protegida solo por una lista de `--exclude`; un cambio en
esa lista o un `--delete-excluded` pierde la cartera del municipio.

El `docker-compose.yml` de la rama ya monta `/var/lib/cyberrit` y exige `DATABASE_URL`;
faltan los datos reales, que hay que mover:

```bash
# 4.1 Respaldo consistente (no copia en frío)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  mkdir -p /opt/cyberrit/backups /var/lib/cyberrit &&
  sqlite3 /opt/cyberrit/backend/test.db \".backup '/opt/cyberrit/backups/test-db-pre-mov-\$(date +%Y%m%d-%H%M%S).db'\" &&
  ls -lh /opt/cyberrit/backups | tail -3"

# 4.2 Copiar al nuevo destino y verificar conteos antes de tocar la configuración
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  cp -a /opt/cyberrit/backend/test.db /var/lib/cyberrit/cartera.db &&
  docker run --rm -v /opt/cyberrit/backend:/old -v /var/lib/cyberrit:/new python:3.11-slim sh -c '
    apt-get -qq update && apt-get -qqy install sqlite3 >/dev/null &&
    for t in clients obligations cobro_processes payment_agreements users; do
      echo \"\$t old=\$(sqlite3 /old/test.db \"select count(*) from \$t\") new=\$(sqlite3 /new/cartera.db \"select count(*) from \$t\")\"
    done'"

# 4.3 Apuntar la aplicación al nuevo archivo
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  cd /opt/cyberrit && \
  grep -q '^DATABASE_URL=' .env || echo 'DATABASE_URL=sqlite:////var/lib/cyberrit/cartera.db' >> .env; \
  sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:////var/lib/cyberrit/cartera.db|' .env && \
  docker compose up -d backend"

# 4.4 Confirmar que los datos se ven y SOLO ENTONCES retirar el .db antiguo
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co \
  "curl -s http://127.0.0.1:8055/health && docker logs cartera_backend --tail 20"
# mv /opt/cyberrit/backend/test.db /opt/cyberrit/backups/test.db.retirado
```

Rollback: restaurar `DATABASE_URL=sqlite:////app/test.db` en `.env`,
`docker compose up -d backend`, y `mv` del archivo retirado a su sitio.

Nota: `run_migrations.py` ahora deduce su objetivo de `DATABASE_URL` (antes usaba una
ruta fija), así que el script de migraciones sigue apuntando a la base correcta.

---

## 5. R6 — Pasar el contenedor a configuración de producción (P1)

La rama niega el arranque si `ENVIRONMENT=production` coincide con valores de
desarrollo (así es como se validó, §8). Para que el servidor adopte la postura segura:

```bash
# 5.1 Dejar el .env del servidor en modo producción
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  cd /opt/cyberrit && \
  sed -i 's|^ENVIRONMENT=.*|ENVIRONMENT=production|; s|^DEBUG=.*|DEBUG=False|' .env && \
  { grep -q '^EXPOSE_API_DOCS=' .env || echo 'EXPOSE_API_DOCS=False'; } >> .env && \
  { grep -q '^SEED_DEMO_DATA=' .env || echo 'SEED_DEMO_DATA=False'; } >> .env && \
  { grep -q '^CARTERA_DATA_DIR=' .env || echo 'CARTERA_DATA_DIR=/var/lib/cyberrit'; } >> .env"

# 5.2 Desplegar código de la rama (sin --reload) y levantar
./deploy_to_server.sh            # o ./update_system.sh si solo cambia backend

# 5.3 Verificar que la superficie pública desapareció
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co "
  for u in /health /docs /openapi.json /redoc; do
    printf '%-16s %s\n' \$u \"\$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8055\$u)\"; done"
```

Esperado: `200`, `404`, `404`, `404`. El frontend no usa `/docs`, así que la
aplicación sigue funcionando igual para los usuarios.

Si el contenedor no arranca, el log dice exactamente qué falta (clave corta, base sin
definir, docs activas): es el comportamiento diseñado. Rollback: devolver
`ENVIRONMENT=development` en `.env` y `docker compose up -d backend`.

---

## 6. R9 — Esquema sin migraciones completas (P2)

Comparación real: una base construida **solo con Alembic** tiene 20 tablas; la base
activa del servidor tiene 24.

Sin revisión de Alembic (las creó `create_all` desde los modelos):
`import_batches`, `permissions`, `process_configs`, `workflow_transitions`.

Además, `backend/run_migrations.py` crea algunas tablas con DDL escrito a mano que
**no coincide** con la revisión equivalente (p. ej. `notifications` con `link` y
`notification_type DEFAULT 'info'`, frente a `007_notifications.py` sin `link` y
`DEFAULT 'GENERAL'`). Qué forma tiene la tabla en el servidor depende de cuál de los
dos caminos la creó primero.

Procedimiento recomendado (ventana de mantenimiento, 15 min):

```bash
# 6.1 Stampar la base activa en la revisión que realmente tiene (no aplica DDL)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co \
  "cd /opt/cyberrit && docker compose exec -T backend alembic stamp 007_notifications"

# 6.2 A partir de ahí, cambios de esquema SOLO con 'alembic revision' + 'upgrade head'
```

Antes de cerrar las 4 tablas huérfanas hay que decidir si `permissions` y
`process_configs` siguen vivas (los modelos registrados son `TenantProcessConfig`,
`WorkflowTransition`, `ImportBatch`); la revisión nueva debe crearse con
`alembic revision --autogenerate` sobre una base stampada, revisando el DDL generado a
mano antes de aceptarlo. **No** se generó automáticamente en esta rama para no firmar
migraciones no revisadas.

---

## 7. Limpieza adicional del servidor (P3)

```bash
# 7.1 Configuraciones de nginx huérfanas (5 archivos versionados activos en sites-enabled)
ssh -i ~/.ssh/id_ed25519_tmsoft root@giron.tiksgroup.co \
  "ls -1 /etc/nginx/sites-enabled/ && nginx -T | grep -c 'server_name'"

# 7.2 El `dist` del frontend vive en dos sitios (volumen y dentro de la imagen).
# Decidir uno: montar ./frontend/dist (despliegue rápido) O empaquetarlo en la imagen
# (reproducible). Mientras existan ambos, un despliegue puede dejar la versión vieja.
```

---

## 8. Validación ejecutada el 2026-11-24 (rama `hardening/riesgos-pre-tarea`)

| Prueba | Resultado |
|--------|-----------|
| `alembic heads` | 1 cabecera: `008_merge_cabeceras` (antes: 2) |
| `alembic upgrade head` desde base vacía | OK, 21 tablas, versión `008_merge_cabeceras` |
| Arranque con `ENVIRONMENT=production` y valores de desarrollo | **Rechazado** con detalle de `SECRET_KEY`, `SEED_DEMO_DATA`, `EXPOSE_API_DOCS` |
| Arranque con producción bien configurada | `docs_url`, `redoc_url`, `openapi_url` = `None`; semilla desactivada |
| Contrato de API en desarrollo | 84 rutas = las 84 de producción |
| `/health` | `{"status":"healthy"}` |
| `pytest backend/tests` | 27 pruebas en verde |
| `bash -n` de los scripts de despliegue | Sin errores de sintaxis |
| Índices de git tras limpieza | 0 archivos `.env`, `.pyc`, `.bak` versionados |
