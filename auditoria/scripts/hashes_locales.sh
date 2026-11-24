#!/bin/bash
# Fase 2: genera los arboles de hashes de las referencias locales comparables.
set -euo pipefail

PROYECTO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$PROYECTO/auditoria/produccion"
WT="$PROYECTO/.worktrees"
HASHES="$PROYECTO/auditoria/scripts/hashes.sh"

cd "$PROYECTO"

echo "[1/4] fetch de todas las ramas y tags"
git fetch --all --tags --prune

echo "[2/4] estado del repositorio"
{
    echo "HEAD=$(git rev-parse --short HEAD) rama=$(git rev-parse --abbrev-ref HEAD)"
    echo "origin/main=$(git rev-parse --short origin/main)"
    echo "origin/refactor/ajuste-global-reglas=$(git rev-parse --short origin/refactor/ajuste-global-reglas)"
    echo "working_tree_sucio=$(git status --porcelain | wc -l) entradas"
    echo "ramas_remotas:"
    git ls-remote --heads origin
    echo "tags:"
    git ls-remote --tags origin | wc -l
} >"$OUT/10_estado_local.txt"
cat "$OUT/10_estado_local.txt"

echo "[3/4] worktrees desanexados"
mkdir -p "$WT"
rm -rf "$WT/main" "$WT/rama"
git worktree add --detach "$WT/main" main >/dev/null
git worktree add --detach "$WT/rama" origin/refactor/ajuste-global-reglas >/dev/null

echo "[4/4] hashes de cada referencia"
bash "$HASHES" "$WT/main" >"$OUT/hashes_main.txt"
bash "$HASHES" "$WT/rama" >"$OUT/hashes_rama.txt"
bash "$HASHES" "$PROYECTO" >"$OUT/hashes_working_tree.txt"

wc -l "$OUT/hashes_main.txt" "$OUT/hashes_rama.txt" "$OUT/hashes_working_tree.txt" "$OUT/hashes_remoto.txt"
