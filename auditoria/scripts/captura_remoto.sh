#!/bin/bash
# Captura EN SOLO LECTURA del estado desplegado en giron.tiksgroup.co (/opt/cyberrit).
# Ninguna orden remota escribe, reinicia ni modifica el servidor: solo cat/ls/find/md5sum/
# sha256sum/docker inspect/curl GET local.
set -euo pipefail

SSH_KEY="$HOME/.ssh/id_ed25519_tmsoft"
HOST="root@giron.tiksgroup.co"
APP="/opt/cyberrit"
OUT="$(cd "$(dirname "$0")/.." && pwd)/produccion"
mkdir -p "$OUT/config" "$OUT/diffs"

ssh_run() { ssh -o BatchMode=yes -o ConnectTimeout=15 -i "$SSH_KEY" "$HOST" "$@"; }

echo "[1/7] Metadatos del servidor y contenedores"
ssh_run bash -s >"$OUT/01_metadata.txt" <<'REMOTE'
echo "fecha_servidor=$(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "hostname=$(hostname)"
echo "ultimo_deploy=$(cat /opt/cyberrit/.last_update 2>/dev/null)"
echo "git_en_app=$(ls -d /opt/cyberrit/.git 2>/dev/null || echo 'sin .git')"
echo
echo "== contenedores =="
docker ps -a --format '{{.Names}} | {{.Image}} | {{.Status}}' | grep -Ei 'cartera|cyberrit' || true
echo
echo "== imagenes =="
docker images --format '{{.Repository}}:{{.Tag}} | creada={{.CreatedSince}} | id={{.ID}}' | grep -Ei 'cartera|cyberrit' || true
echo
echo "== mounts =="
docker inspect cartera_backend --format '{{json .Mounts}}'
docker inspect cartera_frontend --format '{{json .Mounts}}'
echo
echo "== cmd backend en ejecucion =="
docker inspect cartera_backend --format '{{json .Config.Cmd}} {{json .Path}} {{json .Args}}'
echo
echo "== redis =="
docker inspect cartera_redis --format '{{json .Config.Cmd}}'
REMOTE

echo "[2/7] Arbol de hashes del codigo en produccion"
ssh_run bash -s >"$OUT/hashes_remoto.txt" <<'REMOTE'
cd /opt/cyberrit
find . -type f \
    \( -name '*.py' -o -name '*.vue' -o -name '*.js' -o -name '*.json' \
       -o -name '*.yml' -o -name '*.yaml' -o -name '*.conf' -o -name '*.md' \
       -o -name '*.ini' -o -name '*.txt' -o -name 'Dockerfile' \) \
    -not -path './node_modules/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/__pycache__/*' \
    -not -path '*/.venv/*' \
    -not -path './frontend/dist/*' \
    -not -path './generados/*' \
    -not -path './.qoder/*' \
    -not -path './backend/logs/*' \
    -not -path './backend/app/uploads/generated/*' \
    -not -name 'package-lock.json' \
    -not -name '*.min.js' \
    -print0 | sort -z | xargs -0 md5sum | sed -e 's|\./||'
REMOTE

echo "[3/7] Listado completo con fechas de modificacion"
ssh_run bash -s >"$OUT/02_listado_mtimes.txt" <<'REMOTE'
cd /opt/cyberrit
find . -type f \
    -not -path '*/node_modules/*' -not -path '*/__pycache__/*' \
    -not -path './frontend/dist/assets/*' -not -path './.git/*' \
    -not -path './backend/app/uploads/*' \
    -not -path './.qoder/*' \
    -printf '%TY-%Tm-%Td %TH:%TM  %s  %p\n' | sort -r
REMOTE

echo "[4/7] Configuracion de despliegue y reverse proxy"
ssh_run bash -s >"$OUT/config/docker-compose.yml" <<'REMOTE'
cat /opt/cyberrit/docker-compose.yml
REMOTE
ssh_run bash -s >"$OUT/config/env_nombres.txt" <<'REMOTE'
echo "# Solo nombres de variable; valores redactados deliberadamente"
sed -E 's/^([A-Za-z_][A-Za-z0-9_]*)=.*/\1=<redactado>/' /opt/cyberrit/.env
REMOTE
ssh_run bash -s >"$OUT/config/nginx_activo.txt" <<'REMOTE'
echo "== sites-enabled =="
ls -la /etc/nginx/sites-enabled/ 2>/dev/null
echo "== conf.d =="
ls -la /etc/nginx/conf.d/ 2>/dev/null
for f in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*cyberrit* /etc/nginx/conf.d/*cartera* /etc/nginx/conf.d/*giron*; do
    [ -f "$f" ] || continue
    echo "===== $f ====="
    cat "$f"
done
echo "== server_name declarados =="
grep -rE '^\s*server_name' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | sort -u
REMOTE
ssh_run bash -s >"$OUT/config/dockerfiles.txt" <<'REMOTE'
for f in /opt/cyberrit/backend/Dockerfile /opt/cyberrit/frontend/Dockerfile /opt/cyberrit/frontend/nginx.conf; do
    echo "===== $f ====="
    cat "$f" 2>/dev/null || echo "(no existe)"
done
REMOTE

echo "[5/7] Build del frontend servido"
ssh_run bash -s >"$OUT/03_frontend_dist.txt" <<'REMOTE'
echo "== index.html =="
ls -la /opt/cyberrit/frontend/dist/index.html 2>/dev/null
cat /opt/cyberrit/frontend/dist/index.html 2>/dev/null
echo
echo "== assets =="
ls -la /opt/cyberrit/frontend/dist/assets/ 2>/dev/null
echo
echo "== index.prod.html versionado en el servidor =="
cat /opt/cyberrit/frontend/index.prod.html 2>/dev/null | grep -oE '/assets/[A-Za-z0-9._-]+' | sort -u
REMOTE
ssh_run bash -s >"$OUT/04_openapi_prod.json" <<'REMOTE'
for url in http://127.0.0.1:8055/openapi.json http://127.0.0.1:8055/api/v1/openapi.json http://127.0.0.1:5055/openapi.json; do
    cuerpo=$(curl -s -m 10 "$url")
    if printf '%s' "$cuerpo" | head -c 1 | grep -q '{'; then
        echo "$cuerpo"
        exit 0
    fi
done
echo '{"error":"openapi no accesible"}'
REMOTE
ssh_run bash -s >"$OUT/07_health_y_frontentranja.txt" <<'REMOTE'
echo "== /health del backend =="
curl -s -m 10 http://127.0.0.1:8055/health; echo
echo
echo "== index.html DENTRO del contenedor de frontend (no tiene bind mount) =="
docker exec cartera_frontend sh -c 'ls -la /usr/share/nginx/html/index.html 2>/dev/null; grep -oE "/assets/index-[A-Za-z0-9_-]+\\.(js|css)" /usr/share/nginx/html/index.html 2>/dev/null | sort -u'
echo
echo "== index.html EN DISCO /opt/cyberrit/frontend/dist =="
grep -oE '/assets/index-[A-Za-z0-9_-]+\.(js|css)' /opt/cyberrit/frontend/dist/index.html 2>/dev/null | sort -u
echo
echo "== assets dentro del contenedor =="
docker exec cartera_frontend sh -c 'ls /usr/share/nginx/html/assets 2>/dev/null | wc -l'
echo "== assets en disco =="
ls /opt/cyberrit/frontend/dist/assets 2>/dev/null | wc -l
REMOTE

echo "[6/7] Inventario de datos (sin extraer contenido)"
ssh_run bash -s >"$OUT/05_datos_inventario.txt" <<'REMOTE'
echo "== /opt/riap/db =="
ls -la /opt/riap/db 2>/dev/null
echo
echo "== sha256 de bases sqlite =="
find /opt/riap/db /opt/cyberrit -maxdepth 3 -name '*.db' -exec sha256sum {} \; 2>/dev/null
echo
echo "== tablas y version de esquema =="
python3 - <<'PY' 2>/dev/null || echo "sin acceso python/sqlite en el servidor"
import sqlite3, glob
for db in sorted(glob.glob('/opt/riap/db/*.db') + glob.glob('/opt/cyberrit/backend/*.db')):
    print('---', db)
    try:
        con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
        cur = con.cursor()
        tablas = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print('tablas(%d):' % len(tablas), ', '.join(tablas))
        if 'alembic_version' in tablas:
            print('alembic_version:', list(cur.execute('SELECT version_num FROM alembic_version')))
        for t in ('tenants', 'clients', 'obligations', 'payment_agreements', 'notifications'):
            if t in tablas:
                print('  filas %s = %s' % (t, cur.execute('SELECT COUNT(*) FROM %s' % t).fetchone()[0]))
        con.close()
    except Exception as exc:
        print('  error:', exc)
PY
REMOTE

echo "[7/7] Inventario de modulos por area"
ssh_run bash -s >"$OUT/06_inventario_modulos.txt" <<'REMOTE'
for d in frontend/src/views frontend/src/components backend/app/api/v1/endpoints \
         backend/app/models backend/app/services backend/app/schemas backend/alembic/versions; do
    echo "===== $d ====="
    ls -la /opt/cyberrit/$d 2>/dev/null | awk '{print $5, $6, $7, $8, $9}'
done
REMOTE

echo
echo "Captura remota completada en $OUT"
wc -l "$OUT"/hashes_remoto.txt "$OUT"/02_listado_mtimes.txt
