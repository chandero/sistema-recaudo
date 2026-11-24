#!/bin/bash
# Genera diffs unificados entre cada referencia local y la copia del servidor.
# Salida: auditoria/produccion/diffs/<ref>__<ruta_con_slash_doble>.diff
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$RAIZ/auditoria/produccion"
SRC="$OUT/copia_servidor"
DIFFS="$OUT/diffs"
mkdir -p "$DIFFS"
rm -f "$DIFFS"/*.diff

generar() {
    local etiqueta="$1" lista="$2" base="$3" n=0 vacias=0
    while IFS= read -r ruta; do
        [ -z "$ruta" ] && continue
        local destino="$DIFFS/${etiqueta}__${ruta//\//__}.diff"
        if [ ! -f "$base/$ruta" ]; then
            echo "(no existe en $etiqueta) --- $ruta" >"$destino"
            vacias=$((vacias + 1))
            continue
        fi
        if diff -u --label "$etiqueta/$ruta" --label "produccion/$ruta" \
                "$base/$ruta" "$SRC/$ruta" >"$destino"; then
            rm -f "$destino"
            continue
        fi
        n=$((n + 1))
    done <"$lista"
    echo "$etiqueta: $n diffs generados, $vacias archivos ausentes en la referencia"
}

generar "rama" "$OUT/11_distintos_rama.txt" "$RAIZ/.worktrees/rama"
generar "main" "$OUT/11_distintos_main.txt" "$RAIZ/.worktrees/main"

ls "$DIFFS" | wc -l
