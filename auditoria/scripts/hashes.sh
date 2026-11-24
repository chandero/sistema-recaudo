#!/bin/bash
# Generador de hashes identico para el lado remoto y el lado local.
# Uso: hashes.sh <directorio_raiz>
# Imprime en stdout: "<md5>  <ruta/relativa>" ordenado por ruta.
# Se excluyen deliberadamente artefactos que nunca se despliegan como codigo.
set -euo pipefail

RAIZ="${1:?falta el directorio raiz}"

cd "$RAIZ"

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
    -not -path './.worktrees/*' \
    -not -path './auditoria/*' \
    -not -path './.git/*' \
    -not -name 'package-lock.json' \
    -not -name '*.min.js' \
    -print0 \
  | sort -z \
  | xargs -0 md5sum \
  | sed -e 's|\./||'
