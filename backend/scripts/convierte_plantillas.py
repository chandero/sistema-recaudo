"""
Convierte los formatos oficiales de la Alcaldía de Girón (con datos reales
diligenciados) en plantillas editables para docxtpl.

La sustitución se hace sobre word/document.xml localizando el texto visible
de cada <w:t>. Cuando Word partió un valor en varios runs, los trozos se
unen escribiendo el placeholder en el primer run y vaciando los siguientes,
de modo que el formato del primer run (fuente, negrita, tamaño) se conserva.
Solo usa la librería estándar para poder ejecutarse en el host o en el
contenedor sin dependencias extra.

Uso:
    python3 scripts/convierte_plantillas.py [directorio_de_originales]

Los originales se buscan por nombre; si no existen, el script informa y
continúa con los planes que sí tenga disponibles.
"""
from __future__ import annotations

import os
import re
import sys
import zipfile
from typing import Dict, List, Tuple

# (texto_busqueda, placeholder, ocurrencias_esperadas)
Reemplazo = Tuple[str, str, int]

# Mismo destino que UPLOAD_DIR en app/api/v1/endpoints/documents.py,
# relativo a la raíz de backend/ donde corre uvicorn.
PLANTILLA_DESTINO = os.path.join("app", "uploads", "templates")

PLANES: Dict[str, Dict[str, object]] = {
    "auto_de_archivo_original.docx": {
        "destino": os.path.join(PLANTILLA_DESTINO, "1_auto_de_archivo.docx"),
        "codigo": "AUTO_ARCHIVO",
        "reemplazos": [
            ("0447", "{{numero_resolucion}}", 1),
            ("2025-03-04", "{{fecha_resolucion}}", 1),
            ("000000", "{{cuenta_usuario}}", 1),
            ("CLL 35 18 57 RINCON DE GIRON", "{{direccion_usuario}}", 1),
            ("MARLENY BARRERA BARON", "{{nombre_usuario}}", 2),
            ("30208284", "{{documento_usuario}}", 2),
            ("2024-12-19", "{{fecha_pago}}", 1),
        ],
    },
    "constancia_secretarial_original.docx": {
        "destino": os.path.join(PLANTILLA_DESTINO, "1_constancia_secretarial.docx"),
        "codigo": "CONSTANCIA_SECRETARIAL",
        "reemplazos": [
            ("08 de mayo de 2025", "{{fecha_constancia}}", 1),
            ("1886", "{{numero_resolucion}}", 2),
            ("09 de Abril de 2025", "{{fecha_resolucion_larga}}", 2),
            ("000000", "{{cuenta_usuario}}", 2),
            ("C 68 32 09 LO 18 MZ O CONJ RES LA", "{{direccion_usuario}}", 2),
            ("YAEZ PEREZ ALCIDES", "{{nombre_usuario}}", 2),
            ("5529239", "{{documento_usuario}}", 2),
            ("18 de Junio de 2025", "{{fecha_ejecutoria_larga}}", 1),
        ],
    },
}

_ETIQUETA_TEXTO = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)


def _tramos_texto(xml: str) -> List[Tuple[int, int]]:
    """Posiciones [inicio, fin) del texto dentro de cada <w:t>."""
    return [(m.start(1), m.end(1)) for m in _ETIQUETA_TEXTO.finditer(xml)]


def _texto_visible(xml: str, tramos: List[Tuple[int, int]]) -> str:
    return "".join(xml[inicio:fin] for inicio, fin in tramos)


def _reconstruir(
    xml: str,
    tramos: List[Tuple[int, int]],
    nuevos_contenidos: Dict[int, str],
) -> str:
    """Reescribe el XML sustituyendo solo el contenido de los runs indicados."""
    partes: List[str] = []
    cursor = 0
    for indice, (inicio, fin) in enumerate(tramos):
        partes.append(xml[cursor:inicio])
        partes.append(nuevos_contenidos.get(indice, xml[inicio:fin]))
        cursor = fin
    partes.append(xml[cursor:])
    return "".join(partes)


def _aplicar_reemplazo(xml: str, busqueda: str, placeholder: str) -> Tuple[str, bool]:
    """Sustituye la primera aparición de la búsqueda, uniendo runs si hace falta."""
    tramos = _tramos_texto(xml)
    texto = _texto_visible(xml, tramos)
    posicion = texto.find(busqueda)
    if posicion < 0:
        return xml, False

    fin_buscado = posicion + len(busqueda)
    nuevos: Dict[int, str] = {}
    acumulado = 0
    for indice, (inicio, fin) in enumerate(tramos):
        # El run ocupa [run_inicio, run_fin) dentro del texto visible acumulado,
        # que es donde se buscó el valor, no dentro del XML.
        longitud = fin - inicio
        run_inicio = acumulado
        run_fin = acumulado + longitud
        acumulado = run_fin
        if run_fin <= posicion or run_inicio >= fin_buscado:
            continue
        contenido = xml[inicio:fin]
        corte_ini = max(posicion - run_inicio, 0)
        corte_fin = min(fin_buscado - run_inicio, longitud)
        prefijo = contenido[:corte_ini]
        sufijo = contenido[corte_fin:]
        if run_inicio <= posicion:
            # Primer run afectado: aquí queda el placeholder, con su formato.
            nuevos[indice] = f"{prefijo}{placeholder}{sufijo}"
        else:
            # Runs posteriores: se borra el trozo cubierto, se conserva el resto.
            nuevos[indice] = sufijo
    return _reconstruir(xml, tramos, nuevos), True


def convertir(origen: str, destino: str, reemplazos: List[Reemplazo]) -> Dict[str, int]:
    """Aplica el plan de reemplazos y escribe la plantilla resultante."""
    with zipfile.ZipFile(origen) as archivo:
        xml = archivo.read("word/document.xml").decode("utf-8")
        informacion = [
            (item, archivo.getinfo(item.filename), archivo.read(item.filename))
            for item in archivo.infolist()
        ]

    resumen: Dict[str, int] = {}
    for busqueda, placeholder, esperadas in reemplazos:
        aplicadas = 0
        for _ in range(esperadas):
            xml, ok = _aplicar_reemplazo(xml, busqueda, placeholder)
            if not ok:
                break
            aplicadas += 1
        if aplicadas != esperadas:
            raise RuntimeError(
                f"{os.path.basename(origen)}: se esperaban {esperadas} apariciones "
                f"de {busqueda!r} y se encontraron {aplicadas}"
            )
        resumen[placeholder] = aplicadas

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as salida:
        for item, info, datos in informacion:
            if item.filename == "word/document.xml":
                datos = xml.encode("utf-8")
            salida.writestr(info, datos)
    return resumen


def main(originales: str) -> int:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Los originales suelen entregarse fuera de backend/; se acepta ruta
    # absoluta, relativa al punto de llamada o relativa a la raíz del repo.
    candidatos = [
        os.path.abspath(originales),
        os.path.join(ruta_base, originales),
        os.path.join(os.path.dirname(ruta_base), originales),
    ]
    origen_dir = next((c for c in candidatos if os.path.isdir(c)), candidatos[0])
    os.chdir(ruta_base)

    error = False
    for nombre, plan in PLANES.items():
        origen = os.path.join(origen_dir, nombre)
        if not os.path.exists(origen):
            print(f"[OMITIDO] no existe el original {origen}")
            error = True
            continue
        try:
            resumen = convertir(origen, str(plan["destino"]), list(plan["reemplazos"]))
        except RuntimeError as exc:
            print(f"[ERROR] {exc}")
            error = True
            continue
        print(f"[OK] {nombre} -> {plan['destino']}")
        for placeholder, veces in resumen.items():
            print(f"      {placeholder}: {veces}")
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "plantillas_nuevas"))
