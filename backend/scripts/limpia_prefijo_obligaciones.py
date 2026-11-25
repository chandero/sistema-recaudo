#!/usr/bin/env python3
"""
Quita el prefijo "Importación de cartera - " del número de las obligaciones.

El importador guardaba cada obligación con la descripción
"Importación de cartera - <número>". Ese texto ya no se escribe (hoy la
descripción es el número, o el concepto del archivo si el CSV lo trae), pero las
filas cargadas antes de la corrección lo conservan. La descripción es lo que la
aplicación muestra como número de obligación y lo que se imprime como
"cuenta" en el Auto de Archivo y en la Constancia Secretarial: el prefijo llega,
por tanto, a documentos oficiales.

La utilidad no inventa ni destruye datos: solo recorta el prefijo. Si al quitarlo
una fila se quedaría sin valor, se informa en lugar de dejar la descripción
vacía. Es idempotente, así que puede ejecutarse más de una vez.

Sin --aplicar solo muestra lo que haría (vista previa). Con --aplicar escribe y
deja además un respaldo JSON con (id, antes, después) para revertir fila a fila.

Uso dentro del contenedor del backend (working dir /app):
    docker exec -w /app cartera_backend python scripts/limpia_prefijo_obligaciones.py
    docker exec -w /app cartera_backend python scripts/limpia_prefijo_obligaciones.py --aplicar

Fuera del contenedor, desde backend/:
    python scripts/limpia_prefijo_obligaciones.py --aplicar
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

# Acepta las variantes de espaciado, guion y tilde que pudo dejar el importador.
_PREFIJO = re.compile(r"^\s*Importaci[oó]n\s+de\s+cartera\s*-{1,2}\s*", re.IGNORECASE)

RESPALDO_POR_DEFECTO = "respaldo_prefijo_obligaciones.json"
MUESTRA_EN_PANTALLA = 5


def lleva_prefijo(valor: str | None) -> bool:
    """True si la descripción empieza con el prefijo del importador."""
    return bool(valor) and bool(_PREFIJO.match(valor))


def recortar_prefijo(valor: str | None) -> str | None:
    """Descripción sin el prefijo, o None si no lleva prefijo que recortar."""
    if not lleva_prefijo(valor):
        return None
    return _PREFIJO.sub("", valor).strip()


def planificar_cambios(filas) -> tuple[list[tuple[str, int]], list[int]]:
    """(cambios, anomalias) a partir de pares (id, description).

    Cada cambio es (nuevo_valor, id). Se consideran anomalías las filas cuyo
    único contenido era el prefijo: recortarlas dejaría la descripción vacía,
    así que no se tocan y se reportan para decidir caso por caso.
    """
    cambios: list[tuple[str, int]] = []
    anomalias: list[int] = []
    for identificador, valor in filas:
        if not lleva_prefijo(valor):
            continue
        nuevo = recortar_prefijo(valor)
        if nuevo:
            cambios.append((nuevo, identificador))
        else:
            anomalias.append(identificador)
    return cambios, anomalias


def ruta_de_la_base(motor) -> str:
    """Identificador de la base que se va a tocar, para verificar antes de escribir."""
    return str(motor.url)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="Escribe los cambios (por defecto solo vista previa)")
    parser.add_argument("--respaldo", default=RESPALDO_POR_DEFECTO, help="Archivo JSON con los valores originales")
    args = parser.parse_args()

    from app.core.database import engine

    print(f"Base de datos objetivo: {ruta_de_la_base(engine)}")
    if not os.path.isfile(_ruta_de_archivo(engine)):
        print("  Advertencia: ese archivo de base de datos no existe; revise desde dónde se ejecuta.")

    with engine.connect() as conexion:
        filas = conexion.execute(
            text("SELECT id, description FROM obligations ORDER BY id")
        ).fetchall()
        total = conexion.execute(text("SELECT COUNT(*) FROM obligations")).scalar()

    cambios, anomalias = planificar_cambios(filas)
    originales = {identificador: valor for identificador, valor in filas}
    print(f"Obligaciones en la base: {total}")
    print(f"Con el prefijo 'Importación de cartera - ': {len(cambios) + len(anomalias)}")
    print(f"Sin cambios necesarios: {total - len(cambios) - len(anomalias)}")

    for nuevo, identificador in cambios[:MUESTRA_EN_PANTALLA]:
        print(f"  id {identificador}: '{originales[identificador]}' -> '{nuevo}'")
    if len(cambios) > MUESTRA_EN_PANTALLA:
        print(f"  ... y {len(cambios) - MUESTRA_EN_PANTALLA} más")
    if anomalias:
        print(f"  Anomalías (quedarían vacías, no se tocan): ids {anomalias[:20]}")

    if not cambios:
        print("No hay nada que corregir.")
        return 0

    if not args.aplicar:
        print("\nVista previa: no se escribió nada. Repita con --aplicar para ejecutar.")
        return 0

    # El respaldo se escribe antes de tocar la base: si el UPDATE falla a mitad,
    # los valores originales siguen disponibles en el archivo.
    respaldo = {
        "generado": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "base": ruta_de_la_base(engine),
        "cambios": [
            {"id": identificador, "antes": originales[identificador], "despues": nuevo}
            for nuevo, identificador in cambios
        ],
    }
    with open(args.respaldo, "w", encoding="utf-8") as archivo:
        json.dump(respaldo, archivo, ensure_ascii=False, indent=2)
    print(f"\nRespaldo de valores originales en: {os.path.abspath(args.respaldo)}")

    # updated_at se deja intacto a propósito: es una normalización de texto, no
    # una edición del funcionario, y no debe parecer que 1417 casos cambiaron hoy.
    with engine.begin() as conexion:
        conexion.execute(
            text("UPDATE obligations SET description = :nuevo WHERE id = :id"),
            [{"nuevo": nuevo, "id": identificador} for nuevo, identificador in cambios],
        )

    with engine.connect() as conexion:
        restantes = conexion.execute(
            text("SELECT id, description FROM obligations")
        ).fetchall()

    pendientes = [identificador for identificador, valor in restantes if lleva_prefijo(valor)]
    if pendientes:
        print(f"FALTA: {len(pendientes)} obligaciones siguen con el prefijo (ids {pendientes[:20]})")
        return 1

    print(f"Corregidas {len(cambios)} obligaciones. Ninguna conserva el prefijo.")
    return 0


def _ruta_de_archivo(motor) -> str:
    """Ruta del archivo SQLite, vacía si la URL no es de SQLite."""
    url = str(motor.url)
    for prefijo in ("sqlite+pysqlite:///", "sqlite:///"):
        if url.startswith(prefijo):
            return url[len(prefijo):]
    return url


if __name__ == "__main__":
    raise SystemExit(main())
