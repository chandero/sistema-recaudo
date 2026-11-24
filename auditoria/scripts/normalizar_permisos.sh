#!/usr/bin/env bash
# Normaliza permisos tras el volcado desde el servidor: el servidor conserva modos
# 755 heredados de rsync/chmod -R y git registraria falsos cambios de modo.
# Regla: respetar el modo que ya tenia el archivo en git; los archivos nuevos seran
# 644 salvo que comiencen con shebang (entonces 755).
set -euo pipefail
cd "$(dirname "$0")/../.."

git diff --raw | while IFS= read -r linea; do
    old=$(printf '%s' "$linea" | awk '{print $1}' | tr -d ':')
    path=$(printf '%s' "$linea" | awk -F'\t' '{print $2}')
    [ -n "$path" ] && [ -f "$path" ] || continue
    case "$old" in
        100755) chmod 755 "$path" ;;
        100644) chmod 644 "$path" ;;
    esac
done

git ls-files --others --exclude-standard | while IFS= read -r path; do
    [ -f "$path" ] || continue
    if [ "$(head -c 2 "$path")" = '#!' ]; then chmod 755 "$path"; else chmod 644 "$path"; fi
done

echo "archivos aun con cambio de modo: $(git diff --raw | awk '$2!=$3' | wc -l)"
