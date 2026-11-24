#!/bin/bash
# Fase 4: construye la rama baseline/produccion-20261124 replicando el codigo del servidor.
# Fuente: auditoria/produccion/copia_servidor (obtenida por rsync de solo lectura).
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$RAIZ/auditoria/produccion/copia_servidor"
RAMA="baseline/produccion-20261124"
BASE="origin/refactor/ajuste-global-reglas"

cd "$RAIZ"

[ -d "$SRC" ] || { echo "falta la copia del servidor en $SRC"; exit 1; }

echo "[1/4] rama nueva desde $BASE"
git checkout -q --detach "$BASE"
git checkout -q -b "$RAMA" 2>/dev/null || { git checkout -q "$RAMA"; git reset -q --hard "$BASE"; }

echo "[2/4] .gitignore cubre datos, artefactos y la copia de auditoria"
if ! grep -q '^generados/' .gitignore; then
    printf '\n# Artefactos generados en servidor y auxiliar\ngenerados/\n.worktrees/\nauditoria/produccion/copia_servidor/\n' >>.gitignore
fi

echo "[3/4] volcar el codigo de produccion sobre el arbol de trabajo"
# --delete en el codigo para que la rama refleje exactamente el servidor;
# uploads se sincroniza sin borrado para no destruir plantillas locales.
for area in backend frontend scripts alembic; do
    [ -e "$SRC/$area" ] || continue
    case "$area" in
        backend|frontend)
            rsync -a --delete \
                --exclude='app/uploads/***' \
                --exclude='uploads/***' \
                --exclude='node_modules/' --exclude='dist/' --exclude='__pycache__/' \
                --exclude='*.pyc' --exclude='logs/' --exclude='*.db' --exclude='backups/' \
                "$SRC/$area/" "$area/"
            ;;
        *)
            rsync -a --delete "$SRC/$area/" "$area/"
            ;;
    esac
done

# Plantillas subidas: solo anadir las que faltan, nunca borrar las locales.
if [ -d "$SRC/backend/app/uploads" ]; then
    mkdir -p backend/app/uploads
    rsync -a --ignore-existing "$SRC/backend/app/uploads/" "backend/app/uploads/"
fi

# Raiz: scripts de despliegue, configs nginx, compose, docs. .env NO se copia (secretos).
for f in "$SRC"/*; do
    base="$(basename "$f")"
    case "$base" in
        backend|frontend|scripts|node_modules|dist|.env|.last_update|generados|backups) continue ;;
    esac
    cp -a "$f" "$RAIZ/$base"
done
for f in .env.example .qwenrules; do
    [ -f "$SRC/$f" ] && cp -a "$SRC/$f" "$RAIZ/$f"
done
[ -d "$SRC/.lingma" ] && rsync -a "$SRC/.lingma/" ".lingma/"

echo "[4/4] estado resultante"
git status --short | head -40
echo "total cambios: $(git status --porcelain | wc -l)"
