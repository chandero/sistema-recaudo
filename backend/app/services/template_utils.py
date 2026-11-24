"""
Utilidades de plantillas DOCX compartidas entre la API y los scripts.

La extracción de variables vive aquí para que el inventario que muestra el
`variables_schema` guardado en base de datos sea idéntico al que valida el
endpoint de reemplazo y al que registra `scripts/registrar_plantillas.py`.
"""
from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List, Optional

# Etiqueta legible de cada variable que los generadores saben resolver.
ETIQUETAS_PLACEHOLDER: Dict[str, str] = {
    "numero_resolucion": "Número de resolución",
    "fecha_resolucion": "Fecha de resolución (AAAA-MM-DD)",
    "fecha_resolucion_larga": "Fecha de resolución en letras",
    "fecha_constancia": "Fecha de la constancia en letras",
    "fecha_pago": "Fecha de pago total (AAAA-MM-DD)",
    "fecha_ejecutoria_larga": "Fecha de ejecutoria en letras",
    "nombre_usuario": "Nombre del contribuyente",
    "documento_usuario": "Identificación del contribuyente",
    "direccion_usuario": "Dirección del contribuyente",
    "cuenta_usuario": "Cuenta / referencia de la obligación",
}

# Variables que no pueden faltar en el DOCX de cada código de plantilla.
VARIABLES_OBLIGATORIAS: Dict[str, List[str]] = {
    "AUTO_ARCHIVO": [
        "numero_resolucion",
        "fecha_resolucion",
        "cuenta_usuario",
        "direccion_usuario",
        "nombre_usuario",
        "documento_usuario",
        "fecha_pago",
    ],
    "CONSTANCIA_SECRETARIAL": [
        "fecha_constancia",
        "numero_resolucion",
        "fecha_resolucion_larga",
        "cuenta_usuario",
        "direccion_usuario",
        "nombre_usuario",
        "documento_usuario",
        "fecha_ejecutoria_larga",
    ],
}

_TAG = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_PARTES = re.compile(r"word/(document|header\d*|footer\d*)\.xml$")


def extraer_placeholders(contenido: bytes) -> List[str]:
    """Devuelve en orden de aparición los {{variable}} del cuerpo y encabezados."""
    texto = ""
    with zipfile.ZipFile(io.BytesIO(contenido)) as archivo:
        for nombre in archivo.namelist():
            if _PARTES.match(nombre):
                # Word suele partir '{{campo}}' en varios runs: el placeholder
                # solo se ve al concatenar el texto plano de los contiguos.
                texto += re.sub(r"<[^>]+>", "", archivo.read(nombre).decode("utf-8", "ignore"))
    hallados: List[str] = []
    for variable in _TAG.findall(texto):
        if variable not in hallados:
            hallados.append(variable)
    return hallados


def construir_schema(placeholders: List[str], fuente: str) -> Dict[str, Any]:
    """Arma el `variables_schema` que consume el frontend."""
    validos = [v for v in placeholders if v in ETIQUETAS_PLACEHOLDER]
    return {
        "variables": validos,
        "etiquetas": {v: ETIQUETAS_PLACEHOLDER[v] for v in validos},
        "desconocidas": [v for v in placeholders if v not in ETIQUETAS_PLACEHOLDER],
        "fuente": fuente,
    }


def validar_plantilla(contenido: bytes, code: Optional[str] = None) -> List[str]:
    """Comprueba que el binario es un DOCX editable con sus variables.

    Devuelve la lista de placeholders detectados. Lanza `ValueError` con un
    mensaje legible para el funcionario cuando el archivo no sirve.
    """
    if not contenido:
        raise ValueError("el archivo está vacío")
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as archivo:
            partes = archivo.namelist()
    except zipfile.BadZipFile as exc:
        raise ValueError("el archivo no es un DOCX válido (paquete Office 2007)") from exc
    if "word/document.xml" not in partes:
        raise ValueError("el DOCX no tiene word/document.xml; no es un documento de Word")

    placeholders = extraer_placeholders(contenido)
    if not placeholders:
        raise ValueError(
            "la plantilla no contiene variables {{...}}: se imprimiría igual para "
            "todos los casos y conservaría los datos del archivo original"
        )
    faltantes = [v for v in VARIABLES_OBLIGATORIAS.get(code or "", []) if v not in placeholders]
    if faltantes:
        raise ValueError(
            "faltan variables requeridas para esta plantilla: " + ", ".join(faltantes)
        )
    return placeholders
