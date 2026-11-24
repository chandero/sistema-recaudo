#!/bin/bash
# Fase 3: clasifica cada archivo frente al arbol de produccion.
# Requiere: hashes_remoto.txt, hashes_main.txt, hashes_rama.txt, hashes_working_tree.txt
set -euo pipefail

OUT="$(cd "$(dirname "$0")/../.." && pwd)/auditoria/produccion"
cd "$OUT"

# Convierte "md5  ruta" -> "ruta md5" ordenado por ruta.
normalizar() { awk '{print $2, $1}' "$1" | sort >"$2"; }

normalizar hashes_remoto.txt remoto.norm
normalizar hashes_main.txt main.norm
normalizar hashes_rama.txt rama.norm
normalizar hashes_working_tree.txt wt.norm

RESUMEN="11_resumen_comparacion.csv"
echo "referencia,total_ref,total_prod,identicos,distintos,solo_en_servidor,solo_en_referencia,pct_coincidencia_con_prod" >"$RESUMEN"

TOTAL_PROD=$(wc -l <remoto.norm)

for par in "main:main" "rama:rama" "wt:working_tree_main"; do
    norm="${par%%:*}"
    label="${par##*:}"
    ref="$norm.norm"

    prod_only=$(comm -23 <(awk '{print $1}' remoto.norm) <(awk '{print $1}' "$ref") | wc -l)
    ref_only=$(comm -13 <(awk '{print $1}' remoto.norm) <(awk '{print $1}' "$ref") | wc -l)
    common=$(comm -12 <(awk '{print $1}' remoto.norm) <(awk '{print $1}' "$ref") | wc -l)
    ident=$(join remoto.norm "$ref" | awk '$2==$3' | wc -l)
    dist=$((common - ident))
    total_ref=$(wc -l <"$ref")
    pct=$(awk -v i="$ident" -v t="$TOTAL_PROD" 'BEGIN{printf "%.1f", (t>0? i*100/t : 0)}')
    echo "$label,$total_ref,$TOTAL_PROD,$ident,$dist,$prod_only,$ref_only,$pct" >>"$RESUMEN"

    join remoto.norm "$ref" | awk '$2!=$3 {print $1}' >"11_distintos_${label}.txt"
    comm -23 <(awk '{print $1}' remoto.norm) <(awk '{print $1}' "$ref") >"11_solo_servidor_${label}.txt"
    comm -13 <(awk '{print $1}' remoto.norm) <(awk '{print $1}' "$ref") >"11_solo_referencia_${label}.txt"
done

echo "== RESUMEN =="
column -s, -t "$RESUMEN"
rm -f remoto.norm main.norm rama.norm wt.norm
