#!/usr/bin/env python3
"""Compara las rutas API que responde el backend en produccion contra las rutas que
declaran las referencias locales (main y refactor/ajuste-global-reglas).

Las rutas locales se derivan por analisis estatico de app/api/v1/api.py (include_router)
y de los decoradores @router.* de cada modulo de endpoints, sin importar la aplicacion.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(sys.argv[1])
OUT = RAIZ / "auditoria/produccion"
BASE_API = "/api/v1"
DECORADOR = re.compile(r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']')
INCLUYE = re.compile(r'include_router\(\s*(\w+)\.router[^)]*prefix=["\']([^"\']*)["\']')


def rutas_ref(rel_ref: str):
    raiz = RAIZ / rel_ref / "backend" / "app" / "api" / "v1"
    api_py = raiz / "api.py"
    if not api_py.exists():
        return None
    rutas = set()
    for modulo, prefijo in INCLUYE.findall(api_py.read_text(encoding="utf-8", errors="ignore")):
        ep = raiz / "endpoints" / f"{modulo}.py"
        if not ep.exists():
            continue
        for _, path in DECORADOR.findall(ep.read_text(encoding="utf-8", errors="ignore")):
            rutas.add((BASE_API + prefijo + path).replace("//", "/") or "/")
    return rutas


def normalizar(p: str) -> str:
    """Unifica nombres de parametro {xxx_id} para poder comparar."""
    return re.sub(r"\{[^}]+\}", "{}", p)


with open(OUT / "04_openapi_prod.json", encoding="utf-8") as fh:
    prod = set(json.load(fh).get("paths", {}).keys())

prod_norm = {normalizar(p): p for p in prod}
lineas = [f"rutas declaradas en produccion: {len(prod)}", ""]

for etiqueta, rel in (("main", ".worktrees/main"), ("rama", ".worktrees/rama")):
    local = rutas_ref(rel)
    if local is None:
        lineas.append(f"[{etiqueta}] no se encontro backend/app/api/v1/api.py")
        continue
    local_norm = {normalizar(p) for p in local}
    solo_prod = sorted(set(prod_norm) - local_norm)
    solo_local = sorted(local_norm - set(prod_norm))
    lineas += [
        f"[{etiqueta}] rutas declaradas localmente: {len(local)}",
        f"  solo en produccion ({len(solo_prod)}):",
    ]
    lineas += [f"    {prod_norm[p]}" for p in solo_prod]
    lineas += [f"  solo en la referencia local ({len(solo_local)}):"]
    lineas += [f"    {p}" for p in solo_local]
    lineas.append("")

(OUT / "12_rutas_api_prod_vs_local.txt").write_text("\n".join(lineas), encoding="utf-8")
print("\n".join(lineas[:1] + lineas[2:9]))
print("...")
print("detalle completo en auditoria/produccion/12_rutas_api_prod_vs_local.txt")
